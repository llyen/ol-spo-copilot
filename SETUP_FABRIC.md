# Wdrożenie w Microsoft Fabric — SPO Copilot

> ⚠️ Instrukcja dotyczy środowiska demonstracyjnego z danymi syntetycznymi.

Wdrożenie jest zautomatyzowane skryptami z katalogu [`fabric/`](fabric/README.md)
oraz [`deploy_fabric.py`](deploy_fabric.py) (REST API Fabric + `az` CLI). Czas: ok. 35–45 minut,
z czego większość to wykonanie notatników.
Wymagana pojemność Fabric (F2+ lub Trial) i uprawnienia do tworzenia elementów.

Wdrożenie referencyjne (stan zweryfikowany):

| Element | Nazwa |
|---|---|
| Workspace | `OL-ZK-Demo-SPO-Copilot` (pojemność `fcdemo`, F8) |
| Lakehouse | `OL_SPO_Lakehouse` |
| Eventhouse / baza KQL | `OL_SPO_Eventhouse` |
| Eventstream | `OL_SPO_Eventstream` |
| Model semantyczny | `OL_SPO_SemanticModel` (Direct Lake) |
| Raport | `OL_SPO_Raport` |
| Activator | `OL_SPO_Activator` |
| Data Agent | `OL_SPO_DataAgent` |

---

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

Oczekiwany wynik `04`: top-1 ≈ 0,906, top-3 ≈ 0,938, MRR ≈ 0,932.

Zaloguj się do Azure (`az login`) — skrypt wdrożeniowy pobiera tokeny przez `az account
get-access-token` dla trzech zasobów: `https://api.fabric.microsoft.com` (API Fabric),
`https://storage.azure.com` (OneLake) oraz URI klastra Kusto (polecenia KQL).

## 1. Workspace i elementy bazowe

W portalu Fabric utwórz workspace i przypisz pojemność, następnie utwórz Lakehouse
i Eventhouse (oba przez UI — kilka kliknięć, API nie daje tu przewagi).
Ustaw strefę czasową workspace na `Europe/Warsaw` — dane mają offset `+02:00`.

Skopiuj `config.example.json` → `config.json` i uzupełnij identyfikatory
(`workspace_id`, `lakehouse_id`, `eventhouse_id`, `kql_database`, `kql_cluster_uri`).
`config.json` jest w `.gitignore` — nie trafia do repozytorium.

## 2. Wdrożenie automatyczne

```powershell
python deploy_fabric.py --config config.json --step all
```

Kroki wykonywane przez skrypt:

| Krok | Co robi |
|---|---|
| `upload` | wgrywa `datasets/`, `datasets/derived/` i moduły `corpus/*.py` do OneLake (`Files/raw`, `Files/derived`, `Files/code/corpus`) |
| `notebooks` | konwertuje `notebooks/*.py` na `.ipynb`, przepisuje ścieżki na `/lakehouse/default/Files` i publikuje notatniki z przypiętym Lakehouse |
| `kql` | wykonuje `kql/01_create_tables.kql` i `kql/02_update_policies.kql` |
| `history` | jednorazowy ingest historii z OneLake (`kql/06_ingest_history.kql`) |

Pojedynczy krok: `--step upload` / `notebooks` / `kql` / `history`.

> **`--step history` nie jest idempotentny.** Ponowne uruchomienie zduplikuje dane.
> Przed powtórzeniem wyczyść tabele: `.clear table <nazwa> data` dla tabeli surowej
> i docelowej, a dopiero potem ponów ingest.

## 3. Uruchomienie notatników

W portalu uruchom kolejno `01` → `05` (albo przez API, `POST /items/{id}/jobs/instances?jobType=RunNotebook`).
Notatnik `01` tworzy 12 tabel Delta w Lakehouse, w tym mostek `bridge_procedure_hazard`.

Następnie uruchom **`06_semantic_prep`** — notatnik działa wyłącznie w Fabric.
Materializuje kolumny, których Direct Lake nie potrafi policzyć po stronie modelu
(kolumny wyliczane DAX są w tym trybie niedostępne):

- kolumny czasu: `started_ts`/`started_date`, `event_ts`/`event_date`/`completed_ts`,
  `decided_ts`/`decided_date`, `asked_ts`/`asked_date`
- kolumny wyliczane z `MODEL.md`: `overdue_minutes`, `sla_bucket`, `is_flood_scenario`,
  `duration_hours`, `sla_path_hours`
- wymiar czasu `dim_date` (polskie nazwy miesięcy i dni)

## 4. Eventstream

Topologia (jeden custom endpoint, cztery filtry, cztery destynacje Eventhouse):

```
spo_endpoint (CustomEndpoint) → spo_stream (DefaultStream)
   ├─ filter_activation      (_stream = "activation")      → activation_raw
   ├─ filter_step_execution  (_stream = "step_execution")  → step_execution_raw
   ├─ filter_decision_log    (_stream = "decision_log")    → decision_log_raw
   └─ filter_assistant_query (_stream = "assistant_query") → assistant_query_raw
```

Ograniczenia, na które trzeba uważać:

- w topologii może istnieć **tylko jeden** węzeł `DefaultStream`; cztery osobne źródła
  są odrzucane komunikatem *„There are more than one default stream in the topology"*;
- nazwy węzłów mogą zawierać wyłącznie litery, cyfry i podkreślenia (bez myślników);
- destynacja poprzedzona operatorem musi mieć `dataIngestionMode: ProcessedIngestion`
  (`DirectIngestion` kończy się błędem *„The given key was not present in the dictionary"*);
- po każdej zmianie definicji węzły przechodzą w stan `Creating` — kolejna aktualizacja
  przed ich ustabilizowaniem zostanie odrzucona (odczekaj 2–3 minuty).

`ProcessedIngestion` mapuje pola zdarzenia **po nazwach kolumn tabeli docelowej**.
Tabele `*_raw` mają jedną kolumnę `payload` typu `dynamic`, dlatego
`simulate_realtime.py` wysyła kopertę `{"_stream": "...", "payload": {...}}`.

Uruchomienie symulacji:

```powershell
$env:EVENTHUB_CONNECTION_STR = "<connection string custom endpointu>"
python simulate_realtime.py --dry-run                      # plan B, bez Fabric
python simulate_realtime.py --speed 60                     # 1 s = 60 s demo
python simulate_realtime.py --stream step_execution --limit 300
```

Connection string pobierzesz z UI Eventstreamu albo z API:
`GET /workspaces/{ws}/eventstreams/{es}/sources/{sourceId}/connection`.

Zdarzenia pojawiają się w tabelach docelowych po 1–3 minutach (batch ingestion).

## 5. Model semantyczny

Model `OL_SPO_SemanticModel` działa w trybie **Direct Lake** nad SQL analytics endpoint
Lakehouse’u i zawiera 13 tabel oraz 28 miar z [`semantic-model/MEASURES.md`](semantic-model/MEASURES.md)
w folderze `_Miary`.

```powershell
python fabric\get_schemas.py            # odczyt schematow tabel Delta
python fabric\create_semantic_model.py  # generacja TMDL i publikacja
```

Relacje ustawiono zgodnie z [`MODEL.md`](semantic-model/MODEL.md), z czterema
**nieaktywnymi** relacjami — silnik odrzuca model z niejednoznacznymi ścieżkami filtrowania:

| Relacja | Dlaczego nieaktywna |
|---|---|
| `fact_activation` → `fact_step_execution` | konflikt z `dim_date`/`dim_procedure` → `fact_step_execution` |
| `fact_activation` → `fact_decision_log` | jw. |
| `dim_procedure` → `fact_step_execution` | kroki filtrowane przez `dim_step` → `dim_procedure` |
| `dim_role` → `fact_step_execution` | kroki filtrowane przez `dim_step` → `dim_role` |

Filtrowanie po procedurze i roli działa poprzez `dim_step`; kontekst pojedynczego
uruchomienia uzyskujesz filtrem po `fact_step_execution[activation_id]`
albo funkcją `USERELATIONSHIP`.

Po każdej zmianie schematu tabel Delta odśwież metadane SQL endpointu, inaczej model
zgłosi *„Invalid object name"*:

```
POST /workspaces/{ws}/sqlEndpoints/{sqlEndpointId}/refreshMetadata?preview=true
```

Weryfikacja modelu (Power BI REST `executeQueries`, zasób
`https://analysis.windows.net/powerbi/api`):

| Miara | Wartość oczekiwana |
|---|---|
| `Uruchomienia procedur` | 986 |
| `Wykonania krokow` | 9 420 |
| `Dotrzymanie SLA %` | 76,1% |
| `Dotrzymanie SLA - powodz %` | 70,5% |
| `Trafnosc routingu %` | 93,5% |
| `Mediana / P95 czasu odpowiedzi` | 1 443 ms / 2 142 ms |
| `Czas do 1. kroku krytycznego (min)` | 19 |

## 6. Raport

Raport `OL_SPO_Raport` (format PBIR, 6 stron wg [`report/REPORT_SPEC.md`](report/REPORT_SPEC.md))
jest publikowany przez API na modelu semantycznym w trybie live connection:

```powershell
python fabric\create_report.py
```

Ciemny motyw operacyjny (`#1B1F23`) z akcentami: bursztyn `#F2A900` (przekroczenia),
czerwień `#D13438` (blokady), zieleń `#0F7B0F` (norma).

Pułapki formatu PBIR:

- `definition/version.json` wymaga wersji trzyczłonowej (`4.0.0`, nie `4.0`);
- `themeCollection.customTheme` wymaga pola `reportVersionAtImport`;
- `settings` nie akceptuje `useNewFilterPaneExperience`.

## 7. Real-Time Dashboard

Dashboard `OL_SPO_Dashboard` to warstwa operacyjna „tu i teraz" — działa bezpośrednio
na bazie KQL, bez pośrednictwa modelu semantycznego:

```powershell
python fabric\create_dashboard.py
```

14 kafelków wg [`kql/03_dashboard_queries.kql`](kql/03_dashboard_queries.kql), rozłożonych
na trzy strony, żeby żadna nie była przeładowana:

| Strona | Zawartość |
|---|---|
| Przebieg operacyjny | 4 kafelki KPI, postęp kroków w czasie, SLA wg procedury, checklista ostatniego uruchomienia, województwa |
| Wąskie gardła i blokady | kroki najczęściej po terminie, powtarzające się blokady, dziennik decyzji |
| Asystent i scenariusz osiowy | wolumen i trafność asystenta, najczęstsze pytania, przebieg POWODZI WRZESIEŃ |

Parametr `Zakres czasu` (`_startTime`/`_endTime`) obowiązuje na wszystkich stronach;
domyślnie 60 miesięcy, bo dane historyczne sięgają 2023 roku. Przy demo na żywo zawęź go
do godzin, żeby widzieć napływ zdarzeń z symulatora.

Kafelek „Checklista ostatniego uruchomienia" sam wybiera najświeższą aktywację
(`toscalar` + funkcja `ActivationProgress`) — nie wymaga parametru tekstowego.

Uwaga do formatu: identyfikatory kafelków, zapytań i stron są generowane
deterministycznie (`uuid5`), więc ponowne uruchomienie skryptu aktualizuje dashboard
w miejscu, zamiast rozsypywać układ.

**Fabric nie waliduje definicji dashboardu przy imporcie** — `updateDefinition`
zwraca `200` nawet dla pliku niezgodnego ze schematem, a błąd zobaczysz dopiero
przy otwieraniu w portalu. Dlatego skrypt sam waliduje definicję wobec oficjalnego
schematu ADX (`https://dataexplorer.azure.com/static/d/schema/52/dashboard.json`)
i przerywa przed wysyłką. Walidację można wyłączyć flagą `--skip-validate`.

Dwie pułapki, które kosztowały najwięcej czasu:

- Źródło danych musi mieć `kind` i `scopeId` równe **`kusto-trident`** (wariant
  Fabric), a `database` i `workspace` to **GUID-y elementów**, nie nazwy. Wariant
  `manual-kusto` przechodzi walidację schematu, ale portal odrzuca go komunikatem
  *„Detected bad id format in database property"*. GUID bazy skrypt pobiera sam
  z API, jeśli w `config.json` nie ma `kql_database_id`.
- Parametr `duration` przyjmuje wyłącznie `months`, `weeks`, `days`, `hours`,
  `minutes`. Wartość `years` unieważnia całą definicję parametru — stąd
  60 miesięcy zamiast 5 lat.

## 8. Activator

Element `OL_SPO_Activator` jest tworzony jako pusty (schemat `ReflexEntities.json`
nie jest udokumentowany — reguł nie da się dziś wiarygodnie wygenerować przez API).
Reguły konfiguruje się w UI na strumieniu `step_execution` Eventstreamu,
zgodnie z [`activator/RULES.md`](activator/RULES.md).

Na demo wystarczą **A1** (krok krytyczny po terminie) i **A4** (zdarzenie złożone
w województwie) — pozostałe reguły generują szum przy przyspieszonej symulacji.

## 9. Data Agent

Element `OL_SPO_DataAgent` również powstaje pusty; źródła danych i instrukcję systemową
dodaje się w UI:

1. Podłącz `OL_SPO_SemanticModel` oraz bazę KQL `OL_SPO_Eventhouse`.
2. Wklej instrukcję systemową z [`ai/DATA_AGENT.md`](ai/DATA_AGENT.md).
3. Przetestuj 24 pytania akceptacyjne — przed demo muszą przechodzić co najmniej
   te trzy z Aktu 5 scenariusza pokazu.

## 10. Fabric App

1. Utwórz aplikację wg [`fabric-app/APP_SPEC.md`](fabric-app/APP_SPEC.md).
2. Jeśli korzystasz z generatora UI, użyj promptu z
   [`fabric-app/RAYFIN_PROMPT.md`](fabric-app/RAYFIN_PROMPT.md).
3. Podłącz model semantyczny i Data Agenta.
4. Sprawdź trzy ekrany: pytanie → karta odpowiedzi → checklista z wpisem decyzji.

## Checklista przed demo

- [ ] Lakehouse: 12 tabel Delta + `dim_date` (po `06_semantic_prep`)
- [ ] Eventhouse: `activation` 986, `step_execution` 9 420, `decision_log` 2 002,
      `assistant_query` 4 200, `corpus_chunk` 513
- [ ] Notatnik `04` zwraca top-1 ≈ 0,906
- [ ] Zapytania z `kql/03` zwracają dane (nie pustki)
- [ ] Model semantyczny: wszystkie 28 miar liczy się bez błędu
- [ ] Raport otwiera się w mniej niż 5 sekund
- [ ] Dashboard: wszystkie 14 kafelków renderuje dane przy parametrze „ostatnie 5 lat"
- [ ] Activator: co najmniej jeden alert wygenerowany w trakcie próbnego ingest
- [ ] Data Agent odpowiada na 3 pytania z Aktu 5
- [ ] Fabric App: pytanie o wał przeciwpowodziowy zwraca SPO-3
- [ ] Plan B przetestowany (`simulate_realtime.py --dry-run`)

## Rozwiązywanie problemów

| Objaw | Przyczyna | Rozwiązanie |
|---|---|---|
| `04` zwraca top-1 poniżej 0,85 | indeks zbudowany na starym korpusie | uruchom `02_build_vector_index.py` ponownie |
| `.alter table ... policy retention` zwraca 400 | forma skrócona nie działa w Eventhouse | użyj formy JSON: `'{"SoftDeletePeriod":"365.00:00:00","Recoverability":"Enabled"}'` |
| Nie da się utworzyć czwartego widoku materializowanego | limit pojemności (F8: 1 równoległa operacja) | `AssistantQualityHourly` jest funkcją, nie MV; sprawdź `.show capacity` |
| `General_BadRequest` bez szczegółów w zapytaniu KQL | alias kolumny to nazwa zarezerwowana (np. `queries`) | zmień alias (w repozytorium: `query_count`) |
| Puste tabele strumieniowe | zdarzenia bez pola `payload` albo brak filtra `_stream` | sprawdź kopertę wysyłaną przez `simulate_realtime.py` |
| `Invalid object name` w modelu semantycznym | SQL endpoint nie zsynchronizował nowych tabel | wywołaj `sqlEndpoints/{id}/refreshMetadata` |
| `Failed to resolve name 'SYNTAXERROR'` po imporcie modelu | wielolinijkowe wyrażenie miary w TMDL na złym poziomie wcięcia | wyrażenie musi być wcięte **głębiej** niż właściwości miary |
| `There are ambiguous paths between ...` | dwie ścieżki filtrowania między tabelami | oznacz jedną relację jako nieaktywną (patrz rozdział 5) |
| Dashboard: „Detected bad id format in database property" | źródło danych typu `manual-kusto` z nazwą bazy zamiast wariantu Fabric | ustaw `kind`/`scopeId` na `kusto-trident`, `database` i `workspace` jako GUID-y |
| Dashboard nie otwiera się mimo `updateDefinition: 200` | definicja niezgodna ze schematem (Fabric nie waliduje przy imporcie) | uruchom `create_dashboard.py` bez `--skip-validate`; parametr `duration` przyjmuje tylko `months/weeks/days/hours/minutes` — `years` psuje cały plik |
| Kafelki dashboardu puste mimo danych w tabelach | parametr czasu obejmuje tylko ostatnie godziny | rozszerz `Zakres czasu` — dane historyczne sięgają 2023 roku |
| Daty przesunięte o 2 h | strefa czasowa workspace | ustaw `Europe/Warsaw`, dane mają offset `+02:00` |
| Krzaczki w polskich tekstach | kodowanie przy uploadzie | wymuś UTF-8; korpus celowo nie zawiera znaków diakrytycznych |
