"""
generate_xer.py — PlanHub v1.0
Page de génération XER — 4 onglets :
  A  Rétro-planning ALAP  (contraintes P6, CPM, ES/EF/LS/LF)
  B  Paramètres XER
  C  Vérificateur
  D  Génération XER
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from datetime import datetime, date as date_type

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
        def __init__(self, calendar="5j", holidays=None):
            self.calendar = calendar
        def calculate(self, tasks, target_date, links=None):
            return {}
        def get_summary(self):
            return {}

try:
    from core.xer_generator import XERGenerator, encode_xer
except ImportError:
    def encode_xer(content):
        return content.encode("utf-8", errors="replace")
    class XERGenerator:
        def __init__(self): pass
        def generate(self, project, tasks, resources, task_resources,
                     calendar="5j", p6_version="15.1"):
            lines = [f"ERMHDR\t{p6_version}\t2024-01-01\tProject\tADMIN\tSYSTEM\tPlanHub\t\t"]
            lines.append("%T\tTASK\n%F\ttask_id\ttask_code\ttask_name")
            for i, t in enumerate(tasks):
                lines.append(f"%R\t{i+1}\t{t.get('activity_id','A'+str(i))}\t{t.get('designation','Tâche')}")
            lines.append("%E")
            return "\n".join(lines)


# ── Constantes ────────────────────────────────────────────────────────────────
P6_VERSION_MAP = {
    "Primavera P6 v8":   "8.2",
    "Primavera P6 v15":  "15.1",
    "Primavera P6 v19":  "19.12",
    "Primavera P6 v20":  "20.12",
    "Primavera P6 v21+": "21.12",
}
P6_VERSIONS  = ["Primavera P6 v8", "Primavera P6 v15", "Primavera P6 v19",
                "Primavera P6 v20", "Primavera P6 v21+"]
DEVISES      = ["FCFA", "XOF", "USD", "EUR"]
CALENDRIERS  = ["Cal_5j (5 jours)", "Cal_6j (6 jours)"]
WBS_LEVELS   = ["3", "4", "5"]
LINK_TYPES   = ["FS", "SS", "FF", "SF"]
LOG_COLORS   = {"ok": "#00E676", "warn": "#FFD740", "err": "#FF5252", "info": "#40C4FF"}

# ── Contraintes P6 ────────────────────────────────────────────────────────────
CSTR_INFO = [
    # (code,  libellé complet,                   fond,      texte)
    ("ALAP", "Au plus tard — défaut ALAP",       "#E3F2FD", "#1565C0"),
    ("FNLT", "Finish No Later Than  (FIN ≤ date)","#FFF3E0", "#E65100"),
    ("MFO",  "Must Finish On  (FIN = date)",     "#FCE4EC", "#C62828"),
    ("FNET", "Finish No Earlier Than (FIN ≥ date)","#E8F5E9","#2E7D32"),
    ("SNLT", "Start No Later Than  (DÉB ≤ date)","#F3E5F5", "#6A1B9A"),
    ("SNET", "Start No Earlier Than (DÉB ≥ date)","#E0F7FA","#00695C"),
    ("MSOB", "Must Start On or Before (DÉB ≤ date)","#FFF8E1","#F57F17"),
]
CSTR_NEEDS_DATE = {"FNLT", "MFO", "FNET", "SNLT", "SNET", "MSOB"}
CSTR_BG = {c: bg for c, _, bg, _ in CSTR_INFO}
CSTR_FG = {c: fg for c, _, _, fg in CSTR_INFO}


# ═════════════════════════════════════════════════════════════════════════════
class GenerateXERPage(ctk.CTkFrame):
    """Page de génération du fichier XER Primavera P6."""

    def __init__(self, parent, project_state: dict, navigate, update_status):
        super().__init__(parent, fg_color="white")
        self.project_state = project_state
        self.navigate      = navigate
        self.update_status = update_status
        self._xer_content  = ""
        self._retro_results = None

        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header()

        nb_frame = ctk.CTkFrame(self, fg_color="white")
        nb_frame.grid(row=1, column=0, sticky="nsew")
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

        # Ouvrir directement l'onglet D (Génération XER)
        self.nb.select(3)

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="#1565C0", corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)
        ctk.CTkLabel(hdr, text="⚙  Générer XER",
                     font=ctk.CTkFont("Segoe UI", 20, "bold"),
                     text_color="white"
                     ).grid(row=0, column=0, padx=20, pady=14, sticky="w")
        ctk.CTkLabel(hdr, text="PlanHub  ›  Génération XER",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color="#BBDEFB"
                     ).grid(row=0, column=1, padx=10, pady=14, sticky="e")

    # ═════════════════════════════════════════════════════════════════════════
    # ONGLET A — Rétro-planning ALAP avec contraintes P6
    # ═════════════════════════════════════════════════════════════════════════
    def _build_section_retro(self):
        frame = ctk.CTkScrollableFrame(self.nb, fg_color="white")
        self.nb.add(frame, text="A  Rétro-planning ALAP")
        frame.columnconfigure(0, weight=1)

        # ── Barre de contrôle : date impérative + calendrier + calcul ─────────
        ctrl = ctk.CTkFrame(frame, fg_color="#E8EAF6", corner_radius=8,
                             border_width=1, border_color="#9FA8DA")
        ctrl.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        ctrl.columnconfigure(5, weight=1)

        ctk.CTkLabel(ctrl, text="📅  Date impérative :",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color="#283593"
                     ).grid(row=0, column=0, padx=(16, 6), pady=12, sticky="w")

        self.target_date_var = tk.StringVar(
            value=self.project_state.get("target_date", ""))
        ctk.CTkEntry(ctrl, textvariable=self.target_date_var,
                     width=135, height=36, placeholder_text="AAAA-MM-JJ"
                     ).grid(row=0, column=1, padx=4, pady=10)

        ctk.CTkLabel(ctrl, text="Calendrier :",
                     font=ctk.CTkFont("Segoe UI", 11), text_color="#333"
                     ).grid(row=0, column=2, padx=(16, 4), pady=12)

        self.retro_cal_var = tk.StringVar(value="Cal_5j (5 jours)")
        ctk.CTkComboBox(ctrl, values=CALENDRIERS, variable=self.retro_cal_var,
                        width=155, height=36
                        ).grid(row=0, column=3, padx=4, pady=10)

        ctk.CTkButton(ctrl, text="⚙  Calculer ALAP",
                      fg_color="#283593", hover_color="#1A237E",
                      text_color="white", height=38, corner_radius=8,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      command=self._calculate_retro
                      ).grid(row=0, column=4, padx=(20, 16), pady=10)

        # ── Bandeau info ───────────────────────────────────────────────────────
        info = ctk.CTkFrame(frame, fg_color="#FFF8E1", corner_radius=6,
                             border_width=1, border_color="#FFD54F")
        info.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))
        ctk.CTkLabel(info,
                     text="💡  ☑/☐ = inclure/exclure la tâche  "
                          "·  Colonne Contrainte = clic pour choisir le type P6  "
                          "·  Colonne Date cte = clic pour saisir la date  "
                          "·  ES/EF = dates tôt  ·  LS/LF = dates tard (ALAP)",
                     font=ctk.CTkFont("Segoe UI", 10), text_color="#5D4037",
                     wraplength=820, justify="left"
                     ).pack(padx=10, pady=6, anchor="w")

        # ── Treeview tâches avec colonnes P6 ───────────────────────────────────
        tv_card = ctk.CTkFrame(frame, fg_color="white", corner_radius=8,
                                border_width=1, border_color="#E0E0E0")
        tv_card.grid(row=2, column=0, sticky="ew", padx=16, pady=4)
        tv_card.columnconfigure(0, weight=1)

        ctk.CTkLabel(tv_card, text="Tâches DQE — Contraintes P6 — Résultats ALAP",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color="#1565C0"
                     ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 2))

        style = ttk.Style()
        style.configure("Retro.Treeview", background="white",
                        fieldbackground="white", rowheight=26,
                        font=("Segoe UI", 10))
        style.configure("Retro.Treeview.Heading",
                        background="#283593", foreground="white",
                        font=("Segoe UI", 10, "bold"))
        style.map("Retro.Treeview",
                  background=[("selected", "#C5CAE9")],
                  foreground=[("selected", "#000000")])

        retro_cols = ("sel", "activity_id", "designation", "duree",
                      "contrainte", "date_cte",
                      "es", "ef", "ls", "lf", "marge")
        self.retro_tv = ttk.Treeview(tv_card, columns=retro_cols,
                                      show="headings", height=12,
                                      style="Retro.Treeview")
        col_def = [
            ("sel",         "✓",              38,  "center"),
            ("activity_id", "N°",             70,  "center"),
            ("designation", "Désignation",   230,  "w"),
            ("duree",       "Durée (j)",      65,  "center"),
            ("contrainte",  "Contrainte ✎",  118,  "center"),
            ("date_cte",    "Date cte ✎",    105,  "center"),
            ("es",          "ES  Début tôt",  105,  "center"),
            ("ef",          "EF  Fin tôt",    105,  "center"),
            ("ls",          "LS  Début tard", 105,  "center"),
            ("lf",          "LF  Fin tard",   105,  "center"),
            ("marge",       "Marge (j)",       65,  "center"),
        ]
        for cid, clbl, cw, ca in col_def:
            self.retro_tv.heading(cid, text=clbl)
            self.retro_tv.column(cid, width=cw, anchor=ca, minwidth=35)

        vsb = ttk.Scrollbar(tv_card, orient="vertical",   command=self.retro_tv.yview)
        hsb = ttk.Scrollbar(tv_card, orient="horizontal", command=self.retro_tv.xview)
        self.retro_tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.retro_tv.grid(row=1, column=0, sticky="ew", padx=(8, 0))
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew", padx=(8, 0))

        # Tags de couleur
        self.retro_tv.tag_configure("critical",
                                     background="#FFCDD2", foreground="#B71C1C",
                                     font=("Segoe UI", 10, "bold"))
        self.retro_tv.tag_configure("normal",
                                     background="white", foreground="#212121")
        self.retro_tv.tag_configure("inactive",
                                     background="#F5F5F5", foreground="#BDBDBD")

        self.retro_tv.bind("<Button-1>", self._retro_cell_click)

        # État interne
        self._retro_selected:   set  = set()   # activity_ids incluses
        self._task_constraints: dict = {}       # {aid: {"type":..., "date":...}}
        self._links_data:       list = []

        # ── Légende contraintes ────────────────────────────────────────────────
        leg = ctk.CTkFrame(frame, fg_color="transparent")
        leg.grid(row=3, column=0, sticky="w", padx=16, pady=(2, 8))
        ctk.CTkLabel(leg, text="Types P6 : ",
                     font=ctk.CTkFont("Segoe UI", 9), text_color="#757575"
                     ).pack(side="left")
        for code, _, bg, fg in CSTR_INFO:
            f = tk.Frame(leg, bg=bg, bd=1, relief="solid")
            f.pack(side="left", padx=3)
            tk.Label(f, text=f" {code} ",
                     font=("Segoe UI", 9, "bold"), bg=bg, fg=fg).pack()

        # ── Liens logiques ─────────────────────────────────────────────────────
        link_card = ctk.CTkFrame(frame, fg_color="white", corner_radius=8,
                                  border_width=1, border_color="#E0E0E0")
        link_card.grid(row=4, column=0, sticky="ew", padx=16, pady=4)
        link_card.columnconfigure(0, weight=1)

        ctk.CTkLabel(link_card,
                     text="Liens logiques  (Prédécesseur → Successeur · Type · Lag)",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color="#1565C0"
                     ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 2))

        lr = ctk.CTkFrame(link_card, fg_color="transparent")
        lr.grid(row=1, column=0, sticky="ew", padx=8, pady=6)

        ctk.CTkLabel(lr, text="Préd. :", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=4)
        self.link_pred = ctk.CTkEntry(lr, width=80, height=30, placeholder_text="A0001")
        self.link_pred.pack(side="left", padx=2)

        ctk.CTkLabel(lr, text="Succ. :", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=(8, 4))
        self.link_succ = ctk.CTkEntry(lr, width=80, height=30, placeholder_text="A0002")
        self.link_succ.pack(side="left", padx=2)

        ctk.CTkLabel(lr, text="Type :", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=(8, 4))
        self.link_type_var = tk.StringVar(value="FS")
        ctk.CTkComboBox(lr, values=LINK_TYPES, variable=self.link_type_var,
                        width=70, height=30).pack(side="left", padx=2)

        ctk.CTkLabel(lr, text="Lag (j):", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=(8, 4))
        self.link_lag = ctk.CTkEntry(lr, width=55, height=30, placeholder_text="0")
        self.link_lag.pack(side="left", padx=2)

        ctk.CTkButton(lr, text="＋ Ajouter",
                      fg_color="#1565C0", hover_color="#0D47A1",
                      text_color="white", height=30, corner_radius=6,
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._add_link).pack(side="left", padx=10)

        ctk.CTkButton(lr, text="🗑 Effacer tout",
                      fg_color="#B71C1C", hover_color="#7F0000",
                      text_color="white", height=30, corner_radius=6,
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._clear_links).pack(side="left", padx=2)

        self.links_list = tk.StringVar(value=[])
        self._links_lb  = tk.Listbox(link_card, listvariable=self.links_list,
                                      height=4, font=("Segoe UI", 10),
                                      bg="white", selectbackground="#BBDEFB")
        self._links_lb.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))

        # ── Gantt ──────────────────────────────────────────────────────────────
        ctk.CTkLabel(frame,
                     text="Diagramme de Gantt ALAP (rouge = chemin critique) :",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color="#1565C0"
                     ).grid(row=5, column=0, sticky="w", padx=16, pady=(8, 2))

        self.gantt_frame = ctk.CTkFrame(frame, fg_color="white", height=210,
                                         corner_radius=8, border_width=1,
                                         border_color="#E0E0E0")
        self.gantt_frame.grid(row=6, column=0, sticky="ew", padx=16, pady=(0, 20))
        self.gantt_frame.columnconfigure(0, weight=1)
        self._build_gantt_placeholder(self.gantt_frame)

    # ── Gantt placeholder ──────────────────────────────────────────────────────
    def _build_gantt_placeholder(self, parent):
        if HAS_MATPLOTLIB:
            self._fig_gantt = Figure(figsize=(9, 2.8), dpi=80, facecolor="white")
            self._ax_gantt  = self._fig_gantt.add_subplot(111)
            self._ax_gantt.set_facecolor("#FAFAFA")
            self._ax_gantt.set_title(
                "Calculez le rétro-planning pour afficher le Gantt ALAP",
                fontsize=9, color="#888888")
            self._canvas_gantt = FigureCanvasTkAgg(self._fig_gantt, master=parent)
            self._canvas_gantt.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
        else:
            ctk.CTkLabel(parent,
                         text="(matplotlib non installé — Gantt non disponible)\n"
                              "Installez : pip install matplotlib",
                         font=ctk.CTkFont("Segoe UI", 11), text_color="#888888"
                         ).pack(pady=20)

    # ── Clic dans le treeview ──────────────────────────────────────────────────
    def _retro_cell_click(self, event):
        region = self.retro_tv.identify("region", event.x, event.y)
        if region != "cell":
            return
        col    = self.retro_tv.identify_column(event.x)
        row_id = self.retro_tv.identify_row(event.y)
        if not row_id:
            return
        aid = self.retro_tv.set(row_id, "activity_id")

        if col == "#1":                  # ✓ sélection
            if aid in self._retro_selected:
                self._retro_selected.discard(aid)
            else:
                self._retro_selected.add(aid)
            self._reload_retro_table(self._retro_results)

        elif col == "#5":                # Contrainte → popup choix
            self._edit_constraint_popup(row_id, aid)

        elif col == "#6":                # Date cte → popup saisie
            self._edit_date_popup(row_id, aid)

    # ── Popup choix contrainte P6 ──────────────────────────────────────────────
    def _edit_constraint_popup(self, row_id, aid):
        try:
            bbox = self.retro_tv.bbox(row_id, "contrainte")
            rx = self.retro_tv.winfo_rootx() + (bbox[0] if bbox else 200)
            ry = self.retro_tv.winfo_rooty() + (bbox[1] + bbox[3] if bbox else 300)
        except Exception:
            rx = self.winfo_rootx() + 300
            ry = self.winfo_rooty() + 200

        pop = tk.Toplevel(self)
        pop.title(f"Contrainte P6 — {aid}")
        pop.geometry(f"310x320+{rx}+{ry}")
        pop.configure(bg="#FFFFFF")
        pop.grab_set()
        pop.resizable(False, False)

        tk.Label(pop, text=f"  Contrainte — {aid}",
                 font=("Segoe UI", 11, "bold"),
                 bg="#283593", fg="white", pady=8
                 ).pack(fill="x")

        current = self._task_constraints.get(aid, {}).get("type", "ALAP")
        var = tk.StringVar(value=current)

        inner = tk.Frame(pop, bg="#FFFFFF")
        inner.pack(fill="both", expand=True, padx=8, pady=6)

        for code, label, bg, fg in CSTR_INFO:
            needs = "  📅" if code in CSTR_NEEDS_DATE else ""
            rb = tk.Radiobutton(
                inner,
                text=f"  {code}{needs}  —  {label}",
                variable=var, value=code,
                font=("Segoe UI", 10), bg=bg,
                activebackground=bg, fg=fg,
                selectcolor=bg,
                anchor="w", pady=5,
            )
            rb.pack(fill="x", pady=2, padx=4)

        def _apply():
            chosen = var.get()
            if aid not in self._task_constraints:
                self._task_constraints[aid] = {"type": "ALAP", "date": ""}
            self._task_constraints[aid]["type"] = chosen
            if chosen == "ALAP":
                self._task_constraints[aid]["date"] = ""
            self._reload_retro_table(self._retro_results)
            pop.destroy()

        tk.Button(pop, text="✓  Appliquer", command=_apply,
                  bg="#283593", fg="white",
                  font=("Segoe UI", 11, "bold"), relief="flat", pady=7
                  ).pack(fill="x", padx=8, pady=(4, 10))

    # ── Popup saisie date contrainte ───────────────────────────────────────────
    def _edit_date_popup(self, row_id, aid):
        cstr_type = self._task_constraints.get(aid, {}).get("type", "ALAP")
        if cstr_type not in CSTR_NEEDS_DATE:
            messagebox.showinfo(
                "Date contrainte",
                f"La contrainte «{cstr_type}» ne nécessite pas de date.\n"
                "Choisissez d'abord FNLT, MFO, FNET, SNLT, SNET ou MSOB.",
                parent=self)
            return

        try:
            bbox = self.retro_tv.bbox(row_id, "date_cte")
            rx = self.retro_tv.winfo_rootx() + (bbox[0] if bbox else 300)
            ry = self.retro_tv.winfo_rooty() + (bbox[1] + bbox[3] if bbox else 300)
        except Exception:
            rx = self.winfo_rootx() + 400
            ry = self.winfo_rooty() + 200

        pop = tk.Toplevel(self)
        pop.title(f"Date contrainte — {aid}")
        pop.geometry(f"270x140+{rx}+{ry}")
        pop.configure(bg="#FFFFFF")
        pop.grab_set()
        pop.resizable(False, False)

        bg_col = CSTR_BG.get(cstr_type, "#FFFFFF")
        fg_col = CSTR_FG.get(cstr_type, "#000000")
        tk.Label(pop, text=f"  {cstr_type} — {aid}",
                 font=("Segoe UI", 11, "bold"),
                 bg=bg_col, fg=fg_col, pady=7
                 ).pack(fill="x")

        current = self._task_constraints.get(aid, {}).get("date", "")
        var = tk.StringVar(value=current)

        row_f = tk.Frame(pop, bg="#FFFFFF")
        row_f.pack(fill="x", padx=14, pady=12)
        tk.Label(row_f, text="Date (AAAA-MM-JJ) :",
                 font=("Segoe UI", 10), bg="#FFFFFF").pack(side="left")
        entry = tk.Entry(row_f, textvariable=var, width=13,
                         font=("Segoe UI", 11), relief="solid", bd=1)
        entry.pack(side="left", padx=6)
        entry.focus_set()
        entry.select_range(0, "end")

        def _apply(event=None):
            date_str = var.get().strip()
            # Validation format
            if date_str:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Format incorrect",
                                         "Format attendu : AAAA-MM-JJ\nEx : 2025-12-31",
                                         parent=pop)
                    return
            if aid not in self._task_constraints:
                self._task_constraints[aid] = {"type": cstr_type, "date": ""}
            self._task_constraints[aid]["date"] = date_str
            self._reload_retro_table(self._retro_results)
            pop.destroy()

        entry.bind("<Return>", _apply)
        tk.Button(pop, text="✓  OK", command=_apply,
                  bg=bg_col, fg=fg_col,
                  font=("Segoe UI", 11, "bold"), relief="flat", pady=6
                  ).pack(fill="x", padx=14, pady=(0, 10))

    # ── Liens ──────────────────────────────────────────────────────────────────
    def _add_link(self):
        pred = self.link_pred.get().strip()
        succ = self.link_succ.get().strip()
        if not pred or not succ:
            return
        ltype = self.link_type_var.get()
        lag   = self.link_lag.get().strip() or "0"
        lk = {"pred": pred, "succ": succ, "type": ltype, "lag": lag}
        self._links_data.append(lk)
        self._links_lb.insert("end", f"{pred} → {succ}  [{ltype}  lag={lag}j]")

    def _clear_links(self):
        self._links_data = []
        self.links_list.set([])

    # ── Rechargement du treeview ───────────────────────────────────────────────
    def _reload_retro_table(self, results=None):
        for item in self.retro_tv.get_children():
            self.retro_tv.delete(item)

        tasks = self.project_state.get("dqe_tasks", [])
        if not tasks:
            return

        has_selection = bool(self._retro_selected)

        for task in tasks:
            aid = task.get("activity_id", "")
            sel = "☑" if aid in self._retro_selected else "☐"

            cstr      = self._task_constraints.get(aid, {})
            cstr_type = cstr.get("type", "ALAP")
            cstr_date = cstr.get("date", "")

            es = ef = ls = lf = marge = ""
            tag = "inactive" if (has_selection and aid not in self._retro_selected) \
                  else "normal"

            if results and aid in results:
                r = results[aid]
                fmt = "%d/%m/%Y"
                es = r["early_start"].strftime(fmt)  if r.get("early_start")  else ""
                ef = r["early_finish"].strftime(fmt) if r.get("early_finish") else ""
                ls = r["late_start"].strftime(fmt)   if r.get("late_start")   else ""
                lf = r["late_finish"].strftime(fmt)  if r.get("late_finish")  else ""
                f_val = r.get("total_float", 0)
                marge = (f"{f_val:+d} j" if isinstance(f_val, int)
                         else str(f_val))
                if r.get("is_critical") and \
                   not (has_selection and aid not in self._retro_selected):
                    tag = "critical"

            self.retro_tv.insert("", "end", iid=aid, values=(
                sel, aid,
                task.get("designation", ""),
                task.get("duree", ""),
                cstr_type,
                cstr_date,
                es, ef, ls, lf, marge,
            ), tags=(tag,))

    # ── Calcul ALAP ────────────────────────────────────────────────────────────
    def _calculate_retro(self):
        target_str = self.target_date_var.get().strip()
        if not target_str:
            messagebox.showwarning(
                "Date impérative",
                "Saisissez la date impérative au format AAAA-MM-JJ.")
            return
        try:
            target_date = datetime.strptime(target_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror(
                "Format date",
                "Format attendu : AAAA-MM-JJ\nExemple : 2025-12-31")
            return

        all_tasks = self.project_state.get("dqe_tasks", [])
        if not all_tasks:
            messagebox.showwarning("DQE vide",
                                   "Aucune tâche dans le DQE. "
                                   "Importez un DQE avant de calculer.")
            return

        # Tâches à planifier (toutes si aucune sélection, sinon celles cochées)
        tasks_sel = ([t for t in all_tasks if t.get("activity_id") in self._retro_selected]
                     if self._retro_selected else all_tasks)

        # Calendrier
        cal = "6j" if "6j" in self.retro_cal_var.get() else "5j"

        # Convertir pour le moteur CPM
        rp_tasks = []
        for t in tasks_sel:
            aid          = t.get("activity_id", "")
            cstr         = self._task_constraints.get(aid, {})
            cstr_type    = cstr.get("type", "ALAP")
            cstr_date_s  = cstr.get("date", "")
            cstr_date    = None
            if cstr_date_s and cstr_type in CSTR_NEEDS_DATE:
                try:
                    cstr_date = datetime.strptime(cstr_date_s, "%Y-%m-%d").date()
                except ValueError:
                    pass

            rp_tasks.append({
                "activity_id": aid,
                "task_name":   t.get("designation", ""),
                "duration":    int(t.get("duree", 0) or 0),
                "cstr_type":   cstr_type,
                "cstr_date":   cstr_date,
            })

        # Liens
        links = [
            {"from_id":   lk["pred"],
             "to_id":     lk["succ"],
             "link_type": lk.get("type", "FS"),
             "lag":       int(lk.get("lag", 0) or 0)}
            for lk in self._links_data
        ]

        try:
            rp      = RetroPlanning(calendar=cal)
            results = rp.calculate(rp_tasks, target_date, links)
            self._retro_results = results
            self._reload_retro_table(results)
            self._draw_gantt(results)

            summary    = rp.get_summary()
            nb_crit    = summary.get("nb_critical", 0)
            proj_start = summary.get("project_start")
            proj_fin   = summary.get("project_finish")
            s_str = proj_start.strftime("%d/%m/%Y") if proj_start else "—"
            f_str = proj_fin.strftime("%d/%m/%Y")   if proj_fin   else "—"

            self.update_status(
                f"ALAP — Début tard : {s_str}  ›  Fin tard : {f_str}  "
                f"·  {nb_crit} tâche(s) critique(s)")

            messagebox.showinfo(
                "Rétro-planning ALAP — Résultat",
                f"✅  Calcul terminé !\n\n"
                f"Date impérative     : {target_str}\n"
                f"Début au plus tard  : {s_str}\n"
                f"Fin au plus tard    : {f_str}\n"
                f"Tâches critiques    : {nb_crit}\n\n"
                f"Les colonnes LS / LF (rouge) indiquent\n"
                f"les dates à respecter pour finir à temps.")

        except Exception as ex:
            import traceback
            messagebox.showerror("Erreur calcul ALAP",
                                 f"{ex}\n\n{traceback.format_exc()}")

    # ── Gantt ──────────────────────────────────────────────────────────────────
    def _draw_gantt(self, results):
        if not HAS_MATPLOTLIB or not results:
            return
        self._ax_gantt.clear()

        tasks_sorted = sorted(results.values(),
                              key=lambda r: r.get("late_start") or date_type.today())
        shown = tasks_sorted[:18]

        if not shown:
            return

        # Référence temporelle = early_start minimum
        all_es = [r["early_start"] for r in shown if r.get("early_start")]
        if not all_es:
            return
        t0 = min(all_es)

        y_labels = []
        for i, r in enumerate(shown):
            aid = r["activity_id"]
            # Barre tôt (bleu clair)
            if r.get("early_start") and r.get("early_finish"):
                es_off = (r["early_start"] - t0).days
                ef_off = (r["early_finish"] - t0).days
                self._ax_gantt.barh(i, ef_off - es_off + 1, left=es_off,
                                     color="#90CAF9", alpha=0.6, height=0.35,
                                     label="Dates tôt" if i == 0 else "")
            # Barre tard (rouge si critique, bleu foncé sinon)
            if r.get("late_start") and r.get("late_finish"):
                ls_off = (r["late_start"] - t0).days
                lf_off = (r["late_finish"] - t0).days
                color  = "#EF5350" if r.get("is_critical") else "#1565C0"
                self._ax_gantt.barh(i, lf_off - ls_off + 1, left=ls_off,
                                     color=color, alpha=0.85, height=0.35,
                                     align="edge",
                                     label="Dates tard" if i == 0 else "")
            y_labels.append(r.get("task_name", aid)[:28] or aid)

        self._ax_gantt.set_yticks(range(len(y_labels)))
        self._ax_gantt.set_yticklabels(y_labels, fontsize=7)
        self._ax_gantt.set_xlabel("Jours depuis le démarrage tôt", fontsize=8)
        self._ax_gantt.set_title(
            "Gantt ALAP  —  🔵 dates tôt  🔴 critique  🔵 chemin non-critique",
            fontsize=9)
        self._ax_gantt.invert_yaxis()
        self._fig_gantt.tight_layout()
        self._canvas_gantt.draw()

    # ═════════════════════════════════════════════════════════════════════════
    # ONGLET B — Paramètres XER
    # ═════════════════════════════════════════════════════════════════════════
    def _build_section_params(self):
        frame = ctk.CTkScrollableFrame(self.nb, fg_color="white")
        self.nb.add(frame, text="B  Paramètres XER")
        frame.columnconfigure(1, weight=1)

        params = [
            ("Nom du projet :",      "name",       "entry"),
            ("Identifiant projet :", "proj_id",    "entry"),
            ("Date démarrage :",     "start_date", "entry"),
            ("Calendrier :",         "calendar",   "combo_cal"),
            ("Devise :",             "currency",   "combo_dev"),
            ("Version P6 :",         "p6_version", "combo_p6"),
            ("Niveau WBS max :",     "wbs_level",  "combo_wbs"),
        ]

        self._param_vars = {}
        for row, (lbl, key, wtype) in enumerate(params):
            ctk.CTkLabel(frame, text=lbl,
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         text_color="#333333"
                         ).grid(row=row, column=0, sticky="w", padx=(24, 8), pady=8)

            val = self.project_state.get(key, "")
            var = tk.StringVar(value=str(val) if val else "")
            self._param_vars[key] = var

            if wtype == "entry":
                ctk.CTkEntry(frame, textvariable=var, width=320, height=34
                             ).grid(row=row, column=1, sticky="w", padx=(0, 24), pady=8)
            elif wtype == "combo_cal":
                ctk.CTkComboBox(frame, values=CALENDRIERS, variable=var,
                                width=200, height=34
                                ).grid(row=row, column=1, sticky="w", padx=(0, 24), pady=8)
            elif wtype == "combo_dev":
                ctk.CTkComboBox(frame, values=DEVISES, variable=var,
                                width=120, height=34
                                ).grid(row=row, column=1, sticky="w", padx=(0, 24), pady=8)
            elif wtype == "combo_p6":
                ctk.CTkComboBox(frame, values=P6_VERSIONS, variable=var,
                                width=220, height=34
                                ).grid(row=row, column=1, sticky="w", padx=(0, 24), pady=8)
            elif wtype == "combo_wbs":
                ctk.CTkComboBox(frame, values=WBS_LEVELS, variable=var,
                                width=100, height=34
                                ).grid(row=row, column=1, sticky="w", padx=(0, 24), pady=8)

        ctk.CTkButton(frame, text="💾 Enregistrer les paramètres",
                      fg_color="#1565C0", hover_color="#0D47A1", text_color="white",
                      height=40, corner_radius=8,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      command=self._save_params
                      ).grid(row=len(params), column=0, columnspan=2,
                             pady=20, padx=24, sticky="ew")

    def _save_params(self):
        for key, var in self._param_vars.items():
            self.project_state[key] = var.get()
        self.update_status("Paramètres XER enregistrés")
        messagebox.showinfo("Paramètres", "Paramètres XER enregistrés avec succès.")

    # ═════════════════════════════════════════════════════════════════════════
    # ONGLET C — Vérificateur
    # ═════════════════════════════════════════════════════════════════════════
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
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      command=self._run_checks
                      ).pack(side="left")

        results_outer = ctk.CTkScrollableFrame(frame, fg_color="white")
        results_outer.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
        results_outer.columnconfigure(0, weight=1)
        self.checks_frame = results_outer

    def _run_checks(self):
        for w in self.checks_frame.winfo_children():
            w.destroy()

        ps     = self.project_state
        checks = []

        def chk(icon, msg, level="ok"):
            checks.append((icon, msg, level))

        tasks     = ps.get("dqe_tasks", [])
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

        no_dur = [t.get("activity_id", "?") for t in tasks
                  if not t.get("duree") or str(t.get("duree")) == "0"]
        if no_dur:
            chk("⚠", f"Tâches sans durée : {', '.join(no_dur[:5])}", "warn")
        else:
            chk("✓", "Toutes les tâches ont une durée", "ok")

        no_des = [t.get("activity_id", "?") for t in tasks
                  if not t.get("designation", "").strip()]
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

        color_map = {"ok": "#1B5E20", "warn": "#E65100", "err": "#B71C1C"}
        bg_map    = {"ok": "#E8F5E9", "warn": "#FFF8E1", "err": "#FFEBEE"}

        ctk.CTkLabel(self.checks_frame, text="Résultats de la vérification :",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color="#1565C0"
                     ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        for i, (icon, msg, level) in enumerate(checks):
            row_fr = ctk.CTkFrame(self.checks_frame,
                                   fg_color=bg_map[level], corner_radius=6)
            row_fr.grid(row=i + 1, column=0, sticky="ew", pady=2)
            ctk.CTkLabel(row_fr, text=f"  {icon}  {msg}",
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=color_map[level], anchor="w"
                         ).pack(fill="x", padx=8, pady=4)

        err_count  = sum(1 for _, _, l in checks if l == "err")
        warn_count = sum(1 for _, _, l in checks if l == "warn")
        ok_count   = sum(1 for _, _, l in checks if l == "ok")
        self.update_status(
            f"Résultat : {ok_count} OK — {warn_count} avertissement(s) — {err_count} erreur(s)")

    # ═════════════════════════════════════════════════════════════════════════
    # ONGLET D — Génération XER
    # ═════════════════════════════════════════════════════════════════════════
    def _build_section_generate(self):
        frame = ctk.CTkFrame(self.nb, fg_color="white")
        self.nb.add(frame, text="D  Génération XER")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        top = ctk.CTkFrame(frame, fg_color="white")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=16)
        top.columnconfigure(1, weight=1)

        ctk.CTkButton(top, text="⚙ Générer le fichier XER",
                      fg_color="#1565C0", hover_color="#0D47A1", text_color="white",
                      height=44, corner_radius=8,
                      font=ctk.CTkFont("Segoe UI", 14, "bold"),
                      command=self._generate_xer
                      ).grid(row=0, column=0, padx=(0, 12))

        ctk.CTkButton(top, text="💾 Télécharger .xer",
                      fg_color="#2E7D32", hover_color="#1B5E20", text_color="white",
                      height=44, corner_radius=8,
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      command=self._download_xer
                      ).grid(row=0, column=1, padx=(0, 12), sticky="w")

        # Statistiques
        self.stats_frame = ctk.CTkFrame(frame, fg_color="#E3F2FD", corner_radius=8,
                                         border_width=1, border_color="#90CAF9")
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
        self.stats_var = tk.StringVar(value="Statistiques : générez d'abord le fichier XER.")
        ctk.CTkLabel(self.stats_frame, textvariable=self.stats_var,
                     font=ctk.CTkFont("Segoe UI", 11), text_color="#1565C0"
                     ).pack(padx=12, pady=8)

        # Journal coloré
        log_outer = ctk.CTkFrame(frame, fg_color="#1E1E2E", corner_radius=8)
        log_outer.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 16))
        log_outer.columnconfigure(0, weight=1)
        log_outer.rowconfigure(1, weight=1)

        ctk.CTkLabel(log_outer, text="Journal de génération",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color="#AAAACC"
                     ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))

        self.log_text = tk.Text(log_outer, bg="#1E1E2E", fg="#A0CFFF",
                                 font=("Courier New", 10), wrap="word",
                                 state="disabled", relief="flat", height=14)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

        log_vsb = ttk.Scrollbar(log_outer, orient="vertical",
                                  command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_vsb.set)
        log_vsb.grid(row=1, column=1, sticky="ns")

        self.log_text.tag_configure("ok",   foreground="#00E676")
        self.log_text.tag_configure("warn", foreground="#FFD740")
        self.log_text.tag_configure("err",  foreground="#FF5252")
        self.log_text.tag_configure("info", foreground="#40C4FF")
        self.log_text.tag_configure("head", foreground="#CE93D8",
                                     font=("Courier New", 10, "bold"))

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
        self._log(f"  PlanHub — Génération XER  "
                  f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]", "head")
        self._log("=" * 60, "head")

        ps    = self.project_state
        tasks = ps.get("dqe_tasks", [])

        if not tasks:
            self._log("❌ Aucune tâche dans le DQE — génération annulée.", "err")
            messagebox.showerror("Erreur",
                                  "Le DQE est vide. Ajoutez des tâches avant de générer.")
            return

        self._log(f"✓ Projet   : {ps.get('name', '—')}", "ok")
        self._log(f"✓ ID       : {ps.get('proj_id', '—')}", "ok")
        self._log(f"✓ {len(tasks)} tâche(s) importées du DQE", "info")

        resources     = ps.get("resources", [])
        task_resources = ps.get("task_resources", [])
        self._log(f"✓ {len(resources)} ressource(s)", "info")

        cal_raw    = ps.get("calendar", "5j")
        calendar   = "6j" if "6j" in str(cal_raw) else "5j"
        p6_label   = ps.get("p6_version", "Primavera P6 v15")
        p6_version = P6_VERSION_MAP.get(p6_label, "15.1")

        project = {
            "proj_id":    ps.get("proj_id", "PROJ001") or "PROJ001",
            "name":       ps.get("name", "Projet PlanHub") or "Projet PlanHub",
            "start_date": ps.get("start_date", ""),
            "currency":   ps.get("currency", "FCFA"),
            "tasks":      tasks,
        }

        try:
            gen     = XERGenerator()
            content = gen.generate(
                project=project, tasks=tasks,
                resources=resources, task_resources=task_resources,
                calendar=calendar, p6_version=p6_version,
            )
            self._xer_content = content

            nb_tasks_xer = len([t for t in tasks if t.get("task_type") != "TT_WBS"])
            wbs_codes    = {t.get("wbs", t.get("wbs_code", ""))
                            for t in tasks if t.get("wbs", t.get("wbs_code", ""))}

            self._log(f"✓ WBS exportés    : {len(wbs_codes)}", "ok")
            self._log(f"✓ Tâches générées : {nb_tasks_xer}", "ok")
            self._log(f"✓ Ressources      : {len(resources)}", "ok")
            self._log(f"✓ Calendrier      : Cal_{calendar}", "ok")
            self._log(f"✓ Version P6      : {p6_version}", "ok")
            self._log(f"✓ Encodage        : latin-1 (standard P6)", "ok")
            self._log("✓ Fichier XER généré avec succès !", "ok")
            self._log("=" * 60, "head")

            self.stats_var.set(
                f"WBS : {len(wbs_codes)}  |  Tâches : {nb_tasks_xer}"
                f"  |  Ressources : {len(resources)}")
            self.update_status("XER généré — prêt au téléchargement")

        except Exception as ex:
            import traceback
            self._log(f"❌ Erreur : {ex}", "err")
            self._log(traceback.format_exc(), "err")
            messagebox.showerror("Erreur de génération", str(ex))

    def _download_xer(self):
        if not self._xer_content:
            messagebox.showwarning("XER non généré",
                                   "Veuillez d'abord générer le fichier XER.")
            return

        proj_name    = self.project_state.get("name", "projet").replace(" ", "_")
        default_name = f"{proj_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.xer"

        path = filedialog.asksaveasfilename(
            title="Enregistrer le fichier XER",
            defaultextension=".xer",
            filetypes=[("Fichiers XER", "*.xer"), ("Tous les fichiers", "*.*")],
            initialfile=default_name,
        )
        if not path:
            return

        try:
            xer_bytes = encode_xer(self._xer_content)
            with open(path, "wb") as f:
                f.write(xer_bytes)
            self._log(f"✓ Fichier téléchargé : {path}", "ok")
            messagebox.showinfo("Succès", f"Fichier XER enregistré :\n{path}")
            self.update_status(f"XER téléchargé : {path}")
        except Exception as ex:
            messagebox.showerror("Erreur d'enregistrement", str(ex))

    # ── Refresh ────────────────────────────────────────────────────────────────
    def refresh(self):
        self._reload_retro_table(self._retro_results)
        ps = self.project_state
        if hasattr(self, "_param_vars"):
            for key, var in self._param_vars.items():
                var.set(str(ps.get(key, "") or ""))
        self.nb.select(3)   # toujours onglet D
        self.update_status("Page Génération XER rechargée")
