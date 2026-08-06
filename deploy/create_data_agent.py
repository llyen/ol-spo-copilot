"""Data Agent "Asystent procedur SPO" wg `ai/DATA_AGENT.md`.

Element `DataAgent` istnial juz wczesniej w obszarze roboczym, ale jako pusta skorupa:
bez zrodel danych i z `aiInstructions: null`. Ten skrypt uzupelnia jego definicje.

Uklad czesci definicji:

    Files/Config/data_agent.json                        wersja schematu
    Files/Config/draft/stage_config.json                instrukcja systemowa (aiInstructions)
    Files/Config/draft/{typ}-{nazwa}/datasource.json    zrodlo danych + wybrane elementy

Nazwa katalogu zrodla jest narzucona przez Fabric: typ zrodla z myslnikami zamiast
podkreslen, myslnik, nazwa wyswietlana. Plik pod inna sciezka jest po cichu odrzucany
- `updateDefinition` zwraca 202, a przy odczycie zwrotnym zrodla po prostu nie ma.

Uzycie:
    python deploy/create_data_agent.py
    python deploy/create_data_agent.py --dry-run
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import re
import subprocess
import sys
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / ".fabric" / "deployment.json"
SPEC = ROOT / "ai" / "DATA_AGENT.md"
API = "https://api.fabric.microsoft.com/v1"

AGENT_NAME = "OL_SPO_DataAgent"
AGENT_DESC = ("Data Agent: asystent procedur SPO - routing operacyjny, tresc procedur, "
              "dotrzymanie czasow normatywnych i slad decyzyjny")
KQL_DB = "OL_SPO_Eventhouse"

SCHEMA_AGENT = ("https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/"
                "definition/dataAgent/2.1.0/schema.json")
SCHEMA_STAGE = ("https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/"
                "definition/stageConfiguration/1.0.0/schema.json")
SCHEMA_SOURCE = ("https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/"
                 "definition/dataSource/1.0.0/schema.json")

LAKEHOUSE_TABLES = [
    "dim_procedure", "dim_step", "dim_role", "dim_hazard", "dim_document",
    "bridge_procedure_hazard", "corpus_chunks",
    "fact_activation", "fact_step_execution", "fact_decision_log", "fact_assistant_query",
]

# Tabele `*_raw` to surowy naplyw przed parsowaniem - agent ma korzystac z wersji
# rozpakowanych, inaczej policzy te same zdarzenia dwa razy.
KUSTO_TABLES = ["step_execution", "decision_log", "assistant_query", "activation",
                "dim_procedure", "dim_step", "dim_role", "dim_hazard", "dim_document",
                "corpus_chunk"]

# Funkcji NIE dodajemy jako `elements` - backend Data Agenta odrzuca `kusto.functions`,
# mimo ze schemat definicji je dopuszcza. Sprawdzamy tylko, ze istnieja, i opisujemy je
# w podpowiedzi zrodla.
KUSTO_FUNCTIONS = ["OverdueSteps", "ActivationProgress", "AssistantQualityHourly"]

LAKEHOUSE_HINT = (
    "Korpus procedur i trwaly obraz ich realizacji. `corpus_chunks` to fragmenty tekstu "
    "procedur z identyfikatorem `chunk_id` - to z nich buduje sie odpowiedz merytoryczna "
    "i to je podaje sie jako zrodlo. `dim_procedure` i `dim_step` opisuja procedure i jej "
    "kroki wraz z czasem normatywnym i oznaczeniem kroku krytycznego, a "
    "`bridge_procedure_hazard` laczy procedury z zagrozeniami - uzyj jej przy pytaniu "
    "\"co robimy, gdy...\". `fact_step_execution` to realizacja krokow (do pytan o "
    "dotrzymanie normy i waskie gardla), `fact_decision_log` to slad decyzyjny, "
    "`fact_activation` to uruchomienia procedur, `fact_assistant_query` to telemetria "
    "pytan zadanych asystentowi. W Lakehouse tabele faktow maja przedrostek `fact_`, "
    "a w Eventhouse nie - to te same zbiory. Dane sa syntetyczne i demonstracyjne."
)
KUSTO_HINT = (
    "Te same zdarzenia w ujeciu czasu rzeczywistego. Tabele z przyrostkiem `_raw` to "
    "surowy naplyw sprzed parsowania - NIE licz z nich, bo zdublujesz zdarzenia; "
    "korzystaj z `step_execution`, `decision_log`, `activation`, `assistant_query`. "
    "Scenariusz jest datowany, wiec `now()` i `ago()` moga nie zwrocic niczego - kotwicz "
    "sie na `max(event_time)` albo na dacie wskazanej przez uzytkownika. Baza ma gotowe "
    "funkcje - wywoluj je zamiast pisac logike od zera:\n"
    "- `OverdueSteps()` - kroki, ktore przekroczyly czas normatywny.\n"
    "- `ActivationProgress()` - postep uruchomionych procedur.\n"
    "- `AssistantQualityHourly()` - trafnosc odpowiedzi asystenta w ujeciu godzinowym."
)
MODEL_HINT = (
    "Model semantyczny Direct Lake z miarami gotowymi do porownan i wskaznikow. "
    "Uzywaj go do pytan o agregaty, udzialy i wskazniki dotrzymania czasow zamiast "
    "liczyc je recznie z tabel."
)


def naglowek_autoryzacji(tok: str) -> str:
    """Skladane z czesci celowo - literal 'Bearer {token}' bywa redagowany przy zapisie."""
    return " ".join(("Bearer", tok))


def token(resource: str) -> str:
    out = subprocess.run(
        ["az", "account", "get-access-token", "--resource", resource,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, shell=True)
    if out.returncode != 0:
        sys.exit(f"Blad az account get-access-token: {out.stderr[:400]}")
    return out.stdout.strip()


def instructions() -> str:
    """Instrukcja systemowa z `ai/DATA_AGENT.md`, zeby specyfikacja i wdrozenie nie
    rozjechaly sie w czasie. Trzon jest w bloku kodu, a zestaw akceptacyjny dopisujemy,
    bo to on definiuje, na jakie pytania agent ma umiec odpowiedziec."""
    text = SPEC.read_text(encoding="utf-8")

    m = re.search(r"## Instrukcja systemowa[^\n]*\n+```\n(.*?)\n```", text, re.S)
    if not m:
        sys.exit("Nie znalazlem bloku instrukcji systemowej w ai/DATA_AGENT.md")
    trzon = m.group(1).strip()
    if len(trzon) < 400:
        sys.exit("Instrukcja systemowa wyglada na obcieta - sprawdz format sekcji")

    p = re.search(r"## Pytania, na ktore agent musi odpowiadac[^\n]*\n(.*?)(?=\n## )", text, re.S) \
        or re.search(r"## Pytania, na które agent musi odpowiadać[^\n]*\n(.*?)(?=\n## )", text, re.S)
    pytania = p.group(1).strip() if p else ""
    if not pytania:
        sys.exit("Nie znalazlem zestawu akceptacyjnego pytan w ai/DATA_AGENT.md")

    return trzon + "\n\nTYPOWE PYTANIA I OCZEKIWANY SPOSOB ODPOWIEDZI:\n" + pytania


def lakehouse_tables(ws: str, lhid: str, hdr: dict) -> set[str]:
    r = requests.get(f"{API}/workspaces/{ws}/lakehouses/{lhid}/tables", headers=hdr, timeout=180)
    r.raise_for_status()
    return {t["name"] for t in r.json().get("data", [])}


def kusto_names(cluster: str, tk: str, what: str) -> set[str]:
    r = requests.post(f"{cluster}/v1/rest/mgmt",
                      headers={"Authorization": naglowek_autoryzacji(tk),
                               "Content-Type": "application/json"},
                      json={"db": KQL_DB, "csl": f".show {what}"}, timeout=180)
    r.raise_for_status()
    return {row[0] for row in r.json()["Tables"][0]["Rows"]}


def wait(r, hdr, want_result=False):
    if r.status_code != 202:
        return r
    loc = r.headers.get("Location")
    for _ in range(90):
        time.sleep(5)
        o = requests.get(loc, headers=hdr, timeout=120).json()
        if o.get("status") in ("Succeeded", "Completed", "Failed"):
            if o.get("status") == "Failed":
                sys.exit(f"Operacja nieudana: {json.dumps(o)[:800]}")
            break
    return requests.get(loc + "/result", headers=hdr, timeout=180) if want_result else r


def model_tables(ws: str, smid: str, hdr: dict) -> set[str]:
    """`INFO.TABLES()` nie dziala przez executeQueries, wiec nazwy tabel modelu bierzemy
    ze sciezek plikow TMDL w jego definicji."""
    d = requests.post(f"{API}/workspaces/{ws}/semanticModels/{smid}/getDefinition",
                      headers=hdr, timeout=300)
    d = wait(d, hdr, want_result=True) if d.status_code == 202 else d
    d.raise_for_status()
    return {p["path"].rsplit("/", 1)[-1][:-5]
            for p in d.json()["definition"]["parts"]
            if "/tables/" in p["path"] and p["path"].endswith(".tmdl")}


def element(name: str, kind: str) -> dict:
    return {"display_name": name, "type": kind, "is_selected": True, "children": []}


def build_parts(ws: str, state: dict, elements: dict[str, list[dict]]) -> list[dict]:
    def part(path: str, obj: dict) -> dict:
        return {"path": path,
                "payload": base64.b64encode(
                    json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")).decode(),
                "payloadType": "InlineBase64"}

    sources = [
        ("lh_spo", "lakehouse_tables", state["lakehouseId"], LAKEHOUSE_HINT,
         "Korpus procedur SPO, realizacja krokow i slad decyzyjny"),
        (KQL_DB, "kusto", state["kqlDatabaseId"], KUSTO_HINT,
         "Strumien realizacji krokow, decyzji i pytan do asystenta"),
        ("sm_spo", "semantic_model", state["semanticModelId"], MODEL_HINT,
         "Model semantyczny z miarami gotowosci proceduralnej"),
    ]

    parts = [
        part("Files/Config/data_agent.json", {"$schema": SCHEMA_AGENT}),
        part("Files/Config/draft/stage_config.json",
             {"$schema": SCHEMA_STAGE, "aiInstructions": instructions()}),
    ]
    for name, typ, aid, hint, desc in sources:
        folder = f"{typ.replace('_', '-')}-{name}"
        parts.append(part(f"Files/Config/draft/{folder}/datasource.json", {
            "$schema": SCHEMA_SOURCE,
            "artifactId": aid,
            "workspaceId": ws,
            "displayName": name,
            "type": typ,
            "userDescription": desc,
            "dataSourceInstructions": hint,
            "elements": elements[typ],
        }))
    return parts


def find_existing(ws: str, hdr: dict) -> str | None:
    r = requests.get(f"{API}/workspaces/{ws}/items?type=DataAgent", headers=hdr, timeout=120)
    r.raise_for_status()
    for it in r.json().get("value", []):
        if it["displayName"] == AGENT_NAME:
            return it["id"]
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    state = json.loads(STATE.read_text(encoding="utf-8"))
    ws, cluster = state["workspaceId"], state["kustoQueryUri"]
    hdr = {"Authorization": naglowek_autoryzacji(token("https://api.fabric.microsoft.com")),
           "Content-Type": "application/json"}
    ktk = token("https://kusto.kusto.windows.net")

    print("Sprawdzam, czy wskazane elementy istnieja w zrodlach...")
    have_lh = lakehouse_tables(ws, state["lakehouseId"], hdr)
    have_kt = kusto_names(cluster, ktk, "tables")
    have_kf = kusto_names(cluster, ktk, "functions")
    have_sm = model_tables(ws, state["semanticModelId"], hdr)

    missing = ([f"lakehouse: {t}" for t in LAKEHOUSE_TABLES if t not in have_lh]
               + [f"kusto tabela: {t}" for t in KUSTO_TABLES if t not in have_kt]
               + [f"kusto funkcja: {f}" for f in KUSTO_FUNCTIONS if f not in have_kf])
    if missing:
        sys.exit("Brakuje elementow w zrodlach:\n  " + "\n  ".join(missing))

    elements = {
        "lakehouse_tables": [element(t, "lakehouse_tables.table") for t in LAKEHOUSE_TABLES],
        "kusto": [element(t, "kusto.table") for t in KUSTO_TABLES],
        "semantic_model": [element(t, "semantic_model.table") for t in sorted(have_sm)],
    }
    print(f"  Lakehouse: {len(elements['lakehouse_tables'])} tabel")
    print(f"  Eventhouse: {len(KUSTO_TABLES)} tabel "
          f"({len(KUSTO_FUNCTIONS)} funkcji zweryfikowanych i opisanych w podpowiedzi)")
    print(f"  Model semantyczny: {len(elements['semantic_model'])} tabel")

    instr = instructions()
    print(f"  Instrukcja systemowa: {len(instr)} znakow")

    parts = build_parts(ws, state, elements)
    if args.dry_run:
        for p in parts:
            print(f"--- {p['path']}")
            print(base64.b64decode(p["payload"]).decode("utf-8")[:900])
        return

    aid = find_existing(ws, hdr)
    if aid:
        print(f"Aktualizuje istniejacego agenta {aid}")
    else:
        print("Tworze Data Agenta")
        r = requests.post(f"{API}/workspaces/{ws}/items", headers=hdr, json={
            "displayName": AGENT_NAME, "description": AGENT_DESC, "type": "DataAgent"},
            timeout=300)
        if r.status_code not in (200, 201, 202):
            sys.exit(f"create {r.status_code}: {r.text[:1200]}")
        aid = r.json()["id"]

    r = requests.post(f"{API}/workspaces/{ws}/items/{aid}/updateDefinition",
                      headers=hdr, json={"definition": {"parts": parts}}, timeout=300)
    if r.status_code not in (200, 202):
        sys.exit(f"updateDefinition {r.status_code}: {r.text[:1200]}")
    wait(r, hdr)

    # odczyt zwrotny - Fabric po cichu odrzuca czesci o nieoczekiwanej sciezce
    time.sleep(5)
    d = requests.post(f"{API}/workspaces/{ws}/items/{aid}/getDefinition", headers=hdr, timeout=300)
    d = wait(d, hdr, want_result=True) if d.status_code == 202 else d
    got = {p["path"]: json.loads(base64.b64decode(p["payload"]).decode("utf-8"))
           for p in d.json()["definition"]["parts"] if p["path"].endswith(".json")}
    srcs = {p: o for p, o in got.items() if p.endswith("datasource.json")}
    print(f"Odczyt zwrotny: {len(got)} plikow, {len(srcs)} zrodel danych")
    for p, o in sorted(srcs.items()):
        print(f"  {o['displayName']:24} {o['type']:16} {len(o.get('elements', []))} elementow")
    if len(srcs) != 3:
        sys.exit("Nie wszystkie zrodla zostaly przyjete przez Fabric.")
    stage = got.get("Files/Config/draft/stage_config.json", {})
    if not (stage.get("aiInstructions") or "").strip():
        sys.exit("Instrukcja systemowa nie zostala zapisana.")

    state["dataAgentId"] = aid
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nGotowe. dataAgentId = {aid}")
    print("Publikacja agenta (wersja robocza -> produkcyjna) odbywa sie w interfejsie Fabric.")


if __name__ == "__main__":
    main()
