"""Tworzy Real-Time Dashboard OL_SPO_Dashboard nad baza KQL Eventhouse.

Zrodlo zapytan: kql/03_dashboard_queries.kql. Uklad: trzy strony
(przebieg operacyjny, waskie gardla, asystent i scenariusz osiowy).
"""
import argparse
import base64
import json
import subprocess
import uuid
from pathlib import Path

import requests

API = "https://api.fabric.microsoft.com/v1"
BASE = Path(__file__).resolve().parent.parent

# --- kafelki ------------------------------------------------------------------
# (id, strona, tytul, typ wizualizacji, x, y, szerokosc, wysokosc, zapytanie)
TILES = [
    ("t01", "p1", "Uruchomione procedury", "stat", 0, 0, 6, 4, """
activation
| where event_time between (_startTime .. _endTime)
| summarize ["Uruchomione procedury"] = dcount(activation_id)
"""),
    ("t02", "p1", "Dotrzymanie SLA %", "stat", 6, 0, 6, 4, """
step_execution
| where event_time between (_startTime .. _endTime)
| summarize ["Dotrzymanie SLA %"] = round(100.0 * countif(sla_met) / count(), 1)
"""),
    ("t03", "p1", "Kroki zablokowane", "stat", 12, 0, 6, 4, """
step_execution
| where event_time between (_startTime .. _endTime)
| where status == "zablokowany"
| summarize ["Kroki zablokowane"] = count()
"""),
    ("t04", "p1", "Czas do 1. kroku krytycznego (min)", "stat", 18, 0, 6, 4, """
step_execution
| where event_time between (_startTime .. _endTime)
| where is_critical
| summarize arg_min(step_no, *) by activation_id
| join kind=inner (activation | project activation_id, started_at) on activation_id
| extend ttfc = datetime_diff('minute', completed_at, started_at)
| summarize ["Czas do 1. kroku krytycznego (min)"] = percentile(ttfc, 50)
"""),
    ("t05", "p1", "Postep realizacji krokow w czasie", "timechart", 0, 4, 12, 8, """
step_execution
| where event_time between (_startTime .. _endTime)
| summarize wykonane = countif(status == "wykonany"),
            zablokowane = countif(status == "zablokowany"),
            pominiete = countif(status == "pominiety")
  by bin(event_time, 1d)
"""),
    ("t06", "p1", "Dotrzymanie SLA wg procedury", "bar", 12, 4, 12, 8, """
step_execution
| where event_time between (_startTime .. _endTime)
| summarize wykonania = count(), sla_pct = round(100.0 * countif(sla_met) / count(), 1)
  by procedure_code
| where wykonania >= 10
| order by sla_pct asc
| project procedure_code, sla_pct
"""),
    ("t09", "p1", "Checklista ostatniego uruchomienia", "table", 0, 12, 12, 8, """
let ostatnie = toscalar(
    activation
    | where event_time between (_startTime .. _endTime)
    | top 1 by started_at desc
    | project activation_id);
ActivationProgress(ostatnie)
"""),
    ("t13", "p1", "Uruchomienia wg wojewodztwa", "table", 12, 12, 12, 8, """
activation
| where event_time between (_startTime .. _endTime)
| summarize uruchomienia = count(), sredni_sla = round(avg(sla_compliance_pct), 1)
  by voivodeship_name
| order by uruchomienia desc
"""),
    ("t07", "p2", "Kroki najczesciej przekraczajace norme", "table", 0, 0, 24, 9, """
step_execution
| where event_time between (_startTime .. _endTime)
| summarize wykonania = count(),
            przekroczenia_pct = round(100.0 * countif(not(sla_met)) / count(), 1),
            mediana_min = round(percentile(elapsed_minutes, 50), 1),
            norma_min = any(sla_minutes)
  by procedure_code, step_no, step_title
| where wykonania >= 10
| extend stosunek_do_normy = round(mediana_min / norma_min, 2)
| order by przekroczenia_pct desc
| take 15
"""),
    ("t08", "p2", "Powtarzajace sie blokady", "table", 0, 9, 12, 8, """
step_execution
| where event_time between (_startTime .. _endTime)
| where isnotempty(blocker_reason)
| summarize wystapienia = count(), procedury = dcount(procedure_code),
            pierwsze = min(event_time), ostatnie = max(event_time)
  by blocker_reason
| order by wystapienia desc
"""),
    ("t10", "p2", "Dziennik decyzji", "table", 12, 9, 12, 8, """
decision_log
| where event_time between (_startTime .. _endTime)
| project decided_at, procedure_code, step_no, decision_type, decided_by_name,
          subject, classification
| order by decided_at desc
| take 50
"""),
    ("t11", "p3", "Zapytania do asystenta - wolumen i trafnosc", "timechart", 0, 0, 12, 8, """
assistant_query
| where event_time between (_startTime .. _endTime)
| summarize pytania = count(), trafnosc_pct = round(100.0 * countif(is_correct) / count(), 1)
  by bin(event_time, 1d)
"""),
    ("t12", "p3", "Najczestsze pytania oficerow", "table", 12, 0, 12, 8, """
assistant_query
| where event_time between (_startTime .. _endTime)
| summarize pytania = count(), trafnosc = round(avg(toreal(is_correct)) * 100, 1),
            mediana_ms = percentile(latency_ms, 50)
  by question, top_procedure
| order by pytania desc
| take 20
"""),
    ("t14", "p3", "POWODZ WRZESIEN - przebieg", "table", 0, 8, 24, 9, """
activation
| where event_name == "POWODZ WRZESIEN"
| project started_at, procedure_code, procedure_name, level, voivodeship_name,
          steps_total, steps_blocked, sla_compliance_pct
| order by started_at asc
"""),
]

PAGES = [("p1", "Przebieg operacyjny"),
         ("p2", "Waskie gardla i blokady"),
         ("p3", "Asystent i scenariusz osiowy")]

# stabilne identyfikatory - powtorne uruchomienie nie przestawia kafelkow
NS = uuid.UUID("6f1d6b3e-9d3a-4a1a-9f7c-1c2b3a4d5e6f")


def guid(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def visual_options(visual: str, title: str) -> dict:
    if visual == "stat":
        return {"colorRulesDisabled": False, "colorStyle": "light", "colorRules": [],
                "textSize": "auto"}
    if visual == "table":
        return {"table__enableRenderLinks": True}
    if visual == "bar":
        return {"multipleYAxes": {"base": {"id": "-1", "columns": [], "label": "",
                                           "yAxisMaximumValue": None, "yAxisMinimumValue": None,
                                           "yAxisScale": "linear", "horizontalLines": []},
                                  "additional": [], "showMultiplePanels": False},
                "hideLegend": False, "legendLocation": "bottom",
                "xColumnTitle": "", "xAxisScale": "linear", "verticalLine": ""}
    return {"multipleYAxes": {"base": {"id": "-1", "columns": [], "label": "",
                                       "yAxisMaximumValue": None, "yAxisMinimumValue": None,
                                       "yAxisScale": "linear", "horizontalLines": []},
                              "additional": [], "showMultiplePanels": False},
            "hideLegend": False, "legendLocation": "bottom",
            "xColumnTitle": "", "xAxisScale": "linear", "verticalLine": ""}


def build(cluster_uri: str, database: str, title: str) -> dict:
    ds_id = guid("datasource")
    dashboard = {
        "$schema": "https://raw.githubusercontent.com/Azure/azure-kusto-dashboards/master/schema/52/dashboard.json",
        "id": guid("dashboard"),
        "schema_version": "52",
        "title": title,
        "autoRefresh": {"enabled": True, "defaultDuration": "5m", "minimumDuration": "1m"},
        "baseQueries": [],
        "dataSources": [{"id": ds_id, "name": database, "clusterUri": cluster_uri,
                         "database": database, "kind": "manual-kusto", "scopeId": "kusto"}],
        "pages": [{"id": guid(pid), "name": name} for pid, name in PAGES],
        "parameters": [{
            "kind": "duration", "id": guid("param-time"), "displayName": "Zakres czasu",
            "description": "", "beginVariableName": "_startTime", "endVariableName": "_endTime",
            "defaultValue": {"kind": "dynamic", "count": 5, "unit": "years"},
            "showOnPages": {"kind": "all"},
        }],
        "queries": [],
        "tiles": [],
    }
    for tid, page, tile_title, visual, x, y, w, h, query in TILES:
        qid = guid(f"query-{tid}")
        dashboard["queries"].append({
            "id": qid,
            "dataSource": {"kind": "inline", "dataSourceId": ds_id},
            "text": query.strip(),
            "usedVariables": ["_startTime", "_endTime"],
        })
        dashboard["tiles"].append({
            "id": guid(f"tile-{tid}"),
            "title": tile_title,
            "visualType": visual,
            "pageId": guid(page),
            "layout": {"x": x, "y": y, "width": w, "height": h},
            "queryRef": {"kind": "query", "queryId": qid},
            "visualOptions": visual_options(visual, tile_title),
            "usedParamVariables": ["_startTime", "_endTime"],
        })
    return dashboard


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(BASE / "config.json"))
    args = ap.parse_args()

    cfg = json.load(open(args.config, encoding="utf-8"))["fabric"]
    ws = cfg["workspace_id"]
    name = cfg.get("dashboard", "OL_SPO_Dashboard")
    dashboard = build(cfg["kql_cluster_uri"], cfg["kql_database"], "SPO Copilot - obraz operacyjny")

    tok = subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, shell=True).stdout.strip()
    headers = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

    definition = {"parts": [{
        "path": "RealTimeDashboard.json",
        "payload": base64.b64encode(json.dumps(dashboard, ensure_ascii=False).encode("utf-8")).decode(),
        "payloadType": "InlineBase64",
    }]}

    items = requests.get(f"{API}/workspaces/{ws}/items?type=KQLDashboard", headers=headers).json()["value"]
    existing = next((i for i in items if i["displayName"] == name), None)
    if existing:
        r = requests.post(f"{API}/workspaces/{ws}/kqlDashboards/{existing['id']}/updateDefinition",
                          headers=headers, json={"definition": definition})
    else:
        r = requests.post(f"{API}/workspaces/{ws}/kqlDashboards", headers=headers,
                          json={"displayName": name, "definition": definition})
    print(("update" if existing else "create") + f": {r.status_code} {r.text[:800]}")


if __name__ == "__main__":
    main()
