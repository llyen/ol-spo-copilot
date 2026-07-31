# Model danych — SPO Copilot

> ⚠️ Wszystkie dane są **w 100% syntetyczne**, wygenerowane deterministycznie
> (`generate_datasets.py`, `seed=42`). Treści procedur odwzorowują *strukturę i logikę*
> Standardowych Procedur Operacyjnych z KPZK, ale **nie są dokumentacją operacyjną**
> żadnej instytucji i nie mogą być tak wykorzystywane.

Kodowanie: UTF-8. Separator CSV: `,`. Dziesiętny: `.`. Daty: ISO-8601 z offsetem `+02:00`.
Nazwy tabel i kolumn: angielskie, bez znaków diakrytycznych. Treść dokumentów: polska.

## Spis tabel

| Plik | Typ | Wierszy | Ziarno |
|---|---|---|---|
| `dim_role.csv` | wymiar | 22 | 1 rola / komórka odpowiedzialna |
| `dim_hazard.csv` | wymiar | 20 | 1 zagrożenie KPZK (Z01–Z20) |
| `dim_procedure.csv` | wymiar | 16 | 1 Standardowa Procedura Operacyjna |
| `dim_step.csv` | wymiar | 155 | 1 krok procedury |
| `dim_document.csv` | wymiar | 49 | 1 dokument korpusu |
| `eval_questions.csv` | referencyjna | 32 | 1 pytanie kontrolne |
| `corpus_chunks.jsonl` | korpus | 513 | 1 fragment dokumentu (chunk) |
| `fact_activation.jsonl` | fakt | 986 | 1 uruchomienie procedury |
| `fact_step_execution.jsonl` | fakt / strumień | 9 420 | 1 wykonanie kroku |
| `fact_decision_log.jsonl` | fakt / strumień | 2 002 | 1 wpis w dzienniku decyzji |
| `fact_assistant_query.jsonl` | fakt / strumień | 4 200 | 1 zapytanie do asystenta |
| `record_counts.json` | metadane | — | liczności wszystkich zbiorów |

Zakres czasu: historia operacyjna **2023-01-02 … 2026-09-11** (960 uruchomień) oraz
scenariusz osiowy **POWÓDŹ WRZESIEŃ**, D-3 … D+10 wokół `D0 = 2026-09-15 06:00+02:00`
(26 uruchomień).

---

## 1. `dim_role.csv`

| Kolumna | Typ | Opis |
|---|---|---|
| `role_code` | string | klucz główny, np. `R_DYZ_RCB` |
| `role_name` | string | nazwa roli, np. „Oficer dyzurny RCB" |
| `institution` | string | instytucja, w której rola występuje |
| `level` | string | `krajowy`, `wojewodzki`, `powiatowy`, `gminny`, `operatorski` |

## 2. `dim_hazard.csv`

| Kolumna | Typ | Opis |
|---|---|---|
| `hazard_code` | string | `Z01`…`Z20` (kanoniczna lista KPZK) |
| `hazard_name` | string | nazwa zagrożenia |
| `risk_matrix` | string | pozycja w matrycy ryzyka (prawdopodobieństwo; skutki) |

## 3. `dim_procedure.csv`

| Kolumna | Typ | Opis |
|---|---|---|
| `procedure_id` | string | `P001`…`P016` |
| `procedure_code` | string | `SPO-1`…`SPO-16` — klucz biznesowy |
| `procedure_name` | string | pełna nazwa procedury |
| `owner_role` | string | FK → `dim_role.role_code` |
| `owner_institution` | string | instytucja właściciela |
| `phase` | string | faza ZK: `zapobieganie`, `przygotowanie`, `reagowanie`, `odbudowa` |
| `hazard_codes` | string | lista zagrożeń rozdzielona `\|`, np. `Z02\|Z07` |
| `legal_basis` | string | podstawa prawna (syntetyczna, uproszczona) |
| `step_count` | int | liczba kroków |
| `total_sla_minutes` | int | suma czasów normatywnych ścieżki |
| `critical_step_count` | int | liczba kroków krytycznych |
| `keywords` | string | słowa kluczowe rozdzielone `\|` (wsparcie routingu) |

## 4. `dim_step.csv`

| Kolumna | Typ | Opis |
|---|---|---|
| `step_id` | string | `SPO-15-03` — klucz główny |
| `procedure_code` | string | FK → `dim_procedure` |
| `step_no` | int | numer kroku w procedurze |
| `step_title` | string | treść kroku |
| `role_code` | string | FK → `dim_role` |
| `role_name`, `institution` | string | denormalizacja dla wygody raportów |
| `sla_minutes` | int | czas normatywny liczony od uruchomienia procedury |
| `output_document` | string | dokument wytwarzany przez krok (pusty = brak) |
| `is_critical` | int (0/1) | krok krytyczny blokuje kolejne etapy |

## 5. `dim_document.csv`

| Kolumna | Typ | Opis |
|---|---|---|
| `document_id` | string | `DOC-SPO-1`, `DOC-WZK-02`, `DOC-OL-16`, `DOC-KPZK` |
| `doc_type` | string | `spo` (16), `plan_wojewodzki` (16), `plan_ol` (16), `kpzk` (1) |
| `title` | string | tytuł dokumentu |
| `procedure_code` | string | wypełnione tylko dla `doc_type = spo` |
| `voivodeship_code` | string | TERYT województwa dla planów wojewódzkich i OL |
| `owner_institution` | string | dysponent dokumentu |
| `section_count`, `chunk_count`, `char_count` | int | metryki objętości |

## 6. `corpus_chunks.jsonl`

Jednostka wyszukiwania. Rozmiar fragmentu dobrany tak, by jedna odpowiedź asystenta
mieściła się w 3–4 cytowaniach (średnio 387 znaków, łącznie ok. 199 tys. znaków).

| Kolumna | Typ | Opis |
|---|---|---|
| `chunk_id` | string | `C00001`… — identyfikator cytowania |
| `document_id` | string | FK → `dim_document` |
| `doc_type` | string | jak wyżej |
| `procedure_code` | string | pusty dla planów i KPZK (routing wtedy przez wzmianki `SPO-n` w treści) |
| `section` | string | sekcja dokumentu, np. `5. Przebieg - kroki` |
| `chunk_title` | string | tytuł fragmentu (w indeksie liczony z podwójną wagą) |
| `text` | string | treść fragmentu |
| `hazard_codes` | string | lista `Z..` rozdzielona `\|` |
| `role_codes` | string | lista ról rozdzielona `\|` |
| `char_count` | int | długość tekstu |
| `doc_title` | string | tytuł dokumentu nadrzędnego (używany przez retriever) |

Struktura sekcji dokumentu SPO: `1. Cel`, `2. Podstawa prawna`, `3. Przesłanki uruchomienia`,
`4. Uczestnicy i odpowiedzialności`, `5. Przebieg – kroki` (osobny fragment na każdy krok),
`6. Dokumenty wytwarzane`, `7. Wskaźniki i czasy normatywne`, `8. Powiązania`.

## 7. `fact_activation.jsonl`

| Kolumna | Typ | Opis |
|---|---|---|
| `activation_id` | string | `ACT-00001`… |
| `procedure_code`, `procedure_name` | string | uruchomiona procedura |
| `event_name` | string | `historia operacyjna` albo `POWODZ WRZESIEN` |
| `hazard_code` | string | zagrożenie, w którego kontekście uruchomiono procedurę |
| `level` | string | poziom reagowania |
| `voivodeship_code`, `voivodeship_name` | string | województwo |
| `initiated_by_role`, `initiated_by_institution` | string | kto uruchomił |
| `trigger_text` | string | przesłanka uruchomienia (z korpusu procedury) |
| `started_at`, `closed_at` | datetime | ramy czasowe |
| `duration_minutes` | float | czas trwania |
| `steps_total`, `steps_completed`, `steps_blocked`, `steps_sla_breached` | int | przebieg |
| `sla_compliance_pct` | float | odsetek kroków w czasie normatywnym |
| `status` | string | `zamkniete` |
| `event_time` | datetime | znacznik dla Eventstream (= `started_at`) |

## 8. `fact_step_execution.jsonl` (strumień główny)

| Kolumna | Typ | Opis |
|---|---|---|
| `execution_id` | string | `EXE-000001`… |
| `activation_id` | string | FK → `fact_activation` |
| `procedure_code`, `step_id`, `step_no`, `step_title` | — | FK → `dim_step` |
| `role_code`, `institution`, `level`, `voivodeship_code` | string | kontekst wykonania |
| `event_name` | string | zdarzenie nadrzędne |
| `planned_start` | datetime | moment, od którego liczony jest czas normatywny |
| `started_at`, `completed_at` | datetime | faktyczna realizacja |
| `sla_minutes` | int | norma z `dim_step` |
| `elapsed_minutes` | float | `completed_at - planned_start` |
| `sla_met` | int (0/1) | `elapsed_minutes <= sla_minutes` i krok nie jest zablokowany |
| `is_critical` | int (0/1) | z `dim_step` |
| `status` | string | `wykonany`, `zablokowany`, `pominiety` |
| `blocker_reason` | string | przyczyna blokady (pusty, gdy brak) |
| `output_document` | string | wytworzony dokument |
| `event_time` | datetime | znacznik dla Eventstream (= `completed_at`) |

**Charakterystyka danych (świadomie wbudowana):**

- ogólne dotrzymanie czasów normatywnych ≈ **76,1%**, w scenariuszu powodziowym ≈ **70,5%**;
- pięć kroków ma wbudowaną chroniczną nieterminowość (m.in. `SPO-3` krok 4 — wersje językowe
  komunikatu, `SPO-10` krok 3 — kontakt z operatorem IK, `SPO-2` krok 3 — opinia merytoryczna);
- jedna przyczyna blokad dominuje przez cztery lata (nieaktualna lista punktów kontaktowych
  operatorów IK, **201 wystąpień**) — to materiał na wniosek systemowy, nie na alert operacyjny.

## 9. `fact_decision_log.jsonl`

| Kolumna | Typ | Opis |
|---|---|---|
| `decision_id` | string | `DEC-00001`… |
| `activation_id`, `procedure_code`, `step_no` | — | kontekst decyzji |
| `decided_at` | datetime | czas decyzji |
| `decision_type` | string | 8 typów (uruchomienie procedury, eskalacja, zatwierdzenie komunikatu, …) |
| `decided_by_role`, `decided_by_name` | string | decydent |
| `subject` | string | przedmiot decyzji |
| `rationale` | string | uzasadnienie (pole obowiązkowe w aplikacji) |
| `classification` | string | `jawne` (≈72%), `zastrzezone`, `poufne` |
| `event_time` | datetime | znacznik dla Eventstream |

## 10. `fact_assistant_query.jsonl`

| Kolumna | Typ | Opis |
|---|---|---|
| `query_id` | string | `Q-000001`… |
| `asked_at` | datetime | czas pytania |
| `user_role` | string | 8 ról użytkowników |
| `channel` | string | `Fabric App`, `Teams`, `Data Agent` |
| `question` | string | treść pytania |
| `expected_procedure` | string | procedura oczekiwana (etykieta) |
| `top_procedure` | string | procedura zwrócona przez asystenta |
| `confidence` | float | pewność routingu 0–1 |
| `is_correct` | int (0/1) | `top_procedure == expected_procedure` |
| `cited_chunk_ids` | string | lista `chunk_id` rozdzielona `\|` |
| `latency_ms` | int | czas odpowiedzi |
| `feedback` | string | `pomocne`, `brak oceny`, `niepomocne` |
| `event_time` | datetime | znacznik dla Eventstream |

## 11. `eval_questions.csv`

Zestaw kontrolny do pomiaru jakości routingu (32 pytania × oczekiwana procedura).
Uruchamiany notatnikiem `04_retrieval_eval.py` przy każdej zmianie korpusu.

---

## Zbiory pochodne (`datasets/derived/`)

| Plik | Zawartość |
|---|---|
| `vector_index.npz`, `vector_vocab.json`, `vector_index_manifest.csv` | indeks TF-IDF nad korpusem |
| `vector_index_summary.json` | metryki indeksu (fragmenty, słownik, rozmiar) |
| `answer_cards.json` | 32 pełne karty odpowiedzi asystenta (procedura + checklista + cytowania) |
| `answer_card_example.md` | jedna karta w formie prezentowanej w aplikacji |
| `retrieval_eval.json`, `retrieval_eval_per_question.csv` | wyniki ewaluacji routingu |
| `assistant_usage_by_role.csv`, `assistant_usage_summary.json` | telemetria użycia asystenta |
| `sla_by_procedure.csv`, `sla_worst_steps.csv` | dotrzymanie czasów normatywnych |
| `recurring_blockers.csv` | powtarzające się blokady (lessons learned) |
| `time_to_first_critical_step.csv` | czas reakcji per procedura |
| `step_analytics_summary.json` | zbiorcze metryki przebiegu |
| `bridge_procedure_hazard.csv` | mostek procedura ↔ zagrożenie |
| `dry_run_*.jsonl` | próbka strumienia z `simulate_realtime.py --dry-run` |

## Powtarzalność

`generate_datasets.py` ustawia `random.seed(42)` i `numpy.random.default_rng(42)`.
Ponowne uruchomienie generatora daje identyczne pliki, co pozwala odtworzyć każdą
liczbę użytą w dokumentacji i w scenariuszu demo.
