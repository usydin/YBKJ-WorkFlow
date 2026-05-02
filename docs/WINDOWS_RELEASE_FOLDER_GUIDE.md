# Windows 发布目录说明 (YBKJ-WorkFlow)

本文档旨在说明打包后的发布包目录结构，帮助用户及测试人员了解文件用途及数据维护方法。

## 1. 目录结构概览 (dist 目录)

打包完成后，`dist\YBKJ-WorkFlow` 目录即为完整的绿色版发布包，结构如下：

```text
YBKJ-WorkFlow/
├── YBKJ-WorkFlow.exe        # 主程序 (启动入口)
├── assets/                  # 静态资源 (Logo, 图标等)
├── docs/                    # 用户文档与说明
├── dataset/                 # 数据集与样例 (仅供参考)
│   └── samples/             # 预置的测试样例
├── _internal/               # 程序内部依赖 (Python 运行环境及 DLL)
│
│   # --- 以下目录为程序运行后自动生成 ---
├── datapool/                # 数据持久化目录 (极其重要)
│   ├── sqlite/              # SQLite 数据库
│   └── jsonl/               # 原始输入备份
├── logs/                    # 运行日志目录
├── reports/                 # 导出的各类报告 (如质量检查报告)
├── outputs/                 # 业务产出 (Excel, Word 等)
└── config.local.json        # 本地个性化配置文件
```

## 2. 文件用途分类

### 2.1 核心程序文件
- **YBKJ-WorkFlow.exe**: 必须双击此文件启动应用。
- **_internal/**: 包含 Python 解释器和所有依赖库。**绝对不可删除或移动**，否则程序无法启动。

### 2.2 数据持久化文件 (需重点备份)
- **datapool/sqlite/ybkj_workflow.db**: 存储了所有已录入和解析的维保数据、员工别名映射。
- **datapool/jsonl/raw_inputs.jsonl**: 存储了所有录入的原始文本备份，用于数据追溯。

### 2.3 运行生成文件 (可清理)
- **logs/**: 若程序运行正常且磁盘空间紧张，可定期清理旧日志。
- **reports/**: 历史质量检查报告。
- **outputs/**: 导出的 Excel 结果，用户应将其移动到自己的工作目录。

## 3. 常见维护操作

### 3.1 如何迁移绿色版？
直接将整个 `YBKJ-WorkFlow` 文件夹（包含主程序和 `_internal`）拷贝到新电脑或 U 盘即可。由于采用相对路径，数据会随程序一起移动。

### 3.2 如何备份数据？
定期将 `datapool` 目录整体拷贝到安全位置。

### 3.3 如何重置应用？
若需彻底清空所有数据重新开始，请删除 `datapool` 目录和 `config.local.json` 文件。

### 3.4 如何查看日志？
若程序发生闪退或报错，请查看 `logs\app.log` 或 `logs\error.log`。

### 3.5 提交问题反馈
若遇到无法解决的问题，请提供以下信息给开发者：
1. 报错截图。
2. `logs` 目录下的日志文件。
3. `exe --self-check` 的命令输出。
