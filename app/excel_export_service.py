from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side

from app.config import APP_INFO, OUTPUTS_DIR, normalize_worker_names_text, split_worker_names_text
from app.database import SQLiteDataPool


class ExcelExportService:
    def __init__(self, data_pool: SQLiteDataPool) -> None:
        self.data_pool = data_pool
        self.logger = logging.getLogger("ybkj_workflow.excel_export")
        self.export_dir = OUTPUTS_DIR / "excel"

    def export_maintenance_excel(
        self, date: str | None = None, filters: dict[str, Any] | None = None
    ) -> tuple[Path, dict[str, Any]]:
        """
        Query confirmed records and export to Excel.
        Returns (file_path, summary_stats).
        """
        records = self.data_pool.list_confirmed_records_for_report(date, filters)
        
        if not records:
            raise ValueError("没有符合条件的已确认记录可供导出。")

        wb = self.build_workbook(records, filters)
        file_path = self.save_workbook(wb, date)

        summary = self._calculate_summary(records)
        
        self.logger.info(
            "Excel exported: path=%s, records=%s, date=%s, filters=%s",
            file_path.name, len(records), date, filters
        )
        
        return file_path, summary

    def build_workbook(self, records: list[dict[str, Any]], filters: dict[str, Any] | None = None) -> Workbook:
        wb = Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        # 1. Fire Alarm Sheet
        fire_records = [r for r in records if r.get("system_category") == "火灾报警"]
        self._build_fire_alarm_sheet(wb, fire_records)

        # 2. Surveillance Sheet
        video_records = [r for r in records if r.get("system_category") == "视频监控"]
        self._build_surveillance_sheet(wb, video_records)

        # 3. Other Devices Sheet
        other_records = [r for r in records if r.get("system_category") not in ("火灾报警", "视频监控")]
        self._build_other_devices_sheet(wb, other_records)

        # 4. Statistics Sheet
        self._build_statistics_sheet(wb, records)

        # 5. Export Info Sheet
        self._build_info_sheet(wb, filters)

        return wb

    def save_workbook(self, wb: Workbook, date_str: str | None) -> Path:
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        target_date = date_str or datetime.now().strftime("%Y-%m-%d")
        base_name = f"维修记录_{target_date}.xlsx"
        file_path = self.export_dir / base_name

        if file_path.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            file_path = self.export_dir / f"维修记录_{target_date}_{timestamp}.xlsx"

        wb.save(file_path)
        return file_path

    def _build_fire_alarm_sheet(self, wb: Workbook, records: list[dict[str, Any]]) -> None:
        ws = wb.create_sheet("火灾报警维修记录")
        headers = [
            "日期", "发现时间", "完成时间", "发现人", "故障部位", 
            "故障情况描述", "维修人员", "维修方法", "结果", "下次维修时间",
            "作业票号", "软件调试", "线路测试", "设备测试", "人工(人)", "用时(H)", "备注"
        ]
        ws.append(headers)
        self._style_header(ws)

        for r in records:
            worker_names = normalize_worker_names_text(str(r.get("worker_names", "")))
            person_count = self._estimate_person_count(worker_names)
            
            row = [
                r.get("work_date", ""),
                r.get("start_time", ""),
                r.get("end_time", ""),
                r.get("wechat_nickname", ""),
                f"{r.get('location', '')} {r.get('device_or_part', '')}".strip(),
                r.get("problem_description", "") or r.get("source_raw_text", "")[:50],
                worker_names,
                r.get("solution", ""),
                r.get("result", "") or r.get("status", ""),
                "", # 下次维修时间
                "", # 作业票号
                "", # 软件调试
                "", # 线路测试
                "", # 设备测试
                person_count if person_count > 0 else "",
                r.get("duration_hours", 0),
                r.get("note", "")
            ]
            ws.append(row)
        
        self._setup_sheet_view(ws)
        self._auto_column_width(ws)

    def _build_surveillance_sheet(self, wb: Workbook, records: list[dict[str, Any]]) -> None:
        ws = wb.create_sheet("监控维修记录")
        headers = [
            "日期", "报修时间", "完成时间", "报修单位", "地点", 
            "问题描述", "解决方法", "结果", "下次维修时间", "工作票号",
            "维修人员", "软件调试", "线路测试", "电源测试", "设备测试", 
            "人工(人)", "用时(H)", "用料", "备注"
        ]
        ws.append(headers)
        self._style_header(ws)

        for r in records:
            worker_names = normalize_worker_names_text(str(r.get("worker_names", "")))
            person_count = self._estimate_person_count(worker_names)

            row = [
                r.get("work_date", ""),
                r.get("start_time", ""),
                r.get("end_time", ""),
                r.get("project", ""),
                f"{r.get('location', '')} {r.get('device_or_part', '')}".strip(),
                r.get("problem_description", "") or r.get("source_raw_text", "")[:50],
                r.get("solution", ""),
                r.get("result", "") or r.get("status", ""),
                "", # 下次维修时间
                "", # 工作票号
                worker_names,
                "", "", "", "", # 调试/测试
                person_count if person_count > 0 else "",
                r.get("duration_hours", 0),
                "", # 用料
                r.get("note", "")
            ]
            ws.append(row)
        
        self._setup_sheet_view(ws)
        self._auto_column_width(ws)

    def _build_other_devices_sheet(self, wb: Workbook, records: list[dict[str, Any]]) -> None:
        ws = wb.create_sheet("其他装置及设备")
        headers = [
            "日期", "开始时间", "完成时间", "项目/服务对象", "地点", 
            "工作类型", "工作内容", "处理方法", "结果", "维修人员",
            "人工(人)", "用时(H)", "备注"
        ]
        ws.append(headers)
        self._style_header(ws)

        for r in records:
            worker_names = normalize_worker_names_text(str(r.get("worker_names", "")))
            person_count = self._estimate_person_count(worker_names)

            row = [
                r.get("work_date", ""),
                r.get("start_time", ""),
                r.get("end_time", ""),
                r.get("project", ""),
                f"{r.get('location', '')} {r.get('device_or_part', '')}".strip(),
                r.get("work_type", ""),
                r.get("problem_description", "") or r.get("source_raw_text", "")[:50],
                r.get("solution", ""),
                r.get("result", "") or r.get("status", ""),
                worker_names,
                person_count if person_count > 0 else "",
                r.get("duration_hours", 0),
                r.get("note", "")
            ]
            ws.append(row)
        
        self._setup_sheet_view(ws)
        self._auto_column_width(ws)

    def _build_statistics_sheet(self, wb: Workbook, records: list[dict[str, Any]]) -> None:
        ws = wb.create_sheet("维修工时统计")
        
        # 1. By System Category
        ws.append(["按系统类别统计"])
        ws.append(["系统类别", "记录数", "总工时(H)"])
        cat_stats = {}
        for r in records:
            cat = r.get("system_category") or "其他"
            hours = float(r.get("duration_hours") or 0)
            count, total_h = cat_stats.get(cat, (0, 0.0))
            cat_stats[cat] = (count + 1, total_h + hours)
        
        for cat, (count, total_h) in sorted(cat_stats.items()):
            ws.append([cat, count, round(total_h, 2)])
        ws.append([])

        # 2. By Work Type
        ws.append(["按工作类型统计"])
        ws.append(["工作类型", "记录数", "总工时(H)"])
        type_stats = {}
        for r in records:
            wt = r.get("work_type") or "其他"
            hours = float(r.get("duration_hours") or 0)
            count, total_h = type_stats.get(wt, (0, 0.0))
            type_stats[wt] = (count + 1, total_h + hours)
        
        for wt, (count, total_h) in sorted(type_stats.items()):
            ws.append([wt, count, round(total_h, 2)])
        ws.append([])

        # 3. By Person
        ws.append(["按人员统计"])
        ws.append(["维修人员", "参与记录数", "总工时(H)"])
        person_stats = {}
        missing_hours_count = 0
        for r in records:
            worker_names = normalize_worker_names_text(str(r.get("worker_names", "")).strip())
            hours = float(r.get("duration_hours") or 0)
            if float(r.get("duration_hours") or 0) == 0:
                missing_hours_count += 1
            
            names = split_worker_names_text(worker_names)
            if not names:
                names = ["人员待确认"]
            
            for name in names:
                count, total_h = person_stats.get(name, (0, 0.0))
                person_stats[name] = (count + 1, total_h + hours)
        
        for name, (count, total_h) in sorted(person_stats.items()):
            ws.append([name, count, round(total_h, 2)])
        
        if missing_hours_count > 0:
            ws.append([])
            ws.append([f"注：共有 {missing_hours_count} 条记录未填写工时，已按 0 计算。"])

        self._style_header(ws, row_idx=2)
        self._style_header(ws, row_idx=len(cat_stats) + 4)
        self._style_header(ws, row_idx=len(cat_stats) + len(type_stats) + 6)
        self._auto_column_width(ws)

    def _build_info_sheet(self, wb: Workbook, filters: dict[str, Any] | None) -> None:
        ws = wb.create_sheet("导出说明")
        ws.append(["友邦维保工作流系统 / 维保日报通 导出报告"])
        ws.append(["基础信息"])
        ws.append(["软件名称", APP_INFO.project_name_cn])
        ws.append(["英文名称", APP_INFO.project_name_en])
        ws.append(["版本号", APP_INFO.version])
        ws.append(["开发者", APP_INFO.developer])
        ws.append(["版权信息", APP_INFO.copyright_text])
        ws.append([])
        ws.append(["导出详情"])
        ws.append(["导出时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        ws.append(["数据来源", "confirmed parsed_records"])
        
        filter_desc = "全部"
        if filters:
            desc_parts = []
            for k, v in filters.items():
                if v and v != "全部":
                    desc_parts.append(f"{k}={v}")
            if desc_parts:
                filter_desc = ", ".join(desc_parts)
        ws.append(["筛选条件", filter_desc])
        ws.append([])
        ws.append(["重要说明"])
        ws.append(["1. 本 Excel 仅包含 confirm_status = 'confirmed' 的已确认记录。"])
        ws.append(["2. pending (待确认) 和 ignored (已忽略) 记录未包含在内。"])
        ws.append(["3. 数据由系统自动生成，建议人工二次核对。"])
        
        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 60

    def _style_header(self, ws, row_idx: int = 1) -> None:
        bold_font = Font(bold=True)
        alignment = Alignment(horizontal="center", vertical="center")
        border = Border(
            left=Side(style='thin'), 
            right=Side(style='thin'), 
            top=Side(style='thin'), 
            bottom=Side(style='thin')
        )
        for cell in ws[row_idx]:
            cell.font = bold_font
            cell.alignment = alignment
            cell.border = border

    def _setup_sheet_view(self, ws) -> None:
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    def _auto_column_width(self, ws) -> None:
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if cell.value:
                        length = len(str(cell.value).encode('utf-8'))
                        if length > max_length:
                            max_length = length
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width

    def _estimate_person_count(self, worker_names: str) -> int:
        return len(split_worker_names_text(worker_names))

    def _calculate_summary(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        fire_count = sum(1 for r in records if r.get("system_category") == "火灾报警")
        video_count = sum(1 for r in records if r.get("system_category") == "视频监控")
        other_count = len(records) - fire_count - video_count
        total_hours = sum(float(r.get("duration_hours") or 0) for r in records)
        missing_person_count = sum(
            1 for r in records if not normalize_worker_names_text(str(r.get("worker_names", "")))
        )
        
        return {
            "total_count": len(records),
            "fire_count": fire_count,
            "video_count": video_count,
            "other_count": other_count,
            "total_hours": round(total_hours, 2),
            "missing_person_count": missing_person_count
        }
