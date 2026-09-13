# -*- mode: python ; coding: utf-8 -*-
# macOS 打包配置：pyinstaller build_mac.spec
# 产物：dist/字幕遮挡工具.app（也可独立分发，替代手动构建的 .app）
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='字幕遮挡工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='字幕遮挡工具.app',
    icon='icon.icns',
    bundle_identifier='com.example.ccblocker',
    info_plist={
        'NSHighResolutionCapable': True,
    },
)
