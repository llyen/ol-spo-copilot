"""Wdrozenie repozytorium SPO Copilot do Microsoft Fabric.

Uzycie:
    python deploy_fabric.py --config config.json [--step upload|notebooks|kql|all]

Wymaga zalogowanego Azure CLI (`az login`) z dostepem do docelowego workspace Fabric.
Skrypt jest idempotentny - ponowne uruchomienie nadpisuje pliki i definicje elementow.
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import subprocess
import sys
import time

import requests

BASE = pathlib.Path(__file__).resolve().parent
FABRIC_API = "https://api.fabric.microsoft.com/v1"
ONELAKE = "https://onelake.dfs.fabric.microsoft.com"
CHUNK = 4 * 1024 * 1024

# sciezki w Lakehouse
LH_ROOT = "/lakehouse/default/Files"

NOTEBOOK_REWRITES = [
    ('BASE = Path(__file__).resolve().parents[1]', f'BASE = Path("{LH_ROOT}")'),
    ('sys.path.insert(0, str(BASE))', 'sys.path.insert(0, str(BASE / "code"))'),
    ('DATA = BASE / "datasets"', 'DATA = BASE / "raw"'),
    ('OUT = DATA / "derived"', 'OUT = BASE / "derived"'),
    ('Retriever.load(DATA)', 'Retriever.load(DATA, OUT)'),
]

# dodatkowa komorka notatnika 01 - zapis tabel Delta
DELTA_CELL = '''# zapis tabel Delta w Lakehouse (uruchamiane wylacznie w Fabric)
for name in CSV_TABLES:
    df = spark.read.option("header", "true").option("inferSchema", "true").csv(f"Files/raw/{name}.csv")
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(name)
    print(f"tabela {name}: {df.count()} wierszy")

for name in JSONL_TABLES:
    df = spark.read.json(f"Files/raw/{name}.jsonl")
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(name)
    print(f"tabela {name}: {df.count()} wierszy")

bridge_df = spark.read.option("header", "true").csv("Files/derived/bridge_procedure_hazard.csv")
bridge_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("bridge_procedure_hazard")
print(f"tabela bridge_procedure_hazard: {bridge_df.count()} wierszy")
'''


def token(resource: str) -> str:
    out = subprocess.run(
        ["az", "account", "get-access-token", "--resource", resource, "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, shell=True,
    )
    if out.returncode != 0:
        sys.exit(f"Blad az account get-access-token: {out.stderr.strip()}")
    return out.stdout.strip()


def api_headers() -> dict:
    return {"Authorization": f"Bearer {token('https://api.fabric.microsoft.com')}",
            "Content-Type": "application/json"}


# --- 1. upload plikow do OneLake -------------------------------------------

def upload_file(local: pathlib.Path, remote: str, ws: str, lh: str, headers: dict) -> None:
    url = f"{ONELAKE}/{ws}/{lh}/{remote}"
    r = requests.put(url + "?resource=file", headers=headers)
    r.raise_for_status()
    data = local.read_bytes()
    pos = 0
    while pos < len(data):
        part = data[pos:pos + CHUNK]
        requests.patch(url + f"?action=append&position={pos}", headers=headers, data=part).raise_for_status()
        pos += len(part)
    requests.patch(url + f"?action=flush&position={len(data)}", headers=headers).raise_for_status()
    print(f"  ok {remote} ({len(data):,} B)")


def step_upload(cfg: dict) -> None:
    ws, lh = cfg["fabric"]["workspace_id"], cfg["fabric"]["lakehouse_id"]
    headers = {"Authorization": f"Bearer {token('https://storage.azure.com')}"}
    data = BASE / "datasets"
    print("Upload danych do OneLake:")
    for p in sorted(data.glob("*")):
        if p.is_file() and p.suffix in (".csv", ".jsonl", ".json"):
            upload_file(p, f"Files/raw/{p.name}", ws, lh, headers)
    for p in sorted((data / "derived").glob("*")):
        if p.is_file() and not p.name.startswith("dry_run_"):
            upload_file(p, f"Files/derived/{p.name}", ws, lh, headers)
    print("Upload modulow Python (retriever):")
    for p in sorted((BASE / "corpus").glob("*.py")):
        upload_file(p, f"Files/code/corpus/{p.name}", ws, lh, headers)


# --- 2. notatniki -----------------------------------------------------------

def to_ipynb(path: pathlib.Path) -> dict:
    src = path.read_text(encoding="utf-8")
    for old, new in NOTEBOOK_REWRITES:
        src = src.replace(old, new)
    cells = [c.strip("\n") for c in src.split("# CELL") if c.strip()]
    if path.name.startswith("01_"):
        cells.append(DELTA_CELL)
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "language_info": {"name": "python"},
            "kernelspec": {"name": "synapse_pyspark", "display_name": "Synapse PySpark"},
        },
        "cells": [
            {"cell_type": "code", "source": c.splitlines(keepends=True), "metadata": {}, "outputs": [], "execution_count": None}
            for c in cells
        ],
    }


def existing_items(ws: str, headers: dict) -> dict:
    r = requests.get(f"{FABRIC_API}/workspaces/{ws}/items", headers=headers)
    r.raise_for_status()
    return {(i["type"], i["displayName"]): i["id"] for i in r.json()["value"]}


def step_notebooks(cfg: dict) -> None:
    ws, lh = cfg["fabric"]["workspace_id"], cfg["fabric"]["lakehouse_id"]
    headers = api_headers()
    items = existing_items(ws, headers)
    print("Publikacja notatnikow:")
    for path in sorted((BASE / "notebooks").glob("*.py")):
        nb = to_ipynb(path)
        nb["metadata"]["dependencies"] = {
            "lakehouse": {"default_lakehouse": lh, "default_lakehouse_workspace_id": ws}
        }
        payload = base64.b64encode(json.dumps(nb, ensure_ascii=False).encode("utf-8")).decode()
        definition = {"format": "ipynb", "parts": [
            {"path": "notebook-content.ipynb", "payload": payload, "payloadType": "InlineBase64"}]}
        name = path.stem
        key = ("Notebook", name)
        if key in items:
            url = f"{FABRIC_API}/workspaces/{ws}/items/{items[key]}/updateDefinition"
            body = {"definition": definition}
        else:
            url = f"{FABRIC_API}/workspaces/{ws}/items"
            body = {"displayName": name, "type": "Notebook", "definition": definition}
        r = requests.post(url, headers=headers, json=body)
        if r.status_code in (200, 201, 202):
            print(f"  ok {name}")
        else:
            print(f"  BLAD {name}: {r.status_code} {r.text[:300]}")


# --- 3. skrypty KQL ---------------------------------------------------------

def split_kql(text: str) -> list[str]:
    """Dzieli plik KQL na polecenia (komendy zaczynaja sie od kropki na poczatku linii)."""
    commands, buf = [], []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//") or not stripped:
            if buf and not stripped:
                buf.append(line)
            continue
        if stripped.startswith(".") and buf:
            commands.append("\n".join(buf).strip())
            buf = [line]
        else:
            buf.append(line)
    if buf:
        commands.append("\n".join(buf).strip())
    return [c for c in commands if c.strip().startswith(".")]


def step_kql(cfg: dict) -> None:
    uri = cfg["fabric"]["kql_cluster_uri"].rstrip("/")
    db = cfg["fabric"]["kql_database"]
    headers = {"Authorization": f"Bearer {token(uri)}", "Content-Type": "application/json"}
    print(f"Wykonanie skryptow KQL w {db}:")
    for path in sorted((BASE / "kql").glob("0[12]_*.kql")):
        print(f"  {path.name}")
        for cmd in split_kql(path.read_text(encoding="utf-8")):
            r = requests.post(f"{uri}/v1/rest/mgmt", headers=headers,
                              json={"db": db, "csl": cmd})
            head = cmd.splitlines()[0][:70]
            if r.status_code == 200:
                print(f"    ok  {head}")
            else:
                print(f"    ERR {head} -> {r.status_code} {r.text[:200]}")
            time.sleep(0.3)


# --- 4. jednorazowe zaladowanie historii do Eventhouse ----------------------

def step_history(cfg: dict) -> None:
    uri = cfg["fabric"]["kql_cluster_uri"].rstrip("/")
    db = cfg["fabric"]["kql_database"]
    ws, lh = cfg["fabric"]["workspace_id"], cfg["fabric"]["lakehouse_id"]
    headers = {"Authorization": f"Bearer {token(uri)}", "Content-Type": "application/json"}
    script = (BASE / "kql" / "06_ingest_history.kql").read_text(encoding="utf-8")
    script = script.replace("<workspace-id>", ws).replace("<lakehouse-id>", lh)
    print(f"Ladowanie historii do {db}:")
    for cmd in split_kql(script):
        r = requests.post(f"{uri}/v1/rest/mgmt", headers=headers, json={"db": db, "csl": cmd})
        table = cmd.split("table")[1].split("(")[0].strip() if "table" in cmd else cmd[:40]
        print(f"    {'ok ' if r.status_code == 200 else 'ERR'} {table}"
              + ("" if r.status_code == 200 else f" -> {r.text[:180]}"))
        time.sleep(0.5)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--step", default="all", choices=["upload", "notebooks", "kql", "history", "all"])
    args = ap.parse_args()
    cfg_path = BASE / args.config
    if not cfg_path.exists():
        sys.exit(f"Brak pliku {cfg_path}. Skopiuj config.example.json i uzupelnij identyfikatory.")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    steps = ["upload", "notebooks", "kql", "history"] if args.step == "all" else [args.step]
    for s in steps:
        {"upload": step_upload, "notebooks": step_notebooks,
         "kql": step_kql, "history": step_history}[s](cfg)
    print("\nGOTOWE")


if __name__ == "__main__":
    main()
