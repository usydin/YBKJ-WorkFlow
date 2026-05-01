# YBKJ-WorkFlow

<p align="center">
  <img src="assets/logo.png" alt="YBKJ-WorkFlow Logo" width="180">
</p>

> 友邦维保工作流系统 / 维保日报通  
> Developer: ybkj-pL  
> Version: V1.0 beta  
> Copyright © 2026 @B‘lock10STUdio

## 项目简介

YBKJ-WorkFlow 是一套面向维保部每日工作汇总场景的本地智能工作流系统。

本项目用于将微信工作记录、文本记录、人工录入内容等非结构化信息，转化为结构化数据池，并生成每日工作汇报、维修台账、工作量统计、故障类型分析以及 Excel、Word、PDF、TXT 等多格式输出。

本项目不是简单的微信转 Excel 工具，而是面向维保工作的本地数据入口、数据标准和数据资产沉淀系统。

## 基础信息

- 中文名：友邦维保工作流系统
- 工具名：维保日报通
- 英文名：YBKJ-WorkFlow
- 版本：V1.0 beta
- 开发者：ybkj-pL
- 版权：© 2026 @B‘lock10STUdio
- 目标平台：Windows 10/11、macOS
- 运行原则：本地离线优先

## V1.0 目标

第一阶段面向维保部负责每日工作汇总的人员，先完成：

- 粘贴微信文本
- TXT 导入
- 手动录入
- 智能解析
- 人工校对
- SQLite 数据池
- JSONL 备份
- Excel 导出
- 日报文本生成
- 日志留痕
- corrections.log 修正样本沉淀

## 技术路线

- GUI：Python + PySide6
- 数据池：SQLite
- 备份数据：JSONL
- 解析引擎：规则词库 + 正则抽取 + 相似度匹配
- 导出：openpyxl / python-docx
- 打包：PyInstaller
- 后续预留：OCR、模型训练、企业微信同步

## 设计原则

1. 本地优先，默认离线运行。
2. Excel 是输出，不是核心。
3. 数据池是系统唯一事实来源。
4. 人工校对结果必须沉淀为训练样本。
5. 所有关键操作必须留痕。
6. 企业微信同步作为可选插件，默认关闭。

## 当前完成内容

本次已完成 V1.0 beta 第一阶段基础工程骨架，重点是保证项目可启动、可扩展、界面可用：

- 基于 Python + PySide6 的桌面 GUI 骨架
- 深色左侧导航栏 + 简洁主工作区 + 卡片式工作台首页
- 首页 6 张统计卡片占位
- 关于信息展示区，统一显示名称、版本、开发者、版权
- `assets/logo.png` 的安全加载与缺失降级处理
- `app/config.py` 统一维护项目基础信息和运行路径
- 基础日志系统，自动生成运行日志与错误日志
- `SQLite` 数据池初始化接口，占位阶段可直接创建数据库文件
- `JSONL` 备份接口占位
- 解析引擎、导出接口、企业微信接口预留模块

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

除工作台外，其余页面当前先提供结构化占位页，用于后续逐步接入功能。

## 当前项目结构

```text
YBKJ-WorkFlow/
├─ app/
│  ├─ ui/
│  │  ├─ main_window.py
│  │  └─ styles.py
│  ├─ backup.py
│  ├─ config.py
│  ├─ database.py
│  ├─ exporters.py
│  ├─ logging_setup.py
│  ├─ models.py
│  ├─ parser_engine.py
│  └─ wecom.py
├─ assets/
├─ datapool/
├─ docs/
├─ outputs/
├─ reports/
├─ logs/
├─ app.py
└─ requirements.txt
```

## 启动方式

1. 推荐先创建虚拟环境并安装依赖：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

如果你的环境已经提供可用的 `python` 命令，也可以直接执行：

```bash
pip install -r requirements.txt
```

2. 启动程序：

推荐方式：

```bash
.venv/bin/python app.py
```

通用方式：

```bash
python app.py
```

3. 验证源码是否可编译：

推荐方式：

```bash
.venv/bin/python -m compileall .
```

通用方式：

```bash
python -m compileall .
```

## 当前运行说明

- 所有运行路径均通过相对项目目录推导，不写死系统绝对路径
- 日志文件输出到 `logs/`
- SQLite 数据库默认初始化到 `datapool/sqlite/ybkj_workflow.db`
- JSONL 备份占位文件默认初始化到 `datapool/exports_history/records_backup.jsonl`
- 企业微信接口模块默认关闭，不联网

## 下一阶段建议

- 接入数据录入页表单与文本粘贴区
- 设计 SQLite 业务表结构与字段映射
- 完善解析规则、人工确认流程和 corrections 样本沉淀
- 实现日报文本导出与 Excel 导出
- 增加日志中心页面的文件浏览与筛选能力
