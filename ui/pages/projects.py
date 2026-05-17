"""
ui/pages/projects.py — PlanHub v1.0
Mes projets — liste et historique
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import json
import os


class ProjectsPage(ctk.CTkFrame):
    def __init__(self, parent, project_state, navigate, update_status):
        super().__init__(parent, fg_color="#F5F5F5", corner_radius=0)
        self.project_state = project_state
        self.navigate = navigate
        self.update_status = update_status
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        hdr.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(hdr, text="🗂️  Mes projets",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color="#1565C0").pack(side="left", padx=20, pady=14)

        # Barre de recherche + filtre
        toolbar = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        toolbar.pack(fill="x", padx=20, pady=5)
        row = ctk.CTkFrame(toolbar, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(row, text="🔍", font=ctk.CTkFont("Segoe UI", 14)).pack(side="left", padx=4)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *a: self.refresh())
        search = ctk.CTkEntry(row, textvariable=self._search_var,
                               width=200, height=32, placeholder_text="Rechercher un projet…")
        search.pack(side="left", padx=4)

        from core.library_engine import PROJECT_TYPES
        types = ["Tous les types"] + list(PROJECT_TYPES.values())
        self._type_filter = ctk.CTkComboBox(row, values=types, width=200, height=32,
                                             command=lambda v: self.refresh())
        self._type_filter.set("Tous les types")
        self._type_filter.pack(side="left", padx=12)

        ctk.CTkButton(row, text="📂  Importer .planhub",
                      height=32, corner_radius=7,
                      fg_color="transparent", border_width=1, border_color="#E0E0E0",
                      text_color="#212121",
                      command=self._import_project).pack(side="right", padx=4)

        # Tableau projets
        proj_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        proj_card.pack(fill="both", expand=True, padx=20, pady=5)
        ctk.CTkLabel(proj_card, text="Projets enregistrés",
                     font=ctk.CTkFont("Segoe UI", 13, "bold")).pack(anchor="w", padx=20, pady=(14, 4))

        tree_frame = ctk.CTkFrame(proj_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        style = ttk.Style()
        style.configure("PRJ.Treeview", font=("Segoe UI", 11), rowheight=30)
        style.configure("PRJ.Treeview.Heading", font=("Segoe UI", 11, "bold"))
        style.map("PRJ.Treeview", background=[("selected", "#BBDEFB")])

        cols = ("name", "type", "created", "tasks", "cost", "status")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                   height=10, style="PRJ.Treeview",
                                   yscrollcommand=vsb.set)
        vsb.config(command=self._tree.yview)

        for col, lbl, w in [
            ("name", "Nom du projet", 200), ("type", "Type", 180),
            ("created", "Date création", 120), ("tasks", "Nb tâches", 80),
            ("cost", "Coût total", 120), ("status", "Statut", 100)
        ]:
            self._tree.heading(col, text=lbl)
            self._tree.column(col, width=w)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Menu contextuel
        self._ctx_menu = tk.Menu(self._tree, tearoff=0)
        self._ctx_menu.add_command(label="📂  Ouvrir", command=self._open_selected)
        self._ctx_menu.add_command(label="📋  Dupliquer", command=self._duplicate_selected)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="🗃️  Archiver", command=self._archive_selected)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="🗑️  Supprimer", command=self._delete_selected)
        self._tree.bind("<Button-3>", self._show_context_menu)
        self._tree.bind("<Double-1>", lambda e: self._open_selected())

        # Boutons d'action
        btn_row = ctk.CTkFrame(proj_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 12))
        for lbl, cmd, color in [
            ("📂 Ouvrir", self._open_selected, "#1565C0"),
            ("📋 Dupliquer", self._duplicate_selected, "#42A5F5"),
            ("🗑️ Supprimer", self._delete_selected, "#D32F2F"),
        ]:
            ctk.CTkButton(btn_row, text=lbl, height=32, width=120, corner_radius=7,
                          fg_color=color, command=cmd).pack(side="left", padx=4)

        # Historique XER
        xer_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        xer_card.pack(fill="x", padx=20, pady=(5, 20))
        ctk.CTkLabel(xer_card, text="Historique des fichiers XER générés",
                     font=ctk.CTkFont("Segoe UI", 13, "bold")).pack(anchor="w", padx=20, pady=(14, 4))

        xer_frame = ctk.CTkFrame(xer_card, fg_color="transparent")
        xer_frame.pack(fill="x", padx=10, pady=(0, 14))

        xcols = ("filename", "project", "generated_at", "tasks", "size")
        self._xer_tree = ttk.Treeview(xer_frame, columns=xcols, show="headings",
                                       height=4, style="PRJ.Treeview")
        for col, lbl, w in [
            ("filename", "Fichier XER", 220), ("project", "Projet", 180),
            ("generated_at", "Date génération", 140), ("tasks", "Nb tâches", 80),
            ("size", "Taille", 80)
        ]:
            self._xer_tree.heading(col, text=lbl)
            self._xer_tree.column(col, width=w)
        self._xer_tree.pack(fill="x")
        self._xer_tree.bind("<Double-1>", self._open_xer_file)

    def refresh(self):
        """Rafraîchit la liste des projets."""
        for item in self._tree.get_children():
            self._tree.delete(item)

        search = self._search_var.get().lower() if hasattr(self, '_search_var') else ""
        type_filter = self._type_filter.get() if hasattr(self, '_type_filter') else "Tous les types"

        from core.library_engine import PROJECT_TYPES
        types_inv = {v: k for k, v in PROJECT_TYPES.items()}

        for proj in self.project_state.get("saved_projects", []):
            name = proj.get("name", "")
            ptype = proj.get("project_type", "")
            ptype_name = PROJECT_TYPES.get(ptype, ptype)

            if search and search not in name.lower():
                continue
            if type_filter != "Tous les types" and ptype_name != type_filter:
                continue

            currency = proj.get("currency", "FCFA")
            cost = proj.get("total_cost", 0)
            cost_str = f"{cost:,.0f} {currency}" if cost else "—"

            self._tree.insert("", "end", values=(
                name, ptype_name,
                proj.get("created_at", ""),
                proj.get("nb_tasks", 0),
                cost_str,
                proj.get("status", "En cours"),
            ), iid=proj.get("id", name))

        # XER historique
        for item in self._xer_tree.get_children():
            self._xer_tree.delete(item)
        for xer in self.project_state.get("xer_history", []):
            self._xer_tree.insert("", "end", values=(
                xer.get("filename", ""),
                xer.get("project", ""),
                xer.get("generated_at", ""),
                xer.get("nb_tasks", ""),
                xer.get("size", ""),
            ))

    def _get_selected_id(self):
        sel = self._tree.selection()
        return sel[0] if sel else None

    def _find_project(self, pid):
        for p in self.project_state.get("saved_projects", []):
            if p.get("id", p.get("name")) == pid:
                return p
        return None

    def _open_selected(self):
        pid = self._get_selected_id()
        if not pid:
            messagebox.showinfo("Info", "Sélectionnez un projet.")
            return
        proj = self._find_project(pid)
        if proj:
            self.project_state.update(proj)
            self.update_status()
            self.navigate("dashboard")

    def _duplicate_selected(self):
        pid = self._get_selected_id()
        if not pid:
            return
        proj = self._find_project(pid)
        if proj:
            import copy, uuid
            new_proj = copy.deepcopy(proj)
            new_proj["name"] = proj.get("name", "") + " (copie)"
            new_proj["id"] = str(uuid.uuid4())[:8]
            new_proj["created_at"] = datetime.date.today().strftime("%d/%m/%Y")
            self.project_state.setdefault("saved_projects", []).append(new_proj)
            self.refresh()

    def _archive_selected(self):
        pid = self._get_selected_id()
        if not pid:
            return
        proj = self._find_project(pid)
        if proj:
            proj["status"] = "Archivé"
            self.refresh()

    def _delete_selected(self):
        pid = self._get_selected_id()
        if not pid:
            return
        if not messagebox.askyesno("Supprimer",
                                    f"Supprimer le projet « {pid} » ?\nCette action est irréversible."):
            return
        self.project_state["saved_projects"] = [
            p for p in self.project_state.get("saved_projects", [])
            if p.get("id", p.get("name")) != pid
        ]
        self.refresh()

    def _show_context_menu(self, event):
        item = self._tree.identify_row(event.y)
        if item:
            self._tree.selection_set(item)
            self._ctx_menu.tk_popup(event.x_root, event.y_root)

    def _import_project(self):
        fp = filedialog.askopenfilename(
            title="Importer un projet PlanHub",
            filetypes=[("Projets PlanHub", "*.planhub"), ("JSON", "*.json")]
        )
        if not fp:
            return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                proj = json.load(f)
            import uuid
            proj.setdefault("id", str(uuid.uuid4())[:8])
            proj.setdefault("created_at", datetime.date.today().strftime("%d/%m/%Y"))
            self.project_state.setdefault("saved_projects", []).append(proj)
            self.refresh()
            messagebox.showinfo("Import", f"Projet importé : {proj.get('name', fp)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Import impossible :\n{e}")

    def _open_xer_file(self, event):
        sel = self._xer_tree.selection()
        if not sel:
            return
        vals = self._xer_tree.item(sel[0], "values")
        fp = vals[0] if vals else ""
        if fp and os.path.exists(fp):
            os.startfile(fp)
        else:
            messagebox.showinfo("Info", "Fichier introuvable sur le disque.")
