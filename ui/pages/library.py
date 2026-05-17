"""
library.py - Bibliothèque intelligente de tâches types
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

try:
    from core.library_engine import LibraryEngine
except ImportError:
    class LibraryEngine:
        def get_tasks_for_type(self, ptype):
            return [
                {"designation": f"Tâche exemple {i+1}", "duree": str((i+1)*3),
                 "predecesseur": str(i) if i > 0 else "", "lien": "FS", "lag": "0"}
                for i in range(10)
            ]
        def get_description(self, ptype):
            return f"Bibliothèque pour : {ptype}"


class LibraryPage(ctk.CTkFrame):
    """Bibliothèque de tâches types avec sélection et import dans le DQE."""

    def __init__(self, parent, project_state: dict, navigate, update_status):
        super().__init__(parent, fg_color="white")
        self.project_state = project_state
        self.navigate = navigate
        self.update_status = update_status
        self.engine = LibraryEngine()
        self._tasks_data = []
        self._check_vars = []

        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # En-tête
        self._build_header()
        # Barre d'outils
        self._build_toolbar()
        # Tableau
        self._build_table()
        # Pied
        self._build_footer()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="#1565C0", corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="📚  Bibliothèque de tâches",
                     font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                     text_color="white"
                     ).grid(row=0, column=0, padx=20, pady=14, sticky="w")

        self.type_label = ctk.CTkLabel(hdr, text="Type : —",
                                        font=ctk.CTkFont(family="Segoe UI", size=12),
                                        text_color="#BBDEFB")
        self.type_label.grid(row=0, column=1, padx=10, pady=14, sticky="e")

    def _build_toolbar(self):
        bar = ctk.CTkFrame(self, fg_color="#F5F5F5", corner_radius=0, border_width=1, border_color="#E0E0E0")
        bar.grid(row=1, column=0, sticky="ew")

        btn_cfg = dict(height=32, corner_radius=6, font=ctk.CTkFont(family="Segoe UI", size=11))

        ctk.CTkButton(bar, text="✔ Sélectionner tout", fg_color="#1565C0", hover_color="#0D47A1",
                      text_color="white", command=self._select_all, **btn_cfg
                      ).pack(side="left", padx=(10, 4), pady=8)

        ctk.CTkButton(bar, text="✗ Désélectionner tout", fg_color="#37474F", hover_color="#263238",
                      text_color="white", command=self._deselect_all, **btn_cfg
                      ).pack(side="left", padx=4, pady=8)

        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=8, pady=6)

        ctk.CTkButton(bar, text="📋 Appliquer au DQE", fg_color="#2E7D32", hover_color="#1B5E20",
                      text_color="white", command=self._apply_to_dqe,
                      height=32, corner_radius=6,
                      font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
                      ).pack(side="left", padx=4, pady=8)

        # Filtre
        ctk.CTkLabel(bar, text="Filtrer :", font=ctk.CTkFont(family="Segoe UI", size=11),
                     text_color="#333333"
                     ).pack(side="right", padx=(4, 0), pady=8)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *a: self._apply_filter())
        filter_entry = ctk.CTkEntry(bar, textvariable=self.filter_var, width=180, height=32,
                                     placeholder_text="Rechercher une tâche...")
        filter_entry.pack(side="right", padx=(4, 12), pady=8)

    def _build_table(self):
        table_frame = ctk.CTkFrame(self, fg_color="white")
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Library.Treeview", background="white", fieldbackground="white",
                        rowheight=26, font=("Segoe UI", 10))
        style.configure("Library.Treeview.Heading", background="#1565C0", foreground="white",
                        font=("Segoe UI", 10, "bold"))
        style.map("Library.Treeview", background=[("selected", "#BBDEFB")], foreground=[("selected", "#0D47A1")])

        cols = ("sel", "designation", "duree", "predecesseur", "lien", "lag")
        col_def = [
            ("sel",          "✓",              40,  "center"),
            ("designation",  "Tâche",          350, "w"),
            ("duree",        "Durée type (j)", 110, "center"),
            ("predecesseur", "Prédécesseur",   120, "center"),
            ("lien",         "Lien",           70,  "center"),
            ("lag",          "Lag (j)",        80,  "center"),
        ]

        self.tv = ttk.Treeview(table_frame, columns=cols, show="headings", style="Library.Treeview")
        for col_id, col_lbl, col_w, col_anchor in col_def:
            self.tv.heading(col_id, text=col_lbl)
            self.tv.column(col_id, width=col_w, anchor=col_anchor, minwidth=40)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tv.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tv.xview)
        self.tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tv.bind("<Button-1>", self._on_click)
        self.tv.tag_configure("odd", background="#FAFAFA")
        self.tv.tag_configure("even", background="white")
        self.tv.tag_configure("checked", background="#E8F5E9")

    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="#FFF8E1", corner_radius=0, border_width=1, border_color="#FFE082")
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(1, weight=1)

        ctk.CTkLabel(footer, text="ℹ",
                     font=ctk.CTkFont(family="Segoe UI", size=16),
                     text_color="#F57F17"
                     ).grid(row=0, column=0, padx=(12, 4), pady=8)

        ctk.CTkLabel(footer,
                     text="Ces durées sont indicatives — à adapter selon votre contexte (conditions terrain, ressources disponibles, spécifications locales).",
                     font=ctk.CTkFont(family="Segoe UI", size=11),
                     text_color="#795548",
                     justify="left"
                     ).grid(row=0, column=1, padx=4, pady=8, sticky="w")

        self.sel_count_var = tk.StringVar(value="0 tâche(s) sélectionnée(s)")
        ctk.CTkLabel(footer, textvariable=self.sel_count_var,
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#1565C0"
                     ).grid(row=0, column=2, padx=12, pady=8)

    # ------------------------------------------------------------------
    # Chargement des tâches
    # ------------------------------------------------------------------

    def _load_tasks(self):
        ptype = self.project_state.get("project_type", "")
        self.type_label.configure(text=f"Type : {ptype or '—'}")
        if not ptype:
            self._tasks_data = []
        else:
            try:
                self._tasks_data = self.engine.get_tasks_for_type(ptype)
            except Exception as ex:
                self._tasks_data = []
                messagebox.showerror("Erreur bibliothèque", str(ex))

        self._selected_indices = set()
        self._apply_filter()

    def _apply_filter(self):
        keyword = self.filter_var.get().strip().lower()
        for item in self.tv.get_children():
            self.tv.delete(item)

        for i, task in enumerate(self._tasks_data):
            if keyword and keyword not in task.get("designation", "").lower():
                continue
            sel_mark = "☑" if i in self._selected_indices else "☐"
            tag = "checked" if i in self._selected_indices else ("even" if i % 2 == 0 else "odd")
            self.tv.insert("", "end", iid=str(i), values=(
                sel_mark,
                task.get("designation", ""),
                task.get("duree", ""),
                task.get("predecesseur", ""),
                task.get("lien", "FS"),
                task.get("lag", "0"),
            ), tags=(tag,))

        self._update_count()

    def _on_click(self, event):
        region = self.tv.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.tv.identify_column(event.x)
        if col != "#1":  # colonne checkbox
            return
        item = self.tv.identify_row(event.y)
        if not item:
            return
        idx = int(item)
        if idx in self._selected_indices:
            self._selected_indices.discard(idx)
        else:
            self._selected_indices.add(idx)
        self._apply_filter()

    def _select_all(self):
        self._selected_indices = set(range(len(self._tasks_data)))
        self._apply_filter()

    def _deselect_all(self):
        self._selected_indices.clear()
        self._apply_filter()

    def _update_count(self):
        self.sel_count_var.set(f"{len(self._selected_indices)} tâche(s) sélectionnée(s)")

    # ------------------------------------------------------------------
    # Application au DQE
    # ------------------------------------------------------------------

    def _apply_to_dqe(self):
        if not self._selected_indices:
            messagebox.showwarning("Sélection vide", "Veuillez sélectionner au moins une tâche.")
            return

        selected_tasks = [self._tasks_data[i] for i in sorted(self._selected_indices)]
        existing = self.project_state.setdefault("dqe_tasks", [])

        # Calcul du prochain activity_id
        existing_ids = {t.get("activity_id", "") for t in existing}
        next_idx = 1

        def next_id():
            nonlocal next_idx
            while f"A{next_idx:04d}" in existing_ids:
                next_idx += 1
            aid = f"A{next_idx:04d}"
            existing_ids.add(aid)
            next_idx += 1
            return aid

        new_tasks = []
        for task in selected_tasks:
            dqe_task = {
                "activity_id": next_id(),
                "wbs":         task.get("wbs", "1"),
                "lot":         task.get("lot", ""),
                "designation": task.get("designation", ""),
                "unite":       task.get("unite", "forfait"),
                "quantite":    task.get("quantite", "1"),
                "pu_ht":       task.get("pu_ht", "0"),
                "montant_ht":  task.get("montant_ht", "0"),
                "duree":       task.get("duree", "1"),
                "calendrier":  task.get("calendrier", "Cal_5j"),
                "task_type":   task.get("task_type", "TT_Task"),
                "constraint":  task.get("constraint", "CS_ALAP"),
            }
            new_tasks.append(dqe_task)

        existing.extend(new_tasks)
        self.project_state["dqe_tasks"] = existing

        n = len(new_tasks)
        messagebox.showinfo("Succès", f"{n} tâche(s) ajoutée(s) au DQE avec succès.")
        self.update_status(f"Bibliothèque : {n} tâche(s) ajoutée(s) au DQE")
        self.navigate("dqe_editor")

    # ------------------------------------------------------------------

    def refresh(self):
        self._load_tasks()
        self.update_status(f"Bibliothèque chargée : {len(self._tasks_data)} tâche(s) disponible(s)")
