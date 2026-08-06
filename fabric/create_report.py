"""Tworzy raport Power BI OL_SPO_Raport (PBIR) na modelu OL_SPO_SemanticModel."""
import argparse, base64, json, subprocess, time
from pathlib import Path

import requests

API = "https://api.fabric.microsoft.com/v1"
BASE = Path(__file__).resolve().parent.parent

_ap = argparse.ArgumentParser(description="Tworzy raport Power BI (PBIR) na modelu semantycznym.")
_ap.add_argument("--config", default=str(BASE / "config.json"))
_ap.add_argument("--dataset", help="Identyfikator modelu semantycznego (domyslnie z config.json).")
ARGS = _ap.parse_args()

CFG = json.load(open(ARGS.config, encoding="utf-8"))["fabric"]
WS = CFG["workspace_id"]
DATASET = ARGS.dataset or CFG["semantic_model_id"]
NAME = CFG.get("report", "OL_SPO_Raport")
SCH = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"

W, H = 1280, 720
BG, FG, AMBER, RED, GREEN = "#1B1F23", "#F5F6F7", "#F2A900", "#D13438", "#0F7B0F"


def measure(table, name):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def column(table, name):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def proj(field, table, name, extra=None):
    p = {"field": field, "queryRef": f"{table}.{name}", "nativeQueryRef": name}
    if extra:
        p.update(extra)
    return p


def m(table, name):
    return proj(measure(table, name), table, name)


def c(table, name):
    return proj(column(table, name), table, name)


_seq = [0]


def visual(vtype, x, y, w, h, states, title=None, extra_objects=None, sort=None):
    _seq[0] += 1
    vid = f"v{_seq[0]:03d}"
    objects = {"title": [{"properties": {
        "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{FG}'"}}}}},
        "fontSize": {"expr": {"Literal": {"Value": "12D"}}},
        "show": {"expr": {"Literal": {"Value": "true"}}},
    }}]} if title else {}
    if extra_objects:
        objects.update(extra_objects)
    v = {
        "$schema": f"{SCH}/visualContainer/1.4.0/schema.json",
        "name": vid,
        "position": {"x": x, "y": y, "z": _seq[0], "width": w, "height": h, "tabOrder": _seq[0]},
        "visual": {
            "visualType": vtype,
            "query": {"queryState": {k: {"projections": v_} for k, v_ in states.items()}},
            "objects": objects,
            "drillFilterOtherVisuals": True,
        },
    }
    if sort:
        v["visual"]["query"]["sortDefinition"] = {"sort": sort}
    return v


def textbox(x, y, w, h, paragraphs):
    _seq[0] += 1
    vid = f"v{_seq[0]:03d}"
    return {
        "$schema": f"{SCH}/visualContainer/1.4.0/schema.json",
        "name": vid,
        "position": {"x": x, "y": y, "z": _seq[0], "width": w, "height": h, "tabOrder": _seq[0]},
        "visual": {"visualType": "textbox", "objects": {"general": [{"properties": {
            "paragraphs": [{"textRuns": [{"value": t, "textStyle": {
                "fontSize": f"{s}pt", "color": col, "fontWeight": "bold" if b else "normal"}}]}
                for t, s, col, b in paragraphs]}}]}},
    }


def sort_by(table, name, direction="Ascending"):
    return [{"field": {"Measure": {"Expression": {"SourceRef": {"Entity": table}},
                                   "Property": name}}, "direction": direction}]


# =============================== STRONY =======================================
PAGES = []


def page(name, display, visuals):
    PAGES.append((name, display, visuals))


FA, FS, FD, FQ = "fact_activation", "fact_step_execution", "fact_decision_log", "fact_assistant_query"

# --- 1. Gotowosc proceduralna -------------------------------------------------
page("s1", "1 | Gotowosc proceduralna", [
    textbox(16, 12, 1248, 44, [("Gotowosc proceduralna  \u2014  SPO Copilot", 20, FG, True),
                               ("  dane syntetyczne, demo", 11, "#9AA0A6", False)]),
    visual("card", 16, 64, 300, 110, {"Values": [m(FA, "Uruchomienia procedur")]},
           "Uruchomienia procedur"),
    visual("card", 328, 64, 300, 110, {"Values": [m(FS, "Dotrzymanie SLA %")]}, "Dotrzymanie SLA"),
    visual("card", 640, 64, 300, 110, {"Values": [m(FS, "Kroki zablokowane")]}, "Kroki zablokowane"),
    visual("card", 952, 64, 312, 110, {"Values": [m(FS, "Czas do 1. kroku krytycznego (min)")]},
           "Mediana reakcji (min)"),
    visual("barChart", 16, 186, 460, 300,
           {"Category": [c("dim_procedure", "procedure_code")], "Y": [m(FS, "Dotrzymanie SLA %")]},
           "Dotrzymanie SLA wg procedury (rosnaco)",
           sort=sort_by(FS, "Dotrzymanie SLA %")),
    visual("lineChart", 488, 186, 460, 300,
           {"Category": [c("dim_date", "quarter")], "Y": [m(FS, "Dotrzymanie SLA %")]},
           "Trend kwartalny dotrzymania SLA"),
    visual("slicer", 960, 186, 304, 145, {"Values": [c(FA, "level")]}, "Poziom"),
    visual("slicer", 960, 341, 304, 145, {"Values": [c(FA, "event_name")]}, "Zdarzenie"),
    visual("pivotTable", 16, 498, 932, 206,
           {"Rows": [c("dim_hazard", "hazard_name")],
            "Columns": [c("dim_procedure", "procedure_code")],
            "Values": [m(FA, "Uruchomienia procedur")]},
           "Mapa cieplna: zagrożenie x procedura"),
    visual("slicer", 960, 498, 304, 206, {"Values": [c("dim_date", "year_month")]}, "Miesiac"),
])

# --- 2. Anatomia procedury ----------------------------------------------------
page("s2", "2 | Anatomia procedury", [
    textbox(16, 12, 1248, 44, [("Anatomia procedury", 20, FG, True),
                               ("  wybierz procedure z listy po prawej", 11, "#9AA0A6", False)]),
    visual("slicer", 1000, 64, 264, 640, {"Values": [c("dim_procedure", "procedure_code")]},
           "Procedura"),
    visual("card", 16, 64, 240, 100, {"Values": [m("dim_procedure", "Procedury w korpusie")]},
           "Procedury w zakresie"),
    visual("card", 268, 64, 240, 100, {"Values": [m(FS, "Dotrzymanie SLA %")]}, "Dotrzymanie SLA"),
    visual("card", 520, 64, 240, 100, {"Values": [m(FS, "Mediana przekroczenia (min)")]},
           "Mediana przekroczenia (min)"),
    visual("card", 772, 64, 216, 100, {"Values": [m(FS, "Stosunek czasu do normy")]},
           "Czas / norma"),
    visual("clusteredColumnChart", 16, 176, 972, 250,
           {"Category": [c("dim_step", "step_no")],
            "Y": [m(FS, "Wykonania kroków"), m(FS, "Kroki zablokowane")]},
           "Sciezka kroków procedury"),
    visual("tableEx", 16, 438, 640, 266,
           {"Values": [c("dim_step", "step_title"), c("dim_step", "role_name"),
                       c("dim_step", "sla_minutes"), m(FS, "Przekroczenia SLA %"),
                       c("dim_step", "output_document")]},
           "Kroki procedury"),
    visual("barChart", 668, 438, 320, 266,
           {"Category": [c(FS, "blocker_reason")], "Y": [m(FS, "Kroki zablokowane")]},
           "Blokady w procedurze", sort=sort_by(FS, "Kroki zablokowane", "Descending")),
])

# --- 3. Waskie gardla i lessons learned --------------------------------------
page("s3", "3 | Waskie gardla i lessons learned", [
    textbox(16, 12, 1248, 44, [("Waskie gardla i lessons learned", 20, FG, True),
                               ("  co powtarza się od lat", 11, "#9AA0A6", False)]),
    visual("tableEx", 16, 64, 620, 300,
           {"Values": [c("dim_step", "step_title"), c("dim_procedure", "procedure_code"),
                       m(FS, "Przekroczenia SLA %"), m(FS, "Stosunek czasu do normy"),
                       m(FS, "Mediana przekroczenia (min)")]},
           "Kroki najczesciej po terminie",
           sort=sort_by(FS, "Przekroczenia SLA %", "Descending")),
    visual("tableEx", 648, 64, 616, 300,
           {"Values": [c(FS, "blocker_reason"), m(FS, "Kroki zablokowane"),
                       m(FS, "Lata wystepowania blokady"), m(FS, "Blokada powtarzalna")]},
           "Powtarzajace się blokady",
           sort=sort_by(FS, "Kroki zablokowane", "Descending")),
    visual("columnChart", 16, 376, 620, 240,
           {"Category": [c("dim_date", "year")], "Y": [m(FS, "Kroki zablokowane")]},
           "Os czasu blokad \u2014 problem nie znika"),
    visual("card", 648, 376, 300, 110, {"Values": [m(FS, "Lata wystepowania blokady")]},
           "Lata wystepowania"),
    visual("card", 964, 376, 300, 110, {"Values": [m(FS, "Udzial blokad %")]}, "Udzial blokad"),
    textbox(648, 500, 616, 116, [
        ("Wniosek systemowy", 14, AMBER, True),
        ("Ta sama przyczyna blokuje kroki od czterech lat, w kilkunastu procedurach. "
         "To nie incydent \u2014 to brak wlasciciela danych o infrastrukturze krytycznej. "
         "Usuniecie problemu dotyka SPO-10 i SPO-12.", 11, FG, False)]),
    textbox(16, 628, 1248, 76, [
        ("Rekomendacja", 12, GREEN, True),
        ("Wyznaczyc wlasciciela rejestru operatorów IK i udostepnic go jako produkt danych; "
         "koszt \u2014 jedna integracja, efekt \u2014 skrocenie mediany reakcji o kilkanascie minut "
         "w kazdym uruchomieniu z udziałem IK.", 11, FG, False)]),
])

# --- 4. Dziennik decyzji ------------------------------------------------------
page("s4", "4 | Dziennik decyzji", [
    textbox(16, 12, 1248, 44, [("Dziennik decyzji", 20, FG, True),
                               ("  rozliczalnosc zdarzenia", 11, "#9AA0A6", False)]),
    visual("card", 16, 64, 300, 100, {"Values": [m(FD, "Decyzje w dzienniku")]}, "Decyzje"),
    visual("donutChart", 328, 64, 320, 240,
           {"Category": [c(FD, "classification")], "Y": [m(FD, "Decyzje w dzienniku")]},
           "Rozklad klauzul"),
    visual("columnChart", 660, 64, 604, 240,
           {"Category": [c("dim_date", "year_month")], "Y": [m(FD, "Decyzje w dzienniku")],
            "Series": [c(FD, "decision_type")]},
           "Decyzje w czasie wg typu"),
    visual("slicer", 16, 176, 300, 128, {"Values": [c(FD, "decision_type")]}, "Typ decyzji"),
    visual("tableEx", 16, 316, 1248, 388,
           {"Values": [c(FD, "decided_at"), c(FD, "procedure_code"), c(FD, "step_no"),
                       c(FD, "decision_type"), c(FD, "decided_by_role"), c(FD, "subject"),
                       c(FD, "classification")]},
           "Dziennik decyzji"),
])

# --- 5. Asystent w liczbach ---------------------------------------------------
page("s5", "5 | Asystent w liczbach", [
    textbox(16, 12, 1248, 44, [("Asystent w liczbach", 20, FG, True),
                               ("  jakosc routingu i czasy odpowiedzi", 11, "#9AA0A6", False)]),
    visual("card", 16, 64, 300, 100, {"Values": [m(FQ, "Zapytania do asystenta")]}, "Zapytania"),
    visual("card", 328, 64, 300, 100, {"Values": [m(FQ, "Trafnosc routingu %")]}, "Trafnosc routingu"),
    visual("card", 640, 64, 300, 100, {"Values": [m(FQ, "P95 czasu odpowiedzi (ms)")]},
           "P95 odpowiedzi (ms)"),
    visual("card", 952, 64, 312, 100, {"Values": [m(FQ, "Ocena pomocne %")]}, "Ocena pomocne"),
    visual("barChart", 16, 176, 460, 260,
           {"Category": [c(FQ, "user_role")], "Y": [m(FQ, "Trafnosc routingu %")]},
           "Trafnosc wg roli uzytkownika"),
    visual("areaChart", 488, 176, 460, 260,
           {"Category": [c("dim_date", "year_month")], "Y": [m(FQ, "Zapytania do asystenta")],
            "Series": [c(FQ, "channel")]},
           "Wolumen wg kanału"),
    visual("card", 960, 176, 304, 125, {"Values": [m("corpus_chunks", "Fragmenty korpusu")]},
           "Fragmenty korpusu"),
    visual("card", 960, 311, 304, 125, {"Values": [m("dim_hazard", "Pokrycie zagrożeń procedurami %")]},
           "Pokrycie zagrożeń"),
    visual("tableEx", 16, 448, 932, 256,
           {"Values": [c(FQ, "question"), c(FQ, "top_procedure"), c(FQ, "expected_procedure"),
                       c(FQ, "confidence"), c(FQ, "feedback")]},
           "Kolejka poprawy korpusu \u2014 pytania do przegladu",
           sort=[{"field": column(FQ, "confidence"), "direction": "Ascending"}]),
    visual("card", 960, 448, 304, 256, {"Values": [m(FQ, "Zapytania niskiej pewnosci")]},
           "Zapytania niskiej pewnosci"),
])

# --- 6. POWODZ WRZESIEN -------------------------------------------------------
page("s6", "6 | POWODZ WRZESIEN \u2014 przebieg", [
    textbox(16, 12, 1248, 44, [("POWODZ WRZESIEN \u2014 przebieg", 20, FG, True),
                               ("  scenariusz osiowy programu", 11, "#9AA0A6", False)]),
    visual("card", 16, 64, 300, 100, {"Values": [m(FA, "Uruchomienia POWODZ WRZESIEN")]},
           "Uruchomienia w scenariuszu"),
    visual("card", 328, 64, 300, 100, {"Values": [m(FS, "Dotrzymanie SLA - powódź %")]},
           "SLA \u2014 powódź"),
    visual("card", 640, 64, 300, 100, {"Values": [m(FS, "Dotrzymanie SLA %")]}, "SLA \u2014 historia"),
    visual("card", 952, 64, 312, 100,
           {"Values": [m(FS, "Roznica SLA powódź vs historia (p.p.)")]}, "Roznica (p.p.)"),
    visual("columnChart", 16, 176, 620, 270,
           {"Category": [c("dim_date", "date")], "Y": [m(FS, "Wykonania kroków")],
            "Series": [c(FS, "procedure_code")]},
           "Przebieg dobowy \u2014 kroki wg procedury"),
    visual("map", 648, 176, 616, 270,
           {"Category": [c(FA, "voivodeship_name")], "Size": [m(FA, "Uruchomienia procedur")]},
           "Uruchomienia wg województwa"),
    visual("tableEx", 16, 458, 1248, 246,
           {"Values": [c("dim_date", "date"), m(FA, "Uruchomienia procedur"),
                       m(FS, "Wykonania kroków"), m(FS, "Kroki zablokowane"),
                       m(FS, "Dotrzymanie SLA %")]},
           "Doby o najwiekszym obciazeniu",
           sort=sort_by(FA, "Uruchomienia procedur", "Descending")),
])

# =============================== BUDOWA =======================================
THEME = {
    "name": "OL_SPO_Dark",
    "dataColors": [AMBER, "#4FA3D1", GREEN, RED, "#9B6BC9", "#C77E23", "#7FB77E", "#B0B7BF"],
    "background": BG, "foreground": FG, "tableAccent": AMBER,
    "visualStyles": {"*": {"*": {
        "background": [{"color": {"solid": {"color": "#24292E"}}, "transparency": 0}],
        "border": [{"show": True, "color": {"solid": {"color": "#30363D"}}, "radius": 6}],
        "labels": [{"color": {"solid": {"color": FG}}}],
        "title": [{"fontColor": {"solid": {"color": FG}}, "fontSize": 12}],
    }}},
}


def build_parts():
    parts = {}
    parts["definition.pbir"] = json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": None, "byConnection": {
            "connectionString": None, "pbiServiceModelId": None,
            "pbiModelVirtualServerName": "sobe_wowvirtualserver",
            "pbiModelDatabaseName": DATASET, "name": "EntityDataSource",
            "connectionType": "pbiServiceXmlaStyleLive"}}})
    parts["definition/version.json"] = json.dumps(
        {"$schema": f"{SCH}/versionMetadata/1.0.0/schema.json", "version": "4.0.0"})
    parts["definition/report.json"] = json.dumps({
        "$schema": f"{SCH}/report/1.4.0/schema.json",
        "themeCollection": {"customTheme": {"name": "OL_SPO_Dark", "type": "SharedResources",
                                            "reportVersionAtImport": "5.55"}},
        "layoutOptimization": "None",
        "settings": {"allowChangeFilterTypes": True},
    })
    parts["StaticResources/SharedResources/BaseThemes/OL_SPO_Dark.json"] = json.dumps(THEME)
    parts["definition/pages/pages.json"] = json.dumps({
        "$schema": f"{SCH}/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p[0] for p in PAGES], "activePageName": PAGES[0][0]})
    for pname, display, visuals in PAGES:
        parts[f"definition/pages/{pname}/page.json"] = json.dumps({
            "$schema": f"{SCH}/page/1.4.0/schema.json",
            "name": pname, "displayName": display, "displayOption": "FitToPage",
            "height": H, "width": W})
        for v in visuals:
            parts[f"definition/pages/{pname}/visuals/{v['name']}/visual.json"] = json.dumps(v)
    return [{"path": p, "payload": base64.b64encode(cnt.encode("utf-8")).decode(),
             "payloadType": "InlineBase64"} for p, cnt in parts.items()]


def main():
    tok = subprocess.run(["az", "account", "get-access-token", "--resource",
                          "https://api.fabric.microsoft.com", "--query", "accessToken", "-o", "tsv"],
                         capture_output=True, text=True, shell=True).stdout.strip()
    hh = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    items = requests.get(f"{API}/workspaces/{WS}/items?type=Report", headers=hh).json()["value"]
    existing = next((i for i in items if i["displayName"] == NAME), None)
    definition = {"parts": build_parts()}
    if existing:
        r = requests.post(f"{API}/workspaces/{WS}/reports/{existing['id']}/updateDefinition",
                          headers=hh, json={"definition": definition})
        print("update:", r.status_code, r.text[:1200])
    else:
        r = requests.post(f"{API}/workspaces/{WS}/reports", headers=hh,
                          json={"displayName": NAME, "definition": definition})
        print("create:", r.status_code, r.text[:1200])
    if r.status_code == 202:
        loc = r.headers.get("Location")
        for _ in range(60):
            time.sleep(5)
            s = requests.get(loc, headers=hh).json()
            if s.get("status") in ("Succeeded", "Failed"):
                print(json.dumps(s)[:1500]); break


if __name__ == "__main__":
    main()

