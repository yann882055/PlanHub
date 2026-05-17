"""
ui/sidebar.py — PlanHub v1.0
Barre de navigation latérale
"""

import customtkinter as ctk
from typing import Callable, Dict


MENU_ITEMS = [
    {
        "section": None,
        "items": [
            {"key": "dashboard", "label": "Tableau de bord", "icon": "📊"},
        ]
    },
    {
        "section": "MON PROJET",
        "items": [
            {"key": "dqe_editor", "label": "Mon DQE", "icon": "📝"},
            {"key": "project_type", "label": "Type de projet", "icon": "🏗️"},
            {"key": "library", "label": "Bibliothèque", "icon": "📚"},
            {"key": "resources", "label": "Ressources", "icon": "👷"},
        ]
    },
    {
        "section": "GÉNÉRER",
        "items": [
            {"key": "generate_xer", "label": "Générer XER", "icon": "⚙️"},
        ]
    },
    {
        "section": "ANALYSE",
        "items": [
            {"key": "report", "label": "Rapport / Import XER", "icon": "📋"},
        ]
    },
    {
        "section": "PROJETS",
        "items": [
            {"key": "projects", "label": "Mes projets", "icon": "🗂️"},
        ]
    },
]


class Sidebar(ctk.CTkFrame):
    """Barre de navigation latérale PlanHub."""

    def __init__(self, parent, on_navigate: Callable[[str], None], **kwargs):
        super().__init__(
            parent,
            width=230,
            fg_color="#FAFAFA",
            corner_radius=0,
            border_width=0,
            **kwargs
        )
        self.on_navigate = on_navigate
        self.current_page = "dashboard"
        self._buttons: Dict[str, ctk.CTkButton] = {}

        self.pack_propagate(False)
        self._build()

    def _build(self):
        # ── Logo en haut
        logo_frame = ctk.CTkFrame(self, fg_color="#FAFAFA", height=70, corner_radius=0)
        logo_frame.pack(fill="x", padx=0, pady=0)
        logo_frame.pack_propagate(False)

        # Cercle logo
        logo_canvas = ctk.CTkCanvas(logo_frame, width=38, height=38,
                                     bg="#FAFAFA", highlightthickness=0)
        logo_canvas.place(x=15, y=16)
        logo_canvas.create_oval(2, 2, 36, 36, fill="#1565C0", outline="")
        logo_canvas.create_text(19, 19, text="PH",
                                font=("Segoe UI", 12, "bold"),
                                fill="white")

        ctk.CTkLabel(
            logo_frame,
            text="PlanHub",
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color="#1565C0",
        ).place(x=62, y=16)

        ctk.CTkLabel(
            logo_frame,
            text="v1.0",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color="#9E9E9E",
        ).place(x=62, y=38)

        # Séparateur
        sep = ctk.CTkFrame(self, height=1, fg_color="#E0E0E0", corner_radius=0)
        sep.pack(fill="x", padx=0)

        # ── Scroll zone pour le menu
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="#FAFAFA",
            scrollbar_button_color="#BDBDBD",
            scrollbar_button_hover_color="#9E9E9E",
            corner_radius=0,
        )
        scroll.pack(fill="both", expand=True, padx=0, pady=8)

        for section_data in MENU_ITEMS:
            section = section_data["section"]

            # Label de section
            if section:
                lbl = ctk.CTkLabel(
                    scroll,
                    text=section,
                    font=ctk.CTkFont("Segoe UI", 9, "bold"),
                    text_color="#9E9E9E",
                    anchor="w",
                )
                lbl.pack(fill="x", padx=16, pady=(12, 2))

            for item in section_data["items"]:
                btn = ctk.CTkButton(
                    scroll,
                    text=f"  {item['icon']}  {item['label']}",
                    font=ctk.CTkFont("Segoe UI", 13),
                    anchor="w",
                    height=38,
                    corner_radius=8,
                    fg_color="transparent",
                    text_color="#424242",
                    hover_color="#E3F2FD",
                    command=lambda k=item["key"]: self._navigate(k),
                )
                btn.pack(fill="x", padx=8, pady=2)
                self._buttons[item["key"]] = btn

        # Sélectionner Dashboard par défaut
        self._highlight("dashboard")

    def _navigate(self, page_key: str):
        self._highlight(page_key)
        self.on_navigate(page_key)

    def _highlight(self, page_key: str):
        for key, btn in self._buttons.items():
            if key == page_key:
                btn.configure(fg_color="#E3F2FD", text_color="#1565C0")
            else:
                btn.configure(fg_color="transparent", text_color="#424242")
        self.current_page = page_key

    def set_active(self, page_key: str):
        """Active programmatiquement un élément de menu."""
        self._highlight(page_key)
