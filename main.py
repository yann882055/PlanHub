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
import customtkinter as ctk

from ui.splash import SplashScreen
from ui.main_window import MainWindow


def main():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Splash screen
    splash = SplashScreen()
    splash.show()

    # Fenêtre principale
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
