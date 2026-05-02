# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


block_cipher = None

# Run PyInstaller from the project root directory.
# Example:
#   python -m PyInstaller packaging\windows\ybkj_workflow.spec --noconfirm --clean
project_root = Path.cwd()
app_entry = project_root / "app.py"

if not app_entry.exists():
    raise SystemExit(
        "app.py not found in current working directory. "
        "Please run PyInstaller from the project root."
    )

datas = [
    (str(project_root / "assets"), "assets"),
    (str(project_root / "docs"), "docs"),
    (str(project_root / "dataset" / "samples"), str(Path("dataset") / "samples")),
    (str(project_root / "requirements.txt"), "."),
]

templates_dir = project_root / "templates"
if templates_dir.exists():
    datas.append((str(templates_dir), "templates"))

a = Analysis(
    [str(app_entry)],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtPrintSupport",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "matplotlib",
        "notebook",
        "IPython",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.datas = [
    entry
    for entry in a.datas
    if not any(
        blocked in entry[0]
        for blocked in (
            "logs",
            "datapool",
            "reports",
            "outputs",
            "__pycache__",
        )
    )
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

icon_path = project_root / "assets" / "icon.ico"

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="YBKJ-WorkFlow",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="YBKJ-WorkFlow",
)
