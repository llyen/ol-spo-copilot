# -*- coding: utf-8 -*-
"""Lekki retriever TF-IDF nad korpusem procedur (bez zaleznosci zewnetrznych poza numpy/pandas).

W Microsoft Fabric ten komponent zastepuje sie embeddingami (AI Functions / Azure OpenAI)
zapisanymi w tabeli Delta lub w Eventhouse. Logika routingu do procedury (agregacja wynikow
chunkow do poziomu SPO) pozostaje taka sama.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

STOPWORDS = {
    "i", "w", "z", "na", "do", "o", "sie", "nie", "the", "oraz", "lub", "ktore", "ktora", "ktory",
    "jest", "sa", "byc", "za", "od", "po", "przy", "przez", "dla", "jako", "tez", "ale", "co", "to",
    "ten", "ta", "te", "tym", "tego", "jej", "jego", "ich", "my", "wy", "on", "ona", "ono", "gdy",
    "jesli", "czy", "ze", "juz", "tak", "ma", "mamy", "moze", "mozna", "sposob", "raz", "bez",
}

SPO_PATTERN = re.compile(r"SPO-\d+")

# NFKD nie rozklada polskich liter przekreslonych - bez tej mapy "zaklocenie"
# i "zakłócenie" daja rozne tokeny, a pytanie pisane bez ogonkow nie trafia w korpus.
_TRANSLIT = str.maketrans({"ł": "l", "Ł": "L"})


def normalize(text: str) -> str:
    folded = str(text).translate(_TRANSLIT)
    return unicodedata.normalize("NFKD", folded).encode("ascii", "ignore").decode().lower()


def tokenize(text: str) -> list[str]:
    """Tokenizacja dwupoziomowa: pelny wyraz + prefiks 5-znakowy.

    Jezyk polski jest silnie fleksyjny ("punktow zbornych" / "punkty zborne"),
    a indeksowanie obu wariantow daje odpornosc na odmiane bez psucia precyzji
    (pelny wyraz nadal wnosi wlasna wage IDF).
    """
    out: list[str] = []
    for t in re.findall(r"[a-z0-9]+", normalize(text)):
        if len(t) <= 2 or t in STOPWORDS:
            continue
        out.append(t)
        if len(t) > 5:
            out.append(t[:5])
    return out


class Retriever:
    def __init__(self, chunks: pd.DataFrame, vocab: dict[str, int], idf: np.ndarray, matrix: np.ndarray):
        self.chunks = chunks.reset_index(drop=True)
        self.vocab = vocab
        self.idf = idf
        self.matrix = matrix
        # kody SPO wymienione w tresci chunku - pozwalaja routowac takze z kart KPZK i planow
        self.mentions = [sorted(set(SPO_PATTERN.findall(t))) for t in self.chunks["text"]]

    # --- budowa i zapis -----------------------------------------------------
    @classmethod
    def build(cls, chunks: pd.DataFrame) -> "Retriever":
        doc_title = chunks["doc_title"].astype(str) if "doc_title" in chunks.columns else ""
        search_text = (chunks["chunk_title"].astype(str) + " . " + chunks["chunk_title"].astype(str)
                       + " . " + doc_title + " . " + chunks["text"].astype(str))
        docs_tokens = [tokenize(t) for t in search_text]
        vocab: dict[str, int] = {}
        for toks in docs_tokens:
            for t in set(toks):
                vocab.setdefault(t, len(vocab))
        n_docs = len(docs_tokens)
        df_counts = np.zeros(len(vocab))
        tf = np.zeros((n_docs, len(vocab)), dtype=np.float32)
        for i, toks in enumerate(docs_tokens):
            for t, c in Counter(toks).items():
                j = vocab[t]
                tf[i, j] = 1.0 + np.log(c)
                df_counts[j] += 1
        idf = (np.log((1.0 + n_docs) / (1.0 + df_counts)) + 1.0).astype(np.float32)
        matrix = tf * idf
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return cls(chunks, vocab, idf, (matrix / norms).astype(np.float32))

    def save(self, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(out_dir / "vector_index.npz", matrix=self.matrix, idf=self.idf)
        (out_dir / "vector_vocab.json").write_text(json.dumps(self.vocab, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, data_dir: Path, derived_dir: Path | None = None) -> "Retriever":
        chunks = pd.read_json(Path(data_dir) / "corpus_chunks.jsonl", lines=True)
        derived = Path(derived_dir) if derived_dir else Path(data_dir) / "derived"
        blob = np.load(derived / "vector_index.npz")
        vocab = json.loads((derived / "vector_vocab.json").read_text(encoding="utf-8"))
        return cls(chunks, vocab, blob["idf"], blob["matrix"])

    # --- wyszukiwanie -------------------------------------------------------
    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(len(self.vocab), dtype=np.float32)
        for t, c in Counter(tokenize(text)).items():
            j = self.vocab.get(t)
            if j is not None:
                vec[j] = (1.0 + np.log(c)) * self.idf[j]
        n = float(np.linalg.norm(vec))
        return vec / n if n else vec

    def search(self, question: str, k: int = 6) -> pd.DataFrame:
        scores = self.matrix @ self.embed(question)
        top = np.argsort(-scores)[:k]
        res = self.chunks.iloc[top][
            ["chunk_id", "document_id", "doc_type", "procedure_code", "section", "chunk_title", "text"]
        ].copy()
        res["score"] = np.round(scores[top], 4)
        return res.reset_index(drop=True)

    def route(self, question: str, k: int = 12) -> list[tuple[str, float]]:
        """Agreguje wyniki chunkow do poziomu procedury.

        Chunk przypisany do SPO wnosi swoj wynik wprost; chunk z KPZK lub planu, ktory
        wymienia kod SPO, wnosi 45% wyniku (dziala jak wskaznik odsylajacy).
        """
        scores = self.matrix @ self.embed(question)
        top = np.argsort(-scores)[:k]
        agg: dict[str, float] = {}
        for rank, i in enumerate(top):
            s = float(scores[i])
            if s <= 0:
                continue
            decay = 1.0 / (1.0 + 0.25 * rank)
            code = self.chunks.iloc[i]["procedure_code"]
            if code:
                agg[code] = agg.get(code, 0.0) + s * decay
            for mentioned in self.mentions[i]:
                agg[mentioned] = agg.get(mentioned, 0.0) + s * decay * 0.45
        return sorted(agg.items(), key=lambda kv: -kv[1])
