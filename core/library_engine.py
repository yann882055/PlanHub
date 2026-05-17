"""
core/library_engine.py — PlanHub v1.0
Gestion des bibliothèques de tâches types par type de projet.
"""

import os
import json
from typing import List, Dict, Any, Optional


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "libraries")

PROJECT_TYPES = {
    "barrage_hydro": "Barrage Hydroélectrique",
    "barrage_hydroagricole": "Barrage Hydroagricole",
    "route": "Route",
    "autoroute": "Autoroute",
    "pont": "Pont",
    "metro": "Métro / Transport urbain",
    "batiment": "Bâtiment / Immeuble",
    "centrale_thermique": "Centrale Thermique",
    "centrale_solaire": "Centrale Solaire",
    "assainissement": "Assainissement",
    "eau_potable": "Eau Potable",
    "vrd": "VRD (Voiries et Réseaux Divers)",
}

PROJECT_TYPE_ICONS = {
    "barrage_hydro": "🏗️",
    "barrage_hydroagricole": "🌾",
    "route": "🛣️",
    "autoroute": "🚗",
    "pont": "🌉",
    "metro": "🚇",
    "batiment": "🏢",
    "centrale_thermique": "🔥",
    "centrale_solaire": "☀️",
    "assainissement": "💧",
    "eau_potable": "🚰",
    "vrd": "🔌",
}

PROJECT_TYPE_CATEGORIES = {
    "HYDRAULIQUE": ["barrage_hydro", "barrage_hydroagricole"],
    "TRANSPORT": ["route", "autoroute", "pont", "metro"],
    "BÂTIMENT": ["batiment"],
    "ÉNERGIE": ["centrale_thermique", "centrale_solaire"],
    "RÉSEAUX": ["assainissement", "eau_potable", "vrd"],
}


class LibraryEngine:
    """Moteur de gestion des bibliothèques de tâches types."""

    def __init__(self):
        self._cache: Dict[str, List[Dict]] = {}

    def load(self, project_type: str) -> List[Dict]:
        """Charge la bibliothèque pour un type de projet."""
        if project_type in self._cache:
            return self._cache[project_type]

        filepath = os.path.join(DATA_DIR, f"{project_type}.json")
        if not os.path.exists(filepath):
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            tasks = data.get("tasks", [])
            self._cache[project_type] = tasks
            return tasks
        except Exception:
            return []

    def get_project_types(self) -> Dict[str, str]:
        """Retourne le dictionnaire type_key → nom_affichage."""
        return PROJECT_TYPES.copy()

    def get_categories(self) -> Dict[str, List[str]]:
        """Retourne les catégories de projets."""
        return PROJECT_TYPE_CATEGORIES.copy()

    def apply_to_dqe(
        self,
        selected_task_ids: List[str],
        project_type: str,
        start_activity_number: int = 1000,
        prefix: str = "A",
    ) -> List[Dict]:
        """
        Convertit les tâches sélectionnées de la bibliothèque
        en lignes DQE prêtes à être insérées.

        Returns:
            Liste de dicts compatibles DQE Editor
        """
        all_tasks = self.load(project_type)
        task_dict = {t["id"]: t for t in all_tasks}
        result = []
        act_num = start_activity_number

        for task_id in selected_task_ids:
            task = task_dict.get(task_id)
            if not task:
                continue

            activity_id = f"{prefix}{act_num}"
            dqe_row = {
                "activity_id": activity_id,
                "wbs_code": task.get("wbs", "1.1"),
                "lot": task.get("lot", ""),
                "task_name": task.get("name_fr", task.get("name", "")),
                "task_name_en": task.get("name_en", ""),
                "unit": task.get("unit", "forfait"),
                "quantity": task.get("quantity", 1),
                "unit_price": task.get("unit_price", 0),
                "duration": task.get("duration", 0),
                "calendar": task.get("calendar", "5j"),
                "task_type": task.get("type", "TT_Task"),
                "cstr_type": task.get("constraint", "ASAP"),
                "predecessors": [
                    {
                        "pred_id": pred.get("pred_activity_id", ""),
                        "link_type": pred.get("type", "FS"),
                        "lag": pred.get("lag", 0),
                    }
                    for pred in task.get("predecessors", [])
                ],
                "_library_id": task_id,
            }
            dqe_row["total_ht"] = dqe_row["quantity"] * dqe_row["unit_price"]
            result.append(dqe_row)
            act_num += 10

        return result

    def resolve_predecessor_ids(
        self, tasks: List[Dict], library_tasks: List[Dict]
    ) -> List[Dict]:
        """
        Résout les IDs de prédécesseurs de la bibliothèque
        vers les activity_id du DQE courant.
        """
        lib_id_to_activity = {
            t.get("_library_id", ""): t["activity_id"]
            for t in tasks if "_library_id" in t
        }

        for task in tasks:
            new_preds = []
            for pred in task.get("predecessors", []):
                pred_lib_id = pred.get("pred_id", "")
                if pred_lib_id in lib_id_to_activity:
                    pred["pred_id"] = lib_id_to_activity[pred_lib_id]
                    new_preds.append(pred)
            task["predecessors"] = new_preds

        return tasks
