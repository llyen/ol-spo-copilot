# Fabric App — „SPO Copilot: asystent procedur i dziennik decyzji"

> Dane syntetyczne. Aplikacja operatorska dla oficera dyżurnego CZK (gmina → RCB).
> Zbudowana jako Fabric App (Rayfin) nad Lakehouse + Eventhouse, z zapisem zwrotnym
> (write-back) do tabel realizacji kroków i dziennika decyzji.

## Problem, który rozwiązuje

W kryzysie oficer dyżurny ma minutę na ustalenie, *którą procedurę uruchomić* i *co robić dalej*.
Dziś to oznacza szukanie w kilkudziesięciu dokumentach PDF. Aplikacja zamienia korpus procedur
w jedno pole pytania, checklistę z odpowiedzialnymi i czasami oraz dziennik decyzji,
który jest gotowym śladem audytowym po zdarzeniu.

## Role użytkowników

| Rola | Uprawnienia |
|---|---|
| Oficer dyżurny | pytanie do asystenta, uruchomienie procedury, zmiana statusu kroku, wpis do dziennika |
| Właściciel procedury | wszystko powyżej + zamknięcie procedury, zatwierdzenie odstąpienia od kroku |
| Kierownictwo (RCB/resort) | podgląd wszystkich uruchomień, decyzje niejawne, raporty |
| Analityk | dane zagregowane, bez treści decyzji niejawnych (RLS) |

---

## Ekran 1 — „Zapytaj o procedurę"

Główny ekran startowy. Jedno pole tekstowe i mikrofon.

**Wejście:** pytanie w języku naturalnym (np. *„mamy skażenie chemiczne w porcie, co robimy?"*).

**Wyjście — karta odpowiedzi:**

| Sekcja | Zawartość | Źródło |
|---|---|---|
| Nagłówek | kod i nazwa procedury, właściciel, faza, podstawa prawna | `dim_procedure` |
| Pewność dopasowania | wartość 0–1 + 2 alternatywne procedury do jednego kliknięcia | routing retrievera |
| Pierwszy krok krytyczny | tytuł + czas normatywny — to widzi dyżurny w pierwszej sekundzie | `dim_step` |
| Checklista | wszystkie kroki: nr, tytuł, odpowiedzialny, instytucja, czas, dokument, krytyczność | `dim_step` |
| Lista telefoniczna | role i instytucje uczestniczące, z przyciskiem „powiadom" | `dim_role` |
| Cytowania | 4 fragmenty korpusu z identyfikatorem `chunk_id` i wynikiem dopasowania | `corpus_chunk` |
| Jak nam szło | historyczne dotrzymanie SLA tej procedury, najczęściej blokowany krok | `fact_step_execution` |

**Zasada:** żadna treść nie jest generowana bez cytowania. Jeśli pewność < 0,45 —
aplikacja nie podaje jednej procedury, tylko listę trzech kandydatek i pyta o doprecyzowanie.

**Akcje:** `Uruchom procedurę` · `Pokaż pełny dokument` · `Wyślij listę kontaktową na Teams` · `To nie ta procedura` (feedback do korpusu).

---

## Ekran 2 — „Checklista uruchomienia"

Widok pracy bieżącej po uruchomieniu procedury.

| Pole | Typ | Uwagi |
|---|---|---|
| `activation_id` | tekst (auto) | generowany przy uruchomieniu |
| Procedura, poziom, województwo, zdarzenie | wybór | domyślnie z kontekstu dyżuru |
| Uzasadnienie uruchomienia | tekst | trafia do dziennika decyzji jako pierwszy wpis |
| Lista kroków | tabela edytowalna | status: `oczekuje` / `w toku` / `wykonany` / `zablokowany` / `pominięty` |
| Zegar kroku | licznik | odlicza do czasu normatywnego; po przekroczeniu kolor bursztynowy |
| Blokada | wybór z listy + notatka | lista przyczyn zasilana z historii (`recurring_blockers.csv`) |
| Dokument wyjściowy | załącznik / link | np. protokół, komunikat, decyzja |
| Odstąpienie od kroku | przełącznik + uzasadnienie | wymaga roli właściciela procedury |

**Write-back:** każda zmiana statusu tworzy zdarzenie `step_execution` (Eventstream → Eventhouse),
więc dashboard RCB widzi postęp w czasie rzeczywistym bez żadnego raportowania „na piechotę".

---

## Ekran 3 — „Dziennik decyzji"

| Pole | Typ |
|---|---|
| Czas decyzji | data i godzina (auto) |
| Typ decyzji | lista: uruchomienie procedury, eskalacja poziomu, zatwierdzenie komunikatu, uruchomienie środków, skierowanie sił i środków, wprowadzenie ograniczeń, odstąpienie od kroku, zamknięcie procedury |
| Decydent | rola + osoba (auto z kontekstu) |
| Przedmiot | tekst |
| Uzasadnienie | tekst wieloliniowy — **pole obowiązkowe** |
| Klauzula | jawne / zastrzeżone / poufne |
| Powiązany krok | wybór z checklisty |

Wpisu nie da się usunąć ani edytować po zapisaniu — możliwa jest wyłącznie korekta
w formie nowego wpisu odsyłającego do poprzedniego. To warunek wiarygodności śladu audytowego.

---

## Ekran 4 — „Moje zadania"

Lista kroków przypisanych do roli zalogowanego użytkownika, we wszystkich otwartych
uruchomieniach, posortowana po czasie do przekroczenia normy. Kolor: zielony → bursztynowy → czerwony.

---

## Ekran 5 — „Po zdarzeniu"

Generuje raport zamknięcia uruchomienia: przebieg kroków, przekroczenia, blokady,
pełny dziennik decyzji i propozycję wniosków. Wnioski powstają z porównania przebiegu
z historią: *„krok 4 przekroczył normę — to 18. taki przypadek w tej procedurze"*.

Wyjście: dokument do zatwierdzenia + wpis do rejestru wniosków (`lessons learned`).

---

## Integracje

| Kierunek | Element Fabric |
|---|---|
| odczyt korpusu i procedur | Lakehouse (`dim_procedure`, `dim_step`, `corpus_chunk`) |
| wyszukiwanie | indeks wektorowy (Delta) / AI Functions embeddings |
| zapis realizacji i decyzji | Eventstream → Eventhouse (`step_execution`, `decision_log`) |
| alerty | Data Activator (reguły z `activator/RULES.md`) |
| pytania kierownictwa | Data Agent (`ai/DATA_AGENT.md`) |
| raporty | Power BI (`report/REPORT_SPEC.md`) |
| ochrona danych | etykiety wrażliwości Purview na `decision_log`, RLS w modelu semantycznym |

## Wymagania niefunkcjonalne

- Odpowiedź asystenta poniżej 3 s dla 95% zapytań (dane demo: p95 ≈ 2,1 s).
- Praca w trybie ograniczonej łączności: checklista i lista kontaktowa dostępne offline (cache).
- Pełna rozliczalność: każdy wpis ma autora, czas i identyfikator uruchomienia.
- Językowo: interfejs i korpus po polsku; nazwy techniczne po angielsku.
