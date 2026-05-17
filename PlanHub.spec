# -*- mode: python ; coding: utf-8 -*-
# PlanHub.spec — Fichier de compilation PyInstaller
# Généré pour PlanHub v1.0

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── Collecter les données customtkinter (thèmes, images)
ctk_data = collect_data_files('customtkinter')

# ── Données du projet à inclure
added_files = [
    ('license_validator.py', '.'),
    ('data', 'data'),
    ('assets', 'assets'),
] + ctk_data

# ── Imports cachés nécessaires
hidden_imports = [
    'customtkinter',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL._tkinter_finder',
    'matplotlib',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.pyplot',
    'pandas',
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.utils',
    'reportlab',
    'reportlab.lib',
    'reportlab.lib.pagesizes',
    'reportlab.platypus',
    'reportlab.lib.styles',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.simpledialog',
    'json',
    'datetime',
    'hashlib',
    'threading',
    'copy',
    'uuid',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5', 'PyQt6', 'wx', 'gi',
        'IPython', 'jupyter', 'notebook',
        'scipy', 'sklearn', 'tensorflow',
        'test', 'unittest',
    ],
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
    name='PlanHub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # Compresser l'exe (réduit la taille)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # Pas de fenêtre console (application GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/logo.ico',   # Décommentez si vous avez un fichier .ico
    version_file=None,
)
