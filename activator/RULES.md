# Reguły Data Activator (Reflex) — SPO Copilot

> Dane syntetyczne. Zapytania źródłowe znajdują się w `kql/04_alerts.kql`.
> Zasada nadrzędna: alert ma prowadzić do czynności, a nie tylko informować.
> Każda reguła ma właściciela, próg, akcję i regułę wygaszania (żeby nie zalać dyżurnego).

| ID | Nazwa | Źródło | Warunek | Akcja | Właściciel | Wygaszanie |
|---|---|---|---|---|---|---|
| A1 | Krok krytyczny po terminie | `step_execution` | `is_critical` i `not(sla_met)` i przekroczenie > 15 min | Teams do instytucji odpowiedzialnej + oznaczenie kroku w aplikacji | właściciel procedury | 1 alert na krok |
| A2 | Krok zablokowany > 2× normy | `step_execution` | `status == "zablokowany"` i `elapsed > 2 × sla` | eskalacja do właściciela procedury; przy 3. wystąpieniu — do RCB | dyżurny RCB | 30 min |
| A3 | Uruchomiono procedurę szczebla rządowego | `activation` | `procedure_code in (SPO-1, SPO-5, SPO-6, SPO-7, SPO-16)` | alert do sekretarza RZZK i dyżurnego RCB, przygotowanie materiałów | sekretarz RZZK | brak (każde zdarzenie) |
| A4 | Zdarzenie złożone w województwie | `activation` | ≥ 4 różne procedury w jednym województwie w 6 h | rekomendacja zwołania RZZK (SPO-1) lub ZIK (SPO-16) | dyżurny RCB | 6 h |
| A5 | Spadek dotrzymania czasów normatywnych | `step_execution` | ≥ 20 wykonań w 4 h i dotrzymanie < 60% | alert do kierownictwa RCB — sygnał przeciążenia systemu | kierownictwo RCB | 4 h |
| A6 | Powtarzalna blokada systemowa | `step_execution` | ta sama przyczyna ≥ 10 razy w ≥ 3 procedurach w 30 dni | zadanie do właściciela danych (nie alert operacyjny) | właściciel korpusu | 30 dni |
| A7 | Asystent niepewny lub oceniony negatywnie | `assistant_query` | `confidence < 0,45` lub `feedback == "niepomocne"` | kolejka przeglądu korpusu procedur | właściciel korpusu | dobowo, zbiorczo |
| A8 | Decyzja niejawna w dzienniku | `decision_log` | `classification != "jawne"` | potwierdzenie etykiety wrażliwości i ograniczenie widoczności | inspektor ochrony informacji | brak |
| A9 | Procedura otwarta ponad ścieżkę normatywną | `activation` | `open_minutes > 1,5 × total_sla_minutes` i status ≠ zamknięte | monit do właściciela procedury o zamknięcie lub aktualizację | właściciel procedury | 12 h |

## Kanały

- **Teams** — kanał `RCB / dyżur` (A1, A2, A4, A5), kanał `RZZK / sekretariat` (A3).
- **E-mail** — A6, A7 (zbiorczo, raz na dobę).
- **Fabric App** — wszystkie reguły oznaczają odpowiedni krok lub uruchomienie w interfejsie.
- **Power Automate** — A3 uruchamia szablon zaproszenia na posiedzenie i listę materiałów.

## Dobór progów

Progi wynikają z rozkładu danych demo (`datasets/derived/step_analytics_summary.json`):

- Dotrzymanie czasów normatywnych w historii ≈ 76%, w scenariuszu powodziowym ≈ 70% —
  próg 60% w A5 wyłapuje realne przeciążenie, a nie normalną zmienność.
- Mediana czasu do pierwszego kroku krytycznego ≈ 19 min — próg 15 min przekroczenia w A1
  daje sygnał zanim opóźnienie przełoży się na kolejne kroki.
- Najczęstsza blokada wystąpiła ponad 200 razy w 4 latach — A6 z progiem 10/30 dni
  zamienia ją z szumu operacyjnego w jedno zadanie systemowe.

## Czego świadomie nie alarmujemy

- Przekroczeń na krokach niekrytycznych bez blokady — to szum, obniża zaufanie do alertów.
- Pojedynczych zapytań asystenta o niskiej pewności — zbiorczo, raz na dobę (A7).
- Zamknięć procedur i wpisów jawnych do dziennika — to normalny przebieg pracy.
