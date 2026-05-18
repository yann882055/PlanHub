"""
core/retro_planning.py — PlanHub v1.0
Calcul du rétro-planning ALAP (As Late As Possible) avec contraintes P6.

Contraintes supportées (comme Primavera P6) :
  ALAP  — As Late As Possible          (aucune date requise)
  FNLT  — Finish No Later Than         (LF <= date)
  MFO   — Must Finish On               (LF = date exacte)
  FNET  — Finish No Earlier Than       (EF >= date)
  SNLT  — Start No Later Than          (LS <= date)
  SNET  — Start No Earlier Than        (ES >= date)
  MSOB  — Must Start On or Before      (LS <= date, comme SNLT côté tardif)
"""

import datetime
from typing import List, Dict, Any, Optional


WORK_DAYS_5J = {0, 1, 2, 3, 4}   # Lun–Ven
WORK_DAYS_6J = {0, 1, 2, 3, 4, 5}  # Lun–Sam


# ─────────────────────────────────────────────────────────────────────────────
# Helpers calendrier
# ─────────────────────────────────────────────────────────────────────────────

def add_working_days(
    date: datetime.date,
    days: int,
    calendar: str = "5j",
    holidays: List[datetime.date] = None,
) -> datetime.date:
    """Ajoute N jours ouvrés à une date (N peut être négatif)."""
    holidays = holidays or []
    work_days = WORK_DAYS_5J if calendar == "5j" else WORK_DAYS_6J
    current = date
    remaining = abs(days)
    direction = 1 if days >= 0 else -1
    while remaining > 0:
        current += datetime.timedelta(days=direction)
        if current.weekday() in work_days and current not in holidays:
            remaining -= 1
    return current


def subtract_working_days(
    date: datetime.date,
    days: int,
    calendar: str = "5j",
    holidays: List[datetime.date] = None,
) -> datetime.date:
    """Soustrait N jours ouvrés à une date."""
    return add_working_days(date, -days, calendar, holidays)


def next_working_day(
    date: datetime.date,
    calendar: str = "5j",
    holidays: List[datetime.date] = None,
) -> datetime.date:
    """Retourne le prochain jour ouvré >= date."""
    holidays = holidays or []
    work_days = WORK_DAYS_5J if calendar == "5j" else WORK_DAYS_6J
    current = date
    while current.weekday() not in work_days or current in holidays:
        current += datetime.timedelta(days=1)
    return current


# ─────────────────────────────────────────────────────────────────────────────
# Moteur CPM ALAP
# ─────────────────────────────────────────────────────────────────────────────

class RetroPlanning:
    """
    Calcul CPM en mode ALAP (As Late As Possible).

    Algorithme :
      1. Tri topologique du réseau (Kahn)
      2. Passe arrière  → Late Start / Late Finish depuis la date impérative
      3. Application des contraintes sur les dates tardives (FNLT, MFO, SNLT, MSOB)
      4. Passe avant    → Early Start / Early Finish
      5. Application des contraintes sur les dates tôt (SNET, FNET)
      6. Calcul marges  → Total Float = LS – ES
      7. Chemin critique → Float <= 0
    """

    def __init__(self, calendar: str = "5j", holidays: List[datetime.date] = None):
        self.calendar  = calendar
        self.holidays  = holidays or []
        self.results: Dict[str, Dict] = {}
        self.critical_path: List[str] = []

    # ── Passe arrière (backward pass) ─────────────────────────────────────────
    def _backward_pass(self, topo_order, task_dict, successors, predecessors,
                       target_date):
        """Calcule LF / LS depuis la date impérative."""
        late_finish: Dict[str, datetime.date] = {}
        late_start:  Dict[str, datetime.date] = {}

        # Initialiser toutes les LF = date impérative
        for aid in task_dict:
            late_finish[aid] = target_date

        for aid in reversed(topo_order):
            task = task_dict[aid]
            dur  = int(task.get("duration", 0))
            lf   = late_finish[aid]

            ls = subtract_working_days(lf, dur - 1, self.calendar, self.holidays) \
                 if dur > 0 else lf
            late_start[aid] = ls

            # Propager aux prédécesseurs
            for link in predecessors.get(aid, []):
                pred_id   = link.get("from_id", "")
                link_type = link.get("link_type", "FS")
                lag       = int(link.get("lag", 0))

                if link_type == "FS":
                    new_lf = subtract_working_days(ls, 1 + lag, self.calendar, self.holidays)
                elif link_type == "SS":
                    pred_dur = int(task_dict.get(pred_id, {}).get("duration", 0))
                    new_lf = add_working_days(
                        subtract_working_days(ls, lag, self.calendar, self.holidays),
                        pred_dur - 1, self.calendar, self.holidays)
                elif link_type == "FF":
                    new_lf = subtract_working_days(lf, lag, self.calendar, self.holidays)
                elif link_type == "SF":
                    pred_dur = int(task_dict.get(pred_id, {}).get("duration", 0))
                    new_lf = subtract_working_days(lf, lag + pred_dur, self.calendar, self.holidays)
                else:
                    new_lf = subtract_working_days(ls, 1, self.calendar, self.holidays)

                if pred_id in late_finish and new_lf < late_finish[pred_id]:
                    late_finish[pred_id] = new_lf

        return late_finish, late_start

    # ── Passe avant (forward pass) ────────────────────────────────────────────
    def _forward_pass(self, topo_order, task_dict, successors, predecessors,
                      project_start):
        """Calcule ES / EF depuis le début de projet."""
        early_start:  Dict[str, datetime.date] = {}
        early_finish: Dict[str, datetime.date] = {}

        for aid in task_dict:
            early_start[aid] = project_start

        for aid in topo_order:
            task = task_dict[aid]
            dur  = int(task.get("duration", 0))
            es   = early_start[aid]
            ef   = add_working_days(es, dur - 1, self.calendar, self.holidays) \
                   if dur > 0 else es
            early_finish[aid] = ef

            for succ_id in successors.get(aid, []):
                for link in predecessors.get(succ_id, []):
                    if link.get("from_id") != aid:
                        continue
                    link_type = link.get("link_type", "FS")
                    lag       = int(link.get("lag", 0))

                    if link_type == "FS":
                        new_es = add_working_days(ef, 1 + lag, self.calendar, self.holidays)
                    elif link_type == "SS":
                        new_es = add_working_days(es, lag, self.calendar, self.holidays)
                    elif link_type == "FF":
                        succ_dur = int(task_dict.get(succ_id, {}).get("duration", 0))
                        new_ef   = add_working_days(ef, lag, self.calendar, self.holidays)
                        new_es   = subtract_working_days(new_ef, succ_dur - 1,
                                                         self.calendar, self.holidays)
                    elif link_type == "SF":
                        succ_dur = int(task_dict.get(succ_id, {}).get("duration", 0))
                        new_es   = subtract_working_days(es, succ_dur - 1 - lag,
                                                         self.calendar, self.holidays)
                    else:
                        new_es = add_working_days(ef, 1, self.calendar, self.holidays)

                    if succ_id in early_start and new_es > early_start[succ_id]:
                        early_start[succ_id] = new_es

        # Recalculer EF après propagation
        for aid in topo_order:
            dur = int(task_dict[aid].get("duration", 0))
            es  = early_start[aid]
            early_finish[aid] = add_working_days(es, dur - 1, self.calendar, self.holidays) \
                                 if dur > 0 else es

        return early_start, early_finish

    # ── Application des contraintes P6 ────────────────────────────────────────
    def _apply_late_constraints(self, task_dict, late_finish, late_start):
        """
        Ajuste les dates tardives selon la contrainte P6 de chaque tâche.
        Appelé APRÈS la passe arrière.
        Contraintes : FNLT, MFO, SNLT, MSOB.
        """
        for aid, task in task_dict.items():
            cstr      = task.get("cstr_type", "ALAP")
            cstr_date = task.get("cstr_date")
            if not cstr_date or cstr == "ALAP":
                continue
            dur = int(task.get("duration", 0))

            if cstr == "FNLT":
                # Finish No Later Than → LF = min(LF, cstr_date)
                if late_finish[aid] > cstr_date:
                    late_finish[aid] = cstr_date
                    late_start[aid]  = subtract_working_days(
                        cstr_date, dur - 1, self.calendar, self.holidays) \
                        if dur > 0 else cstr_date

            elif cstr == "MFO":
                # Must Finish On → LF = cstr_date (exact)
                late_finish[aid] = cstr_date
                late_start[aid]  = subtract_working_days(
                    cstr_date, dur - 1, self.calendar, self.holidays) \
                    if dur > 0 else cstr_date

            elif cstr == "SNLT":
                # Start No Later Than → LS = min(LS, cstr_date)
                if late_start[aid] > cstr_date:
                    late_start[aid]  = cstr_date
                    late_finish[aid] = add_working_days(
                        cstr_date, dur - 1, self.calendar, self.holidays) \
                        if dur > 0 else cstr_date

            elif cstr == "MSOB":
                # Must Start On or Before → LS <= cstr_date
                if late_start[aid] > cstr_date:
                    late_start[aid]  = cstr_date
                    late_finish[aid] = add_working_days(
                        cstr_date, dur - 1, self.calendar, self.holidays) \
                        if dur > 0 else cstr_date

    def _apply_early_constraints(self, task_dict, early_start, early_finish):
        """
        Ajuste les dates tôt selon la contrainte P6.
        Appelé APRÈS la passe avant.
        Contraintes : SNET, FNET.
        """
        for aid, task in task_dict.items():
            cstr      = task.get("cstr_type", "ALAP")
            cstr_date = task.get("cstr_date")
            if not cstr_date or cstr == "ALAP":
                continue
            dur = int(task.get("duration", 0))

            if cstr == "SNET":
                # Start No Earlier Than → ES >= cstr_date
                if early_start[aid] < cstr_date:
                    early_start[aid]  = cstr_date
                    early_finish[aid] = add_working_days(
                        cstr_date, dur - 1, self.calendar, self.holidays) \
                        if dur > 0 else cstr_date

            elif cstr == "FNET":
                # Finish No Earlier Than → EF >= cstr_date
                if early_finish[aid] < cstr_date:
                    early_finish[aid] = cstr_date
                    early_start[aid]  = subtract_working_days(
                        cstr_date, dur - 1, self.calendar, self.holidays) \
                        if dur > 0 else cstr_date

    # ── Point d'entrée principal ──────────────────────────────────────────────
    def calculate(
        self,
        tasks: List[Dict[str, Any]],
        target_date: datetime.date,
        links: List[Dict] = None,
    ) -> Dict[str, Dict]:
        """
        Calcule le rétro-planning ALAP complet avec contraintes P6.

        Args:
            tasks : liste de dicts
                    { activity_id, duration, cstr_type, cstr_date (date|None) }
            target_date : date impérative (fin du projet)
            links : liste de dicts
                    { from_id, to_id, link_type (FS/SS/FF/SF), lag (int) }

        Returns:
            Dict activity_id → résultat complet
        """
        links = links or []

        # ── Construire le graphe ──────────────────────────────────────────────
        task_dict  = {t["activity_id"]: t for t in tasks}
        successors: Dict[str, List] = {t["activity_id"]: [] for t in tasks}
        predecessors: Dict[str, List] = {t["activity_id"]: [] for t in tasks}

        for link in links:
            fid = link.get("from_id", "")
            tid = link.get("to_id", "")
            if fid in successors and tid in predecessors:
                successors[fid].append(tid)
                predecessors[tid].append(link)

        # ── Tri topologique (Kahn) ────────────────────────────────────────────
        in_degree = {t["activity_id"]: 0 for t in tasks}
        for link in links:
            tid = link.get("to_id", "")
            if tid in in_degree:
                in_degree[tid] += 1

        queue      = [aid for aid, deg in in_degree.items() if deg == 0]
        topo_order = []
        while queue:
            node = queue.pop(0)
            topo_order.append(node)
            for succ in successors.get(node, []):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        # Ajouter les tâches orphelines du cycle détecté (sécurité)
        for aid in task_dict:
            if aid not in topo_order:
                topo_order.append(aid)

        # ── Passe arrière ─────────────────────────────────────────────────────
        late_finish, late_start = self._backward_pass(
            topo_order, task_dict, successors, predecessors, target_date)

        # ── Contraintes sur dates tardives ────────────────────────────────────
        self._apply_late_constraints(task_dict, late_finish, late_start)

        # ── Passe avant ───────────────────────────────────────────────────────
        project_start = min(late_start.values()) if late_start else target_date
        project_start = next_working_day(project_start, self.calendar, self.holidays)

        early_start, early_finish = self._forward_pass(
            topo_order, task_dict, successors, predecessors, project_start)

        # ── Contraintes sur dates tôt ─────────────────────────────────────────
        self._apply_early_constraints(task_dict, early_start, early_finish)

        # ── Calcul marges + résultats ─────────────────────────────────────────
        self.results = {}
        for task in tasks:
            aid = task["activity_id"]
            ls  = late_start.get(aid,   target_date)
            es  = early_start.get(aid,  project_start)
            lf  = late_finish.get(aid,  target_date)
            ef  = early_finish.get(aid, project_start)

            try:
                total_float = (ls - es).days
            except Exception:
                total_float = 0

            is_critical = total_float <= 0

            self.results[aid] = {
                "activity_id":  aid,
                "task_name":    task.get("task_name", ""),
                "duration":     int(task.get("duration", 0)),
                "early_start":  es,
                "early_finish": ef,
                "late_start":   ls,
                "late_finish":  lf,
                "total_float":  total_float,
                "is_critical":  is_critical,
                "cstr_type":    task.get("cstr_type", "ALAP"),
                "cstr_date":    task.get("cstr_date"),
                # Pour export XER : utiliser les dates ALAP (= dates tardives)
                "target_start":  ls,
                "target_finish": lf,
            }

        self.critical_path = [
            aid for aid, r in self.results.items() if r["is_critical"]
        ]
        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Résumé du rétro-planning calculé."""
        if not self.results:
            return {}
        all_ls = [r["late_start"]   for r in self.results.values() if r.get("late_start")]
        all_lf = [r["late_finish"]  for r in self.results.values() if r.get("late_finish")]
        all_es = [r["early_start"]  for r in self.results.values() if r.get("early_start")]
        return {
            "project_start":    min(all_ls) if all_ls else None,
            "project_finish":   max(all_lf) if all_lf else None,
            "early_project_start": min(all_es) if all_es else None,
            "nb_tasks":         len(self.results),
            "nb_critical":      len(self.critical_path),
            "critical_path":    self.critical_path,
        }
