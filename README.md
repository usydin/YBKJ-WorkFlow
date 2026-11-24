<p align="center"><img src="assets/logo.png" alt="YBKJ-WorkFlow｜维保日报通 logo" width="150"></p>

<h1 align="center">YBKJ-WorkFlow｜维保日报通</h1>

<p align="center"><strong>简体中文</strong> · <a href="README.en.md">English</a></p>

<p align="center">本地优先的维保业务记录、人工确认与日报工作流</p>

![Runtime: V0.8 · Fix record: V0.8.1 · R&D: SNTL Lab · Core: Python · GUI: PySide6 · Data: SQLite / JSONL · Excel: openpyxl](assets/brand/readme-badges.svg)

[版权与授权](COPYRIGHT.md) · [安全政策](SECURITY.md)

## 项目定位

将授权的文本及手动录入记录汇入原始输入池，经规则解析、人工确认、质量核查后生成可信日报与台账。不是简单的聊天文本转 Excel 工具。

## 版本与真实状态

**app/version.py：V0.8-windows-build-test**；CHANGELOG 记录 V0.8.1-windows-build-fix，历史 Windows 11 源码启动、打包、自检及 GUI 启动已通过。版本常量尚未同步至热修名称；未核实正式发布或生产验收。本轮不改运行版本，不重跑打包。

[固定源码](https://github.com/usydin/YBKJ-WorkFlow/tree/589f5882df1a7c5c0317d6af17db874c61e58fb0) · [原始 README（历史）](https://github.com/usydin/YBKJ-WorkFlow/blob/589f5882df1a7c5c0317d6af17db874c61e58fb0/README.md)

## 核心能力

- 原始输入池、规则解析、人员映射与人工修正留痕。
- 仅已确认记录进入日报、统计和 Excel；支持 TXT/Markdown 日报与多表导出。
- 只读数据质量核查、OCR 暂存和模拟研究入口；真实 OCR、模型训练及企业微信自动发送未接通。

## 技术架构

Python、PySide6、SQLite + JSONL、openpyxl；PyInstaller Windows 绿色交付。macOS 为开发/目标环境，不宣称已完成正式交付。

## 安全与数据

本项目公开可见不等于开源授权。禁止公开原始聊天、员工映射、真实日报、客户台账、运行数据库、OCR 图片及凭据。采用合成/脱敏样本；输出需人工确认。历史公开数据及权属仍须独立审核。

## 文档导航

- [变更记录](CHANGELOG.md)
- [技术架构](docs/技术架构说明.md)
- [全流程验证](docs/全流程验证说明.md)
- [Windows 测试记录](docs/WINDOWS_BUILD_TEST_RECORD.md)
- [数据池字段](docs/数据池字段说明.md)

## 研发身份

**SNTL Lab** · 保留原开发者 ybkj-pL 与现有友邦科技维保部署名；SNTL Lab 为工业技术研发身份。历史版权署名的差异以权属复核为准。
