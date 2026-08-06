"""Uruchamia notatniki Fabric po kolei i czeka na zakonczenie.

    python tools/run_notebooks.py --config config.json --notebooks 01_load_corpus 02_build_vector_index
    python tools/run_notebooks.py --config config.json          # wszystkie 01..06
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

FABRIC_API = "https://api.fabric.microsoft.com/v1"
BASE = Path(__file__).resolve().parents[1]
DEFAULT = ["01_load_corpus", "02_build_vector_index", "03_assistant_answers",
           "04_retrieval_eval", "05_step_analytics", "06_semantic_prep"]


def token() -> str:
    out = subprocess.run(
        ["az", "account", "get-access-token", "--resource",
         "https://api.fabric.microsoft.com", "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, shell=True, check=True)
    return out.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--notebooks", nargs="*", default=DEFAULT)
    ap.add_argument("--timeout", type=int, default=2400)
    args = ap.parse_args()

    cfg = json.loads((BASE / args.config).read_text(encoding="utf-8"))
    ws = cfg["fabric"]["workspace_id"]
    headers = {"Authorization": f"Bearer {token()}", "Content-Type": "application/json"}

    items = requests.get(f"{FABRIC_API}/workspaces/{ws}/items?type=Notebook",
                         headers=headers).json()["value"]
    by_name = {i["displayName"]: i["id"] for i in items}

    failed = []
    for name in args.notebooks:
        if name not in by_name:
            print(f"BRAK notatnika {name}")
            failed.append(name)
            continue
        nb = by_name[name]
        r = requests.post(f"{FABRIC_API}/workspaces/{ws}/items/{nb}/jobs/instances?jobType=RunNotebook",
                          headers=headers, json={})
        if r.status_code not in (200, 201, 202):
            print(f"BLAD startu {name}: {r.status_code} {r.text[:300]}")
            failed.append(name)
            continue
        loc = r.headers.get("Location")
        print(f"start {name} ...", flush=True)
        t0 = time.time()
        status = "NotStarted"
        while time.time() - t0 < args.timeout:
            time.sleep(20)
            s = requests.get(loc, headers={"Authorization": headers["Authorization"]})
            if s.status_code != 200:
                continue
            status = s.json().get("status", "?")
            if status in ("Completed", "Failed", "Cancelled", "Deduped"):
                break
        mins = (time.time() - t0) / 60
        print(f"  {status} ({mins:.1f} min)")
        if status != "Completed":
            failed.append(name)
            body = s.json() if s.status_code == 200 else {}
            print("  " + json.dumps(body.get("failureReason") or {}, ensure_ascii=False)[:400])

    print("\nGOTOWE" if not failed else f"\nNIEPOWODZENIA: {', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
