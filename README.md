# PlanHub v1.0
**Du DQE à Primavera P6 en quelques clics**

Logiciel professionnel de gestion de planning BTP pour projets d'infrastructure en Afrique francophone.

---

## 📋 Modules

| Module | Description |
|--------|-------------|
| 📊 Tableau de bord | Vue d'ensemble du projet actif |
| 📝 Mon DQE | Saisie et édition du Détail Quantitatif Estimatif |
| 🏗️ Type de projet | Sélection parmi 12 catégories de projets |
| 📚 Bibliothèque | Tâches types avec relations logiques |
| 👷 Ressources | Gestion MO et matériaux |
| ⚙️ Générer XER | Rétro-planning ALAP + export Primavera P6 |
| 📋 Rapport | Import XER + vues P6 + exports Excel/PDF |
| 🗂️ Mes projets | Gestion des projets et historique |

---

## 🚀 Installation rapide

### Prérequis
- **Python 3.10+** : https://www.python.org/downloads/
- **pip** (inclus avec Python)

### Lancement en mode développement
```bat
install_deps.bat
```

### Compilation en .exe Windows
```bat
build.bat
```
L'exécutable sera généré dans `dist\PlanHub.exe`.

---

## 📦 Dépendances Python
```
customtkinter>=5.2.0
Pillow>=10.0.0
matplotlib>=3.7.0
pandas>=2.0.0
openpyxl>=3.1.0
reportlab>=4.0.0
```

---

## 🔑 Système de licence
- Clé DÉMO : `PLANHUB-DEMO-2024-XXXX` (valide 30 jours)
- Remplacer `license_validator.py` par votre propre système de validation
- Le fichier de licence est stocké dans `planhub.lic` (JSON)

---

## 📁 Structure du projet
```
PlanHub/
├── main.py                     ← Point d'entrée (licence + lancement)
├── license_validator.py        ← Système de licence
├── requirements.txt
├── build.bat                   ← Script compilation Windows
├── install_deps.bat            ← Installation + lancement dev
├── ui/
│   ├── main_window.py          ← Fenêtre principale
│   ├── sidebar.py              ← Navigation latérale
│   ├── splash.py               ← Écran de démarrage
│   └── pages/
│       ├── dashboard.py        ← Tableau de bord
│       ├── dqe_editor.py       ← Éditeur DQE
│       ├── project_type.py     ← Sélection type projet
│       ├── library.py          ← Bibliothèque tâches
│       ├── resources.py        ← Gestion ressources
│       ├── generate_xer.py     ← Génération XER
│       ├── report.py           ← Rapport / Import XER
│       └── projects.py         ← Mes projets
├── core/
│   ├── xer_generator.py        ← Générateur XER (tables P6)
│   ├── xer_parser.py           ← Parseur XER
│   ├── retro_planning.py       ← Calcul ALAP
│   ├── library_engine.py       ← Bibliothèques par type
│   ├── resource_engine.py      ← Gestion ressources
│   └── report_engine.py        ← Export Excel/HTML/PDF
├── data/
│   ├── libraries/              ← 12 bibliothèques JSON
│   └── resources/
│       └── resources_default.json
└── assets/                     ← Logo et icônes
```

---

## 🔄 Correspondances DQE → Primavera P6

| Champ DQE | Table P6 | Champ P6 |
|-----------|----------|----------|
| N° tâche | TASK | activity_id |
| Désignation | TASK | task_name |
| WBS / Lot | PROJWBS | wbs_short_name |
| Durée (jours) | TASK | orig_dur |
| Montant HT | TASK | target_cost |
| Contrainte ALAP | TASK | cstr_type = CS_ALAP |
| Prédécesseur | TASKPRED | pred_task_id |
| Type lien | TASKPRED | pred_type (PR_FS/SS/FF/SF) |
| Lag | TASKPRED | lag_hr_cnt |
| Ressource MO | RSRC | rsrc_type = RT_Labor |
| Affectation | TASKRSRC | task_id + rsrc_id |

---

## 📞 Support
Logiciel développé pour les planificateurs BTP en Afrique francophone.
