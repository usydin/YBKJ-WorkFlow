# YBKJ-WorkFlow

<p align="center">
  <img src="assets/logo.png" alt="YBKJ-WorkFlow Logo" width="180">
</p>

> 友邦维保工作流系统 / 维保日报通  
> Developer: ybkj-pL  
> Version: V1.0 beta  
> Copyright © 2026 @B‘lock10STUdio

## 项目简介

YBKJ-WorkFlow 是一套面向维保部每日工作汇总场景的本地离线智能工作流系统。

系统目标不是“微信转 Excel”，而是把微信聊天文本、TXT 文本、手工补录等多来源原始输入统一沉淀到原始输入池，再逐步解析、确认、汇总，最终输出日报、台账、统计分析与多格式导出结果。

## 基础信息

- 中文名：友邦维保工作流系统
- 工具名：维保日报通
- 英文名：YBKJ-WorkFlow
- 版本：V1.0 beta
- 开发者：ybkj-pL
- 版权：© 2026 @B‘lock10STUdio
- 目标平台：Windows 10/11、macOS
- 运行原则：本地离线优先

## 当前阶段重点

当前版本已经完成以下基础闭环：

- GUI 基础骨架与深浅主题切换
- 数据录入页
- `raw_inputs` 原始输入池入库
- `JSONL` 原始输入备份
- 首页基础计数刷新
- `raw_inputs` 多来源设计扩展
- `employee_aliases` 员工网名映射管理 V0.1
- `parsed_records` 待人工确认表
- 智能解析 `V0.1`
- 智能解析页基础列表展示
- 人工确认页 `V0.1` (支持一键人员映射)
- `corrections.log` 人工修正留痕
- 日报文本生成 `V0.1`
- Excel 导出 `V0.1`
- 统计分析 `V0.1`
- 数据质量检查 `V0.2-flow-check`
- 日报 TXT / Markdown 导出
- 员工映射管理页 (CRUD/搜索/状态管理)
- OCR 暂存区 (V0.5 准备工作)
- OCR Lab 验证框架 (V0.6 技术验证与模拟入口)

## V0.3 真实样例闭环试跑

当前阶段为 `V0.3-real-sample-run`，目标是用几条真实/半真实的微信维修记录，把“录入 -> 解析 -> 人工确认 -> 质量检查 -> 日报 -> Excel -> 统计分析”完整跑通。

推荐试跑入口：

- `dataset/samples/text_samples/realistic_wechat_records_sample.txt`
- `dataset/samples/text_samples/demo_daily_records.txt`
- `docs/V0.3真实样例闭环试跑说明.md`
- `docs/全流程验证说明.md`

本轮不做 OCR、Word/PDF、大模型接入或大规模 GUI 重构，重点是提升真实样例试跑和问题暴露能力。

## V0.4 真实输入体验优化

`V0.4-real-input-polish` 聚焦真实文本录入与闭环引导的易用性优化：

- 数据录入页
  - 增加“真实文本试跑提示”卡片，明确粘贴规则与样例路径
  - 增加“载入真实样例”按钮，直接载入 `dataset/samples/text_samples/realistic_wechat_records_sample.txt`
  - 增加输入统计：字符数、行数、估算记录数
- 智能解析
  - 规则型轻量“解析提示”写入 `parsed_records.note`，识别缺字段、文本过短、多人参与、保留名、疑似重复等
  - 智能解析页新增“解析提示”列，解析完成摘要提示包含“带解析提示”数量
- 人工确认页
  - 增加“解析提示 / 待补全项”提示条，并随字段编辑即时刷新
  - 对缺字段控件增加 placeholder/tooltip，保持现有 `QTabWidget` 结构
- 数据质量
  - 检查规则版本升级为 `V0.4-real-input-polish`
  - 增加“待处理指引”小节，给出进入页面处理的建议路径
- 日报/Excel 导出
  - 明确提示范围：仅包含 `confirmed` 记录
  - 显示当前筛选范围内的待确认/已忽略数量，避免误以为全部数据已导出

## V0.5 OCR 暂存区准备 (V0.5-OCR-prep)

`V0.5-OCR-prep` 聚焦于未来接入 OCR/截图识别结果时的安全性与数据质量：

- **OCR 暂存区概念**：识别结果不直接进入 `raw_inputs`，而是先进入“暂存区”缓冲区。
- **独立存储**：新增 `ocr_staging_records` 独立表，与主流程完全隔离。
- **人工审核流程**：
  - 支持手动粘贴识别后的文本。
  - 支持在暂存区对识别错误的文本进行“清洗”和“修正”。
  - 必须由人工点击“确认导入”后，才正式写入 `raw_inputs` 进入主解析流程。
- **导航集成**：新增“OCR 暂存”导航项，位置紧跟“数据录入”。
- **质量衔接**：数据质量检查页新增 OCR 暂存区统计摘要，提示尚未处理的识别结果。
- **设计文档**：新增 `docs/OCR暂存区设计说明.md`。

本轮不做真正 OCR，不接入大模型，不安装 OCR 库。

## V0.6 OCR 技术验证准备 (V0.6-local-ocr-research)

`V0.6-local-ocr-research` 聚焦于 OCR 技术选型与独立验证框架的搭建，为后续正式接入 OCR 引擎做准备：

- **目录规范**：建立 `dataset/samples/screenshots_raw/`（原始截图）与 `outputs/ocr_text/`（识别产物）目录。
- **技术选型**：完成 `docs/ocr_research/OCR技术选型说明.md`，确立“第一阶段手动、后续可选模块”的演进路线。
- **验证框架**：新增 `tools/ocr_lab/ocr_probe.py` 脚本，支持模拟识别并将结果写入 OCR 暂存区。
- **隐私保护**：通过 `.gitignore` 严格忽略真实图片与识别文本，确保不提交敏感信息。

本轮不集成真实 OCR 引擎，主流程保持稳定。

## 当前功能链路

当前推荐使用链路如下：

1. 数据录入页提交原始文本，写入 `raw_inputs`。
2. 智能解析页将 `pending_parse` 数据解析为 `parsed_records`。
3. 人工确认页核对结构化字段、重新映射人员并确认有效记录。
4. 员工映射页维护微信网名、别名与真实姓名关系。
5. 统计分析页基于 `confirmed` 记录查看人员、项目和系统分布。
6. 日报生成页输出 TXT / Markdown 日报。
7. Excel 导出页导出多 Sheet 维保台账。
8. 数据质量页检查原始输入、解析记录、映射质量和导出准备情况。

建议使用 `realistic_wechat_records_sample.txt` 执行本轮闭环试跑，并重点观察：

- `王权富贵` / `王权富贵Dr.` 是否正确映射到 `王立彦`
- `ybkj-pL` 是否被保留名规则拦截
- 缺少维修人员、地点、系统类别、工作类型的记录是否能被发现并修正
- 疑似重复记录是否能在数据质量页和 Markdown 报告中暴露

## 阶段收尾说明

当前阶段已基本形成可提交的业务闭环，重点收口如下：

- **人工确认页结构收口**：页面主体调整为上方待确认表格 + 下方详情编辑 `QSplitter`，详情区进一步整理为 `QTabWidget`，拆分为“基础信息 / 处理信息 / 原始文本”，适合长期核对。
- **员工映射闭环**：员工别名管理页、解析阶段自动映射、人工确认页“重新映射人员”按钮已形成联动；`ybkj-pL` 作为保留名继续被拦截，不会写入 `worker_names`。
- **统计分析可用**：统计分析页已可基于 `confirmed` 记录查看总览卡片、人员统计、项目统计、系统类别统计、工作类型统计与明细记录。
- **日报与 Excel 导出可用**：日报生成页与 Excel 导出页均基于 `parsed_records.confirm_status = confirmed` 的可信记录工作。
- **数据质量检查可用**：新增“数据质量”页，可只读检查 `raw_inputs`、`parsed_records`、`employee_aliases` 与导出准备状态，并导出 Markdown 检查报告到 `reports/quality/`。
- **真实样例试跑可用**：新增更贴近微信聊天口吻的样例文本、录入提示、人工确认修正提示和试跑说明文档，便于快速发现解析问题。
- **当前验收命令**：建议在提交前执行 `.venv/bin/python -m compileall .`、`.venv/bin/python app.py`，并验证员工映射示例 `王权富贵 -> 王立彦`、`王权富贵Dr. -> 王立彦`、`ybkj-pL -> 空`。

## 多来源输入设计

`raw_inputs` 被定义为长期原始输入池，而不是围绕截图或 OCR 的临时结构。

当前支持或预留的 `source_type`：

- `paste`：粘贴微信聊天文本
- `txt`：单个 TXT 文件导入
- `manual`：手动录入
- `screenshot`：截图 OCR 预留
- `batch_txt`：批量 TXT 导入预留
- `unknown`：未知来源

原始输入至少保留以下字段：

- `created_at`
- `operator_name`
- `source_type`
- `source_name`
- `source_path`
- `default_project`
- `raw_text`
- `status`
- `note`

说明：

- `raw_text` 始终保留完整原文，不在入库阶段覆盖或清洗丢失信息。
- 解析结果进入 `parsed_records`，不覆盖 `raw_inputs`。
- `source_path` 仅记录相对路径或文件名，不写死系统绝对路径。

## 智能解析 V0.1

当前解析引擎具备以下基础能力：

- 识别日期：支持 `2026-4-30`、`2026-04-30`
- 识别时间段：支持 `9:00-17:00`、`15:20-17:00`
- 初步计算 `duration_hours`
- 识别完成状态：完成 / 未完成 / 待确认
- 识别工作类型：安全交底 / 会议类、培训、巡检、测试、维修或维护、其他
- 识别系统类别：火灾报警、视频监控、其他装置及设备
- 项目识别：优先使用 `default_project`，并结合文本关键词辅助判断
- 粗拆分：按日期、编号、时间段、明显工作行进行分段
- 人员识别：优先使用发送人或操作员，并尝试映射真实姓名

当前解析结果写入 `parsed_records`，并默认进入 `confirm_status = pending`，供后续人工确认。

## 人工确认流程

当前系统已形成三层数据流：

- `raw_inputs`：原始输入池，只保留原文，不覆盖
- `parsed_records`：解析后的结构化待确认记录
- `confirmed` 记录：后续日报、统计、Excel 导出的可信来源

`parsed_records.confirm_status` 当前支持：

- `pending`
- `confirmed`
- `ignored`

人工确认页支持：

- 按确认状态、项目、系统类别、工作类型、关键词筛选
- 选择记录后在下方表单中编辑关键字段
- 保存修改
- 确认为有效记录
- 忽略该记录
- 恢复为待确认

所有人工修改和状态流转都会追加写入 `dataset/corrections.log`。

## 日报生成 V0.1

日报生成当前基于 `parsed_records.confirm_status = confirmed` 的可信记录，不直接读取 `raw_inputs`。

当前规则：

- `confirmed` 记录进入日报
- `pending` 记录默认不进入日报
- `ignored` 记录默认不进入日报
- 支持按日期、项目、系统类别、工作类型、人员关键词筛选
- 支持复制日报文本到企业微信或微信
- 支持导出到 `reports/daily/` 目录下的 TXT / Markdown 文件
- 企业微信自动发送接口仅预留，当前版本不主动联网

## 员工网名映射管理 V0.1

微信昵称不等于真实员工姓名，系统提供 `employee_aliases` 维护机制：

- **核心字段**：真实姓名、微信网名、常用别名、班组、启用状态、备注。
- **自动映射**：解析阶段自动根据微信网名查找真实姓名，并回填至 `worker_names`。
- **人工触发**：在人工确认页提供“根据网名映射人员”按钮，支持一键补全。
- **多人识别**：支持通过多种分隔符（、，, 空格等）拆分多人网名并逐一映射。
- **状态管理**：支持停用/启用映射记录，解析时仅使用启用状态的记录。

## 统计分析 V0.1

统计分析页基于 `parsed_records.confirm_status = confirmed` 的可信记录，不直接统计 `pending`、`ignored` 或 `raw_inputs`。

- **筛选条件**：支持开始日期、结束日期、项目、系统类别、工作类型、人员关键词。
- **总览卡片**：显示已确认记录数、总工时、参与人员数、系统类别数量、未填写人员、未填写工时。
- **统计维度**：支持按人员、按项目、按系统类别、按工作类型、按明细记录查看。
- **人员核心字段**：人员统计以 `worker_names` 为准，因此员工映射会直接影响统计准确性。
- **轻量预留**：后续可扩展柱状图、饼图和趋势分析，当前 V0.1 先以表格统计为主。

## 数据质量检查 V0.4-real-input-polish

数据质量页以只读方式检查当前闭环是否适合继续演示、统计和导出。

- **原始输入检查**：`raw_inputs` 总数、未解析数量、已解析数量、空文本数量、重复原始文本数量。
- **解析记录检查**：`parsed_records` 总数、待确认数量、已确认数量、缺少日期/项目或工作内容/系统类别/工作类型/地点/维修人员数量、人员待人工确认数量、保留名误入人员字段数量、疑似重复解析记录数量。
- **员工映射检查**：员工总数、别名总数、未解析别名数量、一对多疑似冲突数量、已启用员工数量、已停用员工数量。
- **导出准备检查**：可用于日报和 Excel 导出的记录数量，以及今日、本周、本月记录数量。
- **综合结论**：输出 `正常 / 需要关注 / 需要处理`，并给出建议动作。
- **报告导出**：支持导出 Markdown 检查报告到 `reports/quality/quality_check_YYYY-MM-DD_HHMMSS.md`。
- **规则说明/待处理指引**：页面和导出 Markdown 同步说明保留名、员工映射、缺字段和重复记录规则，并提供处理入口建议。
- **只读原则**：检查本身不自动修改数据库内容。

## 样本管理

当前样本目录：

- `dataset/samples/screenshots_raw`
- `dataset/samples/text_samples`
- `dataset/samples/parsed_expected`

说明：

- `screenshots_raw` 仅用于当前阶段本地视觉参考，不建议提交高清长图到 GitHub
- 当前主输入路径优先是复制文本、TXT 导入、手动录入
- `realistic_wechat_records_sample.txt` 用于 `V0.3-real-sample-run` 真实样例闭环试跑，文件首行已明确标注为演示样例
- 批量 TXT 与截图 OCR 为后续预留路径
- OCR 不是 `V1.0 beta` 主路径，本轮不实现

## 当前界面结构

左侧导航当前包含以下模块：

- 工作台
- 数据录入
- 智能解析
- 人工确认
- 数据池
- 日报生成
- Excel导出
- 员工映射
- 统计分析
- 数据质量
- 模型训练
- 日志中心
- 设置

其中“工作台”“数据录入”“智能解析”“人工确认”“日报生成”“Excel导出”“员工映射”“统计分析”“数据质量”“设置”已经具备基础可用能力，其余页面仍为占位页。

## 当前项目结构

```text
YBKJ-WorkFlow/
├─ app/
│  ├─ ui/
│  │  ├─ analytics_page.py
│  │  ├─ confirm_page.py
│  │  ├─ data_entry_page.py
│  │  ├─ employee_page.py
│  │  ├─ excel_export_page.py
│  │  ├─ main_window.py
│  │  ├─ parse_page.py
│  │  ├─ quality_page.py
│  │  ├─ report_page.py
│  │  └─ styles.py
│  ├─ analytics_service.py
│  ├─ backup.py
│  ├─ config.py
│  ├─ corrections.py
│  ├─ database.py
│  ├─ intake_service.py
│  ├─ local_config.py
│  ├─ logging_setup.py
│  ├─ models.py
│  ├─ parser_engine.py
│  ├─ quality_service.py
│  ├─ report_service.py
│  └─ wecom.py
├─ dataset/
│  └─ samples/
│     ├─ screenshots_raw/
│     ├─ text_samples/
│     └─ parsed_expected/
├─ datapool/
│  ├─ jsonl/
│  └─ sqlite/
├─ docs/
├─ logs/
├─ outputs/
├─ reports/
├─ assets/
├─ app.py
└─ requirements.txt
```

## 启动方式

1. 创建虚拟环境并安装依赖：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

2. 启动程序：

```bash
.venv/bin/python app.py
```

3. 编译检查：

```bash
.venv/bin/python -m compileall .
```

## 当前运行说明

- 所有运行路径均通过项目目录推导，不写死系统绝对路径
- 运行日志输出到 `logs/`
- SQLite 数据库默认位于 `datapool/sqlite/ybkj_workflow.db`
- 原始输入 JSONL 默认位于 `datapool/jsonl/raw_inputs.jsonl`
- 人工修正留痕默认位于 `dataset/corrections.log`
- 日报导出默认位于 `reports/daily/`
- 数据质量报告默认位于 `reports/quality/`
- 企业微信接口默认关闭，不联网
- `config.local.json`、运行数据库、日志和 JSONL 备份默认不提交到 GitHub

## 本轮不实现

- OCR
- Word / PDF 导出
- 批量 TXT 导入实际执行逻辑
- 复杂模型训练

## 下一步建议

- 为批量 TXT 导入增加任务级入口
- 将 corrections.log 与规则优化联动
- 为 confirmed 记录接入 Word / PDF 导出
- 在人工确认页补充更细的时间校验和批量操作
- 实现自动提取维修人员并同步更新映射表（基于 corrections.log）
