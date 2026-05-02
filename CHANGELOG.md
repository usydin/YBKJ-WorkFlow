# CHANGELOG

## V1.0 beta

### V0.8.1-gui-fix

- GUI 启动修复：解决 `app.py` 调用 `MainWindow` 时参数不匹配导致的启动失败问题（TypeError）。
- 启动入口对齐：将 `MainWindow` 的初始化方式由传递 `services` 字典改为显式传递各个服务参数，与 `MainWindow.__init__` 签名对齐。

### V0.8-windows-build-test

- 打包脚本增强：重构 `build_windows.bat`，增加 Python/PyInstaller 环境检查、项目根目录自动定位及详细的中午操作提示。
- Spec 配置优化：更新 `ybkj_workflow.spec`，规范资源包含路径，显式排除运行产物（logs, datapool 等），并为初次打包保留 console 窗口以便排错。
- 自检逻辑升级：`--self-check` 增加对数据池、报告、输出目录的可写性检查，以及 Assets/Docs 资源的完整性检查。
- 测试文档体系：新增 `WINDOWS_BUILD_TEST_RECORD.md`（打包测试记录模板）与 `WINDOWS_RELEASE_FOLDER_GUIDE.md`（发布目录说明文档）。
- 启动代码清理：移除 `app.py` 中冗余的旧版 GUI 启动逻辑，确保代码整洁。

### V0.7-packaging-prep

- 版本号集中管理：新增 `app/version.py`，统一管理应用名称、版本号、开发者与版权信息，替代原 `config.py` 中的硬编码。
- 路径收口与规范：新增 `app/path_utils.py`，支持 PyInstaller 打包后的 `sys._MEIPASS` 资源映射与 `sys.executable` 运行根目录定位，确保绿色版路径兼容性。
- 命令行诊断增强：`app.py` 新增 `--version` 与 `--self-check` 参数，支持在无 GUI 环境下验证环境完整性、目录权限与数据库连接。
- 打包基础设施：新增 `packaging/windows/` 目录，包含 PyInstaller `.spec` 配置文件、一键打包批处理脚本 `.bat`。
- 运维文档补充：新增 `docs/RUNNING_ARTIFACTS.md`（运行产物说明）与 `docs/WINDOWS_TEST_CHECKLIST.md`（Windows 真机测试清单）。
- 启动流程重构：`app.py` 实现按需加载 GUI 模块，显著提升命令行工具响应速度并降低无界面环境下的运行门槛。

### V0.6-local-ocr-research

- OCR 技术验证：建立 `tools/ocr_lab/` 独立验证框架与 `ocr_probe.py` 脚本，支持模拟识别与暂存区写入。
- 目录规范：新增 `dataset/samples/screenshots_raw/` 与 `outputs/ocr_text/` 目录，并配置严格的 `.gitignore` 规则保护隐私。
- 技术选型：撰写 `docs/ocr_research/OCR技术选型说明.md`，分析不同 OCR 引擎方案并确立演进路线。
- 文档同步：更新 `OCR暂存区设计说明.md` 与 `全流程验证说明.md`，记录验证框架定位与使用方式。

### V0.5-OCR-prep

- OCR 暂存区：新增“OCR 暂存”页面与 `OCRStagingService`，支持手动粘贴截图识别后的文本，提供缓冲层隔离 `raw_inputs`。
- 数据库结构：新增 `ocr_staging_records` 独立表，存储原始识别文本、人工修正文本、状态与导入关联 ID。
- 审核流程：支持在暂存区对识别文本进行“人工修正”，支持标记“忽略”或“确认导入”；导入时自动复用 `IntakeService` 逻辑写入原始输入池并备份 JSONL。
- 导航集成：主窗口左侧导航新增“OCR 暂存”项，位置位于“数据录入”之后。
- 数据质量：升级规则版本至 `V0.5-OCR-prep`，增加 OCR 暂存区摘要统计，并在问题清单和待处理指引中提示未处理的暂存内容。
- 文档支持：新增 `docs/OCR暂存区设计说明.md`。

### V0.4-real-input-polish

- 数据录入页：新增“真实文本试跑提示”卡片、“载入真实样例”按钮与输入统计（字符数/行数/估算记录数），不改原入库逻辑。
- 智能解析：生成规则型轻量“解析提示”，写入 `parsed_records.note`（缺字段、文本过短、多人参与不明确、保留名、疑似重复等），解析页新增“解析提示”列与带提示数量反馈。
- 人工确认：在基础信息页顶部新增“解析提示 / 待补全项”，随字段编辑即时刷新；为缺字段控件补充 placeholder/tooltip。
- 数据质量：规则版本升级为 `V0.4-real-input-polish`；新增“待处理指引”小节，给出明确处理入口建议（人工确认、员工映射、解析页等）。
- 日报/Excel：明确范围提示“仅包含 confirmed 记录”，显示当前筛选范围内待确认/已忽略数量，避免误解导出覆盖全部记录。

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
