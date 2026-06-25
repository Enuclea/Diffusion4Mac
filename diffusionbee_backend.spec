# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

datas = []
binaries = []
hiddenimports = ['psutil', 'diffusers.pipelines.ideogram4', 'diffusers.pipelines.ideogram4.pipeline_ideogram4', 'diffusers.pipelines.ideogram4.pipeline_output', 'diffusers.pipelines.ideogram4.prompt_enhancer']

for pkg in ['transformers', 'tokenizers', 'huggingface_hub', 'diffusers', 'peft', 'accelerate']:
    datas += collect_data_files(pkg, include_py_files=False)
    datas += copy_metadata(pkg)


a = Analysis(
    ['backends/stable_diffusion/diffusionbee_backend.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='diffusionbee_backend',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='diffusionbee_backend',
)
