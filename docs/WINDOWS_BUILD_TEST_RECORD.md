# Windows 打包测试记录模板 (V0.8-windows-build-test)

本模板用于记录在 Windows 11 / Windows 10 环境下执行打包与真机测试的过程，方便追踪问题与验证修复。

## 1. 测试基本信息
- **测试日期**: 2026-05-xx
- **测试人员**: 
- **测试机器**: 
- **Windows 版本**: (例如: Windows 11 Pro 23H2)
- **系统架构**: [ ] 64位 / [ ] 32位
- **Python 版本**: 
- **PyInstaller 版本**: 
- **打包方式**: [ ] build_windows.bat / [ ] 手动执行 pyinstaller
- **Git 提交号**: (使用 `git rev-parse --short HEAD`)

## 2. 源码运行测试 (打包前)
- [ ] `python app.py --version`: [ ] 通过 / [ ] 失败
- [ ] `python app.py --self-check`: [ ] 通过 / [ ] 失败
- [ ] `python app.py --no-gui-diagnose`: [ ] 通过 / [ ] 失败
- [ ] `python app.py` (GUI 启动): [ ] 通过 / [ ] 失败

## 3. 打包过程记录
- **是否成功生成 dist 目录**: [ ] 是 / [ ] 否
- **EXE 名称**: (例如: YBKJ-WorkFlow.exe)
- **dist 目录大小**: (例如: 120MB)
- **是否出现 Warning**: (若有请记录关键信息)
- **是否出现 Missing Module**: 
- **是否出现路径错误**: 

## 3.1 已验证成功的命令
- [ ] `python -m PyInstaller packaging\windows\ybkj_workflow.spec --noconfirm --clean`
- [ ] `dist\YBKJ-WorkFlow\YBKJ-WorkFlow.exe --version`
- [ ] `dist\YBKJ-WorkFlow\YBKJ-WorkFlow.exe --self-check`
- [ ] `dist\YBKJ-WorkFlow\YBKJ-WorkFlow.exe --no-gui-diagnose`
- [ ] `dist\YBKJ-WorkFlow\YBKJ-WorkFlow.exe`

## 4. 打包后命令行测试
- [ ] `exe --version`: [ ] 通过 / [ ] 失败
- [ ] `exe --self-check`: [ ] 通过 / [ ] 失败
- [ ] `exe --no-gui-diagnose`: [ ] 通过 / [ ] 失败

## 5. 打包后 GUI 功能测试
- [ ] **数据录入页**: 粘贴、载入样例是否正常
- [ ] **OCR暂存页**: 页面加载、粘贴文本是否正常
- [ ] **智能解析页**: 解析逻辑、列表展示是否正常
- [ ] **人工确认页**: 字段编辑、人员映射是否正常
- [ ] **员工映射页**: 搜索、新增别名是否正常
- [ ] **数据质量页**: 检查运行、报告生成是否正常
- [ ] **统计分析页**: 图表/数据展示是否正常
- [ ] **日报生成页**: 预览、导出 TXT 是否正常
- [ ] **Excel导出页**: 范围选择、导出操作是否正常

## 6. 文件写入与持久化测试
- [ ] **datapool/sqlite**: 数据库文件是否生成且可读写
- [ ] **datapool/jsonl**: 原始记录是否正常备份
- [ ] **logs/app.log**: 运行日志是否正常产生
- [ ] **reports/quality**: 质量报告是否可导出
- [ ] **outputs/excel**: Excel 文件是否可生成且内容正确

## 7. 路径兼容性测试
- [ ] **英文路径**: (如 `D:\Tools\YBKJ-WorkFlow\`)
- [ ] **中文路径**: (如 `C:\用户\桌面\维保日报通\`)
- [ ] **含空格路径**: (如 `C:\Program Files\YBKJ WorkFlow\`)
- [ ] **移动设备**: (从 U 盘直接运行)

## 8. 绿色迁移测试
- [ ] 将 `dist\YBKJ-WorkFlow` 整体拷贝到另一台**未安装 Python** 的机器
- [ ] 运行自检命令 `exe --self-check`
- [ ] 启动 GUI 并录入/导出数据

## 9. 问题记录表
| 编号 | 问题现象 | 发生环境 | 复现步骤 | 初步判断 | 处理状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | | | | | |

## 9.1 已知问题
- `QFont::setPointSize: Point size <= 0 (-1), must be greater than 0`
  - 当前状态: 非阻塞
  - 影响评估: 当前不影响启动、页面切换、主题切换和正常关闭
  - 后续动作: 若真机出现字体显示异常，再专项修复样式系统

## 10. 测试结论
- [ ] **可进入下一轮**: 所有核心功能在打包后运行正常。
- [ ] **需要修复后重测**: 存在打包导致的功能缺失或崩溃。
- [ ] **暂缓打包**: 存在严重的底层环境兼容性问题。
