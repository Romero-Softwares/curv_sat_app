# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path


PROJECT_DIR = Path(SPECPATH).parent
VERSION_INFO_FILE = PROJECT_DIR / 'packaging' / 'version_info.txt'


a = Analysis(
    [str(PROJECT_DIR / 'main.py')],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=[(str(PROJECT_DIR / 'assets'), 'assets')],
    hiddenimports=['scipy', 'curvsat.application'],
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
    name='ASCC-System-1.0.4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(PROJECT_DIR / 'assets' / 'icons' / 'logo.ico')],
    version=str(VERSION_INFO_FILE),
)
