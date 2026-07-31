# CELL
# 04 - ewaluacja jakosci routingu do procedury (top-1, top-3, MRR)
# Bez pomiaru jakosci asystent procedur jest nie do obrony w instytucji publicznej.
import json
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from corpus.retriever import Retriever  # noqa: E402

DATA = BASE / "datasets"
OUT = DATA / "derived"
retriever = Retriever.load(DATA)

# CELL
evalset = pd.read_csv(DATA / "eval_questions.csv")
rows = []
for r in evalset.itertuples():
    routing = retriever.route(r.question)
    codes = [c for c, _ in routing]
    rank = codes.index(r.expected_procedure) + 1 if r.expected_procedure in codes else 0
    rows.append({
        "question_id": r.question_id,
        "question": r.question,
        "expected_procedure": r.expected_procedure,
        "predicted_procedure": codes[0] if codes else "",
        "rank_of_expected": rank,
        "top1": int(rank == 1),
        "top3": int(1 <= rank <= 3),
        "reciprocal_rank": round(1.0 / rank, 4) if rank else 0.0,
        "top_score": round(routing[0][1], 4) if routing else 0.0,
    })
res = pd.DataFrame(rows)
res.to_csv(OUT / "retrieval_eval_per_question.csv", index=False)

summary = {
    "questions": int(len(res)),
    "top1_accuracy": round(float(res.top1.mean()), 4),
    "top3_accuracy": round(float(res.top3.mean()), 4),
    "mrr": round(float(res.reciprocal_rank.mean()), 4),
    "misses": res.loc[res.top1 == 0, ["question", "expected_procedure", "predicted_procedure"]].to_dict("records"),
}
(OUT / "retrieval_eval.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in summary.items() if k != "misses"}, indent=2))
print(f"pudla: {len(summary['misses'])}")

# CELL
# Telemetria realnego uzycia asystenta (symulowana) - skutecznosc wg roli i kanalu
queries = pd.read_json(DATA / "fact_assistant_query.jsonl", lines=True)
by_role = queries.groupby("user_role").agg(
    pytania=("query_id", "count"),
    trafnosc=("is_correct", "mean"),
    mediana_latencji_ms=("latency_ms", "median"),
    srednia_pewnosc=("confidence", "mean"),
).round(3).sort_values("pytania", ascending=False)
by_role.to_csv(OUT / "assistant_usage_by_role.csv")
print(by_role.to_string())

usage = {
    "queries": int(len(queries)),
    "accuracy": round(float(queries.is_correct.mean()), 4),
    "p50_latency_ms": int(queries.latency_ms.median()),
    "p95_latency_ms": int(queries.latency_ms.quantile(0.95)),
    "helpful_share": round(float((queries.feedback == "pomocne").mean()), 4),
    "unhelpful_share": round(float((queries.feedback == "niepomocne").mean()), 4),
    "top_channel": queries.channel.value_counts().idxmax(),
}
(OUT / "assistant_usage_summary.json").write_text(json.dumps(usage, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(usage, indent=2))
