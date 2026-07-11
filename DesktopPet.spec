# -*- mode: python ; coding: utf-8 -*-

# ----------------------------------------------------------------
# Unused PyQt6 Python-level modules
# ----------------------------------------------------------------
UNUSED_QT_MODULES = [
    'PyQt6.QtBluetooth',
    'PyQt6.QtDBus',
    'PyQt6.QtDesigner',
    'PyQt6.QtHelp',
    'PyQt6.QtMultimedia',
    'PyQt6.QtMultimediaWidgets',
    'PyQt6.QtNetwork',
    'PyQt6.QtNfc',
    'PyQt6.QtOpenGL',
    'PyQt6.QtOpenGLWidgets',
    'PyQt6.QtPdf',
    'PyQt6.QtPdfWidgets',
    'PyQt6.QtPositioning',
    'PyQt6.QtPrintSupport',
    'PyQt6.QtQml',
    'PyQt6.QtQuick',
    'PyQt6.QtQuickWidgets',
    'PyQt6.QtSensors',
    'PyQt6.QtSerialPort',
    'PyQt6.QtSql',
    'PyQt6.QtStateMachine',
    'PyQt6.QtSvg',
    'PyQt6.QtSvgWidgets',
    'PyQt6.QtTest',
    'PyQt6.QtTextToSpeech',
    'PyQt6.QtWebChannel',
    'PyQt6.QtXml',
]

# ----------------------------------------------------------------
# Heavy libs definitely NOT used by our code or rembg
# (numba/llvmlite are JIT compilers — rembg doesn't use them)
# ----------------------------------------------------------------
EXCLUDE_UNUSED_HEAVY = [
    'numba',
    'llvmlite',
]

# ----------------------------------------------------------------
# Qt6 DLLs we actually need
# ----------------------------------------------------------------
KEEP_DLLS = {
    'Qt6Core.dll',
    'Qt6Gui.dll',
    'Qt6Widgets.dll',
    # VC++ runtimes — required by Qt DLLs
    'msvcp140.dll',
    'msvcp140_1.dll',
    'msvcp140_2.dll',
    'msvcp140_atomic_wait.dll',
    'msvcp140_codecvt_ids.dll',
    'vcruntime140.dll',
    'vcruntime140_1.dll',
    'vcruntime140_threads.dll',
    'concrt140.dll',
    'vccorlib140.dll',
    # D3D compiler — needed for Qt rendering
    'd3dcompiler_47.dll',
}

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/assets', 'assets')],
    hiddenimports=[
        # rembg — lazy-imported in image_processor.py, NOT detected by static analysis
        'rembg',
        'rembg.session_factory',
        'rembg.bg',
        # onnxruntime — rembg's ML runtime, often needs explicit listing
        'onnxruntime',
        'onnxruntime.capi',
        # scikit-image filters used by rembg's post-processing
        'skimage',
        'skimage.filters',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=UNUSED_QT_MODULES + EXCLUDE_UNUSED_HEAVY,
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
    name='DesktopPet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
