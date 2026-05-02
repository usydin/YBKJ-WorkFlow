# CHANGELOG

## V1.0 beta

### 初始规划

- 确定项目名称：友邦维保工作流系统 / 维保日报通 / YBKJ-WorkFlow
- 确定开发者：ybkj-pL
- 确定版权：© 2026 @B‘lock10STUdio
- 确定 Logo：assets/logo.png
- 确定 GUI 风格：Obsidian 极简 + 科技运维风
- 确定第一阶段用户：维保部负责每日工作汇总人员
- 确定核心流程：文本录入 → 智能解析 → 人工校对 → 数据池 → 多格式输出
- 确定数据池路线：SQLite + JSONL
- 确定打包路线：源码可运行 → Windows 绿色版 → macOS 版

### 当前阶段收尾

- 收口人工确认页 GUI：主 `QSplitter` + 详情页签化 + 基础信息双列网格。
- 完成员工别名映射管理、人工确认重新映射入口和保留名拦截。
- 补齐统计分析、日报生成与 Excel 导出的基础闭环。
- 恢复深浅主题 `QComboBox` SVG 下拉箭头，并完成阶段编译与启动验收。
