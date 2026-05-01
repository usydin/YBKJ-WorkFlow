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
- `employee_aliases` 员工网名映射预留
- `parsed_records` 待人工确认表
- 智能解析 `V0.1`
- 智能解析页基础列表展示

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

## 员工网名映射预留

微信昵称不等于真实员工姓名，因此系统已预留 `employee_aliases` 表，用于维护：

- 真实姓名
- 微信网名
- 别名
- 班组
- 启用状态
- 创建/更新时间
- 备注

当前逻辑：

- 能匹配则映射为真实姓名
- 不能匹配则保留微信网名
- 同时标记 `employee_confirm_required = true`
- 后续人工修正结果可沉淀到 `dataset/corrections.log`

## 样本管理

当前样本目录：

- `dataset/samples/screenshots_raw`
- `dataset/samples/text_samples`
- `dataset/samples/parsed_expected`

说明：

- `screenshots_raw` 仅用于当前阶段本地视觉参考，不建议提交高清长图到 GitHub
- 当前主输入路径优先是复制文本、TXT 导入、手动录入
- 批量 TXT 与截图 OCR 为后续预留路径
- OCR 不是 `V1.0 beta` 主路径，本轮不实现

## 当前界面结构

左侧导航当前包含以下模块：

- 工作台
- 数据录入
- 智能解析
- 数据池
- 日报生成
- Excel导出
- 统计分析
- 模型训练
- 日志中心
- 设置

其中“数据录入”“智能解析”“工作台”“设置”已经具备基础可用能力，其余页面仍为占位页。

## 当前项目结构

```text
YBKJ-WorkFlow/
├─ app/
│  ├─ ui/
│  │  ├─ data_entry_page.py
│  │  ├─ main_window.py
│  │  ├─ parse_page.py
│  │  └─ styles.py
│  ├─ backup.py
│  ├─ config.py
│  ├─ database.py
│  ├─ intake_service.py
│  ├─ local_config.py
│  ├─ logging_setup.py
│  ├─ models.py
│  ├─ parser_engine.py
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
- 企业微信接口默认关闭，不联网
- `config.local.json`、运行数据库、日志和 JSONL 备份默认不提交到 GitHub

## 本轮不实现

- OCR
- Excel 导出
- 完整人工确认编辑界面
- 批量 TXT 导入实际执行逻辑

## 下一步建议

- 完成 parsed_records 人工确认页
- 增加 employee_aliases 的基础管理界面
- 为批量 TXT 导入增加任务级入口
- 将 corrections.log 与人工确认结果联动
- 为日报和统计分析接入 parsed_records 数据源
