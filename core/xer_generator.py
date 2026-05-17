"""
core/xer_generator.py — PlanHub v1.0
Génération de fichiers XER compatibles Primavera P6
Adapté depuis la logique de DQE_to_XER.html
"""

import os
import uuid
import datetime
from typing import List, Dict, Any, Optional


# ── Types de liens P6
LINK_TYPES = {
    "FS": "PR_FS",
    "SS": "PR_SS",
    "FF": "PR_FF",
    "SF": "PR_SF",
}

# ── Types de contraintes P6
CONSTRAINT_TYPES = {
    "ALAP": "CS_ALAP",
    "ASAP": "CS_ASAP",
    "FIXED": "CS_MSO",
    "NONE": "",
}

# ── Calendriers P6
CALENDAR_IDS = {
    "5j": "1",
    "6j": "2",
}


def guid22() -> str:
    """Génère un GUID 22 caractères style P6."""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    raw = uuid.uuid4().bytes
    result = ""
    for b in raw[:16]:
        result += chars[b % 64]
    return result[:22]


def format_date_p6(d: Optional[datetime.date]) -> str:
    """Formate une date pour P6 : YYYY-MM-DD HH:MM"""
    if d is None:
        return ""
    if isinstance(d, datetime.datetime):
        return d.strftime("%Y-%m-%d %H:%M")
    return d.strftime("%Y-%m-%d") + " 08:00"


def parse_date_p6(s: str) -> Optional[datetime.date]:
    """Parse une date P6 : YYYY-MM-DD HH:MM"""
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


class XERGenerator:
    """Génère un fichier XER depuis les données PlanHub."""

    def __init__(self):
        self._wbs_counter = 50000
        self._task_counter = 60000
        self._taskrsrc_counter = 70000
        self._rsrc_counter = 80000

    def generate(
        self,
        project: Dict[str, Any],
        tasks: List[Dict[str, Any]],
        resources: List[Dict[str, Any]],
        task_resources: List[Dict[str, Any]],
        calendar: str = "5j",
        p6_version: str = "15.1",
    ) -> str:
        """
        Génère le contenu complet d'un fichier XER.

        Args:
            project: Infos projet {proj_id, name, start_date, currency, wbs_list}
            tasks: Liste des tâches
            resources: Liste des ressources
            task_resources: Affectations tâches-ressources
            calendar: '5j' ou '6j'
            p6_version: Version P6 cible

        Returns:
            Contenu XER encodé en latin-1
        """
        self._wbs_counter = 50000
        self._task_counter = 60000
        self._taskrsrc_counter = 70000
        self._rsrc_counter = 80000

        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        proj_id = project.get("proj_id", "PROJ001")
        clndr_id = CALENDAR_IDS.get(calendar, "1")
        obs_id = project.get("obs_id", "1")

        lines = []

        # ── ERMHDR
        lines.append(f"ERMHDR\t{p6_version}\t{today[:10]}\tProject\tADMIN\tSYSTEM\tPlanHub\tProject Management\t")

        # ── CURRTYPE
        currency = project.get("currency", "FCFA")
        lines += self._build_currtype(currency)

        # ── OBS
        lines += self._build_obs(obs_id)

        # ── PROJECT
        lines += self._build_project(project, clndr_id, obs_id)

        # ── CALENDAR
        lines += self._build_calendar(clndr_id, calendar, project.get("holidays", []))

        # ── SCHEDOPTIONS
        lines += self._build_schedoptions(proj_id)

        # ── PROJWBS
        wbs_map = {}  # wbs_code → wbs_id
        lines += self._build_projwbs(project, tasks, wbs_map, proj_id, obs_id)

        # ── TASK
        task_id_map = {}  # activity_id → task_id
        lines += self._build_tasks(tasks, proj_id, clndr_id, wbs_map, task_id_map)

        # ── TASKPRED
        lines += self._build_taskpred(tasks, task_id_map, proj_id)

        # ── RSRC
        rsrc_id_map = {}  # rsrc_code → rsrc_id
        if resources:
            lines += self._build_rsrc(resources, rsrc_id_map)

        # ── TASKRSRC
        if task_resources:
            lines += self._build_taskrsrc(task_resources, task_id_map, rsrc_id_map, proj_id)

        lines.append("%E")
        return "\n".join(lines) + "\n"

    # ─────────────────────────────────────────────────────────────────
    # CURRTYPE
    # ─────────────────────────────────────────────────────────────────
    def _build_currtype(self, currency: str) -> List[str]:
        symbols = {
            "FCFA": "FCFA", "XOF": "XOF", "USD": "$", "EUR": "€"
        }
        sym = symbols.get(currency, currency)
        fields = "curr_id\tbase_flag\tcurr_type\tcurr_short_name\tsymbol\tdecimal_digit_cnt\tthousands_separator\tdecimal_separator\tpos_curr_fmt_type\tneg_curr_fmt_type\texchange_rate"
        lines = ["%T\tCURRTYPE", f"%F\t{fields}"]
        lines.append(f"%R\t1\tY\t{currency}\t{currency}\t{sym}\t0\t,\t.\tCF#\t(CF#)\t1.0000000")
        return lines

    # ─────────────────────────────────────────────────────────────────
    # OBS
    # ─────────────────────────────────────────────────────────────────
    def _build_obs(self, obs_id: str) -> List[str]:
        fields = "obs_id\tparent_obs_id\tobs_name\tobsvalue"
        lines = ["%T\tOBS", f"%F\t{fields}"]
        lines.append(f"%R\t{obs_id}\t\tEntreprise\t")
        return lines

    # ─────────────────────────────────────────────────────────────────
    # PROJECT
    # ─────────────────────────────────────────────────────────────────
    def _build_project(self, project: Dict, clndr_id: str, obs_id: str) -> List[str]:
        proj_id = project.get("proj_id", "PROJ001")
        proj_name = project.get("name", "Projet PlanHub")
        start = format_date_p6(project.get("start_date"))
        total_cost = sum(t.get("target_cost", 0) for t in project.get("tasks", []))

        fields = (
            "proj_id\tobs_id\toriginator_id\tbase_type_id\tcreate_date\tlast_recalc_date\tplan_start_date\t"
            "plan_end_date\tscd_end_date\tadd_act_remain_flag\talloc_res_flag\tbase_proj_id\tpriority\t"
            "sum_base_proj_id\tout_early_start_flag\tout_early_finish_flag\tout_late_start_flag\t"
            "out_late_finish_flag\tout_duration_flag\tout_unit_flag\tout_cost_flag\tcost_qty_recalc_flag\t"
            "batch_sum_flag\tname_sep_char\tded_pct_of_budget_amt\tproject_flag\tstatus_code\tft_id\t"
            "guid\tclndr_id\tsum_assign_level\tcreate_user\tcreate_date2\tlast_chng_date\tcurr_id\t"
            "sum_base_clndr_id\tex_list_type_flag\tex_add_act_remain_flag\tex_add_actual_flag\t"
            "ex_base_type_id\tex_rsrc_id\tex_fin_sched_flag\tex_define_date_flag\tex_rsrc_percent_flag\t"
            "risk_level\ttask_code_base\ttask_code_step\ttask_code_prefix\ttask_code_prefix_flag\t"
            "ded_pct_of_budget_flag"
        )
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = ["%T\tPROJECT", f"%F\t{fields}"]
        values = [
            proj_id, obs_id, "", "BT_OriginalPlan", today, today,
            start, "", "", "N", "N", "", "PT_Normal",
            "", "N", "N", "N", "N", "N", "N", "N", "N",
            "N", "-", "100", "Y", "WS_Open", "",
            guid22(), clndr_id, "RS_Level", "ADMIN", today, today, "1",
            clndr_id, "N", "N", "N", "BT_OriginalPlan", "", "N", "N", "N",
            "RS_Level", "1000", "10", "A", "Y", "N"
        ]
        lines.append("%R\t" + "\t".join(str(v) for v in values))
        return lines

    # ─────────────────────────────────────────────────────────────────
    # CALENDAR
    # ─────────────────────────────────────────────────────────────────
    def _build_calendar(self, clndr_id: str, calendar: str, holidays: List = None) -> List[str]:
        days_per_week = 6 if calendar == "6j" else 5
        name = f"Calendrier {days_per_week}j/semaine"

        # Jours de travail : Lun-Ven (5j) ou Lun-Sam (6j)
        work_days = "(0|1|1|1|1|1|0)" if days_per_week == 5 else "(0|1|1|1|1|1|1)"

        fields = "clndr_id\tdefault_flag\tclndr_name\tclndr_type\tday_hr_cnt\tclndr_data"
        lines = ["%T\tCALENDAR", f"%F\t{fields}"]

        clndr_data = f"(0||){work_days}(8.00|08:00|17:00|)"
        lines.append(f"%R\t{clndr_id}\tY\t{name}\tCA_Base\t8.00\t{clndr_data}")

        # Calendrier 2 si 6j
        if calendar == "6j":
            pass  # déjà inclus

        return lines

    # ─────────────────────────────────────────────────────────────────
    # SCHEDOPTIONS
    # ─────────────────────────────────────────────────────────────────
    def _build_schedoptions(self, proj_id: str) -> List[str]:
        fields = (
            "schedoptions_id\tproj_id\tsched_type\tsched_float_type\tsched_calendar_on_relationship_lag\t"
            "sched_open_critical_flag\tsched_lag_early_start_flag\tsched_retained_logic\t"
            "sched_setplantoforecast\tsched_use_expect_end_flag\tsched_progress_override\t"
            "sched_outer_depend_type\tsched_use_project_end_date_for_late_flag\t"
            "sched_critical_float_thr_cnt\tsched_log_to_file\tsched_data_date"
        )
        lines = ["%T\tSCHEDOPTIONS", f"%F\t{fields}"]
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        values = [
            "1", proj_id, "TS_CPM", "SF_TotalFloat", "N",
            "N", "Y", "Y", "N", "N", "N",
            "SD_ZeroFreeFloat", "N", "0", "N", today
        ]
        lines.append("%R\t" + "\t".join(str(v) for v in values))
        return lines

    # ─────────────────────────────────────────────────────────────────
    # PROJWBS
    # ─────────────────────────────────────────────────────────────────
    def _build_projwbs(
        self,
        project: Dict,
        tasks: List[Dict],
        wbs_map: Dict,
        proj_id: str,
        obs_id: str,
    ) -> List[str]:
        fields = (
            "wbs_id\tproj_id\tobs_id\tseq_num\test_wt\tproj_node_flag\tsum_data_flag\tstatus_code\t"
            "wbs_short_name\twbs_name\tphase_id\tparent_wbs_id\tev_user_pct\tev_etc_user_value\t"
            "orig_cost\tindep_remain_total_cost\tann_dscnt_rate_pct\tdscnt_period_type\t"
            "indep_remain_work_qty\tanticip_start_date\tanticip_end_date\tev_compute_type\t"
            "ev_etc_compute_type\tguid\ttmpl_guid\tplan_open_state"
        )
        lines = ["%T\tPROJWBS", f"%F\t{fields}"]

        # Nœud racine
        root_id = self._wbs_counter
        wbs_map["ROOT"] = root_id

        proj_name = project.get("name", "Projet")
        root_values = [
            root_id, proj_id, obs_id, 0, 1, "Y", "N", "WS_Open",
            proj_id, proj_name, "", "",
            6, "0.88", "0.0000", "0.0000",
            "", "", "", "", "",
            "EC_Cmp_pct", "EE_Rem_hr",
            guid22(), "", ""
        ]
        lines.append("%R\t" + "\t".join(str(v) for v in root_values))

        # Construire arbre WBS depuis les tâches
        wbs_codes = set()
        for task in tasks:
            wbs = task.get("wbs_code", "")
            if wbs:
                # Ajouter tous les ancêtres
                parts = wbs.split(".")
                for i in range(len(parts)):
                    wbs_codes.add(".".join(parts[: i + 1]))

        # Trier pour garantir l'ordre hiérarchique
        sorted_wbs = sorted(wbs_codes, key=lambda x: (x.count("."), x))

        seq = 100
        for wbs_code in sorted_wbs:
            self._wbs_counter += 1
            wbs_id = self._wbs_counter
            wbs_map[wbs_code] = wbs_id

            # Parent
            parent_code = ".".join(wbs_code.split(".")[:-1]) if "." in wbs_code else "ROOT"
            parent_id = wbs_map.get(parent_code, root_id)

            short = wbs_code.split(".")[-1]
            # Chercher le nom dans les tâches récapitulatives
            name = wbs_code
            for task in tasks:
                if task.get("wbs_code") == wbs_code and task.get("task_type") == "TT_WBS":
                    name = task.get("task_name", wbs_code)
                    break

            values = [
                wbs_id, proj_id, obs_id, seq, 1, "N", "N", "WS_Open",
                short, name, "", parent_id,
                6, "0.88", "0.0000", "0.0000",
                "", "", "", "", "",
                "EC_Cmp_pct", "EE_Rem_hr",
                guid22(), "", ""
            ]
            lines.append("%R\t" + "\t".join(str(v) for v in values))
            seq += 100

        return lines

    # ─────────────────────────────────────────────────────────────────
    # TASK
    # ─────────────────────────────────────────────────────────────────
    def _build_tasks(
        self,
        tasks: List[Dict],
        proj_id: str,
        clndr_id: str,
        wbs_map: Dict,
        task_id_map: Dict,
    ) -> List[str]:
        fields = (
            "task_id\tproj_id\twbs_id\tclndr_id\tphys_complete_pct\trev_fdbk_flag\test_wt\t"
            "lock_plan_flag\tauto_compute_act_flag\tcomplete_pct_type\ttask_type\tduration_type\t"
            "status_code\ttask_code\ttask_name\trsrc_id\ttotal_float_hr_cnt\tfree_float_hr_cnt\t"
            "remain_drtn_hr_cnt\tact_work_qty\tremain_work_qty\ttarget_work_qty\ttarget_drtn_hr_cnt\t"
            "target_equip_qty\tact_equip_qty\tremain_equip_qty\tcstr_date\tact_start_date\t"
            "act_end_date\tlate_start_date\tlate_end_date\texpect_end_date\tearly_start_date\t"
            "early_end_date\trestart_date\treend_date\ttarget_start_date\ttarget_end_date\t"
            "rem_late_start_date\trem_late_end_date\tcstr_type\tpriority_type\tsuspend_date\t"
            "resume_date\tfloat_path\tfloat_path_order\tguid\ttmpl_guid\tcstr_date2\tcstr_type2\t"
            "driving_path_flag\tact_this_per_work_qty\tact_this_per_equip_qty\t"
            "external_early_start_date\texternal_late_end_date\tcreate_date\tupdate_date\t"
            "create_user\tupdate_user\tlocation_id"
        )
        lines = ["%T\tTASK", f"%F\t{fields}"]
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        for task in tasks:
            # Ignorer les tâches récapitulatives WBS (elles sont dans PROJWBS)
            if task.get("task_type") == "TT_WBS":
                continue

            self._task_counter += 1
            task_id = self._task_counter
            activity_id = task.get("activity_id", f"A{task_id}")
            task_id_map[activity_id] = task_id

            wbs_code = task.get("wbs_code", "")
            wbs_id = wbs_map.get(wbs_code, wbs_map.get("ROOT", 50000))

            dur_days = task.get("duration", 0)
            dur_hours = int(dur_days) * 8

            start_str = format_date_p6(task.get("target_start_date"))
            end_str = format_date_p6(task.get("target_end_date"))
            cstr_date = format_date_p6(task.get("cstr_date"))

            task_type = task.get("task_type", "TT_Task")
            if task.get("is_milestone"):
                task_type = "TT_Mile"

            cstr_raw = task.get("cstr_type", "")
            cstr_type = CONSTRAINT_TYPES.get(cstr_raw, "")

            target_cost = task.get("target_cost", 0)

            values = [
                task_id, proj_id, wbs_id, clndr_id,
                0, "N", 1, "N", "N",
                "CP_Drtn", task_type, "DT_FixedDrtn", "TK_NotStart",
                activity_id, task.get("task_name", "Tâche"),
                "",  # rsrc_id
                0, 0,  # total_float, free_float
                dur_hours,  # remain_drtn
                0, 0, 0,  # act_work, remain_work, target_work
                dur_hours,  # target_drtn
                0, 0, 0,  # target_equip, act_equip, remain_equip
                cstr_date,  # cstr_date
                "", "",  # act_start, act_end
                start_str, end_str,  # late_start, late_end
                end_str,  # expect_end
                start_str, end_str,  # early_start, early_end
                start_str, end_str,  # restart, reend
                start_str, end_str,  # target_start, target_end
                start_str, end_str,  # rem_late_start, rem_late_end
                cstr_type,  # cstr_type
                "PT_Normal",  # priority
                "", "",  # suspend, resume
                "", "",  # float_path, float_path_order
                guid22(), "", "", "",  # guid, tmpl_guid, cstr_date2, cstr_type2
                "Y",  # driving_path_flag
                0, 0,  # act_this_per_work, act_this_per_equip
                "", "",  # external_early, external_late
                today, today,  # create_date, update_date
                "ADMIN", "ADMIN",  # create_user, update_user
                ""  # location_id
            ]
            lines.append("%R\t" + "\t".join(str(v) for v in values))

        return lines

    # ─────────────────────────────────────────────────────────────────
    # TASKPRED
    # ─────────────────────────────────────────────────────────────────
    def _build_taskpred(
        self,
        tasks: List[Dict],
        task_id_map: Dict,
        proj_id: str,
    ) -> List[str]:
        fields = (
            "taskpred_id\ttask_id\tproj_id\tpred_task_id\tpred_proj_id\t"
            "pred_type\tlag_hr_cnt\tfloat_path\tanom_type\tanom_date\tcomment"
        )
        lines = ["%T\tTASKPRED", f"%F\t{fields}"]
        pred_id = 90000

        for task in tasks:
            activity_id = task.get("activity_id", "")
            task_id = task_id_map.get(activity_id)
            if not task_id:
                continue

            predecessors = task.get("predecessors", [])
            for pred in predecessors:
                pred_act_id = pred.get("pred_id", "")
                pred_task_id = task_id_map.get(pred_act_id)
                if not pred_task_id:
                    continue

                link_type = LINK_TYPES.get(pred.get("link_type", "FS"), "PR_FS")
                lag_days = pred.get("lag", 0)
                lag_hours = int(lag_days) * 8

                pred_id += 1
                values = [
                    pred_id, task_id, proj_id,
                    pred_task_id, proj_id,
                    link_type, lag_hours,
                    "", "", "", ""
                ]
                lines.append("%R\t" + "\t".join(str(v) for v in values))

        return lines

    # ─────────────────────────────────────────────────────────────────
    # RSRC
    # ─────────────────────────────────────────────────────────────────
    def _build_rsrc(self, resources: List[Dict], rsrc_id_map: Dict) -> List[str]:
        fields = (
            "rsrc_id\tparent_rsrc_id\tclndr_id\trsrc_seq_num\trsrc_name\trsrc_short_name\t"
            "pobs_id\tcost_qty_type\trsrc_type\tloc_flag\trsrc_notes\tact_this_per_qty\t"
            "def_qty_per_hr\tcost_per_qty\trsrc_id2\tadd_act_remain_flag\tadj_pct_flag\t"
            "def_cost_qty_link_flag\trsrc_notes2\trsrc_notes3\trsrc_notes4\t"
            "unit_id\tguid\tcreate_date\tupdate_date\tcreate_user\tupdate_user"
        )
        lines = ["%T\tRSRC", f"%F\t{fields}"]
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        for res in resources:
            self._rsrc_counter += 1
            rsrc_id = self._rsrc_counter
            rsrc_id_map[res.get("code", "")] = rsrc_id

            rsrc_type = "RT_Labor" if res.get("type", "LABOR") == "LABOR" else "RT_Material"
            cost_qty = res.get("cost_per_unit", 0)

            values = [
                rsrc_id, "", "1", rsrc_id,
                res.get("name", "Ressource"),
                res.get("code", f"RES{rsrc_id}"),
                "", "CostUnit_Qty", rsrc_type, "N", "",
                0, "1.0000", f"{cost_qty:.4f}",
                "", "N", "N", "Y",
                "", "", "",
                res.get("unit", "H"),
                guid22(), today, today, "ADMIN", "ADMIN"
            ]
            lines.append("%R\t" + "\t".join(str(v) for v in values))

        return lines

    # ─────────────────────────────────────────────────────────────────
    # TASKRSRC
    # ─────────────────────────────────────────────────────────────────
    def _build_taskrsrc(
        self,
        task_resources: List[Dict],
        task_id_map: Dict,
        rsrc_id_map: Dict,
        proj_id: str,
    ) -> List[str]:
        fields = (
            "taskrsrc_id\ttask_id\tproj_id\tcost_qty_link_flag\trole_id\tacct_id\trsrc_id\t"
            "pobs_id\tskill_level\tremain_qty\ttarget_qty\tremain_qty_per_hr\t"
            "target_lag_drtn_hr_cnt\ttarget_qty_per_hr\tact_ot_qty\tact_reg_qty\t"
            "relag_drtn_hr_cnt\tot_factor\tcost_per_qty\ttarget_cost\tact_reg_cost\t"
            "act_ot_cost\tremain_cost\tact_start_date\tact_end_date\trestart_date\t"
            "reend_date\ttarget_start_date\ttarget_end_date\trem_late_start_date\t"
            "rem_late_end_date\trollup_dates_flag\ttarget_crv\tremain_crv\tactual_crv\t"
            "ts_pend_act_end_flag\tguid\trate_type\tact_this_per_cost\tact_this_per_qty\t"
            "curv_id\trsrc_type\tcost_per_qty_source_type\tcreate_user\tcreate_date\t"
            "has_rsrchours\ttaskrsrc_sum_id"
        )
        lines = ["%T\tTASKRSRC", f"%F\t{fields}"]
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        for tr in task_resources:
            task_id = task_id_map.get(tr.get("activity_id", ""))
            rsrc_id = rsrc_id_map.get(tr.get("rsrc_code", ""))
            if not task_id or not rsrc_id:
                continue

            self._taskrsrc_counter += 1
            target_cost = tr.get("target_cost", 0)
            ts = tr.get("target_start", "")
            te = tr.get("target_end", "")

            values = [
                self._taskrsrc_counter, task_id, proj_id,
                "Y", "", "", rsrc_id, "", "",
                0, 0, 0, 0, 0, 0, 0, 0, "",
                "1.0000", f"{target_cost:.4f}",
                "0.0000", "0.0000", f"{target_cost:.4f}",
                "", "", ts, te, ts, te, ts, te,
                "Y", "", "", "",
                "N", guid22(), "COST_PER_QTY",
                "0.0000", 0, "",
                "RT_Labor", "ST_Rsrc",
                "ADMIN", today, "", ""
            ]
            lines.append("%R\t" + "\t".join(str(v) for v in values))

        return lines


def encode_xer(content: str) -> bytes:
    """Encode le contenu XER en latin-1 (standard P6)."""
    return content.encode("latin-1", errors="replace")
