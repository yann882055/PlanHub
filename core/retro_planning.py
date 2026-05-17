"""
core/retro_planning.py — PlanHub v1.0
Calcul du rétro-planning ALAP (As Late As Possible)
Calcul en sens inverse depuis une date cible.
"""

import datetime
from typing import List, Dict, Any, Optional


WORK_DAYS_5J = {0, 1, 2, 3, 4}  # Lun-Ven
WORK_DAYS_6J = {0, 1, 2, 3, 4, 5}  # Lun-Sam


def add_working_days(
    date: datetime.date,
    days: int,
    calendar: str = "5j",
    holidays: List[datetime.date] = None,
) -> datetime.date:
    """Ajoute N jours ouvrés à une date."""
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
    """Soustrait N jours ouvrés à une date (rétro-planning)."""
    return add_working_days(date, -days, calendar, holidays)


def next_working_day(
    date: datetime.date,
    calendar: str = "5j",
    holidays: List[datetime.date] = None,
) -> datetime.date:
    """Retourne le prochain jour ouvré à partir de date."""
    holidays = holidays or []
    work_days = WORK_DAYS_5J if calendar == "5j" else WORK_DAYS_6J
    current = date
    while current.weekday() not in work_days or current in holidays:
        current += datetime.timedelta(days=1)
    return current


class RetroPlanning:
    """
    Calcul du rétro-planning ALAP.

    Principe : depuis la date cible (fin du projet ou date jalon),
    on calcule les dates de début de chaque tâche en remontant
    selon leurs durées et leurs relations logiques.
    """

    def __init__(self, calendar: str = "5j", holidays: List[datetime.date] = None):
        self.calendar = calendar
        self.holidays = holidays or []
        self.results: Dict[str, Dict] = {}
        self.critical_path: List[str] = []

    def calculate(
        self,
        tasks: List[Dict[str, Any]],
        target_date: datetime.date,
        links: List[Dict] = None,
    ) -> Dict[str, Dict]:
        """
        Calcule le rétro-planning ALAP.

        Args:
            tasks: Liste de dicts {activity_id, duration, predecessors, ...}
            target_date: Date cible (fin du dernier jalon)
            links: Liste de liens [{from_id, to_id, link_type, lag}]

        Returns:
            Dict activity_id → {start, finish, float, is_critical, cstr_type, cstr_date}
        """
        links = links or []

        # Construire le graphe
        # task_dict: activity_id → task
        task_dict = {t["activity_id"]: t for t in tasks}

        # successeurs: activity_id → [activity_id]
        successors: Dict[str, List] = {t["activity_id"]: [] for t in tasks}
        # predecesseurs: activity_id → [link_dict]
        predecessors: Dict[str, List] = {t["activity_id"]: [] for t in tasks}

        for link in links:
            from_id = link.get("from_id", "")
            to_id = link.get("to_id", "")
            if from_id in successors and to_id in predecessors:
                successors[from_id].append(to_id)
                predecessors[to_id].append(link)

        # Tri topologique (Kahn's algorithm)
        in_degree = {t["activity_id"]: 0 for t in tasks}
        for link in links:
            to_id = link.get("to_id", "")
            if to_id in in_degree:
                in_degree[to_id] += 1

        queue = [aid for aid, deg in in_degree.items() if deg == 0]
        topo_order = []
        while queue:
            node = queue.pop(0)
            topo_order.append(node)
            for succ in successors.get(node, []):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        # Passe arrière : calculer les dates de fin au plus tard
        # Toutes les tâches sans successeur se terminent à target_date
        late_finish: Dict[str, datetime.date] = {}
        late_start: Dict[str, datetime.date] = {}

        # Initialiser LF = target_date pour toutes
        for task in tasks:
            aid = task["activity_id"]
            late_finish[aid] = target_date

        # Passe arrière (ordre inverse du tri topologique)
        for aid in reversed(topo_order):
            task = task_dict[aid]
            dur = int(task.get("duration", 0))
            lf = late_finish[aid]

            # LS = LF - durée
            if dur > 0:
                ls = subtract_working_days(lf, dur - 1, self.calendar, self.holidays)
            else:
                ls = lf

            late_start[aid] = ls

            # Mettre à jour LF des prédécesseurs
            for link in predecessors.get(aid, []):
                pred_id = link.get("from_id", "")
                link_type = link.get("link_type", "FS")
                lag = int(link.get("lag", 0))

                if link_type == "FS":
                    # Prédécesseur doit finir avant que successeur commence
                    new_lf = subtract_working_days(ls, 1 + lag, self.calendar, self.holidays)
                elif link_type == "SS":
                    new_lf = subtract_working_days(ls, lag, self.calendar, self.holidays)
                    pred_dur = int(task_dict.get(pred_id, {}).get("duration", 0))
                    new_lf = add_working_days(new_lf, pred_dur - 1, self.calendar, self.holidays)
                elif link_type == "FF":
                    new_lf = subtract_working_days(lf, lag, self.calendar, self.holidays)
                elif link_type == "SF":
                    pred_dur = int(task_dict.get(pred_id, {}).get("duration", 0))
                    new_lf = subtract_working_days(lf, lag + pred_dur, self.calendar, self.holidays)
                else:
                    new_lf = subtract_working_days(ls, 1, self.calendar, self.holidays)

                if pred_id in late_finish:
                    if new_lf < late_finish[pred_id]:
                        late_finish[pred_id] = new_lf

        # Passe avant : calculer les dates au plus tôt (forward pass)
        early_start: Dict[str, datetime.date] = {}
        early_finish: Dict[str, datetime.date] = {}

        # Initialiser ES à la date de démarrage (late_start minimal)
        project_start = min(late_start.values()) if late_start else target_date

        for task in tasks:
            aid = task["activity_id"]
            early_start[aid] = project_start

        for aid in topo_order:
            task = task_dict[aid]
            dur = int(task.get("duration", 0))
            es = early_start[aid]
            ef = add_working_days(es, dur - 1, self.calendar, self.holidays) if dur > 0 else es
            early_finish[aid] = ef

            for succ_id in successors.get(aid, []):
                # Trouver le lien
                for link in predecessors.get(succ_id, []):
                    if link.get("from_id") == aid:
                        link_type = link.get("link_type", "FS")
                        lag = int(link.get("lag", 0))

                        if link_type == "FS":
                            new_es = add_working_days(ef, 1 + lag, self.calendar, self.holidays)
                        elif link_type == "SS":
                            new_es = add_working_days(es, lag, self.calendar, self.holidays)
                        elif link_type == "FF":
                            succ_dur = int(task_dict.get(succ_id, {}).get("duration", 0))
                            new_ef = add_working_days(ef, lag, self.calendar, self.holidays)
                            new_es = subtract_working_days(new_ef, succ_dur - 1, self.calendar, self.holidays)
                        elif link_type == "SF":
                            succ_dur = int(task_dict.get(succ_id, {}).get("duration", 0))
                            new_es = subtract_working_days(es, succ_dur - 1 - lag, self.calendar, self.holidays)
                        else:
                            new_es = add_working_days(ef, 1, self.calendar, self.holidays)

                        if succ_id in early_start:
                            if new_es > early_start[succ_id]:
                                early_start[succ_id] = new_es

        # Recalculer EF
        for aid in topo_order:
            task = task_dict[aid]
            dur = int(task.get("duration", 0))
            es = early_start[aid]
            early_finish[aid] = add_working_days(es, dur - 1, self.calendar, self.holidays) if dur > 0 else es

        # Calculer les marges
        self.results = {}
        for task in tasks:
            aid = task["activity_id"]
            ls = late_start.get(aid, target_date)
            es = early_start.get(aid, project_start)
            total_float = 0
            try:
                total_float = (ls - es).days
            except Exception:
                total_float = 0

            is_critical = total_float <= 0

            self.results[aid] = {
                "activity_id": aid,
                "task_name": task.get("task_name", ""),
                "duration": int(task.get("duration", 0)),
                "early_start": early_start.get(aid),
                "early_finish": early_finish.get(aid),
                "late_start": ls,
                "late_finish": late_finish.get(aid, target_date),
                "total_float": total_float,
                "is_critical": is_critical,
                "cstr_type": "ALAP",
                "cstr_date": target_date,
                # Pour P6 : utiliser les dates ALAP (= late dates)
                "target_start": ls,
                "target_finish": late_finish.get(aid, target_date),
            }

        self.critical_path = [aid for aid, r in self.results.items() if r["is_critical"]]
        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé du rétro-planning."""
        if not self.results:
            return {}

        all_starts = [r["late_start"] for r in self.results.values() if r.get("late_start")]
        all_ends = [r["late_finish"] for r in self.results.values() if r.get("late_finish")]

        return {
            "project_start": min(all_starts) if all_starts else None,
            "project_finish": max(all_ends) if all_ends else None,
            "nb_tasks": len(self.results),
            "nb_critical": len(self.critical_path),
            "critical_path": self.critical_path,
        }
