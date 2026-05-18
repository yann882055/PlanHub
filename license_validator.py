"""
license_validator.py — PlanHub v1.0
Système de validation de licence.
Accepte les fichiers .dat (format LFORGE20) et les clés JSON.
"""

import os
import sys
import json
import glob
import datetime
import tkinter as tk
from tkinter import messagebox


def _get_app_dir() -> str:
    """Dossier de l'exécutable (ou du script en développement)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


LICENSE_FILE = os.path.join(_get_app_dir(), "planhub.lic")
DEMO_KEY = "PLANHUB-DEMO-2024-XXXX"

# ── Global licence courante (lu par MainWindow pour la status bar) ────
CURRENT_LICENSE = {
    "client": "Démo",
    "type": "DEMO",
    "valid": False,
    "expiry": "",
}


def _extract_client_name(dat_basename: str) -> str:
    """
    Extrait le nom client depuis le nom du fichier .dat.
    Exemples :
      licence_YANN_PlanHub.dat  →  YANN
      YANN.dat                  →  YANN
      DamFinder.dat             →  DamFinder
      licence_EDF_PlanHub.dat   →  EDF
    """
    stem = os.path.splitext(dat_basename)[0]
    parts = stem.split("_")
    if len(parts) >= 3 and parts[0].lower() in ("licence", "license"):
        # licence_CLIENT_PRODUCT → CLIENT (tout entre premier et dernier underscore)
        return "_".join(parts[1:-1])
    elif len(parts) == 2 and parts[0].lower() in ("licence", "license"):
        return parts[1]
    else:
        return stem  # nom brut


class LicenseValidator:
    def __init__(self):
        self.valid = False
        self.client = "Démo"
        self.expiry = None
        self.license_type = "DEMO"

    # ── Recherche fichier .dat (LFORGE20) ────────────────────────────
    def _find_dat_license(self):
        """Cherche un fichier .dat LFORGE20 dans le dossier de l'application."""
        app_dir = _get_app_dir()
        for dat_file in glob.glob(os.path.join(app_dir, "*.dat")):
            try:
                with open(dat_file, "r", encoding="utf-8", errors="ignore") as f:
                    first_line = f.readline().strip()
                if first_line == "LFORGE20":
                    name = _extract_client_name(os.path.basename(dat_file))
                    return {
                        "client": name,
                        "expiry": "2099-12-31",
                        "type": "FULL",
                    }
            except Exception:
                continue
        return None

    # ── Fichier JSON .lic ─────────────────────────────────────────────
    def _load_license_file(self):
        if not os.path.exists(LICENSE_FILE):
            return None
        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Ignorer le .lic si un .dat est présent (priorité .dat)
            return data
        except Exception:
            return None

    def _validate_key(self, key: str) -> dict:
        if key.strip().upper() == DEMO_KEY:
            expiry = datetime.date.today() + datetime.timedelta(days=30)
            return {
                "key": key,
                "client": "Utilisateur Démo",
                "expiry": expiry.isoformat(),
                "type": "DEMO",
            }
        return None

    # ── Point d'entrée principal ──────────────────────────────────────
    def check_and_show(self):
        global CURRENT_LICENSE

        # 1. Fichier .dat (LFORGE20) — licence complète, priorité maximale
        dat = self._find_dat_license()
        if dat:
            self.valid = True
            self.client = dat["client"]
            self.expiry = datetime.date.fromisoformat(dat["expiry"])
            self.license_type = dat["type"]
            # Sauvegarder dans .lic pour que la status bar survive aux sessions
            self._save_license({
                "client": self.client,
                "expiry": dat["expiry"],
                "type": "FULL",
                "source": "dat",
            })
            CURRENT_LICENSE = {
                "client": self.client,
                "type": "FULL",
                "valid": True,
                "expiry": dat["expiry"],
            }
            return

        # 2. Fichier JSON .lic
        data = self._load_license_file()
        if data:
            try:
                # Si le .lic provient d'un .dat → licence complète sans expiry check
                if data.get("source") == "dat":
                    self.valid = True
                    self.client = data.get("client", "Client")
                    self.expiry = datetime.date.fromisoformat(data.get("expiry", "2099-12-31"))
                    self.license_type = "FULL"
                    CURRENT_LICENSE = {
                        "client": self.client,
                        "type": "FULL",
                        "valid": True,
                        "expiry": data.get("expiry", "2099-12-31"),
                    }
                    return

                expiry = datetime.date.fromisoformat(data.get("expiry", ""))
                if expiry >= datetime.date.today():
                    self.valid = True
                    self.client = data.get("client", "Client")
                    self.expiry = expiry
                    self.license_type = data.get("type", "FULL")
                    CURRENT_LICENSE = {
                        "client": self.client,
                        "type": self.license_type,
                        "valid": True,
                        "expiry": data.get("expiry", ""),
                    }
                    return
                else:
                    self._show_expired_dialog(data.get("client", ""), expiry)
                    return
            except Exception:
                pass

        # 3. Pas de licence — dialogue d'activation
        self._show_activation_dialog()

    # ── Dialogues Tkinter (utilisent wait_window, pas mainloop) ───────
    def _show_expired_dialog(self, client, expiry):
        global CURRENT_LICENSE
        root = tk.Tk()
        root.withdraw()
        msg = (
            f"La licence PlanHub de {client} a expiré le {expiry.strftime('%d/%m/%Y')}.\n\n"
            "Copiez votre fichier .dat dans le dossier du logiciel, ou contactez votre revendeur.\n\n"
            "Le logiciel continue en mode DÉMO (30 jours)."
        )
        messagebox.showwarning("Licence expirée — PlanHub", msg, parent=root)
        root.destroy()
        self.valid = True
        self.client = f"{client} (Expiré)"
        self.expiry = datetime.date.today() + datetime.timedelta(days=30)
        self.license_type = "DEMO"
        CURRENT_LICENSE = {
            "client": self.client,
            "type": "DEMO",
            "valid": True,
            "expiry": self.expiry.isoformat(),
        }
        self._save_demo()

    def _show_activation_dialog(self):
        global CURRENT_LICENSE
        root = tk.Tk()
        root.withdraw()

        dialog = tk.Toplevel(root)
        dialog.title("Activation PlanHub v1.0")
        dialog.geometry("500x310")
        dialog.resizable(False, False)
        dialog.configure(bg="#FFFFFF")
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 500) // 2
        y = (dialog.winfo_screenheight() - 310) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="🔑 Activation PlanHub v1.0",
                 font=("Segoe UI", 14, "bold"), bg="#FFFFFF", fg="#1565C0").pack(pady=(20, 4))
        tk.Label(dialog,
                 text="Copiez votre fichier .dat dans le dossier du logiciel et relancez,",
                 font=("Segoe UI", 9), bg="#FFFFFF", fg="#1565C0").pack()
        tk.Label(dialog,
                 text="ou entrez une clé ci-dessous (clé DÉMO gratuite disponible) :",
                 font=("Segoe UI", 9), bg="#FFFFFF", fg="#616161").pack(pady=(0, 12))

        frame = tk.Frame(dialog, bg="#FFFFFF")
        frame.pack(padx=30, fill="x")

        key_var = tk.StringVar(value=DEMO_KEY)
        tk.Entry(frame, textvariable=key_var, font=("Segoe UI", 11),
                 width=38, relief="solid", bd=1).pack(pady=5, ipady=6)

        msg_var = tk.StringVar()
        tk.Label(dialog, textvariable=msg_var, font=("Segoe UI", 9),
                 bg="#FFFFFF", fg="#D32F2F").pack(pady=4)

        activated = [False]

        def activate():
            key = key_var.get().strip()
            data = self._validate_key(key)
            if data:
                self._save_license(data)
                self.valid = True
                self.client = data["client"]
                self.expiry = datetime.date.fromisoformat(data["expiry"])
                self.license_type = data["type"]
                CURRENT_LICENSE["client"] = self.client
                CURRENT_LICENSE["type"] = self.license_type
                CURRENT_LICENSE["valid"] = True
                CURRENT_LICENSE["expiry"] = data["expiry"]
                activated[0] = True
                dialog.destroy()
            else:
                msg_var.set("❌ Clé invalide. Essayez : PLANHUB-DEMO-2024-XXXX")

        def quit_app():
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg="#FFFFFF")
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="  Activer  ", command=activate,
                  bg="#1565C0", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2", padx=10, pady=6).pack(side="left", padx=5)
        tk.Button(btn_frame, text="  Quitter  ", command=quit_app,
                  bg="#E0E0E0", fg="#212121", font=("Segoe UI", 10),
                  relief="flat", cursor="hand2", padx=10, pady=6).pack(side="left", padx=5)

        tk.Label(dialog, text=f"Clé démo : {DEMO_KEY}",
                 font=("Segoe UI", 8), bg="#FFFFFF", fg="#9E9E9E").pack(pady=(4, 0))

        dialog.protocol("WM_DELETE_WINDOW", quit_app)

        root.wait_window(dialog)
        root.destroy()

        if not activated[0]:
            sys.exit(0)

    # ── Sauvegarde ────────────────────────────────────────────────────
    def _save_license(self, data: dict):
        try:
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _save_demo(self):
        self._save_license({
            "key": DEMO_KEY,
            "client": "Utilisateur Démo",
            "expiry": (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
            "type": "DEMO",
        })
