# Wdrożenie w Microsoft Fabric — SPO Copilot

> ⚠️ Instrukcja dotyczy środowiska demonstracyjnego z danymi syntetycznymi.

Czas wdrożenia: ok. 60–75 minut. Wymagana pojemność Fabric (F2+ lub Trial)
oraz uprawnienia do tworzenia elementów w workspace.

## 0. Przygotowanie lokalne

```powershell
cd C:\repos\OchronaLudnosci\ol-spo-copilot
pip install -r requirements.txt
python generate_datasets.py
python notebooks\01_load_corpus.py
python notebooks\02_build_vector_index.py
python notebooks\03_assistant_answers.py
python notebooks\04_retrieval_eval.py
python notebooks\05_step_analytics.py
```

Skopiuj `config.example.json` → `config.json` i uzupełnij identyfikatory workspace,
Lakehouse oraz endpoint Eventstream. `config.json` i `.env` są w `.gitignore`.

## 1. Workspace

1. Utwórz workspace `OL - SPO Copilot`, przypisz pojemność Fabric.
2. Ustaw język i strefę czasową na polską (`Europe/Warsaw`) — dane mają offset `+02:00`.

## 2. Lakehouse

1. Nowy Lakehouse: **`spo_copilot_lh`**.
2. Wgraj do `Files/raw`:
   - `datasets/dim_*.csv`, `datasets/eval_questions.csv`
   - `datasets/corpus_chunks.jsonl`
   - `datasets/fact_*.jsonl` (ładunek historyczny)
3. Wgraj do `Files/derived` zawartość `datasets/derived/`
   (indeks TF-IDF, karty odpowiedzi, wyniki analityki).

## 3. Notatniki

1. Zaimportuj pliki z `notebooks/` jako notatniki Fabric.
   Pliki mają znaczniki `# CELL` — dzielą się na komórki przy imporcie.
2. Przypnij `spo_copilot_lh` jako domyślny Lakehouse.
3. Uruchom kolejno `01` → `05`. Notatnik `01` tworzy tabele delta z plików raw
   oraz mostek `bridge_procedure_hazard`.
4. Oczekiwany wynik `04`: top-1 ≈ 0,906, top-3 ≈ 0,938, MRR ≈ 0,932.
   Rozbieżność oznacza, że korpus lub indeks nie są zsynchronizowane.

## 4. Eventhouse i baza KQL

1. Utwórz Eventhouse **`spo_copilot_eh`** z bazą **`spo_copilot_kql`**.
2. Uruchom w kolejności:
   - `kql/01_create_tables.kql` — tabele strumieniowe i mapowania ingest
   - `kql/02_update_policies.kql` — zasady aktualizacji i widoki materializowane
3. Sprawdź `kql/03_dashboard_queries.kql` — każde zapytanie powinno zwrócić wynik
   po pierwszym ingest (patrz krok 5).
4. `kql/05_corpus_search.kql` wymaga wgrania `corpus_chunks` do bazy KQL
   (jednorazowy ingest z pliku — służy do wyszukiwania pełnotekstowego w dashboardzie).

## 5. Eventstream

1. Utwórz Eventstream **`es-spo-copilot`**.
2. Źródło: **Custom endpoint** (Event Hub compatible). Skopiuj connection string
   do `config.json` (`eventstream.connection_string`).
3. Cztery destynacje w bazie KQL:

   | Strumień | Tabela docelowa |
   |---|---|
   | `activation` | `activation_stream` |
   | `step_execution` | `step_execution_stream` |
   | `decision_log` | `decision_log_stream` |
   | `assistant_query` | `assistant_query_stream` |

4. Test bez Fabric: `python simulate_realtime.py --dry-run`
   (zapisuje próbkę do `datasets/derived/dry_run_*.jsonl`).
5. Ingest na żywo: `python simulate_realtime.py --speed 60` (1 sekunda = 60 sekund demo).
   Zawężenie okna: `--from 2026-09-15T06:00 --to 2026-09-16T00:00`,
   pojedynczy strumień: `--stream step_execution`.

## 6. Model semantyczny

1. Z Lakehouse utwórz model semantyczny **`spo_copilot_sm`** (Direct Lake).
2. Dodaj tabele zgodnie z [`semantic-model/MODEL.md`](semantic-model/MODEL.md):
   wymiary + fakty + `bridge_procedure_hazard`.
3. Ustaw relacje i kierunki filtrowania dokładnie jak w `MODEL.md`
   (mostek `dim_procedure` ↔ `dim_hazard` ma filtrowanie dwukierunkowe).
4. Wklej 28 miar DAX z [`semantic-model/MEASURES.md`](semantic-model/MEASURES.md).
5. Oznacz `dim_date` jako tabelę dat (jeśli tworzysz ją po stronie modelu).

## 7. Raport

1. Zbuduj raport wg [`report/REPORT_SPEC.md`](report/REPORT_SPEC.md) — 6 stron:
   przegląd, procedura w szczegółach, dotrzymanie czasów, blokady i lessons learned,
   asystent (telemetria), dziennik decyzji.
2. Ustaw stronę startową na „Przegląd".
3. Wyłącz zbędne wizualizacje mapowe — w demo liczy się czas ładowania.

## 8. Activator

1. Utwórz element Activator na strumieniu `step_execution_stream`.
2. Zaimplementuj 9 reguł z [`activator/RULES.md`](activator/RULES.md) (`A1`–`A9`).
3. Na potrzeby demo włącz `A1` (przekroczenie normy na kroku krytycznym)
   i `A4` (blokada powtarzająca się w tym samym zdarzeniu) — reszta generuje szum.

## 9. Data Agent

1. Utwórz Data Agent **`spo-copilot-agent`**, podłącz `spo_copilot_sm`
   oraz bazę `spo_copilot_kql`.
2. Wklej instrukcję systemową z [`ai/DATA_AGENT.md`](ai/DATA_AGENT.md).
3. Przetestuj 24 pytania akceptacyjne z tego samego pliku — przed demo muszą przechodzić
   co najmniej te trzy z Aktu 5 scenariusza pokazu.

## 10. Fabric App

1. Utwórz aplikację wg [`fabric-app/APP_SPEC.md`](fabric-app/APP_SPEC.md).
2. Jeśli korzystasz z generatora UI, użyj promptu z
   [`fabric-app/RAYFIN_PROMPT.md`](fabric-app/RAYFIN_PROMPT.md).
3. Podłącz model semantyczny i Data Agenta.
4. Sprawdź trzy ekrany: pytanie → karta odpowiedzi → checklista z wpisem decyzji.

## Checklista przed demo

- [ ] Wszystkie tabele delta w Lakehouse mają oczekiwaną liczbę wierszy (`record_counts.json`)
- [ ] Notatnik `04` zwraca top-1 ≈ 0,906
- [ ] Zapytania z `kql/03` zwracają dane (nie pustki)
- [ ] Raport otwiera się w mniej niż 5 sekund
- [ ] Activator: co najmniej jeden alert wygenerowany w trakcie próbnego ingest
- [ ] Data Agent odpowiada na 3 pytania z Aktu 5
- [ ] Fabric App: pytanie o wał przeciwpowodziowy zwraca SPO-3
- [ ] Plan B przetestowany (`simulate_realtime.py --dry-run`)
## Rozwiązywanie problemów

| Objaw | Przyczyna | Rozwiązanie |
|---|---|---|
| `04` zwraca top-1 poniżej 0,85 | indeks zbudowany na starym korpusie | uruchom `02_build_vector_index.py` ponownie |
| Puste tabele strumieniowe | brak mapowania ingest | sprawdź nazwy mapowań z `kql/01_create_tables.kql` |
| Daty przesunięte o 2 h | strefa czasowa workspace | ustaw `Europe/Warsaw`, dane mają offset `+02:00` |
| Model semantyczny nie liczy miar per zagrożenie | brak dwukierunkowego filtrowania na mostku | popraw relację wg `MODEL.md` |
| Krzaczki w polskich tekstach | kodowanie przy uploadzie | wymuś UTF-8; korpus celowo nie zawiera znaków diakrytycznych |
