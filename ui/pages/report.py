"""
ui/pages/report.py — PlanHub v1.0
Rapport / Import XER existant
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import datetime


class ReportPage(ctk.CTkFrame):
    def __init__(self, parent, project_state, navigate, update_status):
        super().__init__(parent, fg_color="#F5F5F5", corner_radius=0)
        self.project_state = project_state
        self.navigate = navigate
        self.update_status = update_status
        self._parser = None
        self._all_rows = []
        self._visible_columns = [
            "activity_id", "wbs_code", "activity_name", "orig_dur",
            "start", "finish", "total_float", "budgeted_cost", "pct_complete", "status"
        ]
        self._baseline_parser = None
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        hdr.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(hdr, text="📋  Rapport / Import XER",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color="#1565C0").pack(side="left", padx=20, pady=14)

        # Zone import XER
        import_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        import_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(import_frame, text="Charger un fichier XER",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color="#212121").pack(anchor="w", padx=20, pady=(14, 4))

        row = ctk.CTkFrame(import_frame, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 14))

        self._file_lbl = ctk.CTkLabel(row, text="Aucun fichier chargé",
                                       font=ctk.CTkFont("Segoe UI", 11),
                                       text_color="#9E9E9E")
        self._file_lbl.pack(side="left", padx=(0, 16))

        ctk.CTkButton(row, text="📂  Parcourir…",
                      height=34, corner_radius=7,
                      fg_color="#1565C0", hover_color="#0D47A1",
                      command=self._load_xer).pack(side="left", padx=4)

        ctk.CTkButton(row, text="📊  Baseline (2e XER)",
                      height=34, corner_radius=7,
                      fg_color="#42A5F5", hover_color="#1E88E5",
                      command=self._load_baseline).pack(side="left", padx=4)

        # En-tête rapport personnalisable
        hdr2 = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        hdr2.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(hdr2, text="En-tête du rapport",
                     font=ctk.CTkFont("Segoe UI", 13, "bold")).pack(anchor="w", padx=20, pady=(12, 4))
        g = ctk.CTkFrame(hdr2, fg_color="transparent")
        g.pack(fill="x", padx=20, pady=(0, 12))

        self._hdr_fields = {}
        fields = [("project_name", "Nom projet"), ("report_title", "Titre"),
                  ("planner", "Planificateur"), ("revision", "Révision")]
        for i, (key, lbl) in enumerate(fields):
            ctk.CTkLabel(g, text=lbl + " :", font=ctk.CTkFont("Segoe UI", 11),
                         text_color="#616161").grid(row=0, column=i*2, padx=(0 if i == 0 else 16, 4), pady=4)
            e = ctk.CTkEntry(g, width=140, height=30)
            e.grid(row=0, column=i*2+1, padx=(0, 4), pady=4)
            self._hdr_fields[key] = e
        self._hdr_fields["revision"].insert(0, "Rev 0")

        # Toolbar filtres + actions
        toolbar = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        toolbar.pack(fill="x", padx=20, pady=5)
        trow = ctk.CTkFrame(toolbar, fg_color="transparent")
        trow.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(trow, text="Filtre WBS :", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=4)
        self._filter_wbs = ctk.CTkEntry(trow, width=100, height=30, placeholder_text="ex: 1.1")
        self._filter_wbs.pack(side="left", padx=4)

        ctk.CTkLabel(trow, text="Statut :", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=(12, 4))
        self._filter_status = ctk.CTkComboBox(trow, values=["Tous", "TK_NotStart", "TK_Active", "TK_Complete"],
                                               width=130, height=30)
        self._filter_status.set("Tous")
        self._filter_status.pack(side="left", padx=4)

        ctk.CTkButton(trow, text="🔍 Filtrer", height=30, width=90,
                      corner_radius=7, fg_color="#1565C0",
                      command=self._apply_filter).pack(side="left", padx=8)

        ctk.CTkButton(trow, text="Colonnes", height=30, width=90,
                      corner_radius=7, fg_color="transparent",
                      border_width=1, border_color="#E0E0E0",
                      text_color="#212121",
                      command=self._choose_columns).pack(side="left", padx=4)

        # Export buttons
        for lbl, cmd in [("📥 Excel", self._export_excel),
                          ("🌐 HTML", self._export_html),
                          ("📄 PDF", self._export_pdf)]:
            ctk.CTkButton(trow, text=lbl, height=30, width=80,
                          corner_radius=7, fg_color="#388E3C", hover_color="#2E7D32",
                          command=cmd).pack(side="right", padx=3)

        # Tableau P6
        tree_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        tree_card.pack(fill="both", expand=True, padx=20, pady=(5, 20))

        self._tree_container = ctk.CTkFrame(tree_card, fg_color="transparent")
        self._tree_container.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_tree()

    def _build_tree(self):
        for w in self._tree_container.winfo_children():
            w.destroy()

        style = ttk.Style()
        style.configure("RPT.Treeview", font=("Segoe UI", 10), rowheight=24)
        style.configure("RPT.Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#1565C0", foreground="white")
        style.map("RPT.Treeview", background=[("selected", "#BBDEFB")])

        LABELS = {
            "activity_id": "Activity ID", "wbs_code": "WBS", "wbs_name": "Nom WBS",
            "activity_name": "Désignation", "orig_dur": "Durée", "remain_dur": "Reste",
            "start": "Début", "finish": "Fin",
            "early_start": "Début tôt", "early_finish": "Fin tôt",
            "late_start": "Début tard", "late_finish": "Fin tard",
            "total_float": "Marge tot.", "free_float": "Marge lib.",
            "budgeted_cost": "Coût budgété", "actual_cost": "Coût réel",
            "pct_complete": "%", "cstr_type": "Contrainte",
            "status": "Statut", "predecessors": "Prédécesseurs",
        }

        vsb = ttk.Scrollbar(self._tree_container, orient="vertical")
        hsb = ttk.Scrollbar(self._tree_container, orient="horizontal")

        self._tree = ttk.Treeview(
            self._tree_container,
            columns=self._visible_columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="RPT.Treeview"
        )
        vsb.config(command=self._tree.yview)
        hsb.config(command=self._tree.xview)

        WIDTHS = {"activity_id": 90, "wbs_code": 70, "activity_name": 220,
                  "orig_dur": 60, "start": 110, "finish": 110,
                  "total_float": 70, "budgeted_cost": 110, "pct_complete": 50, "status": 90}

        for col in self._visible_columns:
            self._tree.heading(col, text=LABELS.get(col, col),
                               command=lambda c=col: self._sort_by(c))
            self._tree.column(col, width=WIDTHS.get(col, 100), minwidth=50)

        self._tree.tag_configure("critical", background="#FFCDD2")
        self._tree.tag_configure("milestone", background="#E8F5E9", font=("Segoe UI", 10, "bold"))
        self._tree.tag_configure("late", background="#FFF3E0")

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._tree_container.rowconfigure(0, weight=1)
        self._tree_container.columnconfigure(0, weight=1)

    def _load_xer(self):
        fp = filedialog.askopenfilename(
            title="Ouvrir un fichier XER",
            filetypes=[("Fichiers XER", "*.xer"), ("Tous", "*.*")]
        )
        if not fp:
            return
        from core.xer_parser import XERParser
        self._parser = XERParser()
        ok = self._parser.parse_file(fp)
        if ok:
            self._file_lbl.configure(text=f"✅  {os.path.basename(fp)}", text_color="#388E3C")
            self._populate_tree()
        else:
            messagebox.showerror("Erreur", f"Impossible de parser le fichier XER.\n{self._parser.errors}")

    def _load_baseline(self):
        fp = filedialog.askopenfilename(title="XER Baseline",
                                         filetypes=[("Fichiers XER", "*.xer")])
        if not fp:
            return
        from core.xer_parser import XERParser
        self._baseline_parser = XERParser()
        self._baseline_parser.parse_file(fp)
        messagebox.showinfo("Baseline", f"Baseline chargée : {os.path.basename(fp)}")
        if self._parser:
            self._populate_tree()

    def _populate_tree(self):
        if not self._parser:
            return
        tasks = self._parser.get_tasks()
        wbs_dict = self._parser.build_wbs_dict()
        pred_dict = self._parser.get_task_predecessors()
        self._all_rows = self._parser.get_p6_columns(tasks, wbs_dict, pred_dict)

        # Ajouter colonnes comparaison baseline si dispo
        if self._baseline_parser:
            base_tasks = {t.get("task_code", ""): t for t in self._baseline_parser.get_tasks()}
            for row in self._all_rows:
                base = base_tasks.get(row.get("activity_id", ""), {})
                row["delta_dur"] = int(row.get("orig_dur", 0)) - int(int(base.get("target_drtn_hr_cnt", 0) or 0) // 8)
                row["delta_start"] = row.get("start", "") != base.get("target_start_date", "")

        self._fill_tree(self._all_rows)

    def _fill_tree(self, rows):
        for item in self._tree.get_children():
            self._tree.delete(item)
        for row in rows:
            values = [row.get(c, "") for c in self._visible_columns]
            tags = []
            if row.get("_is_critical"):
                tags.append("critical")
            elif row.get("_is_milestone"):
                tags.append("milestone")
            self._tree.insert("", "end", values=values, tags=tags)

    def _apply_filter(self):
        if not self._all_rows:
            return
        wbs_filter = self._filter_wbs.get().strip().lower()
        status_filter = self._filter_status.get()
        rows = self._all_rows
        if wbs_filter:
            rows = [r for r in rows if wbs_filter in r.get("wbs_code", "").lower()]
        if status_filter != "Tous":
            rows = [r for r in rows if r.get("status", "") == status_filter]
        self._fill_tree(rows)

    def _sort_by(self, col):
        rows = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        rows.sort()
        for i, (_, k) in enumerate(rows):
            self._tree.move(k, "", i)

    def _choose_columns(self):
        ALL_COLUMNS = [
            "activity_id", "wbs_code", "wbs_name", "activity_name", "orig_dur",
            "remain_dur", "start", "finish", "early_start", "early_finish",
            "late_start", "late_finish", "total_float", "free_float",
            "budgeted_cost", "actual_cost", "pct_complete", "cstr_type",
            "status", "predecessors",
        ]
        LABELS = {
            "activity_id": "Activity ID", "wbs_code": "WBS", "wbs_name": "Nom WBS",
            "activity_name": "Désignation", "orig_dur": "Durée orig.",
            "remain_dur": "Durée restante", "start": "Début", "finish": "Fin",
            "early_start": "Début tôt", "early_finish": "Fin tôt",
            "late_start": "Début tard", "late_finish": "Fin tard",
            "total_float": "Marge totale", "free_float": "Marge libre",
            "budgeted_cost": "Coût budgété", "actual_cost": "Coût réel",
            "pct_complete": "% Avancement", "cstr_type": "Contrainte",
            "status": "Statut", "predecessors": "Prédécesseurs",
        }

        dlg = tk.Toplevel(self)
        dlg.title("Sélection des colonnes")
        dlg.geometry("320x480")
        dlg.configure(bg="#FFFFFF")
        dlg.grab_set()

        tk.Label(dlg, text="Colonnes à afficher :", font=("Segoe UI", 12, "bold"),
                 bg="#FFFFFF", fg="#1565C0").pack(padx=20, pady=(16, 8), anchor="w")

        frame = tk.Frame(dlg, bg="#FFFFFF")
        frame.pack(fill="both", expand=True, padx=20)

        vars_ = {}
        for col in ALL_COLUMNS:
            v = tk.BooleanVar(value=col in self._visible_columns)
            vars_[col] = v
            tk.Checkbutton(frame, text=LABELS.get(col, col), variable=v,
                           font=("Segoe UI", 11), bg="#FFFFFF",
                           activebackground="#E3F2FD").pack(anchor="w", pady=2)

        def apply():
            self._visible_columns = [c for c in ALL_COLUMNS if vars_[c].get()]
            self._build_tree()
            if self._all_rows:
                self._fill_tree(self._all_rows)
            dlg.destroy()

        tk.Button(dlg, text="Appliquer", command=apply,
                  bg="#1565C0", fg="white", font=("Segoe UI", 11, "bold"),
                  relief="flat", padx=20, pady=8).pack(pady=16)

    def _get_header_info(self):
        return {
            "project_name": self._hdr_fields["project_name"].get(),
            "title": self._hdr_fields["report_title"].get() or "Rapport d'avancement",
            "planner": self._hdr_fields["planner"].get(),
            "revision": self._hdr_fields["revision"].get() or "Rev 0",
            "report_date": datetime.date.today().strftime("%d/%m/%Y"),
        }

    def _export_excel(self):
        if not self._all_rows:
            messagebox.showwarning("Export", "Aucune donnée à exporter. Chargez un fichier XER.")
            return
        fp = filedialog.asksaveasfilename(
            title="Exporter en Excel", defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")])
        if not fp:
            return
        from core.report_engine import ReportEngine
        engine = ReportEngine()
        h = self._get_header_info()
        engine.set_header(**h)
        if engine.export_excel(self._all_rows, self._visible_columns, fp):
            messagebox.showinfo("Export", f"Fichier Excel exporté :\n{fp}")
        else:
            messagebox.showerror("Erreur", "L'export Excel a échoué.\nVérifiez que openpyxl est installé.")

    def _export_html(self):
        if not self._all_rows:
            messagebox.showwarning("Export", "Aucune donnée à exporter.")
            return
        fp = filedialog.asksaveasfilename(
            title="Exporter en HTML", defaultextension=".html",
            filetypes=[("HTML", "*.html")])
        if not fp:
            return
        from core.report_engine import ReportEngine
        engine = ReportEngine()
        engine.set_header(**self._get_header_info())
        if engine.export_html(self._all_rows, self._visible_columns, fp):
            messagebox.showinfo("Export", f"Fichier HTML exporté :\n{fp}")

    def _export_pdf(self):
        if not self._all_rows:
            messagebox.showwarning("Export", "Aucune donnée à exporter.")
            return
        fp = filedialog.asksaveasfilename(
            title="Exporter en PDF", defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")])
        if not fp:
            return
        from core.report_engine import ReportEngine
        engine = ReportEngine()
        engine.set_header(**self._get_header_info())
        if engine.export_pdf(self._all_rows, self._visible_columns, fp):
            messagebox.showinfo("Export", f"Fichier PDF exporté :\n{fp}")
        else:
            messagebox.showerror("Erreur", "L'export PDF a échoué.\nVérifiez que reportlab est installé.")

    def refresh(self):
        pass
