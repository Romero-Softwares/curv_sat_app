# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path


PROJECT_DIR = Path(SPECPATH)

a = Analysis(
    [str(PROJECT_DIR / "license_generator.py")],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=[(str(PROJECT_DIR / "licensing" / "issuer_private_key.json"), "licensing")],
    hiddenimports=[],
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
    name="GeradorChaveCurvSat",
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
    icon=str(PROJECT_DIR / "assets" / "icons" / "logo.ico"),
)
