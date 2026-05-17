"""
project_type.py - Page de sélection du type de projet
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

try:
    from core.library_engine import LibraryEngine, PROJECT_TYPES, PROJECT_TYPE_ICONS, PROJECT_TYPE_CATEGORIES
except ImportError:
    # Fallback si le module n'est pas encore disponible
    PROJECT_TYPES = [
        "Barrage en BCR", "Barrage en remblai", "Digue de protection",
        "Aménagement hydroélectrique", "Réseau AEP", "Réseau d'assainissement",
        "Route bitumée", "Piste rurale", "Pont", "Échangeur",
        "Bâtiment administratif", "École", "Hôpital", "Logements",
        "Ligne HTA/HTB", "Centrale solaire", "Centrale thermique",
        "Réseau télécom", "Réseau gaz", "Réseau irrigation",
    ]
    PROJECT_TYPE_ICONS = {
        "Barrage en BCR": "🏔", "Barrage en remblai": "🏔", "Digue de protection": "🌊",
        "Aménagement hydroélectrique": "⚡", "Réseau AEP": "💧", "Réseau d'assainissement": "🚰",
        "Route bitumée": "🛣", "Piste rurale": "🛤", "Pont": "🌉", "Échangeur": "🔀",
        "Bâtiment administratif": "🏢", "École": "🏫", "Hôpital": "🏥", "Logements": "🏘",
        "Ligne HTA/HTB": "⚡", "Centrale solaire": "☀", "Centrale thermique": "🔥",
        "Réseau télécom": "📡", "Réseau gaz": "🔥", "Réseau irrigation": "💦",
    }
    PROJECT_TYPE_CATEGORIES = {
        "HYDRAULIQUE": ["Barrage en BCR", "Barrage en remblai", "Digue de protection",
                        "Aménagement hydroélectrique", "Réseau AEP", "Réseau d'assainissement"],
        "TRANSPORT":   ["Route bitumée", "Piste rurale", "Pont", "Échangeur"],
        "BÂTIMENT":    ["Bâtiment administratif", "École", "Hôpital", "Logements"],
        "ÉNERGIE":     ["Ligne HTA/HTB", "Centrale solaire", "Centrale thermique"],
        "RÉSEAUX":     ["Réseau télécom", "Réseau gaz", "Réseau irrigation"],
    }

    class LibraryEngine:
        def get_description(self, ptype):
            return f"Projet de type « {ptype} »."


# Couleurs par catégorie
CATEGORY_COLORS = {
    "HYDRAULIQUE": "#1565C0",
    "TRANSPORT":   "#E65100",
    "BÂTIMENT":    "#2E7D32",
    "ÉNERGIE":     "#F57F17",
    "RÉSEAUX":     "#6A1B9A",
}


class ProjectTypePage(ctk.CTkFrame):
    """Sélection du type de projet avec grille de boutons par catégorie."""

    def __init__(self, parent, project_state: dict, navigate, update_status):
        super().__init__(parent, fg_color="white")
        self.project_state = project_state
        self.navigate = navigate
        self.update_status = update_status
        self.engine = LibraryEngine()
        self._selected_type = project_state.get("project_type", "")
        self._type_buttons = {}

        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # En-tête
        hdr = ctk.CTkFrame(self, fg_color="#1565C0", corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="🗂  Type de projet",
                     font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                     text_color="white"
                     ).grid(row=0, column=0, padx=20, pady=14, sticky="w")

        ctk.CTkLabel(hdr, text="PlanHub  ›  Type de projet",
                     font=ctk.CTkFont(family="Segoe UI", size=11),
                     text_color="#BBDEFB"
                     ).grid(row=0, column=1, padx=10, pady=14, sticky="e")

        # Corps
        body = ctk.CTkScrollableFrame(self, fg_color="white")
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)

        ctk.CTkLabel(body,
                     text="Sélectionnez le type de projet pour charger la bibliothèque de tâches appropriée.",
                     font=ctk.CTkFont(family="Segoe UI", size=12),
                     text_color="#555555"
                     ).grid(row=0, column=0, padx=24, pady=(16, 8), sticky="w")

        # Grille par catégorie
        row_idx = 1
        for cat, types in PROJECT_TYPE_CATEGORIES.items():
            color = CATEGORY_COLORS.get(cat, "#1565C0")

            # Bandeau catégorie
            cat_frame = ctk.CTkFrame(body, fg_color=color, corner_radius=6)
            cat_frame.grid(row=row_idx, column=0, sticky="ew", padx=24, pady=(12, 4))
            ctk.CTkLabel(cat_frame, text=f"  {cat}",
                         font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                         text_color="white"
                         ).pack(side="left", padx=8, pady=6)
            row_idx += 1

            # Boutons de la catégorie
            btn_grid = ctk.CTkFrame(body, fg_color="white")
            btn_grid.grid(row=row_idx, column=0, sticky="ew", padx=24, pady=2)
            for col_i, ptype in enumerate(types):
                icon = PROJECT_TYPE_ICONS.get(ptype, "📁")
                btn = ctk.CTkButton(
                    btn_grid,
                    text=f"{icon}\n{ptype}",
                    width=160,
                    height=72,
                    corner_radius=8,
                    fg_color="#F5F5F5",
                    hover_color="#BBDEFB",
                    text_color="#212121",
                    border_width=1,
                    border_color="#E0E0E0",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    command=lambda t=ptype: self._select_type(t),
                )
                btn.grid(row=0, column=col_i, padx=6, pady=6)
                self._type_buttons[ptype] = (btn, color)
            row_idx += 1

        # Description du type sélectionné
        desc_frame = ctk.CTkFrame(body, fg_color="#E3F2FD", corner_radius=8, border_width=1, border_color="#90CAF9")
        desc_frame.grid(row=row_idx, column=0, sticky="ew", padx=24, pady=12)
        ctk.CTkLabel(desc_frame, text="ℹ  Description :",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#1565C0"
                     ).pack(anchor="w", padx=12, pady=(8, 2))
        self.desc_label = ctk.CTkLabel(desc_frame,
                                       text="Aucun type sélectionné.",
                                       font=ctk.CTkFont(family="Segoe UI", size=11),
                                       text_color="#333333",
                                       wraplength=700,
                                       justify="left"
                                       )
        self.desc_label.pack(anchor="w", padx=12, pady=(0, 8))
        row_idx += 1

        # Bouton Valider
        self.validate_btn = ctk.CTkButton(
            body,
            text="✔  Valider la sélection",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#1565C0",
            hover_color="#0D47A1",
            text_color="white",
            height=44,
            corner_radius=8,
            state="disabled",
            command=self._validate_selection,
        )
        self.validate_btn.grid(row=row_idx, column=0, pady=16, padx=24, sticky="ew")

        # Mettre en surbrillance si déjà sélectionné
        if self._selected_type:
            self._highlight(self._selected_type)
            self._update_description(self._selected_type)

    def _select_type(self, ptype: str):
        self._selected_type = ptype
        self._highlight(ptype)
        self._update_description(ptype)
        self.validate_btn.configure(state="normal")
        self.update_status(f"Type sélectionné : {ptype}")

    def _highlight(self, ptype: str):
        for t, (btn, color) in self._type_buttons.items():
            if t == ptype:
                btn.configure(fg_color=color, text_color="white", border_color=color)
            else:
                btn.configure(fg_color="#F5F5F5", text_color="#212121", border_color="#E0E0E0")

    def _update_description(self, ptype: str):
        try:
            desc = self.engine.get_description(ptype)
        except Exception:
            desc = f"Projet de type « {ptype} ». Sélectionnez ce type pour charger les tâches types associées."
        self.desc_label.configure(text=desc)

    def _validate_selection(self):
        if not self._selected_type:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un type de projet.")
            return
        self.project_state["project_type"] = self._selected_type
        self.update_status(f"Type de projet validé : {self._selected_type}")
        messagebox.showinfo("Type validé",
                            f"Type de projet défini : {self._selected_type}\n\nVous pouvez maintenant charger la bibliothèque de tâches.")
        self.navigate("library")

    def refresh(self):
        self._selected_type = self.project_state.get("project_type", "")
        if self._selected_type and self._selected_type in self._type_buttons:
            self._highlight(self._selected_type)
            self._update_description(self._selected_type)
            self.validate_btn.configure(state="normal")
        self.update_status("Page Type de projet rechargée")
