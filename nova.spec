# PyInstaller spec for nova.exe CLI (operator + kernel client)
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

repo = Path(SPECPATH)

a = Analysis(
    [str(repo / "nova" / "cli.py")],
    pathex=[str(repo)],
    binaries=[],
    datas=[
        (str(repo / "configs"), "configs"),
    ],
    hiddenimports=[
        "nova.runtime_factory",
        "nova.lawful_llm",
        "operator_kernel",
        "operator_kernel.memory",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="nova",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
