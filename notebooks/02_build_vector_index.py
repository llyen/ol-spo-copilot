# CELL
# 02 - budowa indeksu wyszukiwania nad korpusem procedur
# Implementacja referencyjna: TF-IDF + podobienstwo kosinusowe (corpus/retriever.py).
# W Microsoft Fabric ten krok zastepuje sie embeddingami (AI Functions / Azure OpenAI)
# zapisanymi w tabeli Delta albo w Eventhouse; logika routingu do SPO pozostaje ta sama.
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

# CELL
chunks = pd.read_json(DATA / "corpus_chunks.jsonl", lines=True)
retriever = Retriever.build(chunks)
retriever.save(OUT)
chunks[["chunk_id", "document_id", "doc_type", "procedure_code", "section", "chunk_title", "char_count"]].to_csv(
    OUT / "vector_index_manifest.csv", index=False
)
print(f"chunkow: {len(chunks)}, terminow w slowniku: {len(retriever.vocab)}")

# CELL
demo_question = "Mamy skażenie chemiczne w porcie i wielu poszkodowanych. Co robimy?"
hits = retriever.search(demo_question, k=5)
routing = retriever.route(demo_question)
print(demo_question)
print(hits[["chunk_id", "procedure_code", "chunk_title", "score"]].to_string(index=False))
print("routing:", [(c, round(s, 3)) for c, s in routing[:3]])

# CELL
summary = {
    "chunks": int(len(chunks)),
    "vocabulary_terms": int(len(retriever.vocab)),
    "avg_chunk_chars": int(chunks.char_count.mean()),
    "corpus_chars": int(chunks.char_count.sum()),
    "index_bytes": int((OUT / "vector_index.npz").stat().st_size),
    "demo_question": demo_question,
    "demo_top_chunk": str(hits.iloc[0].chunk_id),
    "demo_top_procedure": routing[0][0],
    "demo_top_score": round(float(routing[0][1]), 4),
    "method": "TF-IDF (pełny wyraz + prefiks 5 znakow) + cosine, routing z agregacja chunk -> SPO",
}
(OUT / "vector_index_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=True, indent=2))
