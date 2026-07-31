"""Pobiera schematy tabel Delta z OneLake (potrzebne do wygenerowania modelu TMDL).

Czyta pierwszy plik dziennika transakcji Delta kazdej tabeli i zapisuje mape
nazwa tabeli -> lista (kolumna, typ) do fabric/lakehouse_schemas.json.
"""
import argparse
import json
import subprocess
from pathlib import Path

import requests

DFS = "https://onelake.dfs.fabric.microsoft.com"
BLOB = "https://onelake.blob.fabric.microsoft.com"
BASE = Path(__file__).resolve().parent.parent


def token() -> str:
    return subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://storage.azure.com",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, shell=True).stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(BASE / "config.json"))
    ap.add_argument("--out", default=str(BASE / "fabric" / "lakehouse_schemas.json"))
    args = ap.parse_args()

    cfg = json.load(open(args.config, encoding="utf-8"))["fabric"]
    ws, lh = cfg["workspace_id"], cfg["lakehouse_id"]
    headers = {"Authorization": f"Bearer {token()}", "x-ms-version": "2021-06-08"}

    api = "https://api.fabric.microsoft.com/v1"
    fab = subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, shell=True).stdout.strip()
    tables = [t["name"] for t in requests.get(
        f"{api}/workspaces/{ws}/lakehouses/{lh}/tables",
        headers={"Authorization": f"Bearer {fab}"}).json()["data"]]

    out = {}
    for table in tables:
        listing = requests.get(f"{DFS}/{ws}", headers=headers, params={
            "resource": "filesystem", "recursive": "true",
            "directory": f"{lh}/Tables/{table}/_delta_log"})
        if not listing.ok:
            print(f"{table}: blad listowania {listing.status_code}")
            continue
        logs = sorted(p["name"] for p in listing.json()["paths"] if p["name"].endswith(".json"))
        if not logs:
            print(f"{table}: brak dziennika transakcji")
            continue
        schema = None
        for line in requests.get(f"{BLOB}/{ws}/{logs[0]}", headers=headers).text.splitlines():
            entry = json.loads(line)
            if "metaData" in entry:
                schema = json.loads(entry["metaData"]["schemaString"])
        if schema:
            out[table] = [[f["name"], f["type"]] for f in schema["fields"]]
            print(f"{table}: {len(out[table])} kolumn")

    Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"zapisano {args.out}")


if __name__ == "__main__":
    main()
