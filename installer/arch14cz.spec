# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['..\\bin\\start_arch14cz.py'],
    pathex=['..\\venv\\Lib\\site-packages\\'],
    binaries=[],
    datas=[],
    hiddenimports=[
		'arch14cz_backend',
		'deposit_gui',
		'networkit.base',
		'networkit.helpers',
		'networkit.traversal',
		'scipy.io',
		'xml.dom',
	],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tcl', 'tk', 'wx', 'h5py', 'sip', 'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='arch14cz',
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
    icon='arch14cz_icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='arch14cz',
)
