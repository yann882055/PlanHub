# -*- mode: python ; coding: utf-8 -*-
# PlanHub.spec — Fichier de compilation PyInstaller v1.1
# Corrigé : collect_submodules ui / core / pages

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── Collecter les données customtkinter (thèmes, images)
ctk_data = collect_data_files('customtkinter')

# ── Sous-modules à forcer (correction ModuleNotFoundError)
ui_mods   = collect_submodules('ui')
core_mods = collect_submodules('core')

# ── Données du projet à inclure dans l'exe
added_files = [
    ('data',              'data'),
    ('ui',                'ui'),
    ('core',              'core'),
    ('license_validator.py', '.'),
] + ctk_data

# ── Imports cachés nécessaires
hidden_imports = (
    ui_mods
    + core_mods
    + [
        # UI interne
        'ui.main_window',
        'ui.sidebar',
        'ui.splash',
        'ui.pages.dashboard',
        'ui.pages.dqe_editor',
        'ui.pages.generate_xer',
        'ui.pages.project_type',
        'ui.pages.resources',
        'ui.pages.report',
        'ui.pages.projects',
        # Core
        'core.xer_generator',
        'core.xer_parser',
        'core.report_engine',
        'core.resource_engine',
        'core.retro_planning',
        'core.library_engine',
        # licence
        'license_validator',
        # GUI
        'customtkinter',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        # Data
        'pandas',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'openpyxl.workbook',
        # Export PDF
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.platypus',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        # Charts
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.pyplot',
        # Stdlib
        'json', 'datetime', 'hashlib', 'threading',
        'copy', 'uuid', 'os', 'sys', 'base64',
        'pathlib', 'shutil', 'subprocess', 'winreg',
    ]
)

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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # GUI — pas de console noire
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.ico', # Icône générée avant compilation
    version_file=None,
)
