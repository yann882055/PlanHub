"""
ui/main_window.py — PlanHub v1.0
Fenêtre principale avec barre de titre custom, toolbar, sidebar, contenu, barre de statut.
"""

import customtkinter as ctk
import tkinter as tk
import datetime
import os
from typing import Dict, Optional

from ui.sidebar import Sidebar
from ui.pages.dashboard import DashboardPage
from ui.pages.dqe_editor import DQEEditorPage
from ui.pages.project_type import ProjectTypePage
from ui.pages.resources import ResourcesPage
from ui.pages.generate_xer import GenerateXERPage
from ui.pages.report import ReportPage
from ui.pages.projects import ProjectsPage

try:
    from license_validator import CURRENT_LICENSE
except Exception:
    CURRENT_LICENSE = {"client": "Démo", "type": "DEMO", "valid": False, "expiry": ""}


class MainWindow(ctk.CTk):
    """Fenêtre principale PlanHub."""

    def __init__(self):
        super().__init__()

        # ── Dimensions
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.title("PlanHub v1.0")

        # ── Couleurs
        self.BLUE = "#1565C0"
        self.BLUE_LIGHT = "#42A5F5"
        self.WHITE = "#FFFFFF"
        self.GRAY_BG = "#F5F5F5"
        self.GRAY_BORDER = "#E0E0E0"
        self.TEXT_MAIN = "#212121"
        self.TEXT_SEC = "#616161"

        # ── État global du projet
        self.project_state: Dict = {
            "name": "",
            "proj_id": "",
            "project_type": None,
            "dqe_tasks": [],
            "resources": [],
            "task_resources": [],
            "currency": "FCFA",
            "calendar": "5j",
            "start_date": None,
            "saved_projects": [],
        }

        self._pages: Dict[str, ctk.CTkFrame] = {}
        self._current_page: Optional[str] = None

        ctk.set_appearance_mode("light")
        self.configure(fg_color=self.WHITE)

        self._build_layout()
        self._navigate("dashboard")

    # ─────────────────────────────────────────────────────────────────
    # LAYOUT
    # ─────────────────────────────────────────────────────────────────
    def _build_layout(self):
        # Titlebar + toolbar (haut)
        self._build_titlebar()

        # Corps principal : sidebar + contenu
        body = ctk.CTkFrame(self, fg_color=self.GRAY_BG, corner_radius=0)
        body.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = Sidebar(body, on_navigate=self._navigate)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)

        # Séparateur vertical
        sep = ctk.CTkFrame(body, width=1, fg_color=self.GRAY_BORDER, corner_radius=0)
        sep.pack(side="left", fill="y")

        # Zone contenu principale
        self.content_frame = ctk.CTkFrame(body, fg_color=self.GRAY_BG, corner_radius=0)
        self.content_frame.pack(side="left", fill="both", expand=True)

        # Status bar
        self._build_statusbar()

    def _build_titlebar(self):
        """Barre de titre personnalisée."""
        titlebar = ctk.CTkFrame(
            self, height=52, fg_color=self.WHITE,
            corner_radius=0,
        )
        titlebar.pack(fill="x", side="top")
        titlebar.pack_propagate(False)

        # Bordure bas
        sep = ctk.CTkFrame(titlebar, height=1, fg_color=self.GRAY_BORDER, corner_radius=0)
        sep.pack(side="bottom", fill="x")

        # Logo PH
        logo_canvas = ctk.CTkCanvas(titlebar, width=32, height=32,
                                     bg=self.WHITE, highlightthickness=0)
        logo_canvas.pack(side="left", padx=(14, 6), pady=10)
        logo_canvas.create_oval(1, 1, 31, 31, fill=self.BLUE, outline="")
        logo_canvas.create_text(16, 16, text="PH",
                                font=("Segoe UI", 10, "bold"), fill="white")

        ctk.CTkLabel(
            titlebar, text="PlanHub",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=self.BLUE,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkLabel(
            titlebar, text="v1.0",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=self.TEXT_SEC,
        ).pack(side="left", padx=(0, 20))

        # Toolbar boutons
        self._build_toolbar_buttons(titlebar)

        # Boutons fenêtre (droite)
        btn_frame = ctk.CTkFrame(titlebar, fg_color=self.WHITE, corner_radius=0)
        btn_frame.pack(side="right", padx=4)

        for text, cmd, hover in [
            ("─", self.iconify, "#E0E0E0"),
            ("□", self._toggle_maximize, "#E0E0E0"),
            ("✕", self.destroy, "#D32F2F"),
        ]:
            b = tk.Button(
                btn_frame, text=text, width=3,
                relief="flat", bd=0,
                font=("Segoe UI", 10),
                bg=self.WHITE, fg=self.TEXT_MAIN,
                activebackground=hover,
                cursor="hand2",
                command=cmd,
            )
            b.pack(side="left", ipadx=6, ipady=4)

        # Permettre déplacement fenêtre via titlebar
        titlebar.bind("<ButtonPress-1>", self._start_move)
        titlebar.bind("<B1-Motion>", self._do_move)

    def _build_toolbar_buttons(self, parent):
        """Boutons d'action rapide dans la toolbar."""
        separator_color = self.GRAY_BORDER
        toolbar = ctk.CTkFrame(parent, fg_color=self.WHITE, corner_radius=0)
        toolbar.pack(side="left", padx=10)

        actions = [
            ("➕ Nouveau", self._new_project, "Nouveau projet"),
            ("💾 Sauvegarder", self._save_project, "Sauvegarder"),
            ("📂 Ouvrir", self._open_project, "Ouvrir un projet"),
        ]

        for text, cmd, tooltip in actions:
            btn = ctk.CTkButton(
                toolbar, text=text,
                font=ctk.CTkFont("Segoe UI", 11),
                height=30, width=110,
                corner_radius=6,
                fg_color="transparent",
                text_color=self.TEXT_MAIN,
                hover_color="#E3F2FD",
                border_width=1,
                border_color=self.GRAY_BORDER,
                command=cmd,
            )
            btn.pack(side="left", padx=3, pady=10)

    def _build_statusbar(self):
        """Barre de statut en bas."""
        statusbar = ctk.CTkFrame(
            self, height=28, fg_color=self.BLUE,
            corner_radius=0,
        )
        statusbar.pack(fill="x", side="bottom")
        statusbar.pack_propagate(False)

        # Statut licence (lu depuis CURRENT_LICENSE)
        lic_type = CURRENT_LICENSE.get("type", "DEMO")
        lic_client = CURRENT_LICENSE.get("client", "Démo")
        if lic_type == "FULL":
            lic_icon = "✓ Licence FULL"
            lic_color = "#A5D6A7"
        else:
            lic_icon = "⚠ Mode DÉMO"
            lic_color = "#FFD54F"

        self.status_license = ctk.CTkLabel(
            statusbar, text=lic_icon,
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=lic_color,
        )
        self.status_license.pack(side="left", padx=16, pady=4)

        # Séparateur
        ctk.CTkLabel(statusbar, text="|", text_color="#90CAF9",
                      font=ctk.CTkFont("Segoe UI", 10)).pack(side="left")

        # Client
        self.status_client = ctk.CTkLabel(
            statusbar, text=f"Client : {lic_client}",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color="white",
        )
        self.status_client.pack(side="left", padx=16)

        # Séparateur
        ctk.CTkLabel(statusbar, text="|", text_color="#90CAF9",
                      font=ctk.CTkFont("Segoe UI", 10)).pack(side="left")

        # Projet actif
        self.status_project = ctk.CTkLabel(
            statusbar, text="Aucun projet actif",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color="white",
        )
        self.status_project.pack(side="left", padx=16)

        # Version (droite)
        ctk.CTkLabel(
            statusbar, text="PlanHub v1.0 — BTP & Infrastructures",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color="#90CAF9",
        ).pack(side="right", padx=16)

    # ─────────────────────────────────────────────────────────────────
    # NAVIGATION
    # ─────────────────────────────────────────────────────────────────
    def _navigate(self, page_key: str):
        """Affiche la page demandée."""
        if self._current_page == page_key and page_key in self._pages:
            return

        # Cacher la page courante
        if self._current_page and self._current_page in self._pages:
            self._pages[self._current_page].pack_forget()

        # Créer la page si nécessaire
        if page_key not in self._pages:
            self._pages[page_key] = self._create_page(page_key)

        self._pages[page_key].pack(fill="both", expand=True)
        self._current_page = page_key
        self.sidebar.set_active(page_key)

        # Rafraîchir si la page a une méthode refresh
        page = self._pages[page_key]
        if hasattr(page, "refresh"):
            page.refresh()

    def _create_page(self, page_key: str) -> ctk.CTkFrame:
        """Instancie la bonne page selon la clé."""
        pages = {
            "dashboard": DashboardPage,
            "dqe_editor": DQEEditorPage,
            "project_type": ProjectTypePage,
            "resources": ResourcesPage,
            "generate_xer": GenerateXERPage,
            "report": ReportPage,
            "projects": ProjectsPage,
        }
        PageClass = pages.get(page_key, DashboardPage)
        return PageClass(
            self.content_frame,
            project_state=self.project_state,
            navigate=self._navigate,
            update_status=self._update_status,
        )

    # ─────────────────────────────────────────────────────────────────
    # ACTIONS TOOLBAR
    # ─────────────────────────────────────────────────────────────────
    def _new_project(self):
        from tkinter import messagebox
        if self.project_state.get("dqe_tasks"):
            if not messagebox.askyesno("Nouveau projet",
                                       "Voulez-vous créer un nouveau projet ?\n"
                                       "Les données non sauvegardées seront perdues."):
                return
        self.project_state.update({
            "name": "", "proj_id": "", "project_type": None,
            "dqe_tasks": [], "resources": [], "task_resources": [],
        })
        # Recréer les pages
        for key in list(self._pages.keys()):
            if key != "projects":
                self._pages[key].destroy()
                del self._pages[key]
        self._current_page = None
        self._navigate("dashboard")
        self._update_status()

    def _save_project(self):
        """Sauvegarde le projet courant en JSON."""
        import json
        from tkinter import filedialog, messagebox

        if not self.project_state.get("name"):
            messagebox.showwarning("Sauvegarde", "Aucun projet à sauvegarder.\nCréez d'abord un projet.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Sauvegarder le projet",
            defaultextension=".planhub",
            filetypes=[("Projets PlanHub", "*.planhub"), ("JSON", "*.json")],
            initialfile=self.project_state.get("name", "projet") + ".planhub"
        )
        if not filepath:
            return

        try:
            # Convertir les dates en strings
            state = self.project_state.copy()
            if state.get("start_date") and not isinstance(state["start_date"], str):
                state["start_date"] = str(state["start_date"])

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2, default=str)
            messagebox.showinfo("Sauvegarde", f"Projet sauvegardé :\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder :\n{e}")

    def _open_project(self):
        """Ouvre un projet PlanHub."""
        import json
        from tkinter import filedialog, messagebox

        filepath = filedialog.askopenfilename(
            title="Ouvrir un projet PlanHub",
            filetypes=[("Projets PlanHub", "*.planhub"), ("JSON", "*.json")],
        )
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state = json.load(f)

            self.project_state.update(state)

            # Recréer les pages
            for key in list(self._pages.keys()):
                self._pages[key].destroy()
                del self._pages[key]
            self._current_page = None
            self._navigate("dashboard")
            self._update_status()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le projet :\n{e}")

    # ─────────────────────────────────────────────────────────────────
    # STATUS
    # ─────────────────────────────────────────────────────────────────
    def _update_status(self, message: str = ""):
        """Met à jour la barre de statut."""
        name = self.project_state.get("name", "")
        if name:
            self.status_project.configure(text=f"Projet : {name}")
        else:
            self.status_project.configure(text="Aucun projet actif")

    # ─────────────────────────────────────────────────────────────────
    # DÉPLACEMENT FENÊTRE
    # ─────────────────────────────────────────────────────────────────
    def _start_move(self, event):
    