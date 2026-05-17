"""
core/xer_parser.py — PlanHub v1.0
Parsing des fichiers XER Primavera P6 (encodage latin-1)
"""

import os
import datetime
from typing import Dict, List, Any, Optional, Tuple


class XERParser:
    """Parse un fichier XER et retourne les tables sous forme de dicts."""

    def __init__(self):
        self.header: str = ""
        self.tables: Dict[str, Dict] = {}  # name → {fields:[], records:[]}
        self.table_order: List[str] = []
        self.raw_tables: Dict[str, List[str]] = {}
        self.project_info: Dict[str, Any] = {}
        self.errors: List[str] = []

    def parse_file(self, filepath: str) -> bool:
        """Charge et parse un fichier XER. Retourne True si succès."""
        try:
            with open(filepath, "rb") as f:
                raw = f.read()
            # Essayer latin-1 d'abord, puis UTF-8
            try:
                content = raw.decode("latin-1")
            except Exception:
                content = raw.decode("utf-8", errors="replace")
            return self.parse_string(content)
        except Exception as e:
            self.errors.append(f"Erreur lecture fichier : {e}")
            return False

    def parse_string(self, content: str) -> bool:
        """Parse le contenu XER depuis une chaîne."""
        self.header = ""
        self.tables = {}
        self.table_order = []
        self.raw_tables = {}
        self.errors = []

        lines = content.split("\n")
        current_table = None
        current_fields = None

        for i, line in enumerate(lines):
            line = line.rstrip("\r")

            if i == 0 and line.startswith("ERMHDR"):
                self.header = line
                continue

            if line.startswith("%T\t"):
                current_table = line[3:].strip()
                self.tables[current_table] = {"fields": [], "records": []}
                self.table_order.append(current_table)
                self.raw_tables[current_table] = [line]
                current_fields = None

            elif line.startswith("%F\t") and current_table:
                current_fields = line[3:].split("\t")
                self.tables[current_table]["fields"] = current_fields
                self.raw_tables[current_table].append(line)

            elif line.startswith("%R\t") and current_table and current_fields:
                values = line[3:].split("\t")
                record = {}
                for j, field in enumerate(current_fields):
                    record[field] = values[j] if j < len(values) else ""
                self.tables[current_table]["records"].append(record)
                self.raw_tables[current_table].append(line)

            elif line.strip() == "%E":
                break

        self._extract_project_info()
        return len(self.errors) == 0

    def _extract_project_info(self):
        """Extrait les informations clés du projet."""
        project_records = self.get_records("PROJECT")
        if project_records:
            proj = project_records[0]
            self.project_info = {
                "proj_id": proj.get("proj_id", ""),
                "clndr_id": proj.get("clndr_id", ""),
                "plan_start_date": proj.get("plan_start_date", ""),
                "name": self._get_project_name(proj.get("proj_id", "")),
            }

        # Obs
        obs_records = self.get_records("OBS")
        if obs_records:
            self.project_info["obs_id"] = obs_records[0].get("obs_id", "")

    def _get_project_name(self, proj_id: str) -> str:
        """Récupère le nom du projet depuis PROJWBS."""
        wbs_records = self.get_records("PROJWBS")
        for w in wbs_records:
            if w.get("proj_node_flag") == "Y":
                return w.get("wbs_name", proj_id)
        return proj_id

    # ── Accesseurs
    def get_records(self, table_name: str) -> List[Dict]:
        return self.tables.get(table_name, {}).get("records", [])

    def get_tasks(self) -> List[Dict]:
        return self.get_records("TASK")

    def get_wbs(self) -> List[Dict]:
        return self.get_records("PROJWBS")

    def get_predecessors(self) -> List[Dict]:
        return self.get_records("TASKPRED")

    def get_resources(self) -> List[Dict]:
        return self.get_records("RSRC")

    def get_task_resources(self) -> List[Dict]:
        return self.get_records("TASKRSRC")

    def get_calendars(self) -> List[Dict]:
        return self.get_records("CALENDAR")

    # ── Calculs
    def build_task_dict(self) -> Dict[str, Dict]:
        """Retourne un dict task_id → task."""
        return {t["task_id"]: t for t in self.get_tasks()}

    def build_wbs_dict(self) -> Dict[str, Dict]:
        """Retourne un dict wbs_id → wbs."""
        return {w["wbs_id"]: w for w in self.get_wbs()}

    def get_task_predecessors(self) -> Dict[str, List[Dict]]:
        """Retourne un dict task_id → [predecessors]."""
        result: Dict[str, List] = {}
        for pred in self.get_predecessors():
            tid = pred.get("task_id", "")
            if tid not in result:
                result[tid] = []
            result[tid].append(pred)
        return result

    def calculate_cpm(self) -> Dict[str, Dict]:
        """
        Calcul du chemin critique (CPM) simplifié.
        Retourne un dict task_id → {es, ef, ls, lf, float, is_critical}
        """
        tasks = self.build_task_dict()
        preds = self.get_task_predecessors()
        results = {}

        # Durées en heures → jours
        for tid, task in tasks.items():
            dur = int(task.get("target_drtn_hr_cnt", 0)) / 8
            results[tid] = {
                "es": 0, "ef": dur, "ls": 0, "lf": dur,
                "float": 0, "is_critical": False,
                "dur": dur
            }

        # Forward pass simplifié
        # (implémentation complète dans une future version)
        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du planning."""
        tasks = self.get_tasks()
        wbs = self.get_wbs()
        preds = self.get_predecessors()
        rsrc = self.get_resources()
        task_rsrc = self.get_task_resources()

        total_cost = sum(
            float(t.get("target_cost", 0) or 0) for t in task_rsrc
        )
        total_duration = max(
            (int(t.get("target_drtn_hr_cnt", 0) or 0) for t in tasks), default=0
        ) / 8

        return {
            "nb_tasks": len([t for t in tasks if t.get("task_type") != "TT_WBS"]),
            "nb_wbs": len(wbs),
            "nb_preds": len(preds),
            "nb_resources": len(rsrc),
            "total_cost": total_cost,
            "total_duration": total_duration,
        }

    def get_p6_columns(self, tasks: List[Dict], wbs_dict: Dict, pred_dict: Dict) -> List[Dict]:
        """
        Prépare les données pour affichage style P6.
        Retourne une liste de dicts avec toutes les colonnes P6.
        """
        result = []
        for task in tasks:
            tid = task.get("task_id", "")
            wbs_id = task.get("wbs_id", "")
            wbs = wbs_dict.get(wbs_id, {})
            task_preds = pred_dict.get(tid, [])

            pred_str = ", ".join(
                f"{p.get('pred_task_id','')} {p.get('pred_type','').replace('PR_','')}"
                f"{('+' + str(int(p.get('lag_hr_cnt',0))//8) + 'd') if int(p.get('lag_hr_cnt',0) or 0) > 0 else ''}"
                for p in task_preds
            )

            dur = int(task.get("target_drtn_hr_cnt", 0) or 0) // 8

            row = {
                "activity_id": task.get("task_code", ""),
                "wbs_code": wbs.get("wbs_short_name", ""),
                "wbs_name": wbs.get("wbs_name", ""),
                "activity_name": task.get("task_name", ""),
                "orig_dur": dur,
                "remain_dur": int(task.get("remain_drtn_hr_cnt", 0) or 0) // 8,
                "act_dur": int(task.get("act_drtn_hr_cnt", 0) or 0) // 8,
                "start": task.get("target_start_date", ""),
                "finish": task.get("target_end_date", ""),
                "early_start": task.get("early_start_date", ""),
                "early_finish": task.get("early_end_date", ""),
                "late_start": task.get("late_start_date", ""),
                "late_finish": task.get("late_end_date", ""),
                "total_float": int(task.get("total_float_hr_cnt", 0) or 0) // 8,
                "free_float": int(task.get("free_float_hr_cnt", 0) or 0) // 8,
                "budgeted_cost": task.get("target_cost", "0"),
                "actual_cost": task.get("act_total_cost", "0"),
                "remain_cost": task.get("remain_total_cost", "0"),
                "pct_complete": task.get("phys_complete_pct", "0"),
                "cstr_type": task.get("cstr_type", ""),
                "cstr_date": task.get("cstr_date", ""),
                "status": task.get("status_code", ""),
                "task_type": task.get("task_type", ""),
                "predecessors": pred_str,
                "project_id": task.get("proj_id", ""),
                "_task_id": tid,
                "_is_critical": int(task.get("total_float_hr_cnt", 999) or 999) == 0,
                "_is_milestone": task.get("task_type") == "TT_Mile",
            }
            result.append(row)
        return result
