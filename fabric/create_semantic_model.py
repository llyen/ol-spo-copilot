"""Tworzy model semantyczny OL_SPO_SemanticModel (Direct Lake) w Microsoft Fabric."""
import argparse, base64, json, subprocess, time, uuid
from pathlib import Path

import requests

API = "https://api.fabric.microsoft.com/v1"
BASE = Path(__file__).resolve().parent.parent

_ap = argparse.ArgumentParser(description="Tworzy model semantyczny Direct Lake w Fabric.")
_ap.add_argument("--config", default=str(BASE / "config.json"))
_ap.add_argument("--schemas", default=str(BASE / "fabric" / "lakehouse_schemas.json"),
                 help="Schematy tabel Delta (patrz fabric/get_schemas.py).")
ARGS = _ap.parse_args()

CFG = json.load(open(ARGS.config, encoding="utf-8"))["fabric"]
WS = CFG["workspace_id"]
LAKEHOUSE = CFG["lakehouse_name"]
SQL_EP = CFG["sql_endpoint"]
NAME = CFG.get("semantic_model", "OL_SPO_SemanticModel")

SCHEMAS = json.load(open(ARGS.schemas, encoding="utf-8"))

# Schematy pochodza z fabric/get_schemas.py i zawieraja juz kolumny dodane przez
# notatnik 06_semantic_prep (kolumny czasu, kolumny wyliczane, wymiar dim_date).
SCHEMAS = {t: [tuple(c) for c in cols] for t, cols in SCHEMAS.items()}

DTYPE = {"string": "string", "integer": "int64", "long": "int64", "double": "double",
         "float": "double", "boolean": "boolean", "date": "dateTime", "timestamp": "dateTime"}

MEASURES = {
    "fact_activation": [
        ("Uruchomienia procedur", "DISTINCTCOUNT ( fact_activation[activation_id] )", "#,0"),
        ("Mediana czasu trwania procedury (h)",
         "DIVIDE ( MEDIANX ( fact_activation, fact_activation[duration_minutes] ), 60 )", "#,0.0"),
        ("Uruchomienia POWODZ WRZESIEN",
         'CALCULATE ( [Uruchomienia procedur], fact_activation[event_name] = "POWODZ WRZESIEN" )', "#,0"),
    ],
    "fact_step_execution": [
        ("Wykonania krokow", "COUNTROWS ( fact_step_execution )", "#,0"),
        ("Kroki w normie", "CALCULATE ( [Wykonania krokow], fact_step_execution[sla_met] = 1 )", "#,0"),
        ("Dotrzymanie SLA %", "DIVIDE ( [Kroki w normie], [Wykonania krokow] )", "0.0%"),
        ("Przekroczenia SLA %", "1 - [Dotrzymanie SLA %]", "0.0%"),
        ("Mediana przekroczenia (min)",
         "MEDIANX ( FILTER ( fact_step_execution, fact_step_execution[overdue_minutes] > 0 ), "
         "fact_step_execution[overdue_minutes] )", "#,0.0"),
        ("Stosunek czasu do normy",
         "DIVIDE ( MEDIANX ( fact_step_execution, fact_step_execution[elapsed_minutes] ), "
         "MEDIANX ( fact_step_execution, fact_step_execution[sla_minutes] ) )", "#,0.00"),
        ("Dotrzymanie SLA krokow krytycznych %",
         "CALCULATE ( [Dotrzymanie SLA %], fact_step_execution[is_critical] = 1 )", "0.0%"),
        ("Kroki zablokowane",
         'CALCULATE ( [Wykonania krokow], fact_step_execution[status] = "zablokowany" )', "#,0"),
        ("Udzial blokad %", "DIVIDE ( [Kroki zablokowane], [Wykonania krokow] )", "0.0%"),
        ("Lata wystepowania blokady",
         'CALCULATE ( DISTINCTCOUNT ( dim_date[year] ), FILTER ( fact_step_execution, '
         'fact_step_execution[blocker_reason] <> "" ) )', "#,0"),
        ("Blokada powtarzalna",
         'VAR Wystapienia = [Kroki zablokowane]\n'
         'VAR Lata = [Lata wystepowania blokady]\n'
         'RETURN IF ( Wystapienia >= 10 && Lata >= 3, "wniosek systemowy", "incydentalna" )', None),
        ("Czas do 1. kroku krytycznego (min)",
         'VAR PierwszeKrytyczne =\n'
         '    SUMMARIZE (\n'
         '        FILTER ( fact_step_execution, fact_step_execution[is_critical] = 1 ),\n'
         '        fact_step_execution[activation_id],\n'
         '        "Zakonczenie", MIN ( fact_step_execution[completed_ts] )\n'
         '    )\n'
         'VAR ZeStartem =\n'
         '    ADDCOLUMNS (\n'
         '        PierwszeKrytyczne,\n'
         '        "Reakcja",\n'
         '        DATEDIFF (\n'
         '            LOOKUPVALUE ( fact_activation[started_ts], fact_activation[activation_id],\n'
         '                [activation_id] ),\n'
         '            [Zakonczenie],\n'
         '            MINUTE\n'
         '        )\n'
         '    )\n'
         'RETURN MEDIANX ( ZeStartem, [Reakcja] )', "#,0.0"),
        ("Dotrzymanie SLA - powodz %",
         'CALCULATE ( [Dotrzymanie SLA %], fact_step_execution[event_name] = "POWODZ WRZESIEN" )', "0.0%"),
        ("Roznica SLA powodz vs historia (p.p.)",
         '( [Dotrzymanie SLA - powodz %] - CALCULATE ( [Dotrzymanie SLA %], '
         'fact_step_execution[event_name] <> "POWODZ WRZESIEN" ) ) * 100', "#,0.0"),
    ],
    "fact_decision_log": [
        ("Decyzje w dzienniku", "COUNTROWS ( fact_decision_log )", "#,0"),
    ],
    "fact_assistant_query": [
        ("Zapytania do asystenta", "COUNTROWS ( fact_assistant_query )", "#,0"),
        ("Trafnosc routingu %",
         "DIVIDE ( CALCULATE ( [Zapytania do asystenta], fact_assistant_query[is_correct] = 1 ), "
         "[Zapytania do asystenta] )", "0.0%"),
        ("Mediana czasu odpowiedzi (ms)",
         "MEDIANX ( fact_assistant_query, fact_assistant_query[latency_ms] )", "#,0"),
        ("P95 czasu odpowiedzi (ms)",
         "PERCENTILEX.INC ( fact_assistant_query, fact_assistant_query[latency_ms], 0.95 )", "#,0"),
        ("Ocena pomocne %",
         'DIVIDE ( CALCULATE ( [Zapytania do asystenta], fact_assistant_query[feedback] = "pomocne" ), '
         'CALCULATE ( [Zapytania do asystenta], fact_assistant_query[feedback] <> "brak oceny" ) )', "0.0%"),
        ("Zapytania niskiej pewnosci",
         "CALCULATE ( [Zapytania do asystenta], fact_assistant_query[confidence] < 0.45 )", "#,0"),
    ],
    "dim_procedure": [
        ("Procedury w korpusie", "DISTINCTCOUNT ( dim_procedure[procedure_code] )", "#,0"),
    ],
    "corpus_chunks": [
        ("Fragmenty korpusu", "COUNTROWS ( corpus_chunks )", "#,0"),
    ],
    "dim_step": [
        ("Kroki bez dokumentu wyjsciowego",
         'CALCULATE ( COUNTROWS ( dim_step ), dim_step[output_document] = "" )', "#,0"),
    ],
    "dim_hazard": [
        ("Pokrycie zagrozen procedurami %",
         "DIVIDE ( CALCULATE ( DISTINCTCOUNT ( bridge_procedure_hazard[hazard_code] ), "
         "ALL ( bridge_procedure_hazard ) ), DISTINCTCOUNT ( dim_hazard[hazard_code] ) )", "0.0%"),
    ],
}

RELATIONSHIPS = [
    ("dim_date", "date", "fact_activation", "started_date"),
    ("dim_date", "date", "fact_step_execution", "event_date"),
    ("dim_date", "date", "fact_decision_log", "decided_date"),
    ("dim_date", "date", "fact_assistant_query", "asked_date"),
    ("dim_procedure", "procedure_code", "fact_activation", "procedure_code"),
    ("dim_procedure", "procedure_code", "fact_step_execution", "procedure_code", False),
    ("dim_procedure", "procedure_code", "fact_decision_log", "procedure_code"),
    ("dim_procedure", "procedure_code", "dim_step", "procedure_code"),
    ("dim_procedure", "procedure_code", "dim_document", "procedure_code"),
    ("dim_procedure", "procedure_code", "bridge_procedure_hazard", "procedure_code"),
    ("dim_step", "step_id", "fact_step_execution", "step_id"),
    ("dim_role", "role_code", "fact_step_execution", "role_code", False),
    ("dim_role", "role_code", "dim_step", "role_code"),
    ("dim_hazard", "hazard_code", "fact_activation", "hazard_code"),
    ("dim_hazard", "hazard_code", "bridge_procedure_hazard", "hazard_code"),
    ("fact_activation", "activation_id", "fact_step_execution", "activation_id", False),
    ("fact_activation", "activation_id", "fact_decision_log", "activation_id", False),
]

HIDDEN_TABLES = {"bridge_procedure_hazard", "eval_questions"}
NUMERIC = {"int64", "double"}


def lt():
    return str(uuid.uuid4())


def ind(text, n):
    pad = "\t" * n
    return "\n".join(pad + l if l else l for l in text.split("\n"))


def table_tmdl(name, cols):
    out = [f"table {name}", ""]
    if name in HIDDEN_TABLES:
        out.append("\tisHidden")
        out.append("")
    if name == "dim_date":
        out.append("\tdataCategory: Time")
        out.append("")
    for m_name, expr, fmt in MEASURES.get(name, []):
        if "\n" in expr:
            out.append(f"\tmeasure '{m_name}' =")
            out.append(ind(expr, 3))
        else:
            out.append(f"\tmeasure '{m_name}' = {expr}")
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out.append("\t\tdisplayFolder: _Miary")
        out.append(f"\t\tlineageTag: {lt()}")
        out.append("")
    for col, typ in cols:
        dt = DTYPE.get(typ, "string")
        out.append(f"\tcolumn {col}")
        out.append(f"\t\tdataType: {dt}")
        if dt in NUMERIC:
            out.append("\t\tsummarizeBy: sum" if name.startswith("fact") else "\t\tsummarizeBy: none")
        else:
            out.append("\t\tsummarizeBy: none")
        out.append(f"\t\tsourceColumn: {col}")
        if name == "dim_date" and col == "date":
            out.append("\t\tisKey")
        if dt == "dateTime":
            out.append("\t\tformatString: " + ("Long Date" if typ == "date" else "General Date"))
        out.append(f"\t\tlineageTag: {lt()}")
        out.append("")
    out.append(f"\tpartition {name} = entity")
    out.append("\t\tmode: directLake")
    out.append("\t\tsource")
    out.append(f"\t\t\tentityName: {name}")
    out.append("\t\t\texpressionSource: DatabaseQuery")
    out.append("")
    out.append("\tannotation PBI_ResultType = Table")
    out.append("")
    return "\n".join(out)


def model_tmdl():
    out = ["model Model", "\tculture: pl-PL", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
           "\tsourceQueryCulture: pl-PL", "\tdataAccessOptions", "\t\tlegacyRedirects",
           "\t\treturnErrorValuesAsNull", ""]
    for t in sorted(SCHEMAS):
        out.append(f"ref table {t}")
    out.append("")
    out.append("ref cultureInfo pl-PL")
    out.append("")
    for rel in RELATIONSHIPS:
        f, fc, tt, tc = rel[:4]
        active = rel[4] if len(rel) > 4 else True
        rid = f"rel_{f}_{fc}_{tt}_{tc}"
        out.append(f"relationship {rid}")
        out.append(f"\tfromColumn: {tt}.{tc}")
        out.append(f"\ttoColumn: {f}.{fc}")

        if not active:

            out.append("\tisActive: false")
        out.append("")
    return "\n".join(out)


PBISM = {"version": "4.0", "settings": {"qnaEnabled": True}}
DATABASE = "database\n\tcompatibilityLevel: 1604\n"
EXPR = (f'expression DatabaseQuery =\n'
        f'\t\tlet\n'
        f'\t\t    database = Sql.Database("{SQL_EP}", "{LAKEHOUSE}")\n'
        f'\t\tin\n'
        f'\t\t    database\n'
        f'\tlineageTag: {lt()}\n'
        f'\tannotation PBI_IncludeFutureArtifacts = False\n')
CULTURE = "cultureInfo pl-PL\n\tlinguisticMetadata =\n\t\t\t{\n\t\t\t  \"Version\": \"1.0.0\",\n\t\t\t  \"Language\": \"pl-PL\"\n\t\t\t}\n\t\tcontentType: json\n"


def build_parts():
    parts = {
        "definition.pbism": json.dumps(PBISM),
        "definition/database.tmdl": DATABASE,
        "definition/model.tmdl": model_tmdl(),
        "definition/expressions.tmdl": EXPR,
        "definition/cultures/pl-PL.tmdl": CULTURE,
    }
    for t, cols in SCHEMAS.items():
        parts[f"definition/tables/{t}.tmdl"] = table_tmdl(t, cols)
    return [{"path": p, "payload": base64.b64encode(c.encode("utf-8")).decode(),
             "payloadType": "InlineBase64"} for p, c in parts.items()]


def main():
    tok = subprocess.run(["az", "account", "get-access-token", "--resource",
                          "https://api.fabric.microsoft.com", "--query", "accessToken", "-o", "tsv"],
                         capture_output=True, text=True, shell=True).stdout.strip()
    H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    items = requests.get(f"{API}/workspaces/{WS}/items?type=SemanticModel", headers=H).json()["value"]
    existing = next((i for i in items if i["displayName"] == NAME), None)
    definition = {"parts": build_parts()}
    if existing:
        r = requests.post(f"{API}/workspaces/{WS}/semanticModels/{existing['id']}/updateDefinition",
                          headers=H, json={"definition": definition})
        print("update:", r.status_code, r.text[:1500])
    else:
        r = requests.post(f"{API}/workspaces/{WS}/semanticModels", headers=H,
                          json={"displayName": NAME, "definition": definition})
        print("create:", r.status_code, r.text[:1500])
        if r.status_code == 202:
            loc = r.headers.get("Location")
            for _ in range(60):
                time.sleep(5)
                s = requests.get(loc, headers=H).json()
                if s.get("status") in ("Succeeded", "Failed"):
                    print(json.dumps(s)[:1500]); break


if __name__ == "__main__":
    main()



