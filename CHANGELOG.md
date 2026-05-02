# CHANGELOG

## V1.0 beta

### V0.3-real-sample-run

- 新增 `dataset/samples/text_samples/realistic_wechat_records_sample.txt`，提供 13 条更贴近微信群口吻的脱敏试跑样例。
- 新增 `docs/V0.3真实样例闭环试跑说明.md`，整理从录入、解析、人工确认到日报、Excel、统计与数据质量检查的完整试跑步骤。
- 数据录入页增加试跑提示，明确可直接使用 `realistic_wechat_records_sample.txt` 复制粘贴或导入 `.txt`。
- 人工确认页增加“修正提示”，可针对缺日期、缺系统类别、缺工作类型、缺地点、缺少维修人员、人员待确认、保留名误入等情况给出快速修正指引。
- 数据质量检查升级到 `V0.3-real-sample-run`，新增缺少地点、疑似重复解析记录检查，并在页面与 Markdown 报告中增加规则说明小节。

### V0.2-flow-check

- 新增 `QualityCheckService`，只读检查 `raw_inputs`、`parsed_records`、`employee_aliases` 和导出准备情况。
- 新增“数据质量”页面，位于“统计分析”之后，支持开始检查、刷新和导出 Markdown 检查报告。
- 检查结果支持输出综合结论：`正常 / 需要关注 / 需要处理`，并附带建议动作。
- 新增 `reports/quality/` 导出目录约定，检查报告文件名格式为 `quality_check_YYYY-MM-DD_HHMMSS.md`。
- 新增演示样例 `dataset/samples/text_samples/demo_daily_records.txt`，覆盖正常记录、网名映射、缺失人员、类别不明确和疑似重复场景。
- 新增 `docs/全流程验证说明.md`，用于本轮真实闭环验证和界面验收。

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
