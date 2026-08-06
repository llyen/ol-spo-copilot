"""Buduje scene.json dla Fabric App „Asystent SPO".

Scena zawiera wszystko, czego aplikacja potrzebuje bez zapytania do backendu:
korpus procedur, indeks TF-IDF (ten sam, co w `corpus/retriever.py`), analitykę
SLA z historii oraz zestaw uruchomień w toku.

    python tools/build_scene.py

Uruchomienia w toku są generowane deterministycznie (ziarno 42) i mają czasy
zapisane **względem chwili wejścia do aplikacji**, a nie względem daty
generowania. Dzięki temu demonstracja o dowolnej porze wygląda jak dyżur
w trakcie, a zegary kroków odliczają realnie.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[3]
DATA = BASE / "datasets"
DERIVED = DATA / "derived"
OUT = Path(__file__).resolve().parents[1] / "public" / "data" / "scene.json"

SEED = 42
# Poniżej tego progu asystent nie wskazuje jednej procedury, tylko listę kandydatek.
CONFIDENCE_THRESHOLD = 0.45


def rounded(x: float, n: int = 4) -> float:
    return float(np.round(float(x), n))


def load_frames() -> dict[str, pd.DataFrame]:
    frames = {
        "procedures": pd.read_csv(DATA / "dim_procedure.csv"),
        "steps": pd.read_csv(DATA / "dim_step.csv"),
        "roles": pd.read_csv(DATA / "dim_role.csv"),
        "hazards": pd.read_csv(DATA / "dim_hazard.csv"),
        "documents": pd.read_csv(DATA / "dim_document.csv"),
        "chunks": pd.read_json(DATA / "corpus_chunks.jsonl", lines=True),
        "eval_questions": pd.read_csv(DATA / "eval_questions.csv"),
        "sla_procedure": pd.read_csv(DERIVED / "sla_by_procedure.csv"),
        "worst_steps": pd.read_csv(DERIVED / "sla_worst_steps.csv"),
        "blockers": pd.read_csv(DERIVED / "recurring_blockers.csv"),
        "first_critical": pd.read_csv(DERIVED / "time_to_first_critical_step.csv"),
        "usage": pd.read_csv(DERIVED / "assistant_usage_by_role.csv"),
    }
    # Puste komórki tekstowe wracają z pandas jako NaN, a `json.dumps` zapisuje
    # je jako literał `NaN`, którego `JSON.parse` w przeglądarce nie przyjmuje.
    # Scena bez tej zamiany nie wczyta się w aplikacji w ogóle.
    # Warunek jest na „nie-liczbowa", a nie na `object`: pandas zwraca kolumny
    # tekstowe raz jako `object`, raz jako `str`, a kolumnę pustą w całości
    # jako `float64`.
    for df in frames.values():
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]) or df[col].isna().all():
                df[col] = df[col].astype(object).where(df[col].notna(), "")
    return frames


def build_index() -> dict:
    """Przenosi indeks TF-IDF do postaci rzadkiej nadającej się do JSON.

    Macierz 513x1816 ma tylko ok. 33 tys. wartości niezerowych, więc zapis
    gęsty byłby 28 razy większy bez żadnego zysku.
    """
    blob = np.load(DERIVED / "vector_index.npz")
    vocab: dict[str, int] = json.loads((DERIVED / "vector_vocab.json").read_text(encoding="utf-8"))
    matrix = blob["matrix"]
    idf = blob["idf"]

    terms = [""] * len(vocab)
    for term, j in vocab.items():
        terms[j] = term

    rows = []
    for i in range(matrix.shape[0]):
        nz = np.nonzero(matrix[i])[0]
        rows.append([[int(j), rounded(matrix[i, j], 5)] for j in nz])

    return {
        "terms": terms,
        "idf": [rounded(v, 5) for v in idf.tolist()],
        "rows": rows,
        "nonZero": int(sum(len(r) for r in rows)),
    }


def build_procedures(f: dict[str, pd.DataFrame]) -> list[dict]:
    hazard_name = dict(zip(f["hazards"].hazard_code, f["hazards"].hazard_name))
    sla = f["sla_procedure"].set_index("procedure_code")
    ttfc = f["first_critical"].set_index("procedure_code")["time_to_first_critical_min"].to_dict()
    out = []
    for p in f["procedures"].itertuples():
        steps = f["steps"][f["steps"].procedure_code == p.procedure_code].sort_values("step_no")
        row = sla.loc[p.procedure_code] if p.procedure_code in sla.index else None
        out.append({
            "id": p.procedure_id,
            "code": p.procedure_code,
            "name": p.procedure_name,
            "ownerRole": p.owner_role,
            "ownerInstitution": p.owner_institution,
            "phase": p.phase,
            "legalBasis": p.legal_basis,
            "hazards": [{"code": h, "name": hazard_name.get(h, "")}
                        for h in str(p.hazard_codes).split("|") if h],
            "keywords": [k for k in str(p.keywords).split("|") if k],
            "totalSlaMinutes": int(p.total_sla_minutes),
            "criticalStepCount": int(p.critical_step_count),
            "history": None if row is None else {
                "activations": int(row.uruchomienia),
                "stepExecutions": int(row.wykonania_krokow),
                "slaCompliancePct": rounded(row.sla_compliance_pct, 1),
                "medianMinutes": rounded(row.mediana_czasu_min, 1),
                "blocked": int(row.blokady),
                "timeToFirstCriticalMin": rounded(ttfc.get(p.procedure_code, 0), 1),
            },
            "steps": [{
                "stepId": s.step_id,
                "stepNo": int(s.step_no),
                "title": s.step_title,
                "roleCode": s.role_code,
                "roleName": s.role_name,
                "institution": s.institution,
                "slaMinutes": int(s.sla_minutes),
                "outputDocument": s.output_document,
                "critical": bool(s.is_critical),
            } for s in steps.itertuples()],
        })
    return out


def build_worst_steps(f: dict[str, pd.DataFrame]) -> list[dict]:
    return [{
        "procedureCode": r.procedure_code,
        "stepNo": int(r.step_no),
        "title": r.step_title,
        "roleCode": r.role_code,
        "executions": int(r.wykonania),
        "slaCompliancePct": rounded(r.sla_compliance * 100, 1),
        "medianMinutes": rounded(r.mediana_czasu_min, 1),
        "slaMinutes": int(r.sla_minutes),
        "breachPct": rounded(r.przekroczenie_pct, 1),
        "ratioToNorm": rounded(r.stosunek_do_normy, 2),
    } for r in f["worst_steps"].itertuples()]


def build_activations(f: dict[str, pd.DataFrame], procedures: list[dict]) -> list[dict]:
    """Uruchomienia w toku — materiał dla ekranów „Moje zadania" i „Po zdarzeniu".

    Historia w zbiorach zawiera wyłącznie uruchomienia zamknięte, a aplikacja
    operatorska bez ani jednego otwartego uruchomienia nie ma czego pokazać.
    Statusy kroków wynikają z upływu czasu od startu, a nie z losowania — dzięki
    temu obraz jest spójny: krok „w toku" to ten, do którego doszła realizacja.
    """
    rng = random.Random(SEED)
    by_code = {p["code"]: p for p in procedures}
    blockers = f["blockers"].blocker_reason.tolist()

    plan = [
        ("SPO-3", "Powódź wrześniowa — komunikacja z ludnością", "Z07", "krajowy", "02", "dolnośląskie",
         "Fałszywa informacja o przerwaniu wału w mediach społecznościowych", 205),
        ("SPO-10", "Powódź wrześniowa — infrastruktura krytyczna", "Z07", "krajowy", "02", "dolnośląskie",
         "Zalanie stacji GPZ i ujęcia wody w zlewni Nysy Kłodzkiej", 340),
        ("SPO-6", "Powódź wrześniowa — ewakuacja", "Z07", "wojewódzki", "16", "opolskie",
         "Zarządzenie ewakuacji dwóch gmin nadrzecznych", 140),
        ("SPO-1", "Powódź wrześniowa — posiedzenie RZZK", "Z07", "krajowy", "", "",
         "Wniosek ministra o zwołanie posiedzenia w trybie pilnym", 95),
        ("SPO-12", "Powódź wrześniowa — obieg meldunków", "Z07", "krajowy", "", "",
         "Uruchomienie wzmożonego obiegu meldunków dobowych", 480),
        ("SPO-8", "Skażenie chemiczne — zakład w Kędzierzynie", "Z13", "wojewódzki", "16", "opolskie",
         "Wyciek amoniaku z instalacji chłodniczej", 65),
    ]

    out = []
    for n, (code, event, hazard, level, voiv_code, voiv_name, trigger, age_min) in enumerate(plan, 1):
        proc = by_code[code]
        steps_out, decisions = [], []
        cursor = -age_min  # minuty względem chwili wejścia; ujemne = przeszłość
        blocked_used = False

        for s in proc["steps"]:
            sla = s["slaMinutes"]
            # Realizacja jest nieco szybsza lub wolniejsza od normy; rozrzut daje
            # naturalny obraz opóźnień bez ręcznego ustawiania każdego kroku.
            factor = rng.uniform(0.55, 1.45)
            duration = max(5, round(sla * factor))
            start = cursor + rng.randint(1, max(2, round(sla * 0.15)))
            end = start + duration

            if end < 0:
                status = "wykonany"
                steps_out.append({**s, "status": status, "startedOffsetMin": start,
                                  "completedOffsetMin": end, "blockerReason": ""})
                cursor = end
                if s["critical"] and rng.random() < 0.55:
                    decisions.append({
                        "decisionId": f"DEC-L{n}{s['stepNo']:02d}",
                        "offsetMin": end,
                        "stepNo": s["stepNo"],
                        "decisionType": rng.choice([
                            "zatwierdzenie komunikatu", "skierowanie sił i środków",
                            "uruchomienie środków", "eskalacja poziomu"]),
                        "decidedByRole": s["roleCode"],
                        "decidedByName": s["institution"],
                        "subject": f"{code} krok {s['stepNo']}: {s['title']}",
                        "rationale": (f"Krok {s['stepNo']} zakończony; ustalenia przekazane do "
                                      f"realizacji w ramach zdarzenia \u201e{event}\u201d."),
                        "classification": "zastrzeżone" if rng.random() < 0.25 else "jawne",
                    })
                continue

            if start < 0:
                if not blocked_used and rng.random() < 0.45:
                    blocked_used = True
                    status, blocker = "zablokowany", rng.choice(blockers)
                else:
                    status, blocker = "w toku", ""
                steps_out.append({**s, "status": status, "startedOffsetMin": start,
                                  "completedOffsetMin": None, "blockerReason": blocker})
                cursor = start
            else:
                steps_out.append({**s, "status": "oczekuje", "startedOffsetMin": None,
                                  "completedOffsetMin": None, "blockerReason": ""})
                cursor = start

        first = proc["steps"][0]
        decisions.insert(0, {
            "decisionId": f"DEC-L{n}00",
            "offsetMin": -age_min,
            "stepNo": 0,
            "decisionType": "uruchomienie procedury",
            "decidedByRole": proc["ownerRole"],
            "decidedByName": proc["ownerInstitution"],
            "subject": f"Uruchomienie {code} — {event}",
            "rationale": trigger,
            "classification": "jawne",
        })

        out.append({
            "activationId": f"ACT-L{n:02d}",
            "procedureCode": code,
            "procedureName": proc["name"],
            "eventName": event,
            "hazardCode": hazard,
            "level": level,
            "voivodeshipCode": voiv_code,
            "voivodeshipName": voiv_name,
            "initiatedByRole": proc["ownerRole"],
            "initiatedByInstitution": proc["ownerInstitution"],
            "triggerText": trigger,
            "startedOffsetMin": -age_min,
            "ownerRoleCode": proc["ownerRole"],
            "firstStepRole": first["roleCode"],
            "steps": steps_out,
            "decisions": sorted(decisions, key=lambda d: d["offsetMin"]),
        })
    return out


def main() -> int:
    f = load_frames()
    procedures = build_procedures(f)
    chunks = f["chunks"]

    scene = {
        "meta": {
            "scenario": "POWÓDŹ WRZESIEŃ",
            "title": "Asystent SPO — procedury i dziennik decyzji",
            "confidenceThreshold": CONFIDENCE_THRESHOLD,
            "seed": SEED,
            "counts": {
                "procedures": len(procedures),
                "steps": int(len(f["steps"])),
                "roles": int(len(f["roles"])),
                "hazards": int(len(f["hazards"])),
                "documents": int(len(f["documents"])),
                "chunks": int(len(chunks)),
            },
            "summary": json.loads((DERIVED / "step_analytics_summary.json").read_text(encoding="utf-8")),
            "retrieval": json.loads((DERIVED / "retrieval_eval.json").read_text(encoding="utf-8")),
            "index": json.loads((DERIVED / "vector_index_summary.json").read_text(encoding="utf-8")),
        },
        "procedures": procedures,
        "roles": [{"code": r.role_code, "name": r.role_name, "institution": r.institution,
                   "level": r.level} for r in f["roles"].itertuples()],
        "hazards": [{"code": h.hazard_code, "name": h.hazard_name, "risk": h.risk_matrix}
                    for h in f["hazards"].itertuples()],
        "chunks": [{
            "id": c.chunk_id,
            "documentId": c.document_id,
            "docType": c.doc_type,
            "docTitle": c.doc_title,
            "procedureCode": "" if pd.isna(c.procedure_code) else str(c.procedure_code),
            "section": c.section,
            "title": c.chunk_title,
            "text": c.text,
        } for c in chunks.itertuples()],
        "index": build_index(),
        "analytics": {
            "slaByProcedure": [{
                "procedureCode": r.procedure_code,
                "procedureName": r.procedure_name,
                "phase": r.phase,
                "activations": int(r.uruchomienia),
                "stepExecutions": int(r.wykonania_krokow),
                "slaCompliancePct": rounded(r.sla_compliance_pct, 1),
                "medianMinutes": rounded(r.mediana_czasu_min, 1),
                "blocked": int(r.blokady),
            } for r in f["sla_procedure"].itertuples()],
            "worstSteps": build_worst_steps(f),
            "blockers": [{
                "reason": r.blocker_reason,
                "occurrences": int(r.wystapienia),
                "procedures": int(r.procedury),
                "years": int(r.lata),
                "first": str(r.pierwsze),
                "last": str(r.ostatnie),
            } for r in f["blockers"].itertuples()],
            "usageByRole": [{
                "role": r.user_role,
                "questions": int(r.pytania),
                "accuracy": rounded(r.trafnosc, 4),
                "medianLatencyMs": int(r.mediana_latencji_ms),
                "meanConfidence": rounded(r.srednia_pewnosc, 4),
            } for r in f["usage"].itertuples()],
        },
        "sampleQuestions": [{
            "id": q.question_id,
            "question": q.question,
            "expected": q.expected_procedure,
        } for q in f["eval_questions"].itertuples()],
        "liveActivations": build_activations(f, procedures),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    # `allow_nan=False` jest tu zaporą, nie ozdobą: NaN w JSON-ie przechodzi
    # przez pandas i Pythona, a wywraca się dopiero w przeglądarce.
    OUT.write_text(
        json.dumps(scene, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
        encoding="utf-8",
    )
    size = OUT.stat().st_size
    print(f"zapisano {OUT} ({size / 1_048_576:.2f} MB)")
    print(f"  procedury {len(procedures)} · kroki {scene['meta']['counts']['steps']}"
          f" · fragmenty {len(scene['chunks'])} · termy {len(scene['index']['terms'])}"
          f" · wartości niezerowe {scene['index']['nonZero']}")
    print(f"  uruchomienia w toku {len(scene['liveActivations'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
