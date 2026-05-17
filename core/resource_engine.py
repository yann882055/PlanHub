"""
core/resource_engine.py — PlanHub v1.0
Gestion des ressources (Main d'œuvre et Matière).
"""

import os
import json
import copy
from typing import List, Dict, Any, Optional


DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "resources"
)

CURRENCY_RATES = {
    "FCFA": 1.0,
    "XOF": 1.0,
    "EUR": 655.957,
    "USD": 610.0,
}


class ResourceEngine:
    """Gestion des ressources projet."""

    def __init__(self):
        self._default_resources: List[Dict] = []
        self._project_resources: List[Dict] = []
        self._currency: str = "FCFA"

    def load_defaults(self, project_type: str = None) -> List[Dict]:
        """Charge les ressources par défaut."""
        filepath = os.path.join(DATA_DIR, "resources_default.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._default_resources = data.get("resources", [])
            except Exception:
                self._default_resources = self._get_hardcoded_defaults()
        else:
            self._default_resources = self._get_hardcoded_defaults()

        return copy.deepcopy(self._default_resources)

    def _get_hardcoded_defaults(self) -> List[Dict]:
        """Ressources par défaut codées en dur (fallback)."""
        return [
            # ── Main d'œuvre
            {"code": "RES_001", "name": "Chef de projet", "name_en": "Project Manager",
             "type": "LABOR", "unit": "J", "cost_fcfa": 75000},
            {"code": "RES_002", "name": "Chef de chantier", "name_en": "Site Manager",
             "type": "LABOR", "unit": "J", "cost_fcfa": 50000},
            {"code": "RES_003", "name": "Ingénieur génie civil", "name_en": "Civil Engineer",
             "type": "LABOR", "unit": "J", "cost_fcfa": 60000},
            {"code": "RES_004", "name": "Topographe", "name_en": "Surveyor",
             "type": "LABOR", "unit": "J", "cost_fcfa": 40000},
            {"code": "RES_005", "name": "Contrôleur qualité", "name_en": "QC Inspector",
             "type": "LABOR", "unit": "J", "cost_fcfa": 35000},
            {"code": "RES_006", "name": "Maçon", "name_en": "Mason",
             "type": "LABOR", "unit": "J", "cost_fcfa": 15000},
            {"code": "RES_007", "name": "Coffreur", "name_en": "Formwork Carpenter",
             "type": "LABOR", "unit": "J", "cost_fcfa": 12000},
            {"code": "RES_008", "name": "Ferrailleur", "name_en": "Iron Worker",
             "type": "LABOR", "unit": "J", "cost_fcfa": 13000},
            {"code": "RES_009", "name": "Conducteur d'engin (bulldozer)", "name_en": "Bulldozer Operator",
             "type": "LABOR", "unit": "H", "cost_fcfa": 8000},
            {"code": "RES_010", "name": "Conducteur d'engin (pelle)", "name_en": "Excavator Operator",
             "type": "LABOR", "unit": "H", "cost_fcfa": 8000},
            {"code": "RES_011", "name": "Conducteur camion benne", "name_en": "Dump Truck Driver",
             "type": "LABOR", "unit": "H", "cost_fcfa": 5000},
            {"code": "RES_012", "name": "Manœuvre", "name_en": "Laborer",
             "type": "LABOR", "unit": "J", "cost_fcfa": 5000},
            {"code": "RES_013", "name": "Électricien", "name_en": "Electrician",
             "type": "LABOR", "unit": "J", "cost_fcfa": 18000},
            {"code": "RES_014", "name": "Soudeur", "name_en": "Welder",
             "type": "LABOR", "unit": "J", "cost_fcfa": 15000},
            {"code": "RES_015", "name": "Mécanicien", "name_en": "Mechanic",
             "type": "LABOR", "unit": "J", "cost_fcfa": 15000},
            # ── Matière
            {"code": "MAT_001", "name": "Ciment CEM I", "name_en": "Portland Cement CEM I",
             "type": "MATERIAL", "unit": "T", "cost_fcfa": 85000},
            {"code": "MAT_002", "name": "Acier HA", "name_en": "Rebar Steel HA",
             "type": "MATERIAL", "unit": "T", "cost_fcfa": 650000},
            {"code": "MAT_003", "name": "Gravier 0/31,5", "name_en": "Gravel 0/31.5",
             "type": "MATERIAL", "unit": "m³", "cost_fcfa": 12000},
            {"code": "MAT_004", "name": "Sable", "name_en": "Sand",
             "type": "MATERIAL", "unit": "m³", "cost_fcfa": 8000},
            {"code": "MAT_005", "name": "Béton B25", "name_en": "Concrete B25",
             "type": "MATERIAL", "unit": "m³", "cost_fcfa": 120000},
            {"code": "MAT_006", "name": "Coffrages bois", "name_en": "Timber Formwork",
             "type": "MATERIAL", "unit": "m²", "cost_fcfa": 15000},
            {"code": "MAT_007", "name": "Carburant gasoil", "name_en": "Diesel Fuel",
             "type": "MATERIAL", "unit": "L", "cost_fcfa": 800},
            {"code": "MAT_008", "name": "Explosifs", "name_en": "Explosives",
             "type": "MATERIAL", "unit": "kg", "cost_fcfa": 5000},
            {"code": "MAT_009", "name": "Géotextile", "name_en": "Geotextile",
             "type": "MATERIAL", "unit": "m²", "cost_fcfa": 3000},
            {"code": "MAT_010", "name": "Béton bitumineux", "name_en": "Bituminous Concrete",
             "type": "MATERIAL", "unit": "T", "cost_fcfa": 95000},
        ]

    def set_currency(self, currency: str):
        """Définit la devise active et recalcule les coûts."""
        self._currency = currency

    def get_cost_in_currency(self, res: Dict) -> float:
        """Convertit le coût FCFA vers la devise active."""
        fcfa_cost = res.get("cost_fcfa", 0)
        rate = CURRENCY_RATES.get(self._currency, 1.0)
        if self._currency in ("FCFA", "XOF"):
            return fcfa_cost
        else:
            return fcfa_cost / rate

    def format_cost(self, amount: float) -> str:
        """Formate un montant selon la devise active."""
        symbols = {"FCFA": "FCFA", "XOF": "XOF", "EUR": "€", "USD": "$"}
        sym = symbols.get(self._currency, self._currency)
        if amount >= 1_000_000:
            return f"{amount/1_000_000:.2f}M {sym}"
        elif amount >= 1_000:
            return f"{amount/1_000:.0f}K {sym}"
        else:
            return f"{amount:.0f} {sym}"

    def get_labor_resources(self, resources: List[Dict]) -> List[Dict]:
        return [r for r in resources if r.get("type") == "LABOR"]

    def get_material_resources(self, resources: List[Dict]) -> List[Dict]:
        return [r for r in resources if r.get("type") == "MATERIAL"]

    def calculate_total_cost(
        self,
        task_resources: List[Dict],
        resources: List[Dict],
    ) -> float:
        """Calcule le coût total des affectations ressources."""
        res_dict = {r["code"]: r for r in resources}
        total = 0.0
        for tr in task_resources:
            res = res_dict.get(tr.get("rsrc_code", ""))
            if res:
                cost = self.get_cost_in_currency(res)
                qty = tr.get("quantity", 0)
                total += cost * qty
        return total

    def export_for_xer(self, resources: List[Dict], currency: str = "FCFA") -> List[Dict]:
        """Prépare les ressources pour l'export XER."""
        result = []
        for res in resources:
            result.append({
                "code": res.get("code", ""),
                "name": res.get("name", ""),
                "type": res.get("type", "LABOR"),
                "unit": res.get("unit", "J"),
                "cost_per_unit": res.get(f"cost_{currency.lower()}", res.get("cost_fcfa", 0)),
            })
        return result
