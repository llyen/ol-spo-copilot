# Dane — SPO Copilot

> ⚠️ **Wszystkie pliki w tym katalogu są danymi syntetycznymi.** Powstały z generatora
> `generate_datasets.py` (`seed=42`). Treść procedur odwzorowuje strukturę Standardowych
> Procedur Operacyjnych z KPZK, ale nie jest dokumentacją operacyjną żadnej instytucji.
> Nazwy osób, numery kontaktowe i wartości wskaźników są fikcyjne.

Pełny słownik kolumn: [`../DATA_MODEL.md`](../DATA_MODEL.md).

## Wolumeny

| Plik | Format | Wierszy |
|---|---|---|
| `dim_role.csv` | CSV | 22 |
| `dim_hazard.csv` | CSV | 20 |
| `dim_procedure.csv` | CSV | 16 |
| `dim_step.csv` | CSV | 155 |
| `dim_document.csv` | CSV | 49 |
| `eval_questions.csv` | CSV | 32 |
| `corpus_chunks.jsonl` | JSONL | 513 |
| `fact_activation.jsonl` | JSONL | 986 |
| `fact_step_execution.jsonl` | JSONL | 9 420 |
| `fact_decision_log.jsonl` | JSONL | 2 002 |
| `fact_assistant_query.jsonl` | JSONL | 4 200 |
| `record_counts.json` | JSON | metadane |

Katalog `derived/` zawiera wyniki notatników: indeks TF-IDF, karty odpowiedzi,
wyniki ewaluacji routingu, analitykę czasów normatywnych i blokad oraz próbki
strumienia z `simulate_realtime.py --dry-run`.

## Zakres czasu

- historia operacyjna: **2023-01-02 … 2026-09-11** (960 uruchomień procedur),
- scenariusz osiowy **POWÓDŹ WRZESIEŃ**: `D0 = 2026-09-15 06:00+02:00`, okno D-3 … D+10
  (26 uruchomień), województwa dolnośląskie (02) i opolskie (16) na pierwszym planie.

## Regeneracja

```powershell
python generate_datasets.py
```

Generator jest deterministyczny — ponowne uruchomienie odtwarza identyczne pliki.
