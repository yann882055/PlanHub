"""
ui/pages/report.py — PlanHub v1.0
Rapport / Import XER  ·  deux onglets : Rapport unique + Comparaison baseline
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import datetime


# ── Colonnes disponibles (id → label) ─────────────────────────────────────────
ALL_COLUMNS = {
    "activity_id":   "Activity ID",
    "wbs_code":      "WBS",
    "wbs_name":      "Nom WBS",
    "activity_name": "Désignation",
    "orig_dur":      "Durée orig. (j)",
    "remain_dur":    "Reste (j)",
    "start":         "Début planifié",
    "finish":        "Fin planifiée",
    "early_start":   "Début tôt",
    "early_finish":  "Fin tôt",
    "late_start":    "Début tard",
    "late_finish":   "Fin tard",
    "total_float":   "Marge tot. (j)",
    "free_float":    "Marge lib. (j)",
    "budgeted_cost": "Coût budgété",
    "actual_cost":   "Coût réel",
    "remain_cost":   "Coût restant",
    "pct_complete":  "% Avancement",
    "status":        "Statut",
    "predecessors":  "Prédécesseurs",
}

# Colonnes comparaison baseline (ajoutées seulement quand baseline chargée)
BASELINE_COLUMNS = {
    "bl_start":         "Début baseline",
    "bl_finish":        "Fin baseline",
    "delta_start":      "Écart début (j)",
    "delta_finish":     "Écart fin (j)",
    "bl_budgeted_cost": "Coût budgété BL",
    "bl_actual_cost":   "Coût réel BL",
    "delta_cost":       "Écart coût",
    "bl_orig_dur":      "Durée orig. BL",
    "delta_dur":        "Écart durée (j)",
    "bl_pct_complete":  "% BL",
}

DEFAULT_COLS = [
    "activity_id", "wbs_code", "activity_name",
    "orig_dur", "start", "finish",
    "total_float", "budgeted_cost", "actual_cost", "pct_complete", "status",
]

COMPARE_COLS = [
    "activity_id", "wbs_code", "activity_name",
    "orig_dur", "bl_orig_dur", "delta_dur",
    "start", "bl_start", "delta_start",
    "finish", "bl_finish", "delta_finish",
    "budgeted_cost", "bl_budgeted_cost", "delta_cost",
    "actual_cost", "pct_complete", "status",
]

COL_WIDTHS = {
    "activity_id": 90, "wbs_code": 65, "wbs_name": 160, "activity_name": 220,
    "orig_dur": 70, "remain_dur": 70, "start": 110, "finish": 110,
    "early_start": 110, "early_finish": 110, "late_start": 110, "late_finish": 110,
    "total_float": 75, "free_float": 75, "budgeted_cost": 120, "actual_cost": 120,
    "remain_cost": 110, "pct_complete": 60, "status": 90, "predecessors": 140,
    "bl_start": 110, "bl_finish": 110, "delta_start": 90, "delta_finish": 90,
    "bl_budgeted_cost": 120, "bl_actual_cost": 110, "delta_cost": 110,
    "bl_orig_dur": 80, "delta_dur": 80, "bl_pct_complete": 60,
}


def _parse_xer(filepath: str):
    """Parse un XER et retourne (parser, rows) ou (None, []) si erreur."""
    try:
        from core.xer_parser import XERParser
        p = XERParser()
        ok = p.parse_file(filepath)
        if not ok and p.errors:
            return None, []
        tasks = p.get_tasks()
        wbs_dict = p.build_wbs_dict()
        pred_dict = p.get_task_predecessors()
        rows = p.get_p6_columns(tasks, wbs_dict, pred_dict)
        return p, rows
    except Exception as e:
        return None, []


class ReportPage(ctk.CTkFrame):
    def __init__(self, parent, project_state, navigate, update_status):
        super().__init__(parent, fg_color="#F5F5F5", corner_radius=0)
        self.project_state = project_state
        self.navigate = navigate
        self.update_status = update_status

        # État onglet Rapport
        self._parser = None
        self._all_rows = []
        self._visible_cols = list(DEFAULT_COLS)

        # État onglet Comparaison
        self._parser_cur = None
        self._parser_bl = None
        self._rows_cur = []
        self._rows_bl = []
        self._compare_cols = list(COMPARE_COLS)

        self._build()

    # ─────────────────────────────────────────────────────────────────
    def _build(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="📋  Rapport / Import XER",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color="#1565C0").pack(side="left", padx=20, pady=14)
        sep = ctk.CTkFrame(self, height=1, fg_color="#E0E0E0", corner_radius=0)
        sep.pack(fill="x")

        # Notebook principal
        style = ttk.Style()
        style.configure("RPT.TNotebook", background="#F5F5F5", tabmargins=[2, 4, 0, 0])
        style.configure("RPT.TNotebook.Tab", padding=[16, 7],
                        font=("Segoe UI", 11), background="#E0E0E0")
        style.map("RPT.TNotebook.Tab",
                  background=[("selected", "#1565C0")],
                  foreground=[("selected", "white"), ("!selected", "#424242")])

        nb_frame = ctk.CTkFrame(self, fg_color="#F5F5F5", corner_radius=0)
        nb_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self._nb = ttk.Notebook(nb_frame, style="RPT.TNotebook")
        self._nb.pack(fill="both", expand=True)

        self._build_tab_rapport()
        self._build_tab_compare()

    # ═════════════════════════════════════════════════════════════════
    # ONGLET 1 — Rapport XER unique
    # ═════════════════════════════════════════════════════════════════
    def _build_tab_rapport(self):
        tab = ctk.CTkFrame(self._nb, fg_color="white", corner_radius=0)
        self._nb.add(tab, text="  📄  Rapport XER  ")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)

        # ── Zone import
        imp = ctk.CTkFrame(tab, fg_color="#EEF2FB", corner_radius=8,
                           border_width=1, border_color="#C5D3F0")
        imp.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        imp.columnconfigure(2, weight=1)

        ctk.CTkLabel(imp, text="Fichier XER :",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color="#333").grid(row=0, column=0, padx=(16, 8), pady=10)

        self._rpt_lbl = ctk.CTkLabel(imp, text="Aucun fichier chargé",
                                      font=ctk.CTkFont("Segoe UI", 11),
                                      text_color="#9E9E9E")
        self._rpt_lbl.grid(row=0, column=1, padx=4, sticky="w")

        ctk.CTkButton(imp, text="📂  Charger XER",
                      height=32, corner_radius=6,
                      fg_color="#1565C0", hover_color="#0D47A1",
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._rpt_load).grid(row=0, column=2, padx=8, pady=8, sticky="e")

        # ── Toolbar
        tb = ctk.CTkFrame(tab, fg_color="#FFFFFF", corner_radius=8,
                          border_width=1, border_color="#E0E0E0")
        tb.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        trow = ctk.CTkFrame(tb, fg_color="transparent")
        trow.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(trow, text="WBS :", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=4)
        self._rpt_wbs = ctk.CTkEntry(trow, width=90, height=28, placeholder_text="ex: 1.1")
        self._rpt_wbs.pack(side="left", padx=4)

        ctk.CTkLabel(trow, text="Statut :", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=(10, 4))
        self._rpt_status_cb = ctk.CTkComboBox(
            trow, values=["Tous", "TK_NotStart", "TK_Active", "TK_Complete"],
            width=130, height=28)
        self._rpt_status_cb.set("Tous")
        self._rpt_status_cb.pack(side="left", padx=4)

        ctk.CTkButton(trow, text="🔍 Filtrer", height=28, width=80,
                      corner_radius=6, fg_color="#1565C0",
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._rpt_filter).pack(side="left", padx=8)

        ctk.CTkButton(trow, text="Colonnes ▾", height=28, width=100,
                      corner_radius=6, fg_color="transparent",
                      border_width=1, border_color="#BDBDBD",
                      text_color="#333",
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._rpt_choose_cols).pack(side="left", padx=4)

        # Export
        for lbl, cmd in [("📥 Excel", self._rpt_excel),
                          ("🌐 HTML", self._rpt_html),
                          ("📄 PDF", self._rpt_pdf)]:
            ctk.CTkButton(trow, text=lbl, height=28, width=75,
                          corner_radius=6, fg_color="#388E3C", hover_color="#2E7D32",
                          font=ctk.CTkFont("Segoe UI", 11),
                          command=cmd).pack(side="right", padx=3)

        # ── Tableau
        tree_card = ctk.CTkFrame(tab, fg_color="#FFFFFF", corner_radius=8,
                                  border_width=1, border_color="#E0E0E0")
        tree_card.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 12))
        tree_card.rowconfigure(0, weight=1)
        tree_card.columnconfigure(0, weight=1)

        self._rpt_tree_frame = tree_card
        self._rpt_tree = None
        self._rpt_build_tree()

    def _rpt_build_tree(self):
        """(Re)construit le Treeview avec _visible_cols."""
        for w in self._rpt_tree_frame.winfo_children():
            w.destroy()

        all_labels = {**ALL_COLUMNS, **BASELINE_COLUMNS}

        style = ttk.Style()
        style.configure("RPT.Treeview",
                        font=("Segoe UI", 10), rowheight=24,
                        background="white", fieldbackground="white")
        style.configure("RPT.Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background="#1565C0", foreground="white")
        style.map("RPT.Treeview",
                  background=[("selected", "#BBDEFB")],
                  foreground=[("selected", "#000000")])

        vsb = ttk.Scrollbar(self._rpt_tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(self._rpt_tree_frame, orient="horizontal")

        self._rpt_tree = ttk.Treeview(
            self._rpt_tree_frame,
            columns=self._visible_cols,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="RPT.Treeview",
        )
        vsb.configure(command=self._rpt_tree.yview)
        hsb.configure(command=self._rpt_tree.xview)

        for col in self._visible_cols:
            lbl = all_labels.get(col, col)
            w = COL_WIDTHS.get(col, 100)
            self._rpt_tree.heading(col, text=lbl,
                                   command=lambda c=col: self._rpt_sort(c))
            self._rpt_tree.column(col, width=w, minwidth=50, anchor="w")

        self._rpt_tree.tag_configure("critical", background="#FFCDD2")
        self._rpt_tree.tag_configure("milestone", background="#E8F5E9",
                                      font=("Segoe UI", 10, "bold"))
        self._rpt_tree.tag_configure("late", background="#FFF3E0")

        self._rpt_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._rpt_tree_frame.rowconfigure(0, weight=1)
        self._rpt_tree_frame.columnconfigure(0, weight=1)

    def _rpt_load(self):
        fp = filedialog.askopenfilename(
            title="Charger un fichier XER",
            filetypes=[("Fichiers XER", "*.xer"), ("Tous", "*.*")])
        if not fp:
            return
        p, rows = _parse_xer(fp)
        if p is None or not rows:
            messagebox.showerror("Erreur",
                                  f"Impossible de lire le fichier XER.\n{fp}\n\n"
                                  "Vérifiez que le fichier est un XER Primavera P6 valide.")
            return
        self._parser = p
        self._all_rows = rows
        self._rpt_lbl.configure(
            text=f"✅  {os.path.basename(fp)}  ({len(rows)} activités)",
            text_color="#2E7D32")
        self._rpt_fill(self._all_rows)
        self.update_status(f"XER chargé : {len(rows)} activités")

    def _rpt_fill(self, rows):
        if self._rpt_tree is None:
            return
        for item in self._rpt_tree.get_children():
            self._rpt_tree.delete(item)
        for row in rows:
            vals = [str(row.get(c, "")) for c in self._visible_cols]
            tags = []
            if row.get("_is_critical"):
                tags.append("critical")
            elif row.get("_is_milestone"):
                tags.append("milestone")
            self._rpt_tree.insert("", "end", values=vals, tags=tags)

    def _rpt_filter(self):
        if not self._all_rows:
            return
        wbs_f = self._rpt_wbs.get().strip().lower()
        st_f = self._rpt_status_cb.get()
        rows = self._all_rows
        if wbs_f:
            rows = [r for r in rows
                    if wbs_f in str(r.get("wbs_code", "")).lower()]
        if st_f != "Tous":
            rows = [r for r in rows if r.get("status", "") == st_f]
        self._rpt_fill(rows)

    def _rpt_sort(self, col):
        if self._rpt_tree is None:
            return
        data = [(self._rpt_tree.set(k, col), k)
                for k in self._rpt_tree.get_children("")]
        data.sort(key=lambda x: x[0])
        for i, (_, k) in enumerate(data):
            self._rpt_tree.move(k, "", i)

    def _rpt_choose_cols(self):
        """Dialogue de sélection des colonnes avec menu déroulant."""
        dlg = tk.Toplevel(self)
        dlg.title("Colonnes — Rapport XER")
        dlg.geometry("340x520")
        dlg.configure(bg="#FFFFFF")
        dlg.resizable(False, True)
        dlg.grab_set()

        tk.Label(dlg, text="Colonnes à afficher :",
                 font=("Segoe UI", 12, "bold"),
                 bg="#FFFFFF", fg="#1565C0").pack(padx=20, pady=(16, 4), anchor="w")
        tk.Label(dlg, text="Cochez les colonnes souhaitées :",
                 font=("Segoe UI", 10), bg="#FFFFFF", fg="#616161").pack(padx=20, anchor="w")

        scroll_f = tk.Frame(dlg, bg="#FFFFFF")
        scroll_f.pack(fill="both", expand=True, padx=20, pady=8)

        canvas = tk.Canvas(scroll_f, bg="#FFFFFF", highlightthickness=0)
        vsb = ttk.Scrollbar(scroll_f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg="#FFFFFF")
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        all_cols_ordered = list(ALL_COLUMNS.keys())
        vars_ = {}
        for col in all_cols_ordered:
            v = tk.BooleanVar(value=col in self._visible_cols)
            vars_[col] = v
            row_f = tk.Frame(inner, bg="#FFFFFF")
            row_f.pack(fill="x", pady=1)
            tk.Checkbutton(row_f, text=ALL_COLUMNS[col], variable=v,
                           font=("Segoe UI", 10), bg="#FFFFFF",
                           activebackground="#E3F2FD",
                           anchor="w").pack(fill="x", padx=4)

        def apply_cols():
            self._visible_cols = [c for c in all_cols_ordered if vars_[c].get()]
            if not self._visible_cols:
                self._visible_cols = ["activity_id", "activity_name"]
            self._rpt_build_tree()
            if self._all_rows:
                self._rpt_fill(self._all_rows)
            dlg.destroy()

        btn_f = tk.Frame(dlg, bg="#FFFFFF")
        btn_f.pack(pady=10)
        tk.Button(btn_f, text="Appliquer", command=apply_cols,
                  bg="#1565C0", fg="white",
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", padx=20, pady=6).pack(side="left", padx=6)
        tk.Button(btn_f, text="Annuler", command=dlg.destroy,
                  bg="#E0E0E0", fg="#333",
                  font=("Segoe UI", 11),
                  relief="flat", padx=16, pady=6).pack(side="left", padx=6)

    # ── Exports ──────────────────────────────────────────────────────
    def _rpt_excel(self):
        if not self._all_rows:
            messagebox.showwarning("Export", "Chargez d'abord un fichier XER.")
            return
        fp = filedialog.asksaveasfilename(
            title="Exporter en Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")])
        if not fp:
            return
        try:
            from core.report_engine import ReportEngine
            e = ReportEngine()
            e.export_excel(self._all_rows, self._visible_cols, fp)
            messagebox.showinfo("Export", f"Excel exporté :\n{fp}")
        except Exception as ex:
            messagebox.showerror("Erreur", str(ex))

    def _rpt_html(self):
        if not self._all_rows:
            messagebox.showwarning("Export", "Chargez d'abord un fichier XER.")
            return
        fp = filedialog.asksaveasfilename(
            title="Exporter en HTML",
            defaultextension=".html",
            filetypes=[("HTML", "*.html")])
        if not fp:
            return
        try:
            from core.report_engine import ReportEngine
            ReportEngine().export_html(self._all_rows, self._visible_cols, fp)
            messagebox.showinfo("Export", f"HTML exporté :\n{fp}")
        except Exception as ex:
            messagebox.showerror("Erreur", str(ex))

    def _rpt_pdf(self):
        if not self._all_rows:
            messagebox.showwarning("Export", "Chargez d'abord un fichier XER.")
            return
        fp = filedialog.asksaveasfilename(
            title="Exporter en PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")])
        if not fp:
            return
        try:
            from core.report_engine import ReportEngine
            ReportEngine().export_pdf(self._all_rows, self._visible_cols, fp)
            messagebox.showinfo("Export", f"PDF exporté :\n{fp}")
        except Exception as ex:
            messagebox.showerror("Erreur", str(ex))

    # ═════════════════════════════════════════════════════════════════
    # ONGLET 2 — Comparaison XER vs Baseline
    # ═════════════════════════════════════════════════════════════════
    def _build_tab_compare(self):
        tab = ctk.CTkFrame(self._nb, fg_color="white", corner_radius=0)
        self._nb.add(tab, text="  📊  Comparaison Baseline  ")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)

        # ── Zone import double
        imp = ctk.CTkFrame(tab, fg_color="#EEF2FB", corner_radius=8,
                           border_width=1, border_color="#C5D3F0")
        imp.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        imp.columnconfigure(1, weight=1)
        imp.columnconfigure(3, weight=1)

        # XER courant
        ctk.CTkLabel(imp, text="XER en cours :",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color="#1565C0").grid(row=0, column=0, padx=(16, 8), pady=10, sticky="w")
        self._cmp_cur_lbl = ctk.CTkLabel(imp, text="Non chargé",
                                          font=ctk.CTkFont("Segoe UI", 10),
                                          text_color="#9E9E9E")
        self._cmp_cur_lbl.grid(row=0, column=1, padx=4, sticky="w")
        ctk.CTkButton(imp, text="📂 Charger…",
                      height=30, width=110, corner_radius=6,
                      fg_color="#1565C0", hover_color="#0D47A1",
                      font=ctk.CTkFont("Segoe UI", 10),
                      command=self._cmp_load_cur).grid(row=0, column=2, padx=8, pady=8)

        sep = ctk.CTkFrame(imp, width=1, fg_color="#C5D3F0")
        sep.grid(row=0, column=3, sticky="ns", padx=4)

        # Baseline
        ctk.CTkLabel(imp, text="Baseline :",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color="#E65100").grid(row=0, column=4, padx=(12, 8), pady=10, sticky="w")
        self._cmp_bl_lbl = ctk.CTkLabel(imp, text="Non chargée",
                                         font=ctk.CTkFont("Segoe UI", 10),
                                         text_color="#9E9E9E")
        self._cmp_bl_lbl.grid(row=0, column=5, padx=4, sticky="w")
        ctk.CTkButton(imp, text="📂 Baseline…",
                      height=30, width=120, corner_radius=6,
                      fg_color="#E65100", hover_color="#BF360C",
                      font=ctk.CTkFont("Segoe UI", 10),
                      command=self._cmp_load_bl).grid(row=0, column=6, padx=8, pady=8)

        ctk.CTkButton(imp, text="⟳ Comparer",
                      height=30, width=110, corner_radius=6,
                      fg_color="#2E7D32", hover_color="#1B5E20",
                      font=ctk.CTkFont("Segoe UI", 10, "bold"),
                      command=self._cmp_run).grid(row=0, column=7, padx=(4, 16), pady=8)

        # ── Légende écarts
        leg = ctk.CTkFrame(tab, fg_color="transparent")
        leg.grid(row=0, column=0, sticky="e", padx=20, pady=(52, 0))

        # ── Toolbar
        tb = ctk.CTkFrame(tab, fg_color="#FFFFFF", corner_radius=8,
                          border_width=1, border_color="#E0E0E0")
        tb.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        trow = ctk.CTkFrame(tb, fg_color="transparent")
        trow.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(trow, text="WBS :", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=4)
        self._cmp_wbs = ctk.CTkEntry(trow, width=90, height=28, placeholder_text="ex: 1.1")
        self._cmp_wbs.pack(side="left", padx=4)

        ctk.CTkLabel(trow, text="Écarts :", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=(10, 4))
        self._cmp_ecart = ctk.CTkComboBox(
            trow,
            values=["Tous", "Retard début", "Retard fin", "Dépassement coût", "Durée > BL"],
            width=160, height=28)
        self._cmp_ecart.set("Tous")
        self._cmp_ecart.pack(side="left", padx=4)

        ctk.CTkButton(trow, text="🔍 Filtrer", height=28, width=80,
                      corner_radius=6, fg_color="#1565C0",
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._cmp_filter).pack(side="left", padx=8)

        ctk.CTkButton(trow, text="Colonnes ▾", height=28, width=100,
                      corner_radius=6, fg_color="transparent",
                      border_width=1, border_color="#BDBDBD",
                      text_color="#333",
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._cmp_choose_cols).pack(side="left", padx=4)

        # Légende couleurs
        for color, label in [("#FFCDD2", "Retard"), ("#FFF9C4", "Dépassement"), ("#E8F5E9", "En avance")]:
            f = tk.Frame(trow, bg=color, width=14, height=14, relief="solid", bd=1)
            f.pack(side="right", padx=2)
            tk.Label(trow, text=label, font=("Segoe UI", 9),
                     bg="white", fg="#424242").pack(side="right", padx=2)

        ctk.CTkButton(trow, text="📥 Excel", height=28, width=80,
                      corner_radius=6, fg_color="#388E3C",
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._cmp_excel).pack(side="right", padx=4)

        # ── Tableau comparaison
        cmp_card = ctk.CTkFrame(tab, fg_color="#FFFFFF", corner_radius=8,
                                 border_width=1, border_color="#E0E0E0")
        cmp_card.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 12))
        cmp_card.rowconfigure(0, weight=1)
        cmp_card.columnconfigure(0, weight=1)

        self._cmp_tree_frame = cmp_card
        self._cmp_tree = None
        self._cmp_rows = []
        self._cmp_build_tree()

    def _cmp_build_tree(self):
        for w in self._cmp_tree_frame.winfo_children():
            w.destroy()

        all_labels = {**ALL_COLUMNS, **BASELINE_COLUMNS}

        style = ttk.Style()
        style.configure("CMP.Treeview",
                        font=("Segoe UI", 10), rowheight=24,
                        background="white", fieldbackground="white")
        style.configure("CMP.Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background="#37474F", foreground="white")
        style.map("CMP.Treeview",
                  background=[("selected", "#B3E5FC")],
                  foreground=[("selected", "#000000")])

        vsb = ttk.Scrollbar(self._cmp_tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(self._cmp_tree_frame, orient="horizontal")

        self._cmp_tree = ttk.Treeview(
            self._cmp_tree_frame,
            columns=self._compare_cols,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="CMP.Treeview",
        )
        vsb.configure(command=self._cmp_tree.yview)
        hsb.configure(command=self._cmp_tree.xview)

        for col in self._compare_cols:
            lbl = all_labels.get(col, col)
            w = COL_WIDTHS.get(col, 100)
            self._cmp_tree.heading(col, text=lbl,
                                   command=lambda c=col: self._cmp_sort(c))
            self._cmp_tree.column(col, width=w, minwidth=45, anchor="w")

        # Tags : retard=rouge, dépassement=jaune, avance=vert
        self._cmp_tree.tag_configure("late", background="#FFCDD2")
        self._cmp_tree.tag_configure("over_cost", background="#FFF9C4")
        self._cmp_tree.tag_configure("ahead", background="#E8F5E9")

        self._cmp_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._cmp_tree_frame.rowconfigure(0, weight=1)
        self._cmp_tree_frame.columnconfigure(0, weight=1)

    def _cmp_load_cur(self):
        fp = filedialog.askopenfilename(
            title="XER en cours",
            filetypes=[("Fichiers XER", "*.xer"), ("Tous", "*.*")])
        if not fp:
            return
        p, rows = _parse_xer(fp)
        if p is None:
            messagebox.showerror("Erreur", "Impossible de lire le fichier XER courant.")
            return
        self._parser_cur = p
        self._rows_cur = rows
        self._cmp_cur_lbl.configure(
            text=f"✅ {os.path.basename(fp)} ({len(rows)} activités)",
            text_color="#2E7D32")
        self.update_status(f"XER courant chargé : {len(rows)} activités")

    def _cmp_load_bl(self):
        fp = filedialog.askopenfilename(
            title="XER Baseline",
            filetypes=[("Fichiers XER", "*.xer"), ("Tous", "*.*")])
        if not fp:
            return
        p, rows = _parse_xer(fp)
        if p is None:
            messagebox.showerror("Erreur", "Impossible de lire le fichier XER baseline.")
            return
        self._parser_bl = p
        self._rows_bl = rows
        self._cmp_bl_lbl.configure(
            text=f"✅ {os.path.basename(fp)} ({len(rows)} activités)",
            text_color="#E65100")
        self.update_status(f"Baseline chargée : {len(rows)} activités")

    def _cmp_run(self):
        if not self._rows_cur:
            messagebox.showwarning("Comparaison", "Chargez d'abord le XER en cours.")
            return
        if not self._rows_bl:
            messagebox.showwarning("Comparaison", "Chargez d'abord le XER baseline.")
            return

        # Index baseline par activity_id
        bl_idx = {r.get("activity_id", ""): r for r in self._rows_bl}

        merged = []
        for row in self._rows_cur:
            aid = row.get("activity_id", "")
            bl = bl_idx.get(aid, {})

            # Calculs d'écart durée
            try:
                dur_cur = int(row.get("orig_dur", 0) or 0)
                dur_bl = int(bl.get("orig_dur", 0) or 0)
                delta_dur = dur_cur - dur_bl
            except Exception:
                delta_dur = ""

            # Calculs d'écart coût
            try:
                cost_cur = float(str(row.get("budgeted_cost", 0) or 0).replace(",", ""))
                cost_bl = float(str(bl.get("budgeted_cost", 0) or 0).replace(",", ""))
                delta_cost = cost_cur - cost_bl
            except Exception:
                delta_cost = ""

            # Calculs d'écart dates (en jours)
            def date_diff(d1, d2):
                try:
                    from datetime import datetime
                    fmt = "%Y-%m-%d %H:%M"
                    dt1 = datetime.strptime(d1[:16], fmt)
                    dt2 = datetime.strptime(d2[:16], fmt)
                    return (dt1 - dt2).days
                except Exception:
                    return ""

            delta_start = date_diff(
                row.get("start", ""), bl.get("start", ""))
            delta_finish = date_diff(
                row.get("finish", ""), bl.get("finish", ""))

            r = dict(row)
            r.update({
                "bl_start":         bl.get("start", ""),
                "bl_finish":        bl.get("finish", ""),
                "delta_start":      delta_start,
                "delta_finish":     delta_finish,
                "bl_budgeted_cost": bl.get("budgeted_cost", ""),
                "bl_actual_cost":   bl.get("actual_cost", ""),
                "delta_cost":       f"{delta_cost:+.0f}" if isinstance(delta_cost, float) else "",
                "bl_orig_dur":      bl.get("orig_dur", ""),
                "delta_dur":        f"{delta_dur:+d}" if isinstance(delta_dur, int) else "",
                "bl_pct_complete":  bl.get("pct_complete", ""),
                # tag
                "_late":      isinstance(delta_finish, int) and delta_finish > 0,
                "_over_cost": isinstance(delta_cost, float) and delta_cost > 0,
                "_ahead":     isinstance(delta_finish, int) and delta_finish < 0,
            })
            merged.append(r)

        self._cmp_rows = merged
        self._cmp_fill(merged)
        nb_late = sum(1 for r in merged if r.get("_late"))
        nb_over = sum(1 for r in merged if r.get("_over_cost"))
        self.update_status(
            f"Comparaison : {len(merged)} activités — {nb_late} retard(s) — {nb_over} dépassement(s)")

    def _cmp_fill(self, rows):
        if self._cmp_tree is None:
            return
        for item in self._cmp_tree.get_children():
            self._cmp_tree.delete(item)
        for row in rows:
            vals = [str(row.get(c, "")) for c in self._compare_cols]
            tags = []
            if row.get("_late"):
                tags.append("late")
            elif row.get("_over_cost"):
                tags.append("over_cost")
            elif row.get("_ahead"):
                tags.append("ahead")
            self._cmp_tree.insert("", "end", values=vals, tags=tags)

    def _cmp_filter(self):
        if not self._cmp_rows:
            return
        wbs_f = self._cmp_wbs.get().strip().lower()
        ecart_f = self._cmp_ecart.get()
        rows = self._cmp_rows
        if wbs_f:
            rows = [r for r in rows
                    if wbs_f in str(r.get("wbs_code", "")).lower()]
        if ecart_f == "Retard début":
            rows = [r for r in rows
                    if isinstance(r.get("delta_start"), int) and r["delta_start"] > 0]
        elif ecart_f == "Retard fin":
            rows = [r for r in rows
                    if isinstance(r.get("delta_finish"), int) and r["delta_finish"] > 0]
        elif ecart_f == "Dépassement coût":
            rows = [r for r in rows if r.get("_over_cost")]
        elif ecart_f == "Durée > BL":
            rows = [r for r in rows
                    if isinstance(r.get("delta_dur"), str)
                    and r.get("delta_dur", "").startswith("+")]
        self._cmp_fill(rows)

    def _cmp_sort(self, col):
        if self._cmp_tree is None:
            return
        data = [(self._cmp_tree.set(k, col), k)
                for k in self._cmp_tree.get_children("")]
        data.sort(key=lambda x: x[0])
        for i, (_, k) in enumerate(data):
            self._cmp_tree.move(k, "", i)

    def _cmp_choose_cols(self):
        all_cols_ordered = list(ALL_COLUMNS.keys()) + list(BASELINE_COLUMNS.keys())
        all_labels = {**ALL_COLUMNS, **BASELINE_COLUMNS}

        dlg = tk.Toplevel(self)
        dlg.title("Colonnes — Comparaison")
        dlg.geometry("340x580")
        dlg.configure(bg="#FFFFFF")
        dlg.resizable(False, True)
        dlg.grab_set()

        tk.Label(dlg, text="Colonnes comparaison :",
                 font=("Segoe UI", 12, "bold"),
                 bg="#FFFFFF", fg="#1565C0").pack(padx=20, pady=(16, 4), anchor="w")

        scroll_f = tk.Frame(dlg, bg="#FFFFFF")
        scroll_f.pack(fill="both", expand=True, padx=20, pady=8)

        canvas = tk.Canvas(scroll_f, bg="#FFFFFF", highlightthickness=0)
        vsb = ttk.Scrollbar(scroll_f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg="#FFFFFF")
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        vars_ = {}
        # Séparateur pour baseline
        tk.Label(inner, text="── Colonnes planning ──",
                 font=("Segoe UI", 9), bg="#FFFFFF", fg="#9E9E9E").pack(anchor="w", pady=(4, 0))
        for col in ALL_COLUMNS:
            v = tk.BooleanVar(value=col in self._compare_cols)
            vars_[col] = v
            tk.Checkbutton(inner, text=all_labels[col], variable=v,
                           font=("Segoe UI", 10), bg="#FFFFFF",
                           activebackground="#E3F2FD").pack(anchor="w", padx=4, pady=1)
        tk.Label(inner, text="── Colonnes baseline ──",
                 font=("Segoe UI", 9), bg="#FFFFFF", fg="#E65100").pack(anchor="w", pady=(8, 0))
        for col in BASELINE_COLUMNS:
            v = tk.BooleanVar(value=col in self._compare_cols)
            vars_[col] = v
            tk.Checkbutton(inner, text=all_labels[col], variable=v,
                           font=("Segoe UI", 10), bg="#FFFFFF",
                           activebackground="#FFF3E0").pack(anchor="w", padx=4, pady=1)

        def apply_cols():
            self._compare_cols = [c for c in all_cols_ordered if vars_.get(c, tk.BooleanVar()).get()]
            if not self._compare_cols:
                self._compare_cols = ["activity_id", "activity_name"]
            self._cmp_build_tree()
            if self._cmp_rows:
                self._cmp_fill(self._cmp_rows)
            dlg.destroy()

        btn_f = tk.Frame(dlg, bg="#FFFFFF")
        btn_f.pack(pady=10)
        tk.Button(btn_f, text="Appliquer", command=apply_cols,
                  bg="#1565C0", fg="white",
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", padx=20, pady=6).pack(side="left", padx=6)
        tk.Button(btn_f, text="Annuler", command=dlg.destroy,
                  bg="#E0E0E0", fg="#333",
                  font=("Segoe UI", 11),
                  relief="flat", padx=16, pady=6).pack(side="left", padx=6)

    def _cmp_excel(self):
        if not self._cmp_rows:
            messagebox.showwarning("Export", "Lancez d'abord une comparaison.")
            return
        fp = filedialog.asksaveasfilename(
            title="Exporter comparaison en Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")])
        if not fp:
            return
        try:
            from core.report_engine import ReportEngine
            all_labels = {**ALL_COLUMNS, **BASELINE_COLUMNS}
            ReportEngine().export_excel(self._cmp_rows, self._compare_cols, fp,
                                         col_labels=all_labels)
            messagebox.showinfo("Export", f"Comparaison exportée :\n{fp}")
        except Exception as ex:
            messagebox.showerror("Erreur", str(ex))

    # ─────────────────────────────────────────────────────────────────
    def refresh(self):
        self.update_status("Rapport / Import XER")
