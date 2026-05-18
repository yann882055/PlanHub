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

        # Charger les ressources par défaut selon le type (sans écraser les existantes)
        existing_codes = {r.get("code") for r in self.project_state.get("resources", [])}
        defaults = DEFAULT_RESOURCES.get(self._selected_type, DEFAULT_RESOURCES.get("_generic", []))
        added = 0
        for res in defaults:
            if res["code"] not in existing_codes:
                self.project_state.setdefault("resources", []).append(dict(res))
                existing_codes.add(res["code"])
                added += 1

        self.update_status(f"Type validé : {self._selected_type} — {added} ressource(s) par défaut chargée(s)")
        info_msg = f"Type de projet : {self._selected_type}\n"
        if added > 0:
            info_msg += f"\n{added} ressource(s) par défaut ajoutée(s) à la page Ressources.\n"
            info_msg += "Vous pouvez les modifier dans la page Ressources."
        else:
            info_msg += "\nLes ressources existantes ont été conservées."
        messagebox.showinfo("Type validé", info_msg)
        self.navigate("resources")

    def refresh(self):
        self._selected_type = self.project_state.get("project_type", "")
        if self._selected_type and self._selected_type in self._type_buttons:
            self._highlight(self._selected_type)
            self._update_description(self._selected_type)
            self.validate_btn.configure(state="normal")
        self.update_status("Page Type de projet rechargée")


# ── Ressources par défaut par type de projet ──────────────────────────────────
# Format : {code, name, type (LABOR|MATERIAL|EQUIPMENT), unit, cost_per_unit}
# Les coûts sont indicatifs en FCFA/h ou FCFA/U — le planificateur les ajuste.

_R = lambda code, name, rtype, unit, cost: {
    "code": code, "name": name, "type": rtype, "unit": unit,
    "cost_per_unit": cost, "quantity": 1
}

DEFAULT_RESOURCES = {
    # ── Barrage / Hydroélectrique ─────────────────────────────────────────
    "Barrage en BCR": [
        _R("INGCD",  "Ingénieur génie civil",   "LABOR",     "h",   25000),
        _R("CHEF_CH","Chef de chantier",         "LABOR",     "h",   18000),
        _R("COND_E", "Conducteur d'engins",      "LABOR",     "h",   10000),
        _R("BETON",  "Béton BCR (m³)",           "MATERIAL",  "m³",  45000),
        _R("COFRAGE","Coffrages (m²)",            "MATERIAL",  "m²",   8000),
        _R("ACIER",  "Acier HA (T)",             "MATERIAL",  "T",  850000),
        _R("BULL_D9","Bulldozer D9",             "EQUIPMENT", "h",   55000),
        _R("COMPACT","Compacteur vibrant",        "EQUIPMENT", "h",   35000),
        _R("CENTRAL","Centrale à béton",          "EQUIPMENT", "h",   40000),
    ],
    "Barrage en remblai": [
        _R("INGCD",  "Ingénieur génie civil",   "LABOR",     "h",   25000),
        _R("GEOTEC", "Géotechnicien",           "LABOR",     "h",   22000),
        _R("COND_E", "Conducteur d'engins",     "LABOR",     "h",   10000),
        _R("REMBLAI","Remblai argileux (m³)",   "MATERIAL",  "m³",   3500),
        _R("ENROCH", "Enrochements (m³)",       "MATERIAL",  "m³",  12000),
        _R("BULL_D9","Bulldozer D9",            "EQUIPMENT", "h",   55000),
        _R("COMPACT","Compacteur vibrant",       "EQUIPMENT", "h",   35000),
        _R("PELLE",  "Pelle hydraulique 25T",   "EQUIPMENT", "h",   45000),
    ],
    "Aménagement hydroélectrique": [
        _R("INGEL",  "Ingénieur électromécanique","LABOR",    "h",   30000),
        _R("INGCD",  "Ingénieur génie civil",    "LABOR",    "h",   25000),
        _R("TURB",   "Groupe turbo-alternateur", "EQUIPMENT","U",  500000000),
        _R("TRANSFO","Transformateur HTB",       "EQUIPMENT","U",  150000000),
        _R("BETON",  "Béton armé (m³)",          "MATERIAL", "m³",  65000),
        _R("COND_F", "Conduite forcée (ml)",     "MATERIAL", "ml",  85000),
        _R("MONTEUR","Monteur électromécanique", "LABOR",    "h",   15000),
    ],
    "Digue de protection": [
        _R("INGCD",  "Ingénieur génie civil",   "LABOR",     "h",   25000),
        _R("COND_E", "Conducteur d'engins",     "LABOR",     "h",   10000),
        _R("REMBLAI","Remblai sélectionné (m³)","MATERIAL",  "m³",   3000),
        _R("ENROCH", "Enrochements (m³)",       "MATERIAL",  "m³",  12000),
        _R("GEORAND","Géotextile (m²)",          "MATERIAL",  "m²",   1200),
        _R("PELLE",  "Pelle hydraulique 25T",   "EQUIPMENT", "h",   45000),
        _R("COMPACT","Compacteur",               "EQUIPMENT", "h",   35000),
    ],
    # ── Routes ───────────────────────────────────────────────────────────
    "Route bitumée": [
        _R("INGRTE", "Ingénieur routes",         "LABOR",     "h",   22000),
        _R("CHEF_CH","Chef de chantier",          "LABOR",     "h",   18000),
        _R("BETON_B","Béton bitumineux (T)",      "MATERIAL",  "T",   95000),
        _R("GNT",    "Grave non traitée (m³)",    "MATERIAL",  "m³",  18000),
        _R("ENDUIT", "Enduit superficiel (m²)",   "MATERIAL",  "m²",   3500),
        _R("FINISSE","Finisseur",                  "EQUIPMENT", "h",   65000),
        _R("CYLINDR","Cylindre tandem",            "EQUIPMENT", "h",   35000),
        _R("BULL_D7","Bulldozer D7",              "EQUIPMENT", "h",   40000),
    ],
    "Piste rurale": [
        _R("INGRTE", "Ingénieur routes",          "LABOR",     "h",   22000),
        _R("COND_E", "Conducteur d'engins",       "LABOR",     "h",   10000),
        _R("GNT",    "Grave non traitée (m³)",    "MATERIAL",  "m³",  18000),
        _R("LATITE", "Latérite (m³)",             "MATERIAL",  "m³",   4000),
        _R("BULL_D7","Bulldozer D7",              "EQUIPMENT", "h",   40000),
        _R("NIVELE", "Niveleuse",                  "EQUIPMENT", "h",   45000),
    ],
    "Pont": [
        _R("INGSTR", "Ingénieur structures",      "LABOR",     "h",   28000),
        _R("CHEF_CH","Chef de chantier",           "LABOR",     "h",   18000),
        _R("BETON_A","Béton armé (m³)",            "MATERIAL",  "m³",  75000),
        _R("ACIER",  "Acier HA (T)",              "MATERIAL",  "T",  850000),
        _R("COFRAGE","Coffrages (m²)",             "MATERIAL",  "m²",   8000),
        _R("PRECONTR","Câbles précontrainte (T)", "MATERIAL",  "T",  2500000),
        _R("GRUE",   "Grue mobile 100T",           "EQUIPMENT", "h",   90000),
    ],
    # ── Bâtiment ─────────────────────────────────────────────────────────
    "Bâtiment administratif": [
        _R("ARCHI",  "Architecte",               "LABOR",     "h",   25000),
        _R("INGSTR", "Ingénieur structures",     "LABOR",     "h",   22000),
        _R("MACON",  "Maçon qualifié",           "LABOR",     "h",    8000),
        _R("BETON_A","Béton armé (m³)",           "MATERIAL",  "m³",  65000),
        _R("BRIQUE", "Briques (millier)",         "MATERIAL",  "Mil", 150000),
        _R("CARREL", "Carrelage (m²)",            "MATERIAL",  "m²",  18000),
    ],
    "École": [
        _R("ARCHI",  "Architecte",               "LABOR",     "h",   25000),
        _R("MACON",  "Maçon qualifié",           "LABOR",     "h",    8000),
        _R("BETON_A","Béton armé (m³)",           "MATERIAL",  "m³",  65000),
        _R("BRIQUE", "Briques (millier)",         "MATERIAL",  "Mil", 150000),
        _R("TOITURE","Toiture (m²)",              "MATERIAL",  "m²",  22000),
    ],
    "Hôpital": [
        _R("ARCHI",  "Architecte",               "LABOR",     "h",   25000),
        _R("INGSTR", "Ingénieur structures",     "LABOR",     "h",   22000),
        _R("INGELE", "Ingénieur électricité",    "LABOR",     "h",   20000),
        _R("BETON_A","Béton armé (m³)",           "MATERIAL",  "m³",  65000),
        _R("CLIM",   "CVC/Climatisation (U)",    "EQUIPMENT", "U",  2500000),
        _R("ELECTRO","Équipements électriques",   "MATERIAL",  "U",  500000),
    ],
    # ── Énergie ──────────────────────────────────────────────────────────
    "Centrale solaire": [
        _R("INGELEC","Ingénieur électrique",     "LABOR",     "h",   25000),
        _R("PANSOLR","Panneaux solaires (kWc)",  "MATERIAL",  "kWc", 350000),
        _R("ONDULR", "Onduleurs (kW)",           "EQUIPMENT", "kW",  120000),
        _R("STRUCT", "Structures de montage",    "MATERIAL",  "kWc",  45000),
        _R("CABLE",  "Câbles AC/DC (ml)",        "MATERIAL",  "ml",   1800),
        _R("MONTEUR","Monteur électricien",       "LABOR",     "h",   10000),
    ],
    "Ligne HTA/HTB": [
        _R("INGELEC","Ingénieur électrique",     "LABOR",     "h",   25000),
        _R("PYLONE", "Pylônes (U)",              "MATERIAL",  "U",  850000),
        _R("CONDU",  "Conducteurs ACSR (km)",    "MATERIAL",  "km",  4500000),
        _R("ISOL",   "Isolateurs (U)",           "MATERIAL",  "U",   25000),
        _R("GRUE",   "Grue de levage",           "EQUIPMENT", "h",   55000),
        _R("LIGN",   "Lineman/électricien HT",   "LABOR",     "h",   12000),
    ],
    # ── Réseaux ──────────────────────────────────────────────────────────
    "Réseau AEP": [
        _R("INGHY",  "Ingénieur hydraulique",    "LABOR",     "h",   22000),
        _R("TUYAUX", "Tuyaux PEHD (ml)",         "MATERIAL",  "ml",  12000),
        _R("VANNE",  "Vannes (U)",               "MATERIAL",  "U",   85000),
        _R("CHATEAU","Château d'eau (m³)",        "MATERIAL",  "m³",  450000),
        _R("POMPE",  "Groupe motopompe",          "EQUIPMENT", "U",  1500000),
        _R("FOUILLE","Tranchées (ml)",            "EQUIPMENT", "ml",   8000),
    ],
    "Réseau d'assainissement": [
        _R("INGHY",  "Ingénieur hydraulique",    "LABOR",     "h",   22000),
        _R("TUYAUX", "Tuyaux béton (ml)",        "MATERIAL",  "ml",  18000),
        _R("REGARD", "Regards de visite (U)",    "MATERIAL",  "U",   250000),
        _R("STEP",   "Station épuration (U)",    "EQUIPMENT", "U",  50000000),
        _R("FOUILLE","Tranchées (ml)",           "EQUIPMENT", "ml",   9000),
    ],
    # ── Générique (tous les autres types) ────────────────────────────────
    "_generic": [
        _R("INGCD",  "Ingénieur principal",     "LABOR",     "h",   22000),
        _R("CHEF_CH","Chef de chantier",         "LABOR",     "h",   18000),
        _R("TECHNI", "Technicien",               "LABOR",     "h",   10000),
        _R("OUVRIER","Ouvrier qualifié",         "LABOR",     "h",    6500),
        _R("MATERIAU","Matériaux généraux",      "MATERIAL",  "U",    1000),
        _R("EQUIP",  "Engins/Équipements",       "EQUIPMENT", "h",   35000),
    ],
}
