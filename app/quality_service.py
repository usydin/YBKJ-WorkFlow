from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from app.config import (
    APP_INFO,
    QUALITY_REPORTS_DIR,
    ensure_runtime_directories,
    is_reserved_person_name,
    split_worker_names_text,
    to_relative_source_path,
)
from app.database import SQLiteDataPool


QUALITY_RULE_VERSION = "V0.2-flow-check"
SEVERITY_ORDER = {"严重": 0, "关注": 1, "提示": 2}
SEVERITY_WEIGHT = {"严重": 3, "关注": 2, "提示": 1}


class QualityCheckService:
    def __init__(
        self,
        data_pool: SQLiteDataPool,
        output_dir: Path | None = None,
    ) -> None:
        self.data_pool = data_pool
        self.output_dir = output_dir or QUALITY_REPORTS_DIR
        self.logger = logging.getLogger("ybkj_workflow.quality")

    def run_check(self) -> dict[str, Any]:
        with self.data_pool._connect() as connection:
            raw_input_summary = self._collect_raw_input_summary(connection)
            parsed_record_summary = self._collect_parsed_record_summary(connection)
            employee_mapping_summary = self._collect_employee_mapping_summary(connection)
            export_readiness_summary = self._collect_export_readiness_summary(connection)

        issues = self._build_issues(
            raw_input_summary,
            parsed_record_summary,
            employee_mapping_summary,
            export_readiness_summary,
        )
        conclusion = self._build_conclusion(
            issues,
            raw_input_summary,
            parsed_record_summary,
            export_readiness_summary,
        )
        checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            "checked_at": checked_at,
            "rule_version": QUALITY_RULE_VERSION,
            "data_source": "SQLite / raw_inputs, parsed_records, employee_aliases",
            "raw_inputs": raw_input_summary,
            "parsed_records": parsed_record_summary,
            "employee_mapping": employee_mapping_summary,
            "export_readiness": export_readiness_summary,
            "issues": issues,
            "conclusion": conclusion,
        }
        self.logger.info(
            "Quality check completed: level=%s issues=%s confirmed=%s pending=%s",
            conclusion["level"],
            len(issues),
            parsed_record_summary["confirmed_count"],
            parsed_record_summary["pending_count"],
        )
        return result

    def export_markdown(self, result: dict[str, Any]) -> Path:
        ensure_runtime_directories()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        target_path = self.output_dir / f"quality_check_{timestamp}.md"
        with target_path.open("w", encoding="utf-8") as markdown_file:
            markdown_file.write(self._build_markdown(result, target_path))
        self.logger.info(
            "Quality markdown exported: path=%s level=%s",
            target_path.as_posix(),
            result.get("conclusion", {}).get("level", ""),
        )
        return target_path

    def _collect_raw_input_summary(self, connection) -> dict[str, int]:
        total_count = self._fetch_count(connection, "SELECT COUNT(*) FROM raw_inputs")
        unparsed_count = self._fetch_count(
            connection,
            "SELECT COUNT(*) FROM raw_inputs WHERE status = 'pending_parse'",
        )
        parsed_count = self._fetch_count(
            connection,
            "SELECT COUNT(*) FROM raw_inputs WHERE status = 'parsed'",
        )
        empty_text_count = self._fetch_count(
            connection,
            "SELECT COUNT(*) FROM raw_inputs WHERE TRIM(raw_text) = ''",
        )
        duplicate_text_count = self._fetch_count(
            connection,
            """
            SELECT COALESCE(SUM(group_count - 1), 0)
            FROM (
                SELECT COUNT(*) AS group_count
                FROM raw_inputs
                WHERE TRIM(raw_text) <> ''
                GROUP BY TRIM(raw_text)
                HAVING COUNT(*) > 1
            )
            """,
        )
        return {
            "total_count": total_count,
            "unparsed_count": unparsed_count,
            "parsed_count": parsed_count,
            "empty_text_count": empty_text_count,
            "duplicate_text_count": duplicate_text_count,
        }

    def _collect_parsed_record_summary(self, connection) -> dict[str, int]:
        total_count = self._fetch_count(connection, "SELECT COUNT(*) FROM parsed_records")
        pending_count = self._fetch_count(
            connection,
            "SELECT COUNT(*) FROM parsed_records WHERE confirm_status = 'pending'",
        )
        confirmed_count = self._fetch_count(
            connection,
            "SELECT COUNT(*) FROM parsed_records WHERE confirm_status = 'confirmed'",
        )
        missing_date_count = self._fetch_count(
            connection,
            "SELECT COUNT(*) FROM parsed_records WHERE TRIM(work_date) = ''",
        )
        missing_project_or_content_count = self._fetch_count(
            connection,
            """
            SELECT COUNT(*)
            FROM parsed_records
            WHERE TRIM(project) = ''
               OR (
                    TRIM(problem_description) = ''
                AND TRIM(solution) = ''
                AND TRIM(device_or_part) = ''
               )
            """,
        )
        missing_system_category_count = self._fetch_count(
            connection,
            "SELECT COUNT(*) FROM parsed_records WHERE TRIM(system_category) = ''",
        )
        missing_work_type_count = self._fetch_count(
            connection,
            "SELECT COUNT(*) FROM parsed_records WHERE TRIM(work_type) = ''",
        )
        missing_worker_count = self._fetch_count(
            connection,
            "SELECT COUNT(*) FROM parsed_records WHERE TRIM(worker_names) = ''",
        )
        worker_confirm_required_count = self._fetch_count(
            connection,
            "SELECT COUNT(*) FROM parsed_records WHERE employee_confirm_required = 1",
        )
        reserved_name_in_worker_count = self._count_reserved_name_in_worker_field(connection)
        return {
            "total_count": total_count,
            "pending_count": pending_count,
            "confirmed_count": confirmed_count,
            "missing_date_count": missing_date_count,
            "missing_project_or_content_count": missing_project_or_content_count,
            "missing_system_category_count": missing_system_category_count,
            "missing_work_type_count": missing_work_type_count,
            "missing_worker_count": missing_worker_count,
            "worker_confirm_required_count": worker_confirm_required_count,
            "reserved_name_in_worker_count": reserved_name_in_worker_count,
        }

    def _collect_employee_mapping_summary(self, connection) -> dict[str, int]:
        rows = connection.execute(
            """
            SELECT real_name, wechat_nickname, alias, is_active
            FROM employee_aliases
            """
        ).fetchall()

        all_employees: set[str] = set()
        enabled_employees: set[str] = set()
        active_name_lookup: set[str] = set()
        alias_tokens: set[str] = set()
        conflict_buckets: dict[str, set[str]] = {}

        for row in rows:
            real_name = str(row["real_name"] or "").strip()
            if real_name:
                all_employees.add(real_name)
            if bool(row["is_active"]) and real_name:
                enabled_employees.add(real_name)
                active_name_lookup.add(real_name.casefold())

            for raw_token in (row["wechat_nickname"], row["alias"]):
                token = str(raw_token or "").strip()
                if not token:
                    continue
                alias_tokens.add(token)
                conflict_buckets.setdefault(token.casefold(), set()).add(real_name or "未命名员工")
                if bool(row["is_active"]):
                    active_name_lookup.add(token.casefold())

        disabled_employees = all_employees - enabled_employees
        unresolved_alias_count = self._count_unresolved_aliases(connection, active_name_lookup)
        conflict_count = sum(
            1
            for real_names in conflict_buckets.values()
            if len({name for name in real_names if name}) > 1
        )

        return {
            "employee_total_count": len(all_employees),
            "alias_total_count": len(alias_tokens),
            "unresolved_alias_count": unresolved_alias_count,
            "conflict_count": conflict_count,
            "enabled_employee_count": len(enabled_employees),
            "disabled_employee_count": len(disabled_employees),
        }

    def _collect_export_readiness_summary(self, connection) -> dict[str, int]:
        confirmed_dates = connection.execute(
            """
            SELECT work_date
            FROM parsed_records
            WHERE confirm_status = 'confirmed'
            """
        ).fetchall()

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        today_count = 0
        week_count = 0
        month_count = 0

        for row in confirmed_dates:
            parsed_date = self._parse_work_date(str(row["work_date"] or ""))
            if parsed_date is None:
                continue
            if parsed_date == today:
                today_count += 1
            if parsed_date >= week_start:
                week_count += 1
            if parsed_date >= month_start:
                month_count += 1

        confirmed_count = self._fetch_count(
            connection,
            "SELECT COUNT(*) FROM parsed_records WHERE confirm_status = 'confirmed'",
        )
        return {
            "report_ready_count": confirmed_count,
            "excel_ready_count": confirmed_count,
            "today_count": today_count,
            "week_count": week_count,
            "month_count": month_count,
        }

    def _build_issues(
        self,
        raw_inputs: dict[str, int],
        parsed_records: dict[str, int],
        employee_mapping: dict[str, int],
        export_readiness: dict[str, int],
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []

        self._append_issue(
            issues,
            level="关注",
            issue_type="原始输入",
            count=raw_inputs["unparsed_count"],
            description="存在未解析的原始输入记录",
            action="进入“智能解析”页执行解析，确认 raw_inputs 已转入 parsed_records。",
        )
        self._append_issue(
            issues,
            level="严重",
            issue_type="原始输入",
            count=raw_inputs["empty_text_count"],
            description="存在空文本原始输入",
            action="回查录入来源，避免提交空白文本。",
        )
        self._append_issue(
            issues,
            level="关注",
            issue_type="原始输入",
            count=raw_inputs["duplicate_text_count"],
            description="存在重复原始文本",
            action="建议核对重复录入，避免同一条工作记录被重复解析。",
        )

        self._append_issue(
            issues,
            level="关注",
            issue_type="解析记录",
            count=parsed_records["pending_count"],
            description="存在待确认解析记录",
            action="进入“人工确认”页核对并流转状态。",
        )
        self._append_issue(
            issues,
            level="严重",
            issue_type="解析记录",
            count=parsed_records["missing_date_count"],
            description="存在缺少日期的解析记录",
            action="建议补全 work_date，避免影响按日统计和日报筛选。",
        )
        self._append_issue(
            issues,
            level="关注",
            issue_type="解析记录",
            count=parsed_records["missing_project_or_content_count"],
            description="存在缺少项目或工作内容的解析记录",
            action="补全项目、问题描述或设备部位，提升日报可读性。",
        )
        self._append_issue(
            issues,
            level="关注",
            issue_type="解析记录",
            count=parsed_records["missing_system_category_count"],
            description="存在缺少系统类别的解析记录",
            action="检查解析规则或在人工确认页补全系统类别。",
        )
        self._append_issue(
            issues,
            level="关注",
            issue_type="解析记录",
            count=parsed_records["missing_work_type_count"],
            description="存在缺少工作类型的解析记录",
            action="补全工作类型，避免统计口径失真。",
        )
        self._append_issue(
            issues,
            level="严重",
            issue_type="解析记录",
            count=parsed_records["missing_worker_count"],
            description="存在缺少维修人员的解析记录",
            action="建议进入人工确认页补全维修人员。",
        )
        self._append_issue(
            issues,
            level="关注",
            issue_type="解析记录",
            count=parsed_records["worker_confirm_required_count"],
            description="存在维修人员待人工确认记录",
            action="优先检查员工映射并使用“重新映射人员”或手工修正。",
        )
        self._append_issue(
            issues,
            level="严重",
            issue_type="解析记录",
            count=parsed_records["reserved_name_in_worker_count"],
            description=f"保留名 {APP_INFO.developer} 误入维修人员字段",
            action="请检查解析规则和人工修正逻辑，避免保留名写入 worker_names。",
        )

        self._append_issue(
            issues,
            level="关注",
            issue_type="员工映射",
            count=employee_mapping["unresolved_alias_count"],
            description="存在未解析别名或网名",
            action="在员工映射页补充微信网名/别名与真实姓名映射。",
        )
        self._append_issue(
            issues,
            level="严重",
            issue_type="员工映射",
            count=employee_mapping["conflict_count"],
            description="存在一对多疑似映射冲突",
            action="检查是否有同一别名映射到多个真实姓名，统一口径后再解析。",
        )

        if export_readiness["report_ready_count"] > 0:
            self._append_issue(
                issues,
                level="提示",
                issue_type="导出准备",
                count=export_readiness["report_ready_count"],
                description="当前已有可用于日报和 Excel 导出的已确认记录",
                action="可继续生成日报和导出 Excel 报表。",
            )
        else:
            self._append_issue(
                issues,
                level="关注",
                issue_type="导出准备",
                count=1,
                description="当前没有可用于日报和 Excel 导出的已确认记录",
                action="请先完成智能解析和人工确认闭环。",
            )

        issues.sort(
            key=lambda item: (
                SEVERITY_ORDER.get(str(item["level"]), 99),
                -int(item["count"]),
                str(item["type"]),
            )
        )
        return issues

    def _build_conclusion(
        self,
        issues: list[dict[str, Any]],
        raw_inputs: dict[str, int],
        parsed_records: dict[str, int],
        export_readiness: dict[str, int],
    ) -> dict[str, Any]:
        critical_count = sum(1 for item in issues if item["level"] == "严重")
        warning_count = sum(1 for item in issues if item["level"] == "关注")
        score = sum(SEVERITY_WEIGHT.get(str(item["level"]), 0) for item in issues)

        if critical_count > 0:
            level = "需要处理"
            summary = "存在影响闭环可靠性的严重问题，建议先处理关键字段缺失和映射异常。"
        elif warning_count > 0:
            level = "需要关注"
            summary = "闭环基本可运行，但仍有若干待处理问题会影响数据质量。"
        else:
            level = "正常"
            summary = "当前未发现明显质量问题，可继续进行日报和 Excel 导出。"

        actions = [
            f"原始输入共 {raw_inputs['total_count']} 条，待解析 {raw_inputs['unparsed_count']} 条。",
            f"解析记录中待确认 {parsed_records['pending_count']} 条，已确认 {parsed_records['confirmed_count']} 条。",
        ]

        if parsed_records["worker_confirm_required_count"] > 0:
            actions.append(
                f"存在 {parsed_records['worker_confirm_required_count']} 条维修人员未确认记录，建议进入人工确认页补全。"
            )
        if parsed_records["reserved_name_in_worker_count"] > 0:
            actions.append(
                f"存在保留名 {APP_INFO.developer} 误入维修人员字段，请检查解析规则。"
            )
        if export_readiness["report_ready_count"] > 0:
            actions.append(
                f"当前已有 {export_readiness['report_ready_count']} 条已确认记录，可生成日报和 Excel 报表。"
            )
        else:
            actions.append("当前无已确认记录，建议先完成解析和人工确认后再导出。")

        return {
            "level": level,
            "summary": summary,
            "score": score,
            "critical_issue_count": critical_count,
            "warning_issue_count": warning_count,
            "recommended_actions": actions,
        }

    def _count_reserved_name_in_worker_field(self, connection) -> int:
        rows = connection.execute(
            """
            SELECT worker_names
            FROM parsed_records
            WHERE TRIM(worker_names) <> ''
            """
        ).fetchall()
        count = 0
        for row in rows:
            names = re.split(r"[、，,/\s；;]+", str(row["worker_names"] or "").strip())
            if any(is_reserved_person_name(name) for name in names):
                count += 1
        return count

    def _count_unresolved_aliases(self, connection, active_name_lookup: set[str]) -> int:
        rows = connection.execute(
            """
            SELECT wechat_nickname, worker_names, employee_confirm_required
            FROM parsed_records
            WHERE employee_confirm_required = 1
            """
        ).fetchall()

        unresolved: set[str] = set()
        for row in rows:
            wechat_nickname = str(row["wechat_nickname"] or "").strip()
            if wechat_nickname and not is_reserved_person_name(wechat_nickname):
                if wechat_nickname.casefold() not in active_name_lookup:
                    unresolved.add(wechat_nickname)

            worker_names = split_worker_names_text(str(row["worker_names"] or ""))
            for name in worker_names:
                if name.casefold() not in active_name_lookup and not is_reserved_person_name(name):
                    unresolved.add(name)
        return len(unresolved)

    def _append_issue(
        self,
        issues: list[dict[str, Any]],
        *,
        level: str,
        issue_type: str,
        count: int,
        description: str,
        action: str,
    ) -> None:
        if count <= 0:
            return
        issues.append(
            {
                "level": level,
                "type": issue_type,
                "description": description,
                "count": int(count),
                "action": action,
            }
        )

    def _build_markdown(self, result: dict[str, Any], target_path: Path) -> str:
        raw_inputs = result["raw_inputs"]
        parsed_records = result["parsed_records"]
        employee_mapping = result["employee_mapping"]
        export_readiness = result["export_readiness"]
        conclusion = result["conclusion"]
        issues = result["issues"]

        lines = [
            "# 数据质量检查报告",
            "",
            "## 检查信息",
            f"- 检查时间：{result['checked_at']}",
            f"- 规则版本：{result['rule_version']}",
            f"- 数据来源：{result['data_source']}",
            f"- 导出文件：{to_relative_source_path(target_path)}",
            "",
            "## 原始输入摘要",
            f"- raw_inputs 总数：{raw_inputs['total_count']}",
            f"- 未解析数量：{raw_inputs['unparsed_count']}",
            f"- 已解析数量：{raw_inputs['parsed_count']}",
            f"- 空文本数量：{raw_inputs['empty_text_count']}",
            f"- 重复原始文本数量：{raw_inputs['duplicate_text_count']}",
            "",
            "## 解析记录摘要",
            f"- parsed_records 总数：{parsed_records['total_count']}",
            f"- 待确认数量：{parsed_records['pending_count']}",
            f"- 已确认数量：{parsed_records['confirmed_count']}",
            f"- 缺少日期数量：{parsed_records['missing_date_count']}",
            f"- 缺少项目/工作内容数量：{parsed_records['missing_project_or_content_count']}",
            f"- 缺少系统类别数量：{parsed_records['missing_system_category_count']}",
            f"- 缺少工作类型数量：{parsed_records['missing_work_type_count']}",
            f"- 缺少维修人员数量：{parsed_records['missing_worker_count']}",
            f"- 维修人员需要人工确认数量：{parsed_records['worker_confirm_required_count']}",
            f"- 保留名误入维修人员字段数量：{parsed_records['reserved_name_in_worker_count']}",
            "",
            "## 员工映射摘要",
            f"- 员工总数：{employee_mapping['employee_total_count']}",
            f"- 别名总数：{employee_mapping['alias_total_count']}",
            f"- 未解析别名数量：{employee_mapping['unresolved_alias_count']}",
            f"- 一对多疑似冲突数量：{employee_mapping['conflict_count']}",
            f"- 已启用员工数量：{employee_mapping['enabled_employee_count']}",
            f"- 已停用员工数量：{employee_mapping['disabled_employee_count']}",
            "",
            "## 导出准备摘要",
            f"- 可用于日报的记录数量：{export_readiness['report_ready_count']}",
            f"- 可用于 Excel 导出的记录数量：{export_readiness['excel_ready_count']}",
            f"- 今日记录数量：{export_readiness['today_count']}",
            f"- 本周记录数量：{export_readiness['week_count']}",
            f"- 本月记录数量：{export_readiness['month_count']}",
            "",
            "## 问题清单",
        ]

        if issues:
            lines.extend(
                [
                    "| 等级 | 类型 | 问题说明 | 数量 | 建议动作 |",
                    "| --- | --- | --- | ---: | --- |",
                ]
            )
            for item in issues:
                lines.append(
                    f"| {item['level']} | {item['type']} | {item['description']} | {item['count']} | {item['action']} |"
                )
        else:
            lines.append("- 未发现明显问题。")

        lines.extend(
            [
                "",
                "## 综合结论",
                f"- 结论等级：{conclusion['level']}",
                f"- 结论摘要：{conclusion['summary']}",
                f"- 风险分值：{conclusion['score']}",
                "",
                "## 建议动作",
            ]
        )
        for action in conclusion["recommended_actions"]:
            lines.append(f"- {action}")

        lines.extend(
            [
                "",
                "## 软件信息",
                f"- 软件名称：{APP_INFO.project_name_cn} / {APP_INFO.tool_name}",
                f"- 英文名称：{APP_INFO.project_name_en}",
                f"- 版本：{APP_INFO.version}",
                f"- 开发者：{APP_INFO.developer}",
            ]
        )
        return "\n".join(lines) + "\n"

    def _fetch_count(self, connection, query: str) -> int:
        row = connection.execute(query).fetchone()
        if row is None:
            return 0
        value = row[0]
        return int(value or 0)

    def _parse_work_date(self, value: str) -> date | None:
        normalized_value = value.strip()
        if not normalized_value:
            return None
        try:
            return datetime.strptime(normalized_value, "%Y-%m-%d").date()
        except ValueError:
            return None
