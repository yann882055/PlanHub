"""
license_validator.py — PlanHub v1.0
Système de validation de licence.
REMPLACER ce fichier par votre vrai validateur de licence.
"""

import os
import sys
import json
import hashlib
import datetime
import tkinter as tk
from tkinter import messagebox


LICENSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "planhub.lic")
# Clé de démonstration — à remplacer par votre propre système
DEMO_KEY = "PLANHUB-DEMO-2024-XXXX"


class LicenseValidator:
    def __init__(self):
        self.valid = False
        self.client = "Démo"
        self.expiry = None
        self.license_type = "DEMO"

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    def _load_license_file(self):
        if not os.path.exists(LICENSE_FILE):
            return None
        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _validate_key(self, key: str) -> dict:
        """Valide une clé de licence. Retourne les infos ou None si invalide."""
        # Clé démo toujours valide
        if key.strip().upper() == DEMO_KEY:
            expiry = datetime.date.today() + datetime.timedelta(days=30)
            return {
                "key": key,
                "client": "Utilisateur Démo",
                "expiry": expiry.isoformat(),
                "type": "DEMO"
            }
        # Logique de validation personnalisée à implémenter
        # Exemple : vérification serveur, hash, etc.
        return None

    def check_and_show(self):
        """Point d'entrée principal — appelé avant tout affichage."""
        data = self._load_license_file()

        if data:
            # Vérifier expiration
            try:
                expiry = datetime.date.fromisoformat(data.get("expiry", ""))
                if expiry >= datetime.date.today():
                    self.valid = True
                    self.client = data.get("client", "Client")
                    self.expiry = expiry
                    self.license_type = data.get("type", "FULL")
                    return  # Licence valide, on continue
                else:
                    self._show_expired_dialog(data.get("client", ""), expiry)
            except Exception:
                pass

        # Pas de licence valide — afficher dialogue d'activation
        self._show_activation_dialog()

    def _show_expired_dialog(self, client, expiry):
        root = tk.Tk()
        root.withdraw()
        msg = (
            f"La licence PlanHub de {client} a expiré le {expiry.strftime('%d/%m/%Y')}.\n\n"
            "Contactez votre revendeur pour renouveler votre licence.\n\n"
            "Le logiciel va continuer en mode DÉMO (30 jours)."
        )
        messagebox.showwarning("Licence expirée — PlanHub", msg, parent=root)
        root.destroy()
        # Continuer en mode démo
        self.valid = True
        self.client = f"{client} (Expiré)"
        self.expiry = datetime.date.today() + datetime.timedelta(days=30)
        self.license_type = "DEMO"
        self._save_demo()

    def _show_activation_dialog(self):
        root = tk.Tk()
        root.withdraw()
        root.title("Activation PlanHub")

        dialog = tk.Toplevel(root)
        dialog.title("Activation PlanHub v1.0")
        dialog.geometry("480x280")
        dialog.resizable(False, False)
        dialog.configure(bg="#FFFFFF")
        dialog.grab_set()

        # Centrer
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 480) // 2
        y = (dialog.winfo_screenheight() - 280) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="🔑 Activation PlanHub v1.0",
                 font=("Segoe UI", 14, "bold"), bg="#FFFFFF", fg="#1565C0").pack(pady=(20, 5))
        tk.Label(dialog, text="Entrez votre clé de licence ou utilisez la clé DÉMO :",
                 font=("Segoe UI", 10), bg="#FFFFFF", fg="#616161").pack(pady=(0, 15))

        frame = tk.Frame(dialog, bg="#FFFFFF")
        frame.pack(padx=30, fill="x")

        key_var = tk.StringVar(value=DEMO_KEY)
        entry = tk.Entry(frame, textvariable=key_var, font=("Segoe UI", 11),
                         width=35, relief="solid", bd=1)
        entry.pack(pady=5, ipady=6)

        msg_var = tk.StringVar()
        msg_label = tk.Label(dialog, textvariable=msg_var,
                              font=("Segoe UI", 9), bg="#FFFFFF", fg="#D32F2F")
        msg_label.pack(pady=5)

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
                activated[0] = True
                dialog.destroy()
                root.destroy()
            else:
                msg_var.set("❌ Clé invalide. Utilisez PLANHUB-DEMO-2024-XXXX pour la démo.")

        def quit_app():
            root.destroy()
            sys.exit(0)

        btn_frame = tk.Frame(dialog, bg="#FFFFFF")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="  Activer  ", command=activate,
                  bg="#1565C0", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2", padx=10, pady=6).pack(side="left", padx=5)
        tk.Button(btn_frame, text="  Quitter  ", command=quit_app,
                  bg="#E0E0E0", fg="#212121", font=("Segoe UI", 10),
                  relief="flat", cursor="hand2", padx=10, pady=6).pack(side="left", padx=5)

        tk.Label(dialog, text=f"Clé démo : {DEMO_KEY}",
                 font=("Segoe UI", 8), bg="#FFFFFF", fg="#9E9E9E").pack(pady=(5, 0))

        dialog.protocol("WM_DELETE_WINDOW", quit_app)
        root.mainloop()

        if not activated[0]:
            sys.exit(0)

    def _save_license(self, data: dict):
        try:
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _save_demo(self):
        data = {
            "key": DEMO_KEY,
            "client": "Utilisateur Démo",
            "expiry": (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
            "type": "DEMO"
        }
        self._save_license(data)
