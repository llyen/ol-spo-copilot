# Specyfikacja raportu Power BI — SPO Copilot

> Dane syntetyczne. Raport jest warstwą decyzyjną (przegląd, gotowość, wnioski);
> warstwa operacyjna „tu i teraz" to Real-Time Dashboard na Eventhouse.

Motyw: ciemne tło operacyjne, akcent bursztynowy (`#F2A900`) dla przekroczeń,
czerwony (`#D13438`) dla blokad, zielony (`#0F7B0F`) dla wykonania w normie.

---

## Strona 1 — „Gotowość proceduralna"

Odbiorca: Dyrektor RCB, kierownictwo resortu.

| Element | Wizual | Miara / pole |
|---|---|---|
| 4 kafelki KPI | karty | `Uruchomienia procedur`, `Dotrzymanie SLA %`, `Kroki zablokowane`, `Czas do 1. kroku krytycznego (min)` |
| Ranking procedur | wykres słupkowy poziomy | `Dotrzymanie SLA %` wg `dim_procedure[procedure_code]`, sortowanie rosnąco |
| Trend kwartalny | wykres liniowy | `Dotrzymanie SLA %` wg `dim_date[Kwartał]`, linia odniesienia 80% |
| Mapa cieplna zagrożeń | macierz | wiersze `dim_hazard`, kolumny `dim_procedure`, wartość `Uruchomienia procedur` |
| Filtry | slicery | `dim_date`, `fact_activation[level]`, `fact_activation[event_name]` |

## Strona 2 — „Anatomia procedury" (drill-through z listy procedur)

Odbiorca: właściciel procedury, oficer dyżurny.

| Element | Wizual | Uwagi |
|---|---|---|
| Nagłówek | karta tekstowa | nazwa, właściciel, podstawa prawna, faza, `sla_path_hours` |
| Ścieżka kroków | wykres Gantt (lub słupki skumulowane) | oś: `dim_step[step_no]`, długość: mediana `elapsed_minutes`, linia: `sla_minutes` |
| Tabela kroków | tabela | krok, odpowiedzialny, norma, mediana, `Przekroczenia SLA %`, dokument, krytyczny |
| Blokady w tej procedurze | wykres słupkowy | `blocker_reason` × `Kroki zablokowane` |
| Ostatnie uruchomienia | tabela | `activation_id`, data, poziom, województwo, `sla_compliance_pct` |

## Strona 3 — „Wąskie gardła i lessons learned"

Odbiorca: zespół analiz, audyt, komisja po zdarzeniu. **To jest strona z wow momentem.**

| Element | Wizual | Uwagi |
|---|---|---|
| Top 10 kroków po terminie | tabela z paskami | `Przekroczenia SLA %`, `Stosunek czasu do normy` |
| Powtarzające się blokady | tabela | `blocker_reason`, wystąpienia, liczba procedur, lata występowania, `Blokada powtarzalna` |
| Oś czasu blokady | wykres kolumnowy | wybrana blokada w podziale na lata — pokazuje, że problem nie znika |
| Karta narracyjna | karta tekstowa (DAX) | „Ta sama przyczyna blokuje kroki od {rok} — {n} wystąpień w {p} procedurach" |
| Rekomendacja | tekst statyczny | właściciel danych, koszt usunięcia problemu, powiązanie z SPO-10 / SPO-12 |

## Strona 4 — „Dziennik decyzji"

Odbiorca: kontrola, obsługa prawna, rozliczenie zdarzenia.

| Element | Wizual | Uwagi |
|---|---|---|
| Oś czasu decyzji | wykres punktowy | oś X: `decided_at`, kolor: `decision_type` |
| Tabela dziennika | tabela | data, procedura, krok, typ decyzji, decydent, przedmiot, klauzula |
| Rozkład klauzul | wykres kołowy | `classification` |
| RLS | — | rola `Analityk` widzi wyłącznie `jawne` |

## Strona 5 — „Asystent w liczbach"

Odbiorca: właściciel rozwiązania, IT.

| Element | Wizual | Uwagi |
|---|---|---|
| KPI | karty | `Zapytania do asystenta`, `Trafnosc routingu %`, `P95 czasu odpowiedzi (ms)`, `Ocena pomocne %` |
| Trafność wg roli | wykres słupkowy | `fact_assistant_query[user_role]` |
| Wolumen wg kanału | wykres warstwowy | `channel` w czasie |
| Pytania do przeglądu | tabela | `confidence < 0,45` lub `feedback = "niepomocne"` — kolejka poprawy korpusu |
| Pokrycie korpusu | karta | `Fragmenty korpusu`, `Pokrycie zagrożeń procedurami %` |

## Strona 6 — „POWÓDŹ WRZESIEŃ — przebieg"

Odbiorca: demo, ćwiczenie sztabowe.

| Element | Wizual | Uwagi |
|---|---|---|
| Oś czasu uruchomień | wykres Gantt | procedury D-3 … D+10 |
| Porównanie SLA | karty | `Dotrzymanie SLA - powódź %` vs historia, `Roznica SLA powódź vs historia (p.p.)` |
| Mapa województw | mapa | `Uruchomienia procedur` wg `voivodeship_name` |
| Zdarzenia złożone | tabela | doby, w których równolegle działały ≥4 procedury |

---

## Mobile

Strony 1 i 6 mają układ mobilny: 4 kafelki KPI + ranking procedur + oś czasu.
Dyżurny na telefonie ma odpowiedzieć na jedno pytanie: *czy któraś procedura stoi*.
