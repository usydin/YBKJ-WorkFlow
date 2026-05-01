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
