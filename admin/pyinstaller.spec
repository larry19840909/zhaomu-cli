# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for zhaomu admin panel — onedir mode."""

import sys
from pathlib import Path

block_cipher = None

# 前端静态文件目录
_frontend_dist = Path(__file__).parent / "frontend" / "dist"

datas = []
if _frontend_dist.exists():
    datas.append((str(_frontend_dist), "frontend/dist"))

a = Analysis(
    ['admin/server.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'argon2',
        'argon2._ffi',
        'aiosqlite',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='zhaomu-admin',
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
