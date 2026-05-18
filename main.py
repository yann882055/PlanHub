"""
PlanHub v1.0 — Du DQE à Primavera P6 en quelques clics
Point d'entrée principal
"""

# ══════════════════════════════════════════════════════════
# SYSTÈME DE LICENCE — NE JAMAIS SUPPRIMER CES 2 LIGNES
from license_validator import LicenseValidator
LicenseValidator().check_and_show()
# ══════════════════════════════════════════════════════════

import sys
import os
import subprocess
import customtkinter as ctk

from ui.splash import SplashScreen
from ui.main_window import MainWindow


def create_desktop_shortcut():
    """Crée un raccourci Bureau au premier lancement (exe seulement)."""
    if not getattr(sys, 'frozen', False):
        return  # Mode développement — pas de raccourci

    try:
        exe_path = sys.executable
        work_dir = os.path.dirname(exe_path)

        # Dossier Bureau (fonctionne même si OneDrive déplace le Bureau)
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.isdir(desktop):
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            desktop = winreg.QueryValueEx(key, "Desktop")[0]

        shortcut_path = os.path.join(desktop, "PlanHub.lnk")
        if os.path.exists(shortcut_path):
            return  # Déjà créé

        # Création via PowerShell WScript.Shell (aucune dépendance externe)
        # IconLocation = l'exe lui-même (icône embarquée index 0)
        ps_cmd = (
            f'$s = (New-Object -COM WScript.Shell).CreateShortcut("{shortcut_path}");'
            f'$s.TargetPath = "{exe_path}";'
            f'$s.WorkingDirectory = "{work_dir}";'
            f'$s.IconLocation = "{exe_path}, 0";'
            f'$s.Description = "PlanHub v1.0 - Du DQE a Primavera P6";'
            f'$s.Save()'
        )
        subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            capture_output=True, timeout=15
        )
    except Exception:
        pass  # Silencieux — le raccourci est optionnel


def main():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Raccourci bureau (premier lancement)
    create_desktop_shortcut()

    # Splash screen
    splash = SplashScreen()
    splash.show()

    # Fenêtre principale
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
