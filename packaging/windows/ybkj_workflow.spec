# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# 项目根目录定位
# 注意：在 Windows 打包时，打包脚本会 cd 到项目根目录执行，或者 spec 内部通过路径计算定位
# 这里采用基于 spec 文件位置的相对路径计算，确保在 packaging/windows 目录下运行也能找到根
project_root = os.path.abspath(os.path.join(os.getcwd(), '../../'))
if not os.path.exists(os.path.join(project_root, 'app.py')):
    # 如果当前目录不是项目根，尝试使用 spec 所在目录计算
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

print(f"[Spec] Detected project root: {project_root}")

# 需要打包进 EXE 的静态资源
added_files = [
    (os.path.join(project_root, 'assets'), 'assets'),
    (os.path.join(project_root, 'docs'), 'docs'),
    (os.path.join(project_root, 'dataset/samples'), 'dataset/samples'),
    (os.path.join(project_root, 'requirements.txt'), '.'),
]

# 如果存在 templates 目录也加入
if os.path.exists(os.path.join(project_root, 'templates')):
    added_files.append((os.path.join(project_root, 'templates'), 'templates'))

a = Analysis(
    [os.path.join(project_root, 'app.py')],
    pathex=[project_root],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtPrintSupport', # 常用打印支持
        'openpyxl',
        'pandas',
        'rapidfuzz',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 排除不需要打包的库，减少体积
    excludes=[
        'tkinter', 'unittest', 'email', 'http', 'xml', 'pydoc',
        'matplotlib', 'notebook', 'IPython' # 确保这些不被误抓
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 显式排除运行产物目录，避免被 PyInstaller 误抓取（虽然 datas 已经指定了包含项）
a.datas = [d for d in a.datas if not any(x in d[0] for x in [
    'logs', 'datapool', 'reports', 'outputs', '__pycache__', '.git', '.venv', '.idea', '.vscode'
])]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='YBKJ-WorkFlow', # 如果中文名 '维保日报通' 有编码问题，请改回此名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # V0.8 保持 True 以便排错；稳定后改为 False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 图标路径：优先使用 assets/icon.ico，不存在则不设置
    icon=os.path.join(project_root, 'assets', 'icon.ico') if os.path.exists(os.path.join(project_root, 'assets', 'icon.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='YBKJ-WorkFlow', # 输出目录名
)
