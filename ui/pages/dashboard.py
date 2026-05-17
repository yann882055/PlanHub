"""
dashboard.py - Page d'accueil / Tableau de bord PlanHub
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from datetime import datetime


class DashboardPage(ctk.CTkFrame):
    """Page d'accueil avec statistiques et résumé du projet actif."""

    def __init__(self, parent, project_state: dict, navigate, update_status):
        super().__init__(parent, fg_color="white")
        self.project_state = project_state
        self.navigate = navigate
        self.update_status = update_status

        self._build_ui()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # ── En-tête ──────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="#1565C0", corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="🏠  Tableau de bord",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="white",
        ).grid(row=0, column=0, padx=20, pady=14, sticky="w")

        # Breadcrumb
        ctk.CTkLabel(
            header,
            text="PlanHub  ›  Tableau de bord",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#BBDEFB",
        ).grid(row=0, column=1, padx=10, pady=14, sticky="e")

        # ── Zone alerte ───────────────────────────────────────────────
        self.alert_frame = ctk.CTkFrame(self, fg_color="#FFF9C4", corner_radius=6)
        self.alert_label = ctk.CTkLabel(
            self.alert_frame,
            text="⚠  Aucun projet actif. Créez ou ouvrez un projet pour commencer.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#F57F17",
        )
        self.alert_label.pack(padx=16, pady=8)

        # ── Corps principal (scrollable) ──────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="white")
        scroll.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        scroll.columnconfigure(0, weight=1)
        self.scroll = scroll

        # Cartes statistiques
        self._build_stat_cards(scroll)

        # Résumé projet actif
        self._build_project_summary(scroll)

        # Derniers projets
        self._build_recent_projects(scroll)

        # Grand bouton Nouveau projet
        btn_new = ctk.CTkButton(
            scroll,
            text="➕  Nouveau projet",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#1565C0",
            hover_color="#0D47A1",
            text_color="white",
            height=48,
            corner_radius=8,
            command=lambda: self.navigate("project_type"),
        )
        btn_new.grid(row=10, column=0, pady=24, padx=40, sticky="ew")

    def _build_stat_cards(self, parent):
        """4 cartes statistiques en ligne."""
        frame = ctk.CTkFrame(parent, fg_color="white")
        frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        for i in range(4):
            frame.columnconfigure(i, weight=1)

        self.stat_vars = {
            "nb_taches": tk.StringVar(value="0"),
            "cout_total": tk.StringVar(value="0"),
            "duree_totale": tk.StringVar(value="0 j"),
            "nb_ressources": tk.StringVar(value="0"),
        }

        cards_def = [
            ("📋", "Tâches", "nb_taches", "#1565C0"),
            ("💰", "Coût total HT", "cout_total", "#2E7D32"),
            ("⏱", "Durée totale", "duree_totale", "#E65100"),
            ("👷", "Ressources", "nb_ressources", "#6A1B9A"),
        ]

        self.stat_cards = {}
        for col, (icon, label, key, color) in enumerate(cards_def):
            card = ctk.CTkFrame(frame, fg_color=color, corner_radius=10)
            card.grid(row=0, column=col, padx=8, pady=4, sticky="ew")
            card.columnconfigure(0, weight=1)

            ctk.CTkLabel(
                card, text=icon, font=ctk.CTkFont(size=28), text_color="white"
            ).grid(row=0, column=0, padx=16, pady=(14, 2))
            val_lbl = ctk.CTkLabel(
                card,
                textvariable=self.stat_vars[key],
                font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                text_color="white",
            )
            val_lbl.grid(row=1, column=0, padx=16)
            ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#E3F2FD",
            ).grid(row=2, column=0, padx=16, pady=(2, 14))

            self.stat_cards[key] = val_lbl

    def _build_project_summary(self, parent):
        """Carte résumé du projet actif."""
        outer = ctk.CTkFrame(parent, fg_color="#F5F5F5", corner_radius=10, border_width=1, border_color="#E0E0E0")
        outer.grid(row=1, column=0, sticky="ew", padx=24, pady=8)
        outer.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            outer,
            text="Projet actif",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#1565C0",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        self.summary_frame = ctk.CTkFrame(outer, fg_color="#F5F5F5")
        self.summary_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

    def _build_recent_projects(self, parent):
        """Liste des 5 derniers projets."""
        frame = ctk.CTkFrame(parent, fg_color="#F5F5F5", corner_radius=10, border_width=1, border_color="#E0E0E0")
        frame.grid(row=2, column=0, sticky="ew", padx=24, pady=8)
        frame.columnconfigure(0, weight=1)

        header_row = ctk.CTkFrame(frame, fg_color="#F5F5F5")
        header_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header_row.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_row,
            text="Projets récents",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#1565C0",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header_row,
            text="Voir tout",
            width=80,
            height=28,
            fg_color="#1565C0",
            hover_color="#0D47A1",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=lambda: self.navigate("projects"),
        ).grid(row=0, column=1, sticky="e")

        # Treeview
        cols = ("Nom", "Type", "Date création", "Nb tâches", "Statut")
        tv_frame = ctk.CTkFrame(frame, fg_color="#F5F5F5")
        tv_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        tv_frame.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dashboard.Treeview",
            background="white",
            fieldbackground="white",
            rowheight=28,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Dashboard.Treeview.Heading",
            background="#1565C0",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
        )

        self.recent_tv = ttk.Treeview(
            tv_frame, columns=cols, show="headings", height=5, style="Dashboard.Treeview"
        )
        for c in cols:
            self.recent_tv.heading(c, text=c)
            self.recent_tv.column(c, width=140, anchor="center")
        self.recent_tv.column("Nom", width=200, anchor="w")

        vsb = ttk.Scrollbar(tv_frame, orient="vertical", command=self.recent_tv.yview)
        self.recent_tv.configure(yscrollcommand=vsb.set)
        self.recent_tv.grid(row=0, column=0, sticky="ew")
        vsb.grid(row=0, column=1, sticky="ns")

    # ------------------------------------------------------------------
    # Rafraîchissement
    # ------------------------------------------------------------------

    def refresh(self):
        """Met à jour toutes les données affichées depuis project_state."""
        ps = self.project_state
        tasks = ps.get("dqe_tasks", [])
        resources = ps.get("resources", [])
        currency = ps.get("currency", "FCFA")

        # Alerte si pas de projet actif
        if not ps.get("name", "").strip():
            self.alert_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(4, 0))
        else:
            self.alert_frame.grid_forget()

        # Statistiques
        nb_taches = len(tasks)
        cout_total = sum(
            float(t.get("montant_ht", 0) or 0) for t in tasks
        )
        duree_totale = sum(int(t.get("duree", 0) or 0) for t in tasks)
        nb_ressources = len(resources)

        self.stat_vars["nb_taches"].set(str(nb_taches))
        self.stat_vars["cout_total"].set(f"{cout_total:,.0f} {currency}")
        self.stat_vars["duree_totale"].set(f"{duree_totale} j")
        self.stat_vars["nb_ressources"].set(str(nb_ressources))

        # Résumé projet actif
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        infos = [
            ("Nom du projet", ps.get("name", "—") or "—"),
            ("Type", ps.get("project_type", "—") or "—"),
            ("Identifiant", ps.get("proj_id", "—") or "—"),
            ("Date démarrage", ps.get("start_date", "—") or "—"),
            ("Calendrier", ps.get("calendar", "—") or "—"),
            ("Durée totale", f"{duree_totale} jours"),
        ]
        for i, (lbl, val) in enumerate(infos):
            col = (i % 3) * 2
            row = i // 3
            ctk.CTkLabel(
                self.summary_frame,
                text=f"{lbl} :",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="#555555",
            ).grid(row=row, column=col, sticky="w", padx=(0, 4), pady=2)
            ctk.CTkLabel(
                self.summary_frame,
                text=val,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#212121",
            ).grid(row=row, column=col + 1, sticky="w", padx=(0, 24), pady=2)

        # Derniers projets
        for row in self.recent_tv.get_children():
            self.recent_tv.delete(row)

        saved = ps.get("saved_projects", [])
        for proj in saved[-5:][::-1]:
            self.recent_tv.insert(
                "",
                "end",
                values=(
                    proj.get("name", ""),
                    proj.get("project_type", ""),
                    proj.get("created_at", ""),
                    len(proj.get("dqe_tasks", [])),
                    proj.get("status", "Actif"),
                ),
            )

        self.update_status(f"Tableau de bord rechargé — {nb_taches} tâche(s)")
