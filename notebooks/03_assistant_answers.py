# CELL
# 03 - silnik odpowiedzi asystenta: pytanie -> procedura -> checklista -> cytowania
# Odpowiedz nigdy nie jest generowana "z glowy modelu": powstaje z rekordow procedury
# i zawsze niesie cytowania (chunk_id), co daje slad audytowy wymagany w ZK.
import json
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from corpus.retriever import Retriever  # noqa: E402

DATA = BASE / "datasets"
OUT = DATA / "derived"
OUT.mkdir(exist_ok=True)

retriever = Retriever.load(DATA)
procedures = pd.read_csv(DATA / "dim_procedure.csv")
steps = pd.read_csv(DATA / "dim_step.csv")
roles = pd.read_csv(DATA / "dim_role.csv")
hazards = pd.read_csv(DATA / "dim_hazard.csv")
hazard_name = dict(zip(hazards.hazard_code, hazards.hazard_name))


# CELL
def minutes_label(minutes: float) -> str:
    if minutes < 60:
        return f"{minutes:.0f} min"
    if minutes < 1440:
        return f"{minutes / 60:.1f} h"
    return f"{minutes / 1440:.1f} doby"


def answer(question: str, top_k_alt: int = 2) -> dict:
    routing = retriever.route(question)
    hits = retriever.search(question, k=6)
    if not routing:
        return {"question": question, "status": "brak dopasowania", "citations": []}

    code, raw_score = routing[0]
    total = sum(s for _, s in routing) or 1.0
    confidence = round(raw_score / total, 3)
    proc = procedures[procedures.procedure_code == code].iloc[0]
    proc_steps = steps[steps.procedure_code == code].sort_values("step_no")

    checklist = [
        {
            "step_no": int(s.step_no),
            "title": s.step_title,
            "role": s.role_name,
            "institution": s.institution,
            "sla": minutes_label(s.sla_minutes),
            "sla_minutes": int(s.sla_minutes),
            "output_document": s.output_document if isinstance(s.output_document, str) else "",
            "critical": bool(s.is_critical),
        }
        for s in proc_steps.itertuples()
    ]
    contact_roles = sorted(set(proc_steps.role_code))
    contact_list = [
        {"role_code": r.role_code, "role_name": r.role_name, "institution": r.institution, "level": r.level}
        for r in roles[roles.role_code.isin(contact_roles)].itertuples()
    ]
    citations = [
        {"chunk_id": h.chunk_id, "document_id": h.document_id, "title": h.chunk_title, "score": float(h.score)}
        for h in hits.itertuples()
    ][:4]

    first_critical = proc_steps[proc_steps.is_critical == 1].head(1)
    return {
        "question": question,
        "procedure_code": code,
        "procedure_name": proc.procedure_name,
        "owner": f"{proc.owner_role} / {proc.owner_institution}",
        "phase": proc.phase,
        "legal_basis": proc.legal_basis,
        "hazards": [f"{h} {hazard_name.get(h, '')}".strip() for h in str(proc.hazard_codes).split("|")],
        "confidence": confidence,
        "alternatives": [{"procedure_code": c, "score": round(s, 4)} for c, s in routing[1:1 + top_k_alt]],
        "first_critical_step": None if first_critical.empty else {
            "step_no": int(first_critical.iloc[0].step_no),
            "title": first_critical.iloc[0].step_title,
            "sla": minutes_label(first_critical.iloc[0].sla_minutes),
        },
        "total_sla": minutes_label(int(proc.total_sla_minutes)),
        "steps_total": int(proc.step_count),
        "critical_steps": int(proc.critical_step_count),
        "checklist": checklist,
        "contact_list": contact_list,
        "documents": [c["output_document"] for c in checklist if c["output_document"]],
        "citations": citations,
        "status": "odpowiedz z cytowaniami",
    }


# CELL
evalset = pd.read_csv(DATA / "eval_questions.csv")
cards = [answer(q) for q in evalset.question]
(OUT / "answer_cards.json").write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

hit = sum(1 for c, e in zip(cards, evalset.expected_procedure) if c.get("procedure_code") == e)
print(f"kart odpowiedzi: {len(cards)}, trafien procedury: {hit}/{len(cards)}")

# CELL
# Karta odpowiedzi w formie, w jakiej widzi ja oficer dyzurny w Fabric App.
demo = cards[0]
lines = [
    f"# Odpowiedz asystenta SPO",
    "",
    f"**Pytanie:** {demo['question']}",
    "",
    f"**Właściwa procedura:** {demo['procedure_code']} - {demo['procedure_name']}",
    f"**Właściciel:** {demo['owner']} | **Faza:** {demo['phase']} | **Pewnosc routingu:** {demo['confidence']}",
    f"**Podstawa prawna:** {demo['legal_basis']}",
    f"**Zagrożenia:** {', '.join(demo['hazards'])}",
    "",
    f"**Pierwszy krok krytyczny:** {demo['first_critical_step']['title']} "
    f"(czas normatywny {demo['first_critical_step']['sla']})",
    "",
    "## Checklista",
    "",
    "| # | Krok | Odpowiedzialny | Czas | Dokument | Krytyczny |",
    "|---|---|---|---|---|---|",
]
for s in demo["checklist"]:
    lines.append(
        f"| {s['step_no']} | {s['title']} | {s['role']} | {s['sla']} | {s['output_document'] or '-'} | "
        f"{'tak' if s['critical'] else 'nie'} |"
    )
lines += ["", "## Lista kontaktowa", "", "| Rola | Instytucja | Poziom |", "|---|---|---|"]
for c in demo["contact_list"]:
    lines.append(f"| {c['role_name']} | {c['institution']} | {c['level']} |")
lines += ["", "## Źródła (cytowania)", ""]
for c in demo["citations"]:
    lines.append(f"- `{c['chunk_id']}` {c['title']} (dopasowanie {c['score']:.3f})")
lines += ["", "> Dane syntetyczne. Odpowiedz wygenerowana wyłącznie z korpusu procedur demo."]
(OUT / "answer_card_example.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines[:18]))
