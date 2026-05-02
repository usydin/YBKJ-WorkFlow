# Windows 真机测试清单 (V0.8-windows-build-test)

在发布 Windows 绿色版前，请在目标 Windows 环境（建议 Win10/Win11）执行以下测试流程。详细记录请参考 `docs/WINDOWS_BUILD_TEST_RECORD.md`。

## 0. 打包准备 (Build)
- [ ] **执行打包**: 运行 `packaging\windows\build_windows.bat`，确认无 Error 退出。
- [ ] **产物检查**: 确认 `dist\YBKJ-WorkFlow` 目录生成，且包含 `YBKJ-WorkFlow.exe` 及 `_internal` 目录。

## 1. 基础环境 (Environment)
- [ ] **无 Python 环境测试**: 在未安装 Python 的干净机器上运行，确认能否启动。
- [ ] **路径兼容性**: 测试在中文路径（如 `C:\用户\桌面\维保工具\`) 和含空格路径下运行。
- [ ] **U盘运行**: 从外部驱动器直接运行，确认自检通过。

## 2. 命令行自检 (CLI & Startup)
- [ ] **版本号确认**: `YBKJ-WorkFlow.exe --version` 确认版本为 `V0.8-windows-build-test`。
- [ ] **系统自检**: `YBKJ-WorkFlow.exe --self-check` 确认目录权限、资源存在性均为 `[OK]`。
- [ ] **静默诊断**: `YBKJ-WorkFlow.exe --no-gui-diagnose` 运行无报错。

## 3. 持久化与资源 (Persistence)
- [ ] **运行时目录**: 确认 `datapool/`, `logs/`, `outputs/`, `reports/` 自动创建。
- [ ] **数据库写测试**: 录入一条数据，关闭重启，数据不丢失。
- [ ] **静态资源**: 确认 UI 中的 Logo 图标正常显示（验证 `get_resource_path` 映射）。
- [ ] **文档访问**: 确认 `docs/` 目录下的 Markdown 文件在打包后依然可被程序或用户读取。

## 4. 业务功能验证 (Business Logic)
- [ ] **数据录入**: 成功粘贴 10 条以上维保文本。
- [ ] **智能解析**: 解析结果准确，且包含“解析提示”。
- [ ] **Excel 导出**: 成功在 `outputs/excel/` 生成 `.xlsx` 文件且能正常打开。
- [ ] **质量检查**: 成功生成 `.md` 格式的质量检查报告。

---
**反馈渠道**: 记录所有失败项于 `WINDOWS_BUILD_TEST_RECORD.md` 的问题记录表中，并附带 `logs/app.log`。
