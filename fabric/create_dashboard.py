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
    ("t05", "p1", "Postep realizacji kroków w czasie", "timechart", 0, 4, 12, 8, """
step_execution
| where event_time between (_startTime .. _endTime)
| summarize wykonane = countif(status == "wykonany"),
            zablokowane = countif(status == "zablokowany"),
            pominiete = countif(status == "pominięty")
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
    ("t13", "p1", "Uruchomienia wg województwa", "table", 12, 12, 12, 8, """
activation
| where event_time between (_startTime .. _endTime)
| summarize uruchomienia = count(), sredni_sla = round(avg(sla_compliance_pct), 1)
  by voivodeship_name
| order by uruchomienia desc
"""),
    ("t07", "p2", "Kroki najczesciej przekraczające norme", "table", 0, 0, 24, 9, """
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
    ("t08", "p2", "Powtarzajace się blokady", "table", 0, 9, 12, 8, """
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
    """Deterministyczny identyfikator w ksztalcie UUID v4 - portal generuje wlasnie
    takie i niektore walidatory sprawdzaja pole wersji, a uuid5 daje wersje 5."""
    raw = bytearray(uuid.uuid5(NS, name).bytes)
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(raw)))


def visual_options(visual: str, title: str) -> dict:
    if visual == "stat":
        return {"colorRulesDisabled": False, "colorStyle": "light", "colorRules": []}
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


def build(cluster_uri: str, database: str, title: str, database_id: str) -> dict:
    ds_id = guid("datasource")
    dashboard = {
        "id": guid("dashboard"),
        "schema_version": SCHEMA_VERSION,
        "title": title,
        "autoRefresh": {"enabled": True, "defaultInterval": "5m"},
        "baseQueries": [],
        # Fabric wymaga typu "kusto-trident": database i databaseArtifactId to GUID
        # elementu KQLDatabase, nie nazwa. Pole workspace zostaje zerowe - tak
        # wygladaja definicje eksportowane z portalu, ktory sam rozwiazuje kontekst.
        "dataSources": [{"id": ds_id, "name": database, "clusterUri": cluster_uri,
                         "database": database_id, "databaseArtifactId": database_id,
                         "workspace": "00000000-0000-0000-0000-000000000000",
                         "kind": "kusto-trident"}],
        "pages": [{"id": guid(pid), "name": name} for pid, name in PAGES],
        "parameters": [{
            "kind": "duration", "id": guid("param-time"), "displayName": "Zakres czasu",
            "description": "", "beginVariableName": "_startTime", "endVariableName": "_endTime",
            # schemat dopuszcza tylko months/weeks/days/hours/minutes - "years" psuje caly parametr
            "defaultValue": {"kind": "dynamic", "count": 60, "unit": "months"},
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
        })
    return dashboard


SCHEMA_VERSION = 74
SCHEMA_BASE = f"https://dataexplorer.azure.com/static/d/schema/{SCHEMA_VERSION}/"


def validate(dashboard: dict) -> None:
    """Waliduje definicje wzgledem oficjalnego schematu ADX. Fabric przyjmuje
    niepoprawny plik bez bledu i dopiero UI nie otwiera dashboardu, wiec lepiej
    zlapac to lokalnie. Pomijane, gdy brak jsonschema albo dostępu do sieci."""
    try:
        import re
        import urllib.request
        import jsonschema
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except ImportError:
        print("validate: pominieto (brak jsonschema/referencing)")
        return

    res, todo, seen = {}, ["dashboard.json"], set()
    try:
        while todo:
            fname = todo.pop()
            if fname in seen:
                continue
            seen.add(fname)
            raw = urllib.request.urlopen(SCHEMA_BASE + fname, timeout=30).read().decode("utf-8")
            r = Resource(contents=json.loads(raw), specification=DRAFT202012)
            res[fname] = r
            res[f"/static/d/schema/{SCHEMA_VERSION}/{fname}"] = r
            todo += [m.split("/")[-1] for m in re.findall(r'"\$ref"\s*:\s*"([^"#]+)', raw)
                     if m.endswith(".json")]
    except Exception as exc:
        print(f"validate: pominieto ({exc})")
        return

    validator = jsonschema.Draft202012Validator(
        res["dashboard.json"].contents, registry=Registry().with_resources(res.items()))
    errors = list(validator.iter_errors(dashboard))
    for err in errors:
        print("  ! " + "/".join(str(p) for p in err.absolute_path) + ": " + err.message[:300])
    if errors:
        raise SystemExit(f"validate: {len(errors)} bledow schematu - przerwano")
    print("validate: OK")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(BASE / "config.json"))
    ap.add_argument("--skip-validate", action="store_true")
    args = ap.parse_args()

    cfg = json.load(open(args.config, encoding="utf-8"))["fabric"]
    ws = cfg["workspace_id"]
    name = cfg.get("dashboard", "OL_SPO_Dashboard")

    tok = subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, shell=True).stdout.strip()
    headers = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

    db_id = cfg.get("kql_database_id")
    if not db_id:
        dbs = requests.get(f"{API}/workspaces/{ws}/kqlDatabases", headers=headers).json()["value"]
        db_id = next(d["id"] for d in dbs if d["displayName"] == cfg["kql_database"])
        print(f"kql_database_id: {db_id}")

    dashboard = build(cfg["kql_cluster_uri"], cfg["kql_database"],
                      "SPO Copilot - obraz operacyjny", db_id)
    if not args.skip_validate:
        validate(dashboard)

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
