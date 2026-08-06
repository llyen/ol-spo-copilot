# Scenariusz demo — SPO Copilot (12 minut)

> ⚠️ Pokaz na danych syntetycznych. Nie prezentować jako stanu faktycznego
> jakiejkolwiek instytucji.

## Obsada i kontekst

| Rola w pokazie | Kto mówi | Co pokazuje |
|---|---|---|
| Dyżurny WCZK Opole | prowadzący | Fabric App — pytanie i checklista |
| Dyrektor WBZK | prowadzący | raport Power BI — strony 1–3 |
| Analityk „lessons learned" | prowadzący | raport strony 4–5 + Data Agent |

Oś czasu: **POWÓDŹ WRZESIEŃ**, `D0 = 2026-09-15 06:00`. Punkt wejścia:
**D0 + 4 h**, wysoka woda na Odrze, dwa powiaty w województwie opolskim.

---

## Akt 1 (0:00–3:00) — problem, nie technologia

**Mów:**
> Dyżurny odbiera telefon o 6:00 rano. Ma pięć minut i trzydzieści dokumentów.
> Pytanie brzmi nie „gdzie to jest zapisane", tylko „co mam zrobić w ciągu
> najbliższych trzydziestu minut i kto to podpisuje".

**Pokaż:** slajd/stronę 1 raportu — kafle: 986 uruchomień procedur, 9 420 wykonań kroków,
**76,1% dotrzymania czasów normatywnych**. Zatrzymaj się na tym ostatnim.

> Co czwarty krok procedury kryzysowej wykonywany jest po czasie. W powodzi — co trzeci.

*Nie pokazuj jeszcze żadnej listy dokumentów. Najpierw liczba, potem narzędzie.*

---

## Akt 2 (3:00–6:00) — asystent: pytanie → karta odpowiedzi

**Klikaj:** Fabric App → pole pytania. Wpisz (lub podyktuj):

> „Pękł wał przeciwpowodziowy, woda zalewa dwie wsie, potrzebna ewakuacja
> i ostrzeżenie mieszkańców."

**Co się pojawia (ok. 1,4 s):**
- **SPO-3** — Zasady informowania ludności o zagrożeniach, pewność routingu **0,86**;
- właściciel: rzecznik prasowy RCB, faza: reagowanie;
- checklista 11 kroków z czasami normatywnymi i dokumentami wyjściowymi;
- **cytowania** — konkretne fragmenty (`chunk_id`) z SPO-3, z planu zarządzania
  kryzysowego województwa opolskiego i z KPZK.

**Mów:**
> To nie jest streszczenie wygenerowane „z głowy". Każdy punkt ma cytowanie do fragmentu
> dokumentu. Dyżurny może w sekundę sprawdzić, skąd to się wzięło — i to jest warunek,
> żeby czegokolwiek takiego użyć w zarządzaniu kryzysowym.

**Druga próba — pokaż drugą procedurę:**
> „Wojewoda chce wprowadzić stan klęski żywiołowej w dwóch powiatach."
→ **SPO-5**, pewność **2,52** (bardzo wysoka), 10 kroków, 8 krytycznych.

**Trzecia próba — pokaż zachowanie przy niskiej pewności:**
> „Zalana stacja elektroenergetyczna, operator IK nie odbiera telefonu."
→ SPO-10 (0,387), ale tuż za nim SPO-1 (0,317) i SPO-16 (0,311).

**Mów:**
> Tu asystent nie jest pewny — i mówi to wprost. Zamiast jednej błędnej odpowiedzi
> pokazuje trzy kandydatury z cytowaniami. Decyduje człowiek.

*Trafność mierzona na 32 pytaniach kontrolnych: **top-1 90,6%**, **top-3 93,8%**, MRR 0,932.
Jeśli ktoś zapyta o metodę — notatnik `04_retrieval_eval.py`, wynik odtwarzalny.*

---

## Akt 3 (6:00–8:00) — checklista prowadzi działanie

**Klikaj:** w karcie SPO-3 → „Uruchom procedurę".

- kroki z odliczaniem czasu do normy, krytyczne wyróżnione;
- przy kroku 4 (wersje językowe komunikatu) pojawia się ostrzeżenie:
  **„ten krok historycznie przekracza normę w 89,9% wykonań"**;
- zamknięcie kroku wymaga wpisu do dziennika decyzji: uzasadnienie + klauzula.

**Mów:**
> System nie tylko mówi, co zrobić. Mówi też, gdzie zwykle się sypie — zanim się posypie.
> A wpis do dziennika nie jest dodatkową biurokracją, tylko materiałem, z którego
> za trzy miesiące powstanie wniosek.

---

## Akt 4 (8:00–10:30) — wow: to samo wraca od lat

**Klikaj:** raport → strona **Blokady i lessons learned**.

Górny wiersz tabeli:
> **„Nieaktualna lista punktów kontaktowych operatorów IK" — 201 wystąpień, 4 lata,
> kilkanaście różnych procedur.**

**Mów (wolno):**
> Przez cztery lata, w kilkunastu procedurach, w różnych województwach, kroki blokowała
> jedna i ta sama rzecz: nikt nie wiedział, pod jaki numer zadzwonić do operatora
> infrastruktury krytycznej.
>
> To nie jest alert operacyjny. Tego się nie da rozwiązać w trakcie zdarzenia.
> To jest wniosek do decyzji zarządczej — i pierwszy raz jest widoczny, bo dopiero
> teraz patrzymy na cztery lata naraz, a nie na każde zdarzenie osobno.

**Klikaj dalej:** strona **SLA** → `sla_worst_steps`:
- SPO-3 krok 4 — 89,9% wykonań po czasie;
- SPO-10 krok 3, SPO-2 krok 3, SPO-9 krok 4, SPO-15 krok 3.

> Jeśli krok przekracza normę w dziewięciu na dziesięć przypadków, to nie jest problem
> ludzi. Albo norma jest nierealna, albo procesu nie da się wykonać ręcznie.
> Dane nie rozstrzygają, ale mówią, którą hipotezę sprawdzić najpierw.

---

## Akt 5 (10:30–12:00) — Data Agent i domknięcie

**Klikaj:** Data Agent, wpisz na żywo:

1. „Które procedury najczęściej przekraczają czasy normatywne w scenariuszu powodziowym?"
2. „Ile decyzji zostało zaklasyfikowanych jako niejawne we wrześniu 2026?" (≈28,4% ogółu)
3. „Jaki jest medianowy czas do pierwszego kroku krytycznego?" (**19,3 min**)

**Domknij:**
> Trzy warstwy, jeden zestaw danych. Asystent skraca czas do pierwszego działania.
> Checklista pilnuje, żeby nic nie wypadło. Analityka pokazuje, co poprawić między
> zdarzeniami. Wszystko w jednym środowisku, bez integracji trzech systemów.

---

## Liczby do zacytowania na scenie

<!-- RESULTS_START -->
- Korpus: 16 procedur SPO, 155 kroków, 49 dokumentów, 513 fragmentow (198746 znakow), slownik indeksu 1816 termow.
- Wymiary: 22 rol, 20 zagrożeń, 32 pytan kontrolnych.
- Zdarzenia: 986 uruchomien procedur, 9420 wykonan kroków, 2002 wpisow w dzienniku decyzji, 4200 zapytan do asystenta.
- Trafnosc routingu: top-1 90.6%, top-3 93.8%, MRR 0.932 na 32 pytaniach (3 pudla).
- Telemetria asystenta: trafnosc 93.5%, p50 1443 ms, p95 2142 ms, ocen "pomocne" 46.3%.
- Czasy normatywne: dotrzymanie 76.1% ogolem, 70.5% w scenariuszu powodziowym; najgorsza procedura SPO-2 (70.7%).
- Najgorszy krok: SPO-3 krok 4 - 89.9% wykonan po czasie (Przygotowanie wersji obcojęzycznych i dostępnych dla osób z niepełnosprawnościami).
- Najczestsza blokada: "Nieaktualna lista punktów kontaktowych operatorów infrastruktury krytycznej" - 201 wystapien w 4 lata.
- Przebieg: mediana czasu do pierwszego kroku krytycznego 19.3 min, mediana trwania procedury 38.9 h, decyzje niejawne 28.4%.
<!-- RESULTS_END -->

## Plan B (gdy coś nie działa)

| Ryzyko | Plan B |
|---|---|
| Fabric App nie odpowiada | pokaż `datasets/derived/answer_card_example.md` — pełna karta odpowiedzi w Markdown |
| Brak strumienia na dashboardzie | `python simulate_realtime.py --dry-run`, pokaż `dry_run_*.jsonl` |
| Raport ładuje się długo | strony 4–5 mają statyczne zrzuty w `report/REPORT_SPEC.md` |
| Data Agent zwraca bzdurę | zadaj pytanie z listy 24 zaakceptowanych w `ai/DATA_AGENT.md` |
| Pytanie o źródło danych | odpowiedz wprost: dane syntetyczne, generator `seed=42`, wszystko odtwarzalne |

## Czego nie mówić

- Nie sugeruj, że to odzwierciedla stan gotowości jakiegokolwiek urzędu.
- Nie obiecuj automatycznego podejmowania decyzji — asystent kończy kartę wskazaniem
  roli, która decyduje.
- Nie wchodź w szczegóły TF-IDF, chyba że ktoś zapyta; wtedy: „w produkcji zastępujemy
  to warstwą wektorową Fabric, interfejs się nie zmienia".

## Checklista przed pokazem

- [ ] `python generate_datasets.py` — dane świeże
- [ ] notatniki `01`–`05` przebiegły bez błędu
- [ ] `python update_results.py` — liczby w dokumentacji zgodne z danymi
- [ ] raport otwarty na stronie 1, druga karta przeglądarki na Fabric App
- [ ] Data Agent przetestowany na 3 pytaniach z Aktu 5
- [ ] `simulate_realtime.py --dry-run` sprawdzony jako plan B