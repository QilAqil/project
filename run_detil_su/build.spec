# ============================================================
#  build.spec  –  PyInstaller spec untuk run_detil_su
#
#  Cara build:
#    pyinstaller build.spec
#
#  Output: dist\run_detil_su\run_detil_su.exe
# ============================================================

import os
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

# ── path dasar ───────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(SPEC))   # noqa: F821

# ── berkas data yang ikut dikemas ────────────────────────────
datas = [
    # (sumber,               tujuan di dalam bundle)
    (os.path.join(HERE, "assets"),           "assets"),
    (os.path.join(HERE, "config_detil.yaml"), "."),
]

# ── hidden imports yang sering terlewat PyInstaller ──────────
hiddenimports = [
    "pyautogui",
    "pyperclip",
    "pyscreeze",
    "PIL",
    "PIL._tkinter_finder",
    "yaml",
    "tkinter",
    "tkinter.ttk",
    "tkinter.scrolledtext",
    "threading",
]

a = Analysis(
    scripts        = [os.path.join(HERE, "run_detil_su.py")],
    pathex         = [HERE],
    binaries       = [],
    datas          = datas,
    hiddenimports  = hiddenimports,
    hookspath      = [],
    hooksconfig    = {},
    runtime_hooks  = [],
    excludes       = [
        # buang paket berat yang tidak dipakai
        "torch", "torchvision", "numpy", "pandas",
        "scipy", "sklearn", "matplotlib",
        "easyocr", "cv2", "onnxruntime",
        "transformers", "tokenizers",
    ],
    win_no_prefer_redirects = False,
    win_private_assemblies  = False,
    cipher         = None,
    noarchive      = False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries = True,
    name             = "run_detil_su",
    debug            = False,
    bootloader_ignore_signals = False,
    strip            = False,
    upx              = True,
    console          = False,          # False = tanpa jendela console
    disable_windowed_traceback = False,
    target_arch      = None,
    codesign_identity= None,
    entitlements_file= None,
    icon             = None,           # ganti ke path .ico jika ada
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip    = False,
    upx      = True,
    upx_exclude = [],
    name     = "run_detil_su",
)
