# Model semantyczny — SPO Copilot

> Dane syntetyczne, demo. Model przeznaczony dla warstwy decyzyjnej Power BI
> (raport gotowości procedur i lessons learned). Warstwa operacyjna działa
> bezpośrednio na Eventhouse (Real-Time Dashboard).

## Ziarno i tabele

| Tabela | Typ | Ziarno | Źródło |
|---|---|---|---|
| `dim_procedure` | wymiar | 1 wiersz = 1 procedura SPO | `datasets/dim_procedure.csv` |
| `dim_step` | wymiar | 1 wiersz = 1 krok procedury | `datasets/dim_step.csv` |
| `dim_role` | wymiar | 1 wiersz = 1 rola/komórka odpowiedzialna | `datasets/dim_role.csv` |
| `dim_hazard` | wymiar | 1 wiersz = 1 zagrożenie KPZK (Z01–Z20) | `datasets/dim_hazard.csv` |
| `dim_document` | wymiar | 1 wiersz = 1 dokument korpusu | `datasets/dim_document.csv` |
| `dim_date` | wymiar | 1 wiersz = 1 doba | wyliczany DAX (`CALENDAR`) |
| `fact_activation` | fakt | 1 wiersz = 1 uruchomienie procedury | `datasets/fact_activation.jsonl` |
| `fact_step_execution` | fakt | 1 wiersz = 1 wykonanie kroku | `datasets/fact_step_execution.jsonl` |
| `fact_decision_log` | fakt | 1 wiersz = 1 decyzja w dzienniku | `datasets/fact_decision_log.jsonl` |
| `fact_assistant_query` | fakt | 1 wiersz = 1 zapytanie do asystenta | `datasets/fact_assistant_query.jsonl` |
| `corpus_chunk` | pomocnicza | 1 wiersz = 1 fragment korpusu | `datasets/corpus_chunks.jsonl` |

## Relacje

```
dim_date[date]            1 --- * fact_activation[started_date]
dim_date[date]            1 --- * fact_step_execution[event_date]
dim_date[date]            1 --- * fact_decision_log[decided_date]
dim_date[date]            1 --- * fact_assistant_query[asked_date]

dim_procedure[procedure_code] 1 --- * fact_activation[procedure_code]
dim_procedure[procedure_code] 1 --- * fact_step_execution[procedure_code]
dim_procedure[procedure_code] 1 --- * fact_decision_log[procedure_code]
dim_procedure[procedure_code] 1 --- * dim_step[procedure_code]
dim_procedure[procedure_code] 1 --- * dim_document[procedure_code]   (dla doc_type = "spo")

dim_step[step_id]         1 --- * fact_step_execution[step_id]
dim_role[role_code]       1 --- * fact_step_execution[role_code]
dim_role[role_code]       1 --- * dim_step[role_code]
dim_hazard[hazard_code]   1 --- * fact_activation[hazard_code]

fact_activation[activation_id] 1 --- * fact_step_execution[activation_id]
fact_activation[activation_id] 1 --- * fact_decision_log[activation_id]
```

Kierunek filtrowania: jednokierunkowy od wymiarów do faktów. Wyjątek: relacja
`fact_activation` → `fact_step_execution` jest jednokierunkowa (aktywacja filtruje kroki),
co pozwala liczyć postęp checklisty w kontekście wybranego uruchomienia.

Zagrożenie `hazard_codes` w `dim_procedure` jest listą (`Z02|Z07|...`) — dla analizy
przekrojowej używamy mostka `bridge_procedure_hazard` generowanego w notatniku
`01_load_corpus` (rozbicie po `|`).

## Kolumny wyliczane (kluczowe)

| Tabela | Kolumna | Definicja |
|---|---|---|
| `fact_step_execution` | `overdue_minutes` | `elapsed_minutes - sla_minutes` (dodatnie = po terminie) |
| `fact_step_execution` | `sla_bucket` | `w normie` / `do 2x normy` / `powyżej 2x normy` |
| `fact_activation` | `is_flood_scenario` | `event_name = "POWODZ WRZESIEN"` |
| `fact_activation` | `duration_hours` | `duration_minutes / 60` |
| `dim_procedure` | `sla_path_hours` | `total_sla_minutes / 60` |

## Etykiety wrażliwości

- `fact_decision_log` zawiera kolumnę `classification` (`jawne`, `zastrzeżone`, `poufne`).
  W raporcie stosujemy RLS: role `Analityk` widzi wyłącznie `jawne`, rola `RCB` — wszystko.
- W realnym wdrożeniu tabela dziennika decyzji powinna mieć etykietę wrażliwości Purview
  i pełny audyt dostępu; treść uzasadnień decyzji jest materiałem archiwalnym.
