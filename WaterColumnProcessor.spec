# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src'), ('assets/app_icon.png', 'assets'), ('assets/app_icon.icns', 'assets')],
    hiddenimports=['numpy', 'pandas', 'matplotlib', 'matplotlib.backends.backend_tkagg'],
    hookspath=['.'],
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
    [],
    exclude_binaries=True,
    name='WaterColumnProcessor',
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
    icon=['/Users/rajeevkumar/PycharmProjects/WC_SensorData_v1/assets/app_icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WaterColumnProcessor',
)
app = BUNDLE(
    coll,
    name='WaterColumnProcessor.app',
    icon='/Users/rajeevkumar/PycharmProjects/WC_SensorData_v1/assets/app_icon.icns',
    bundle_identifier='com.watercolumn.processor',
)
