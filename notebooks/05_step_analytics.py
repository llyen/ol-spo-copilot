# CELL
# 05 - analityka wykonania procedur: czasy krokow, dotrzymanie SLA, blokady, wnioski
# To jest warstwa "lessons learned": pokazuje, ktore kroki procedur systematycznie
# nie miesza sie w czasie normatywnym i jakie blokady powtarzaja sie od lat.
import json
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
DATA = BASE / "datasets"
OUT = DATA / "derived"
OUT.mkdir(exist_ok=True)

exe = pd.read_json(DATA / "fact_step_execution.jsonl", lines=True)
act = pd.read_json(DATA / "fact_activation.jsonl", lines=True)
dec = pd.read_json(DATA / "fact_decision_log.jsonl", lines=True)
steps = pd.read_csv(DATA / "dim_step.csv")
proc = pd.read_csv(DATA / "dim_procedure.csv")

# CELL
# Dotrzymanie czasow normatywnych per procedura
by_proc = exe.groupby("procedure_code").agg(
    uruchomienia=("activation_id", "nunique"),
    wykonania_krokow=("execution_id", "count"),
    sla_compliance=("sla_met", "mean"),
    mediana_czasu_min=("elapsed_minutes", "median"),
    blokady=("status", lambda s: int((s == "zablokowany").sum())),
).round(3).sort_values("sla_compliance")
by_proc["sla_compliance_pct"] = (by_proc.sla_compliance * 100).round(1)
by_proc = by_proc.join(proc.set_index("procedure_code")[["procedure_name", "phase"]])
by_proc.to_csv(OUT / "sla_by_procedure.csv")
print(by_proc[["procedure_name", "uruchomienia", "sla_compliance_pct", "blokady"]].to_string())

# CELL
# Kroki, ktore najczesciej przekraczaja czas normatywny (min. 25 wykonan)
by_step = exe.groupby(["procedure_code", "step_no", "step_title", "role_code"]).agg(
    wykonania=("execution_id", "count"),
    sla_compliance=("sla_met", "mean"),
    mediana_czasu_min=("elapsed_minutes", "median"),
    sla_minutes=("sla_minutes", "first"),
).reset_index()
by_step["przekroczenie_pct"] = ((1 - by_step.sla_compliance) * 100).round(1)
by_step["stosunek_do_normy"] = (by_step.mediana_czasu_min / by_step.sla_minutes).round(2)
worst = by_step[by_step.wykonania >= 25].sort_values("przekroczenie_pct", ascending=False)
worst.to_csv(OUT / "sla_worst_steps.csv", index=False)
print(worst.head(10)[["procedure_code", "step_no", "step_title", "wykonania", "przekroczenie_pct", "stosunek_do_normy"]].to_string(index=False))

# CELL
# Powtarzajace sie blokady - wniosek "ta sama przyczyna od lat"
blocked = exe[exe.blocker_reason != ""].copy()
blocked["rok"] = pd.to_datetime(blocked.started_at, utc=True).dt.year
blockers = blocked.groupby("blocker_reason").agg(
    wystapienia=("execution_id", "count"),
    procedury=("procedure_code", "nunique"),
    lata=("rok", "nunique"),
    pierwsze=("rok", "min"),
    ostatnie=("rok", "max"),
).sort_values("wystapienia", ascending=False)
blockers.to_csv(OUT / "recurring_blockers.csv")
print(blockers.to_string())

# CELL
# Czas do wykonania pierwszego kroku krytycznego (kluczowy wskaznik reakcji)
crit = exe[exe.is_critical == 1].sort_values(["activation_id", "step_no"]).groupby("activation_id").first()
crit = crit.join(act.set_index("activation_id")[["event_name", "level", "started_at"]], rsuffix="_act")
crit["time_to_first_critical_min"] = (
    pd.to_datetime(crit.completed_at, utc=True) - pd.to_datetime(crit.started_at_act, utc=True)
).dt.total_seconds() / 60
ttfc = crit.groupby("procedure_code").time_to_first_critical_min.median().round(1).sort_values(ascending=False)
ttfc.to_csv(OUT / "time_to_first_critical_step.csv")
print(ttfc.to_string())

# CELL
flood = act[act.event_name == "POWODZ WRZESIEN"]
hist = act[act.event_name != "POWODZ WRZESIEN"]
summary = {
    "activations_total": int(len(act)),
    "activations_flood_scenario": int(len(flood)),
    "step_executions": int(len(exe)),
    "decisions_logged": int(len(dec)),
    "overall_sla_compliance_pct": round(float(exe.sla_met.mean()) * 100, 1),
    "flood_sla_compliance_pct": round(
        float(exe[exe.event_name == "POWODZ WRZESIEN"].sla_met.mean()) * 100, 1),
    "history_sla_compliance_pct": round(
        float(exe[exe.event_name != "POWODZ WRZESIEN"].sla_met.mean()) * 100, 1),
    "worst_procedure": str(by_proc.index[0]),
    "worst_procedure_sla_pct": float(by_proc.iloc[0].sla_compliance_pct),
    "worst_step": f"{worst.iloc[0].procedure_code} krok {int(worst.iloc[0].step_no)}",
    "worst_step_title": str(worst.iloc[0].step_title),
    "worst_step_breach_pct": float(worst.iloc[0].przekroczenie_pct),
    "top_blocker": str(blockers.index[0]),
    "top_blocker_count": int(blockers.iloc[0].wystapienia),
    "top_blocker_years": int(blockers.iloc[0].lata),
    "median_time_to_first_critical_min": round(float(crit.time_to_first_critical_min.median()), 1),
    "median_activation_duration_h": round(float(act.duration_minutes.median()) / 60, 1),
    "classified_decisions_pct": round(float((dec.classification != "jawne").mean()) * 100, 1),
    "history_activations": int(len(hist)),
}
(OUT / "step_analytics_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=True, indent=2))
