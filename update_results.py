"""Wstrzykuje aktualne liczby z datasets/derived do README.md i DEMO_SCRIPT.md."""

from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
DATA = BASE / "datasets"
OUT = DATA / "derived"


def load(name):
    p = OUT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def count_lines(p, header=False):
    with p.open(encoding="utf-8") as f:
        n = sum(1 for _ in f)
    return n - 1 if header else n


counts = {}
for p in sorted(DATA.glob("*.csv")):
    counts[p.name] = count_lines(p, True)
for p in sorted(DATA.glob("*.jsonl")):
    counts[p.name] = count_lines(p, False)

idx = load("vector_index_summary.json")
ev = load("retrieval_eval.json")
usage = load("assistant_usage_summary.json")
an = load("step_analytics_summary.json")


def pct(x):
    return f"{round(float(x) * 100, 1)}%" if x is not None else "n/d"


block = f"""- Korpus: {counts.get('dim_procedure.csv')} procedur SPO, {counts.get('dim_step.csv')} krokow, {counts.get('dim_document.csv')} dokumentow, {counts.get('corpus_chunks.jsonl')} fragmentow ({idx.get('corpus_chars')} znakow), slownik indeksu {idx.get('vocabulary_terms')} termow.
- Wymiary: {counts.get('dim_role.csv')} rol, {counts.get('dim_hazard.csv')} zagrozen, {counts.get('eval_questions.csv')} pytan kontrolnych.
- Zdarzenia: {counts.get('fact_activation.jsonl')} uruchomien procedur, {counts.get('fact_step_execution.jsonl')} wykonan krokow, {counts.get('fact_decision_log.jsonl')} wpisow w dzienniku decyzji, {counts.get('fact_assistant_query.jsonl')} zapytan do asystenta.
- Trafnosc routingu: top-1 {pct(ev.get('top1_accuracy'))}, top-3 {pct(ev.get('top3_accuracy'))}, MRR {ev.get('mrr')} na {ev.get('questions')} pytaniach ({len(ev.get('misses', []))} pudla).
- Telemetria asystenta: trafnosc {pct(usage.get('accuracy'))}, p50 {usage.get('p50_latency_ms')} ms, p95 {usage.get('p95_latency_ms')} ms, ocen "pomocne" {pct(usage.get('helpful_share'))}.
- Czasy normatywne: dotrzymanie {an.get('overall_sla_compliance_pct')}% ogolem, {an.get('flood_sla_compliance_pct')}% w scenariuszu powodziowym; najgorsza procedura {an.get('worst_procedure')} ({an.get('worst_procedure_sla_pct')}%).
- Najgorszy krok: {an.get('worst_step')} - {an.get('worst_step_breach_pct')}% wykonan po czasie ({an.get('worst_step_title')}).
- Najczestsza blokada: "{an.get('top_blocker')}" - {an.get('top_blocker_count')} wystapien w {an.get('top_blocker_years')} lata.
- Przebieg: mediana czasu do pierwszego kroku krytycznego {an.get('median_time_to_first_critical_min')} min, mediana trwania procedury {an.get('median_activation_duration_h')} h, decyzje niejawne {an.get('classified_decisions_pct')}%."""

for fname in ["README.md", "DEMO_SCRIPT.md"]:
    p = BASE / fname
    s = p.read_text(encoding="utf-8")
    start = "<!-- RESULTS_START -->"
    end = "<!-- RESULTS_END -->"
    if start not in s or end not in s:
        print(f"[pominieto] {fname}: brak znacznikow RESULTS_START/RESULTS_END")
        continue
    a = s.index(start) + len(start)
    b = s.index(end)
    p.write_text(s[:a] + "\n" + block + "\n" + s[b:], encoding="utf-8")
    print(f"[ok] {fname}")

print(block)
