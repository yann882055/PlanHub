"""
resources.py - Page de gestion des ressources (Main d'œuvre + Matière)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

try:
    from core.resource_engine import ResourceEngine
except ImportError:
    class ResourceEngine:
        def load_defaults(self):
            return [
                {"code": "RES001", "nom": "Chef de chantier", "type": "LABOR",  "unite": "h",  "cout": "5000"},
                {"code": "RES002", "nom": "Maçon qualifié",   "type": "LABOR",  "unite": "h",  "cout": "3500"},
                {"code": "RES003", "nom": "Manœuvre",         "type": "LABOR",  "unite": "h",  "cout": "2000"},
                {"code": "MAT001", "nom": "Ciment CEM I",     "type": "MATERIAL","unite": "T",  "cout": "120000"},
                {"code": "MAT002", "nom": "Sable de rivière", "type": "MATERIAL","unite": "m³", "cout": "25000"},
                {"code": "MAT003", "nom": "Gravier 20/40",    "type": "MATERIAL","unite": "m³", "cout": "30000"},
                {"code": "EQP001", "nom": "Bulldozer D6",     "type": "MATERIAL","unite": "h",  "cout": "85000"},
                {"code": "EQP002", "nom": "Pelle 21T",        "type": "MATERIAL","unite": "h",  "cout": "70000"},
            ]


RES_COLUMNS = [
    ("code",  "Code",        100, "center"),
    ("nom",   "Nom",         220, "w"),
    ("type",  "Type",        100, "center"),
    ("unite", "Unité",       80,  "center"),
    ("cout",  "Coût/unité",  130, "e"),
]

RES_TYPES = ["LABOR", "MATERIAL", "EQUIPMENT", "NONLABOR"]
UNITES = ["h", "j", "m³", "m²", "ml", "T", "kg", "U", "forfait"]


class ResourcesPage(ctk.CTkFrame):
    """Gestion des ressources Main d'œuvre et Matière."""

    def __init__(self, parent, project_state: dict, navigate, update_status):
        super().__init__(parent, fg_color="white")
        self.project_state = project_state
        self.navigate = navigate
        self.update_status = update_status
        self.engine = ResourceEngine()
        self._current_tab = "LABOR"
        self._edit_widget = None
        self._edit_item = None

        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_header()
        self._build_tabs()
        self._build_table()
        self._build_footer()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="#1565C0", corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="👷  Ressources",
                     font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                     text_color="white"
                     ).grid(row=0, column=0, padx=20, pady=14, sticky="w")

        ctk.CTkLabel(hdr, text="PlanHub  ›  Ressources",
                     font=ctk.CTkFont(family="Segoe UI", size=11),
                     text_color="#BBDEFB"
                     ).grid(row=0, column=1, padx=10, pady=14, sticky="e")

    def _build_tabs(self):
        """Onglets LABOR / MATERIAL via frame de boutons."""
        tab_bar = ctk.CTkFrame(self, fg_color="#ECEFF1", corner_radius=0, border_width=1, border_color="#CFD8DC")
        tab_bar.grid(row=1, column=0, sticky="ew")

        btn_cfg = dict(height=36, corner_radius=0, font=ctk.CTkFont(family="Segoe UI", size=12))

        self.tab_labor_btn = ctk.CTkButton(
            tab_bar, text="👷 Main d'œuvre (LABOR)",
            fg_color="#1565C0", hover_color="#0D47A1", text_color="white",
            command=lambda: self._switch_tab("LABOR"), **btn_cfg
        )
        self.tab_labor_btn.pack(side="left", padx=0)

        self.tab_mat_btn = ctk.CTkButton(
            tab_bar, text="🧱 Matière / Équipement (MATERIAL)",
            fg_color="#ECEFF1", hover_color="#CFD8DC", text_color="#333333",
            command=lambda: self._switch_tab("MATERIAL"), **btn_cfg
        )
        self.tab_mat_btn.pack(side="left", padx=0)

        # Barre d'outils ressources
        tool_bar = ctk.CTkFrame(self, fg_color="#F5F5F5", corner_radius=0, border_width=1, border_color="#E0E0E0")
        tool_bar.grid(row=1, column=0, sticky="s")

        # Regrouper onglets + barre dans un seul frame
        combined = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        combined.grid(row=1, column=0, sticky="ew")
        combined.columnconfigure(0, weight=1)

        # Onglets
        tabs = ctk.CTkFrame(combined, fg_color="#ECEFF1", corner_radius=0, border_width=1, border_color="#CFD8DC")
        tabs.grid(row=0, column=0, sticky="ew")

        self.tab_labor_btn = ctk.CTkButton(
            tabs, text="👷 Main d'œuvre (LABOR)",
            fg_color="#1565C0", hover_color="#0D47A1", text_color="white",
            height=36, corner_radius=0,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda: self._switch_tab("LABOR")
        )
        self.tab_labor_btn.pack(side="left")

        self.tab_mat_btn = ctk.CTkButton(
            tabs, text="🧱 Matière / Équipement (MATERIAL)",
            fg_color="#ECEFF1", hover_color="#CFD8DC", text_color="#333333",
            height=36, corner_radius=0,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda: self._switch_tab("MATERIAL")
        )
        self.tab_mat_btn.pack(side="left")

        # Barre d'actions
        actions = ctk.CTkFrame(combined, fg_color="#F5F5F5", corner_radius=0, border_width=1, border_color="#E0E0E0")
        actions.grid(row=1, column=0, sticky="ew")

        btn_cfg2 = dict(height=30, corner_radius=6, font=ctk.CTkFont(family="Segoe UI", size=11))

        ctk.CTkButton(actions, text="➕ Ajouter", fg_color="#1565C0", hover_color="#0D47A1",
                      text_color="white", command=self._add_resource, **btn_cfg2
                      ).pack(side="left", padx=(10, 4), pady=6)

        ctk.CTkButton(actions, text="🗑 Supprimer", fg_color="#C62828", hover_color="#B71C1C",
                      text_color="white", command=self._delete_resource, **btn_cfg2
                      ).pack(side="left", padx=4, pady=6)

        ctk.CTkButton(actions, text="🔄 Réinitialiser défauts", fg_color="#37474F", hover_color="#263238",
                      text_color="white", command=self._reset_defaults, **btn_cfg2
                      ).pack(side="left", padx=4, pady=6)

        ctk.CTkButton(actions, text="📂 Charger défauts", fg_color="#2E7D32", hover_color="#1B5E20",
                      text_color="white", command=self._load_defaults, **btn_cfg2
                      ).pack(side="left", padx=4, pady=6)

        # Devise
        ctk.CTkLabel(actions, text="Devise :", font=ctk.CTkFont(family="Segoe UI", size=11),
                     text_color="#333333"
                     ).pack(side="right", padx=(4, 0), pady=6)
        self.currency_label = ctk.CTkLabel(
            actions, text=self.project_state.get("currency", "FCFA"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#1565C0"
        )
        self.currency_label.pack(side="right", padx=(4, 14), pady=6)

        self._tab_combined = combined

    def _build_table(self):
        table_frame = ctk.CTkFrame(self, fg_color="white")
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("Res.Treeview", background="white", fieldbackground="white",
                        rowheight=26, font=("Segoe UI", 10))
        style.configure("Res.Treeview.Heading", background="#1565C0", foreground="white",
                        font=("Segoe UI", 10, "bold"))
        style.map("Res.Treeview", background=[("selected", "#BBDEFB")], foreground=[("selected", "#0D47A1")])

        cols = [c[0] for c in RES_COLUMNS]
        self.tv = ttk.Treeview(table_frame, columns=cols, show="headings", style="Res.Treeview")
        for col_id, col_lbl, col_w, col_anchor in RES_COLUMNS:
            self.tv.heading(col_id, text=col_lbl)
            self.tv.column(col_id, width=col_w, anchor=col_anchor, minwidth=50)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tv.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tv.xview)
        self.tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tv.bind("<Double-1>", self._on_double_click)
        self.tv.tag_configure("odd", background="#FAFAFA")
        self.tv.tag_configure("even", background="white")

    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="#ECEFF1", corner_radius=0, border_width=1, border_color="#CFD8DC")
        footer.grid(row=3, column=0, sticky="ew")
        self.count_var = tk.StringVar(value="0 ressource(s)")
        ctk.CTkLabel(footer, textvariable=self.count_var,
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#1565C0"
                     ).pack(side="left", padx=16, pady=8)

        ctk.CTkLabel(footer, text="Double-clic sur une cellule pour modifier.",
                     font=ctk.CTkFont(family="Segoe UI", size=10),
                     text_color="#777777"
                     ).pack(side="right", padx=16, pady=8)

    # ------------------------------------------------------------------
    # Navigation onglets
    # ------------------------------------------------------------------

    def _switch_tab(self, tab: str):
        self._current_tab = tab
        if tab == "LABOR":
            self.tab_labor_btn.configure(fg_color="#1565C0", text_color="white")
            self.tab_mat_btn.configure(fg_color="#ECEFF1", text_color="#333333")
        else:
            self.tab_mat_btn.configure(fg_color="#1565C0", text_color="white")
            self.tab_labor_btn.configure(fg_color="#ECEFF1", text_color="#333333")
        self._reload_table()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _add_resource(self):
        resources = self.project_state.setdefault("resources", [])
        # Calcul prochain code
        prefix = "RES" if self._current_tab == "LABOR" else "MAT"
        existing_codes = {r.get("code", "") for r in resources}
        idx = 1
        while f"{prefix}{idx:03d}" in existing_codes:
            idx += 1
        code = f"{prefix}{idx:03d}"

        new_res = {
            "code":  code,
            "nom":   "Nouvelle ressource",
            "type":  self._current_tab,
            "unite": "h",
            "cout":  "0",
        }
        resources.append(new_res)
        self.project_state["resources"] = resources
        self._reload_table()
        self.update_status("Ressource ajoutée")

    def _delete_resource(self):
        selected = self.tv.selection()
        if not selected:
            messagebox.showwarning("Sélection", "Sélectionnez une ressource à supprimer.")
            return
        if not messagebox.askyesno("Confirmation", f"Supprimer {len(selected)} ressource(s) ?"):
            return
        codes_to_del = {self.tv.item(i, "values")[0] for i in selected}
        self.project_state["resources"] = [
            r for r in self.project_state.get("resources", [])
            if r.get("code") not in codes_to_del
        ]
        self._reload_table()
        self.update_status(f"{len(codes_to_del)} ressource(s) supprimée(s)")

    def _reset_defaults(self):
        if messagebox.askyesno("Réinitialiser",
                               "Supprimer toutes les ressources et revenir aux valeurs par défaut ?"):
            self.project_state["resources"] = []
            self._load_defaults()

    def _load_defaults(self):
        try:
            defaults = self.engine.load_defaults()
            existing = self.project_state.setdefault("resources", [])
            existing_codes = {r.get("code") for r in existing}
            added = 0
            for res in defaults:
                if res.get("code") not in existing_codes:
                    existing.append(res)
                    added += 1
            self.project_state["resources"] = existing
            self._reload_table()
            self.update_status(f"{added} ressource(s) par défaut chargée(s)")
        except Exception as ex:
            messagebox.showerror("Erreur", f"Impossible de charger les défauts :\n{ex}")

    # ------------------------------------------------------------------
    # Édition inline
    # ------------------------------------------------------------------

    def _on_double_click(self, event):
        if self._edit_widget:
            try:
                self._edit_widget.destroy()
            except Exception:
                pass
            self._edit_widget = None

        region = self.tv.identify("region", event.x, event.y)
        if region != "cell":
            return

        col_id = self.tv.identify_column(event.x)
        item = self.tv.identify_row(event.y)
        if not item:
            return

        col_index = int(col_id.replace("#", "")) - 1
        col_name = RES_COLUMNS[col_index][0]
        current_val = self.tv.item(item, "values")[col_index]

        bbox = self.tv.bbox(item, col_id)
        if not bbox:
            return

        # Combobox pour type et unité
        if col_name == "type":
            var = tk.StringVar(value=current_val)
            cb = ttk.Combobox(self.tv, textvariable=var, values=RES_TYPES, state="readonly")
            cb.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
            cb.focus()
            cb.bind("<<ComboboxSelected>>", lambda e, i=item, c=col_name, ci=col_index, w=cb, v=var:
                    self._save_combo(i, c, ci, w, v))
            cb.bind("<Escape>", lambda e, w=cb: w.destroy())
            self._edit_widget = cb
        elif col_name == "unite":
            var = tk.StringVar(value=current_val)
            cb = ttk.Combobox(self.tv, textvariable=var, values=UNITES, state="readonly")
            cb.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
            cb.focus()
            cb.bind("<<ComboboxSelected>>", lambda e, i=item, c=col_name, ci=col_index, w=cb, v=var:
                    self._save_combo(i, c, ci, w, v))
            cb.bind("<Escape>", lambda e, w=cb: w.destroy())
            self._edit_widget = cb
        else:
            var = tk.StringVar(value=current_val)
            entry = tk.Entry(self.tv, textvariable=var, font=("Segoe UI", 10))
            entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
            entry.focus()
            entry.select_range(0, "end")
            entry.bind("<Return>", lambda e, i=item, c=col_name, w=entry, v=var:
                       self._save_entry(i, c, w, v))
            entry.bind("<Escape>", lambda e, w=entry: w.destroy())
            self._edit_widget = entry

    def _save_entry(self, item, col_name, widget, var):
        value = var.get()
        widget.destroy()
        self._edit_widget = None
        self._update_resource(item, col_name, value)

    def _save_combo(self, item, col_name, col_index, widget, var):
        value = var.get()
        widget.destroy()
        self._edit_widget = None
        self._update_resource(item, col_name, value)

    def _update_resource(self, item, col_name, value):
        current_code = self.tv.item(item, "values")[0]
        resources = self.project_state.get("resources", [])
        for res in resources:
            if res.get("code") == current_code:
                res[col_name] = value
                break
        self._reload_table()

    # ------------------------------------------------------------------
    # Rechargement tableau
    # ------------------------------------------------------------------

    def _reload_table(self):
        for row in self.tv.get_children():
            self.tv.delete(row)

        all_res = self.project_state.get("resources", [])
        filtered = [r for r in all_res if r.get("type", "LABOR") == self._current_tab
                    or (self._current_tab == "MATERIAL" and r.get("type") in ("MATERIAL", "EQUIPMENT", "NONLABOR"))]

        for i, res in enumerate(filtered):
            tag = "even" if i % 2 == 0 else "odd"
            self.tv.insert("", "end", values=(
                res.get("code", ""),
                res.get("nom", ""),
                res.get("type", ""),
                res.get("unite", ""),
                f"{float(res.get('cout', 0) or 0):,.0f} {self.project_state.get('currency', 'FCFA')}",
            ), tags=(tag,))

        self.count_var.set(f"{len(filtered)} ressource(s) — Total : {len(all_res)}")

    def refresh(self):
        self.currency_label.configure(text=self.project_state.get("currency", "FCFA"))
        self._reload_table()
        self.update_status("Page Ressources rechargée")
