"""
generate_xer.py - Page de génération XER (4 sections)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from datetime import datetime, date

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from core.retro_planning import RetroPlanning
except ImportError:
    class RetroPlanning:
        def __init__(self, tasks, target_date):
            self.tasks = tasks
            self.target_date = target_date
        def calculate(self):
            return {"tasks": self.tasks, "critical": []}

try:
    from core.xer_generator import XERGenerator, encode_xer
except ImportError:
    def encode_xer(content):
        return content.encode("utf-8", errors="replace")
    class XERGenerator:
        def __init__(self):
            pass
        def generate(self, project, tasks, resources, task_resources, calendar="5j", p6_version="15.1"):
            lines = [f"ERMHDR\t{p6_version}\t2024-01-01\tProject\tADMIN\tSYSTEM\tPlanHub\t\t"]
            lines.append("%T\tTASK\n%F\ttask_id\ttask_code\ttask_name")
            for i, t in enumerate(tasks):
                lines.append(f"%R\t{i+1}\t{t.get('activity_id','A'+str(i))}\t{t.get('designation','Tâche')}")
            lines.append("%E")
            return "\n".join(lines)


# Mapping version P6 label → string numérique
P6_VERSION_MAP = {
    "Primavera P6 v8":   "8.2",
    "Primavera P6 v15":  "15.1",
    "Primavera P6 v19":  "19.12",
    "Primavera P6 v20":  "20.12",
    "Primavera P6 v21+": "21.12",
}


P6_VERSIONS = ["Primavera P6 v8", "Primavera P6 v15", "Primavera P6 v19",
               "Primavera P6 v20", "Primavera P6 v21+"]
DEVISES = ["FCFA", "XOF", "USD", "EUR"]
CALENDRIERS = ["Cal_5j (5 jours)", "Cal_6j (6 jours)"]
WBS_LEVELS = ["3", "4", "5"]
LINK_TYPES = ["FS", "SS", "FF", "SF"]
LOG_COLORS = {"ok": "#00E676", "warn": "#FFD740", "err": "#FF5252", "info": "#40C4FF"}


class GenerateXERPage(ctk.CTkFrame):
    """Page de génération du fichier XER Primavera P6."""

    def __init__(self, parent, project_state: dict, navigate, update_status):
        super().__init__(parent, fg_color="white")
        self.project_state = project_state
        self.navigate = navigate
        self.update_status = update_status
        self._xer_content = ""
        self._retro_results = None

        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header()

        # Notebook via ttk
        nb_frame = ctk.CTkFrame(self, fg_color="white")
        nb_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        nb_frame.columnconfigure(0, weight=1)
        nb_frame.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("XER.TNotebook", background="white")
        style.configure("XER.TNotebook.Tab", padding=[12, 6],
                        font=("Segoe UI", 10), background="#ECEFF1")
        style.map("XER.TNotebook.Tab",
                  background=[("selected", "#1565C0")],
                  foreground=[("selected", "white"), ("!selected", "#333333")])

        self.nb = ttk.Notebook(nb_frame, style="XER.TNotebook")
        self.nb.grid(row=0, column=0, sticky="nsew")

        self._build_section_retro()
        self._build_section_params()
        self._build_section_checker()
        self._build_section_generate()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="#1565C0", corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)
        ctk.CTkLabel(hdr, text="⚙  Générer XER",
                     font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                     text_color="white"
                     ).grid(row=0, column=0, padx=20, pady=14, sticky="w")
        ctk.CTkLabel(hdr, text="PlanHub  ›  Génération XER",
                     font=ctk.CTkFont(family="Segoe UI", size=11),
                     text_color="#BBDEFB"
                     ).grid(row=0, column=1, padx=10, pady=14, sticky="e")

    # ── Section A : Rétro-planning ALAP ───────────────────────────────

    def _build_section_retro(self):
        frame = ctk.CTkScrollableFrame(self.nb, fg_color="white")
        self.nb.add(frame, text="A  Rétro-planning ALAP")
        frame.columnconfigure(1, weight=1)

        # Champ date cible
        date_row = ctk.CTkFrame(frame, fg_color="white")
        date_row.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(16, 8))

        ctk.CTkLabel(date_row, text="Date cible :",
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color="#333333"
                     ).pack(side="left", padx=(0, 8))

        self.target_date_var = tk.StringVar(value=self.project_state.get("target_date", ""))
        date_entry = ctk.CTkEntry(date_row, textvariable=self.target_date_var, width=160, height=34,
                                   placeholder_text="AAAA-MM-JJ")
        date_entry.pack(side="left", padx=4)

        ctk.CTkButton(date_row, text="📅 Calculer rétro-planning",
                      fg_color="#1565C0", hover_color="#0D47A1", text_color="white",
                      height=34, corner_radius=6,
                      font=ctk.CTkFont(family="Segoe UI", size=11),
                      command=self._calculate_retro
                      ).pack(side="left", padx=12)

        # Tableau des tâches DQE avec cases à cocher
        ctk.CTkLabel(frame, text="Tâches DQE :",
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color="#1565C0"
                     ).grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(8, 4))

        tv_frame = ctk.CTkFrame(frame, fg_color="white")
        tv_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=4)
        tv_frame.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("Retro.Treeview", background="white", fieldbackground="white",
                        rowheight=24, font=("Segoe UI", 10))
        style.configure("Retro.Treeview.Heading", background="#1565C0", foreground="white",
                        font=("Segoe UI", 10, "bold"))

        retro_cols = ("sel", "activity_id", "designation", "duree", "lien", "lag", "date_debut", "date_fin")
        self.retro_tv = ttk.Treeview(tv_frame, columns=retro_cols, show="headings",
                                      height=10, style="Retro.Treeview")
        col_def = [
            ("sel",          "✓",           40,  "center"),
            ("activity_id",  "N°",          70,  "center"),
            ("designation",  "Désignation", 260, "w"),
            ("duree",        "Durée (j)",   80,  "center"),
            ("lien",         "Lien",        70,  "center"),
            ("lag",          "Lag (j)",     70,  "center"),
            ("date_debut",   "Début calc.", 110, "center"),
            ("date_fin",     "Fin calc.",   110, "center"),
        ]
        for cid, clbl, cw, ca in col_def:
            self.retro_tv.heading(cid, text=clbl)
            self.retro_tv.column(cid, width=cw, anchor=ca, minwidth=40)

        vsb = ttk.Scrollbar(tv_frame, orient="vertical", command=self.retro_tv.yview)
        hsb = ttk.Scrollbar(tv_frame, orient="horizontal", command=self.retro_tv.xview)
        self.retro_tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.retro_tv.grid(row=0, column=0, sticky="ew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.retro_tv.bind("<Button-1>", self._toggle_retro_sel)
        self.retro_tv.tag_configure("critical", foreground="#C62828", font=("Segoe UI", 10, "bold"))
        self.retro_tv.tag_configure("normal", foreground="#212121")

        self._retro_selected = set()

        # Définition des liens
        ctk.CTkLabel(frame, text="Liens entre tâches (Prédécesseur → Successeur — Type — Lag) :",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#1565C0"
                     ).grid(row=3, column=0, columnspan=2, sticky="w", padx=20, pady=(12, 4))

        links_frame = ctk.CTkFrame(frame, fg_color="#F5F5F5", corner_radius=6)
        links_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=4)
        links_frame.columnconfigure(0, weight=1)

        link_row = ctk.CTkFrame(links_frame, fg_color="#F5F5F5")
        link_row.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        ctk.CTkLabel(link_row, text="Prédécesseur :",
                     font=ctk.CTkFont(family="Segoe UI", size=11)).pack(side="left", padx=4)
        self.link_pred = ctk.CTkEntry(link_row, width=80, height=30, placeholder_text="A0001")
        self.link_pred.pack(side="left", padx=4)

        ctk.CTkLabel(link_row, text="Successeur :",
                     font=ctk.CTkFont(family="Segoe UI", size=11)).pack(side="left", padx=4)
        self.link_succ = ctk.CTkEntry(link_row, width=80, height=30, placeholder_text="A0002")
        self.link_succ.pack(side="left", padx=4)

        ctk.CTkLabel(link_row, text="Type :",
                     font=ctk.CTkFont(family="Segoe UI", size=11)).pack(side="left", padx=4)
        self.link_type_var = tk.StringVar(value="FS")
        link_type_cb = ctk.CTkComboBox(link_row, values=LINK_TYPES, variable=self.link_type_var, width=70, height=30)
        link_type_cb.pack(side="left", padx=4)

        ctk.CTkLabel(link_row, text="Lag (j) :",
                     font=ctk.CTkFont(family="Segoe UI", size=11)).pack(side="left", padx=4)
        self.link_lag = ctk.CTkEntry(link_row, width=60, height=30, placeholder_text="0")
        self.link_lag.pack(side="left", padx=4)

        ctk.CTkButton(link_row, text="+ Ajouter lien", fg_color="#1565C0", hover_color="#0D47A1",
                      text_color="white", height=30, corner_radius=6,
                      font=ctk.CTkFont(family="Segoe UI", size=11),
                      command=self._add_link
                      ).pack(side="left", padx=8)

        self.links_list = tk.StringVar(value=[])
        links_lb = tk.Listbox(links_frame, listvariable=self.links_list,
                               height=4, font=("Segoe UI", 10),
                               bg="white", selectbackground="#BBDEFB")
        links_lb.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        self._links_data = []
        self._links_lb = links_lb

        # Gantt simplifié
        ctk.CTkLabel(frame, text="Gantt simplifié :",
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color="#1565C0"
                     ).grid(row=5, column=0, columnspan=2, sticky="w", padx=20, pady=(12, 4))

        self.gantt_frame = ctk.CTkFrame(frame, fg_color="white", height=180)
        self.gantt_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=20, pady=4)
        self.gantt_frame.columnconfigure(0, weight=1)
        self._build_gantt_placeholder(self.gantt_frame)

    def _build_gantt_placeholder(self, parent):
        if HAS_MATPLOTLIB:
            self._fig_gantt = Figure(figsize=(8, 2.5), dpi=80, facecolor="white")
            self._ax_gantt = self._fig_gantt.add_subplot(111)
            self._ax_gantt.set_facecolor("#FAFAFA")
            self._ax_gantt.set_title("Diagramme de Gantt — calculer le rétro-planning pour afficher",
                                      fontsize=9, color="#888888")
            self._canvas_gantt = FigureCanvasTkAgg(self._fig_gantt, master=parent)
            self._canvas_gantt.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
        else:
            ctk.CTkLabel(parent,
                         text="(matplotlib non installé — Gantt non disponible)\nInstallez : pip install matplotlib",
                         font=ctk.CTkFont(family="Segoe UI", size=11),
                         text_color="#888888"
                         ).pack(pady=20)

    def _toggle_retro_sel(self, event):
        region = self.retro_tv.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.retro_tv.identify_column(event.x)
        if col != "#1":
            return
        item = self.retro_tv.identify_row(event.y)
        if not item:
            return
        if item in self._retro_selected:
            self._retro_selected.discard(item)
        else:
            self._retro_selected.add(item)
        self._reload_retro_table(self._retro_results)

    def _add_link(self):
        pred = self.link_pred.get().strip()
        succ = self.link_succ.get().strip()
        ltype = self.link_type_var.get()
        lag = self.link_lag.get().strip() or "0"
        if pred and succ:
            link = {"pred": pred, "succ": succ, "type": ltype, "lag": lag}
            self._links_data.append(link)
            self._links_lb.insert("end", f"{pred} → {succ}  [{ltype}  lag={lag}j]")

    def _calculate_retro(self):
        target = self.target_date_var.get().strip()
        if not target:
            messagebox.showwarning("Date cible", "Veuillez saisir une date cible (AAAA-MM-JJ).")
            return
        tasks = self.project_state.get("dqe_tasks", [])
        if not tasks:
            messagebox.showwarning("DQE vide", "Aucune tâche dans le DQE.")
            return
        try:
            rp = RetroPlanning(tasks, target)
            results = rp.calculate()
            self._retro_results = results
            self._reload_retro_table(results)
            self._draw_gantt(results)
            self.update_status(f"Rétro-planning calculé — date cible : {target}")
        except Exception as ex:
            messagebox.showerror("Erreur rétro-planning", str(ex))

    def _reload_retro_table(self, results):
        for item in self.retro_tv.get_children():
            self.retro_tv.delete(item)
        if not results:
            return
        critical_ids = {t.get("activity_id") for t in results.get("critical", [])}
        for task in results.get("tasks", self.project_state.get("dqe_tasks", [])):
            aid = task.get("activity_id", "")
            sel = "☑" if aid in self._retro_selected else "☐"
            tag = "critical" if aid in critical_ids else "normal"
            self.retro_tv.insert("", "end", iid=aid, values=(
                sel, aid,
                task.get("designation", ""),
                task.get("duree", ""),
                task.get("lien", "FS"),
                task.get("lag", "0"),
                task.get("date_debut", ""),
                task.get("date_fin", ""),
            ), tags=(tag,))

    def _draw_gantt(self, results):
        if not HAS_MATPLOTLIB or not results:
            return
        self._ax_gantt.clear()
        tasks = results.get("tasks", [])
        if not tasks:
            return
        critical_ids = {t.get("activity_id") for t in results.get("critical", [])}

        y_labels = []
        for i, task in enumerate(tasks[:15]):  # Limiter à 15 pour la lisibilité
            try:
                start = float(task.get("offset_j", i))
                dur = max(float(task.get("duree", 1) or 1), 0.5)
                color = "#EF5350" if task.get("activity_id") in critical_ids else "#1565C0"
                self._ax_gantt.barh(i, dur, left=start, color=color, alpha=0.8, height=0.6)
            except (ValueError, TypeError):
                pass
            y_labels.append(task.get("activity_id", f"T{i}"))

        self._ax_gantt.set_yticks(range(len(y_labels)))
        self._ax_gantt.set_yticklabels(y_labels, fontsize=7)
        self._ax_gantt.set_xlabel("Jours", fontsize=8)
        self._ax_gantt.set_title("Gantt rétro-planning (rouge = chemin critique)", fontsize=9)
        self._ax_gantt.invert_yaxis()
        self._fig_gantt.tight_layout()
        self._canvas_gantt.draw()

    # ── Section B : Paramètres XER ────────────────────────────────────

    def _build_section_params(self):
        frame = ctk.CTkScrollableFrame(self.nb, fg_color="white")
        self.nb.add(frame, text="B  Paramètres XER")
        frame.columnconfigure(1, weight=1)

        params = [
            ("Nom du projet :",      "name",         "entry"),
            ("Identifiant projet :", "proj_id",       "entry"),
            ("Date démarrage :",     "start_date",    "entry"),
            ("Calendrier :",         "calendar",      "combo_cal"),
            ("Devise :",             "currency",      "combo_dev"),
            ("Version P6 :",         "p6_version",    "combo_p6"),
            ("Niveau WBS max :",     "wbs_level",     "combo_wbs"),
        ]

        self._param_vars = {}
        for row, (lbl, key, wtype) in enumerate(params):
            ctk.CTkLabel(frame, text=lbl,
                         font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                         text_color="#333333"
                         ).grid(row=row, column=0, sticky="w", padx=(24, 8), pady=8)

            val = self.project_state.get(key, "")
            var = tk.StringVar(value=str(val) if val else "")
            self._param_vars[key] = var

            if wtype == "entry":
                w = ctk.CTkEntry(frame, textvariable=var, width=320, height=34)
                w.grid(row=row, column=1, sticky="w", padx=(0, 24), pady=8)
            elif wtype == "combo_cal":
                w = ctk.CTkComboBox(frame, values=CALENDRIERS, variable=var, width=200, height=34)
                w.grid(row=row, column=1, sticky="w", padx=(0, 24), pady=8)
            elif wtype == "combo_dev":
                w = ctk.CTkComboBox(frame, values=DEVISES, variable=var, width=120, height=34)
                w.grid(row=row, column=1, sticky="w", padx=(0, 24), pady=8)
            elif wtype == "combo_p6":
                w = ctk.CTkComboBox(frame, values=P6_VERSIONS, variable=var, width=220, height=34)
                w.grid(row=row, column=1, sticky="w", padx=(0, 24), pady=8)
            elif wtype == "combo_wbs":
                w = ctk.CTkComboBox(frame, values=WBS_LEVELS, variable=var, width=100, height=34)
                w.grid(row=row, column=1, sticky="w", padx=(0, 24), pady=8)

        ctk.CTkButton(frame, text="💾 Enregistrer les paramètres",
                      fg_color="#1565C0", hover_color="#0D47A1", text_color="white",
                      height=40, corner_radius=8,
                      font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                      command=self._save_params
                      ).grid(row=len(params), column=0, columnspan=2, pady=20, padx=24, sticky="ew")

    def _save_params(self):
        for key, var in self._param_vars.items():
            self.project_state[key] = var.get()
        self.update_status("Paramètres XER enregistrés")
        messagebox.showinfo("Paramètres", "Paramètres XER enregistrés avec succès.")

    # ── Section C : Vérificateur ──────────────────────────────────────

    def _build_section_checker(self):
        frame = ctk.CTkFrame(self.nb, fg_color="white")
        self.nb.add(frame, text="C  Vérificateur")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        btn_row = ctk.CTkFrame(frame, fg_color="white")
        btn_row.grid(row=0, column=0, sticky="ew", padx=24, pady=16)

        ctk.CTkButton(btn_row, text="🔍 Lancer la vérification",
                      fg_color="#1565C0", hover_color="#0D47A1", text_color="white",
                      height=40, corner_radius=8,
                      font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                      command=self._run_checks
                      ).pack(side="left")

        # Zone résultats
        results_outer = ctk.CTkScrollableFrame(frame, fg_color="white")
        results_outer.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
        results_outer.columnconfigure(0, weight=1)
        self.checks_frame = results_outer

    def _run_checks(self):
        for w in self.checks_frame.winfo_children():
            w.destroy()

        ps = self.project_state
        checks = []

        # Vérifications
        def chk(icon, msg, level="ok"):
            checks.append((icon, msg, level))

        tasks = ps.get("dqe_tasks", [])
        resources = ps.get("resources", [])

        if not ps.get("name", "").strip():
            chk("❌", "Nom du projet manquant", "err")
        else:
            chk("✓", f"Nom du projet : {ps['name']}", "ok")

        if not ps.get("proj_id", "").strip():
            chk("❌", "Identifiant projet manquant", "err")
        else:
            chk("✓", f"Identifiant : {ps['proj_id']}", "ok")

        if not tasks:
            chk("❌", "Aucune tâche dans le DQE", "err")
        else:
            chk("✓", f"{len(tasks)} tâche(s) dans le DQE", "ok")

        # Tâches sans durée
        no_dur = [t.get("activity_id", "?") for t in tasks
                  if not t.get("duree") or str(t.get("duree")) == "0"]
        if no_dur:
            chk("⚠", f"Tâches sans durée : {', '.join(no_dur[:5])}", "warn")
        else:
            chk("✓", "Toutes les tâches ont une durée", "ok")

        # Tâches sans désignation
        no_des = [t.get("activity_id", "?") for t in tasks if not t.get("designation", "").strip()]
        if no_des:
            chk("⚠", f"Tâches sans désignation : {', '.join(no_des[:5])}", "warn")

        if not resources:
            chk("⚠", "Aucune ressource définie (optionnel)", "warn")
        else:
            chk("✓", f"{len(resources)} ressource(s) définie(s)", "ok")

        if not ps.get("start_date", "").strip():
            chk("⚠", "Date de démarrage non définie", "warn")
        else:
            chk("✓", f"Date démarrage : {ps['start_date']}", "ok")

        # Affichage
        color_map = {"ok": "#1B5E20", "warn": "#E65100", "err": "#B71C1C"}
        bg_map = {"ok": "#E8F5E9", "warn": "#FFF8E1", "err": "#FFEBEE"}

        ctk.CTkLabel(self.checks_frame, text="Résultats de la vérification :",
                     font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                     text_color="#1565C0"
                     ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        for i, (icon, msg, level) in enumerate(checks):
            row_fr = ctk.CTkFrame(self.checks_frame, fg_color=bg_map[level], corner_radius=6)
            row_fr.grid(row=i + 1, column=0, sticky="ew", pady=2)
            ctk.CTkLabel(row_fr, text=f"  {icon}  {msg}",
                         font=ctk.CTkFont(family="Segoe UI", size=11),
                         text_color=color_map[level],
                         anchor="w"
                         ).pack(fill="x", padx=8, pady=4)

        err_count = sum(1 for _, _, l in checks if l == "err")
        warn_count = sum(1 for _, _, l in checks if l == "warn")
        ok_count = sum(1 for _, _, l in checks if l == "ok")

        summary = f"Résultat : {ok_count} OK — {warn_count} avertissement(s) — {err_count} erreur(s)"
        self.update_status(summary)

    # ── Section D : Génération XER ────────────────────────────────────

    def _build_section_generate(self):
        frame = ctk.CTkFrame(self.nb, fg_color="white")
        self.nb.add(frame, text="D  Génération XER")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        # Bouton générer
        top = ctk.CTkFrame(frame, fg_color="white")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=16)
        top.columnconfigure(1, weight=1)

        ctk.CTkButton(top, text="⚙ Générer le fichier XER",
                      fg_color="#1565C0", hover_color="#0D47A1", text_color="white",
                      height=44, corner_radius=8,
                      font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                      command=self._generate_xer
                      ).grid(row=0, column=0, padx=(0, 12))

        ctk.CTkButton(top, text="💾 Télécharger .xer",
                      fg_color="#2E7D32", hover_color="#1B5E20", text_color="white",
                      height=44, corner_radius=8,
                      font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                      command=self._download_xer
                      ).grid(row=0, column=1, padx=(0, 12), sticky="w")

        # Statistiques
        self.stats_frame = ctk.CTkFrame(frame, fg_color="#E3F2FD", corner_radius=8, border_width=1, border_color="#90CAF9")
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
        self.stats_var = tk.StringVar(value="Statistiques : générez d'abord le fichier XER.")
        ctk.CTkLabel(self.stats_frame, textvariable=self.stats_var,
                     font=ctk.CTkFont(family="Segoe UI", size=11),
                     text_color="#1565C0"
                     ).pack(padx=12, pady=8)

        # Log coloré
        log_outer = ctk.CTkFrame(frame, fg_color="#1E1E2E", corner_radius=8)
        log_outer.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 16))
        log_outer.columnconfigure(0, weight=1)
        log_outer.rowconfigure(1, weight=1)

        ctk.CTkLabel(log_outer, text="Journal de génération",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#AAAACC"
                     ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))

        self.log_text = tk.Text(log_outer, bg="#1E1E2E", fg="#A0CFFF",
                                 font=("Courier New", 10), wrap="word",
                                 state="disabled", relief="flat", height=14)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

        log_vsb = ttk.Scrollbar(log_outer, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_vsb.set)
        log_vsb.grid(row=1, column=1, sticky="ns")

        # Tags couleur log
        self.log_text.tag_configure("ok",   foreground="#00E676")
        self.log_text.tag_configure("warn", foreground="#FFD740")
        self.log_text.tag_configure("err",  foreground="#FF5252")
        self.log_text.tag_configure("info", foreground="#40C4FF")
        self.log_text.tag_configure("head", foreground="#CE93D8", font=("Courier New", 10, "bold"))

    def _log(self, msg: str, tag: str = "info"):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n", tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _generate_xer(self):
        self._clear_log()
        self._log("=" * 60, "head")
        self._log(f"  PlanHub — Génération XER  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]", "head")
        self._log("=" * 60, "head")

        ps = self.project_state
        tasks = ps.get("dqe_tasks", [])

        if not tasks:
            self._log("❌ Aucune tâche dans le DQE — génération annulée.", "err")
            messagebox.showerror("Erreur", "Le DQE est vide. Ajoutez des tâches avant de générer le XER.")
            return

        self._log(f"✓ Projet   : {ps.get('name', '—')}", "ok")
        self._log(f"✓ ID       : {ps.get('proj_id', '—')}", "ok")
        self._log(f"✓ {len(tasks)} tâche(s) importées du DQE", "info")
        resources = ps.get("resources", [])
        task_resources = ps.get("task_resources", [])
        self._log(f"✓ {len(resources)} ressource(s)", "info")

        # Calendrier
        cal_raw = ps.get("calendar", "5j")
        calendar = "6j" if "6j" in str(cal_raw) else "5j"

        # Version P6
        p6_label = ps.get("p6_version", "Primavera P6 v15")
        p6_version = P6_VERSION_MAP.get(p6_label, "15.1")

        # Construction du dict projet
        project = {
            "proj_id":    ps.get("proj_id", "PROJ001") or "PROJ001",
            "name":       ps.get("name", "Projet PlanHub") or "Projet PlanHub",
            "start_date": ps.get("start_date", ""),
            "currency":   ps.get("currency", "FCFA"),
            "tasks":      tasks,
        }

        try:
            gen = XERGenerator()
            content = gen.generate(
                project=project,
                tasks=tasks,
                resources=resources,
                task_resources=task_resources,
                calendar=calendar,
                p6_version=p6_version,
            )
            self._xer_content = content

            # Statistiques
            nb_tasks_xer = len([t for t in tasks if t.get("task_type") != "TT_WBS"])
            wbs_codes = set(
                t.get("wbs", t.get("wbs_code", ""))
                for t in tasks if t.get("wbs", t.get("wbs_code", ""))
            )
            nb_wbs = len(wbs_codes)

            self._log(f"✓ WBS exportés   : {nb_wbs}", "ok")
            self._log(f"✓ Tâches générées: {nb_tasks_xer}", "ok")
            self._log(f"✓ Ressources     : {len(resources)}", "ok")
            self._log(f"✓ Calendrier     : Cal_{calendar}", "ok")
            self._log(f"✓ Version P6     : {p6_version}", "ok")
            self._log(f"✓ Encodage       : latin-1 (standard P6)", "ok")
            self._log("✓ Fichier XER généré avec succès !", "ok")
            self._log("=" * 60, "head")

            self.stats_var.se