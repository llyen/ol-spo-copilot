# Stan wdrożenia — Scenariusz 12: Copilot procedur SPO

Dane w całości syntetyczne. Środowisko demonstracyjne, nie produkcyjne.

## 1. Środowisko

| Element | Wartość |
|---|---|
| Obszar roboczy | `OL-ZK-Demo-SPO-Copilot` — `38200f9e-b92b-4fc4-8322-553bd9168ac4` |
| Pojemność | `fcdemo` (F8, West Europe, `rg-fabric-cap-demo`) |
| Lakehouse | `38b50b91-a2df-4907-90c2-d090ee8267d0` |
| Eventhouse | `235d9382-d902-4a35-bb5b-ec6f6105b72c` |
| Baza KQL | `43157bf5-14f2-44bd-9162-8bcebfd98ea4` |
| Eventstream | `51fa5a02-e5a7-4f27-85f5-c14fdd179b54` |
| Model semantyczny | `55d5fa62-af2f-4b50-8cad-94e70acc8a8a` |
| Raport | `173c1523-b68d-40f5-88d4-771d6a764cb4` |
| Pulpit czasu rzeczywistego | `8edda02d-a385-45c4-8950-c97af25b6be7` |
| Reflex | `097bf9c3-892b-4717-a3ff-314c9d308b30` |
| Data Agent | `b0cc386e-d8d3-47ac-9310-224cb83ec758` |

Data Agent byl pierwotnie utworzony jako pusta skorupa - bez zrodel danych i z pusta
instrukcja systemowa. Uzupelnia go `deploy/create_data_agent.py`: podpina Lakehouse
(11 tabel), Eventhouse (10 tabel) i model semantyczny (13 tabel), a instrukcje sklada
z `ai/DATA_AGENT.md`, wiec zmiana specyfikacji wymaga ponownego uruchomienia skryptu.
Funkcje KQL sa weryfikowane, ale opisane w podpowiedzi zrodla zamiast podpiete jako
elementy - backend agenta odrzuca elementy typu `kusto.functions`. Publikacja agenta
z wersji roboczej do produkcyjnej pozostaje krokiem w interfejsie; API jej nie udostepnia.

Kolejność wdrażania warstwy danych opisuje `SETUP_FABRIC.md`.

## 2. Fabric App „Asystent SPO" — wdrożona

| Element | Wartość |
|---|---|
| Adres | https://tangy-poppy-03a3300f0e-westeurope.webapp.fabricapps.net |
| Rayfin Item ID | `5d524e1d-852d-423e-8e54-cfabd91cd701` |
| Wdrożenie | `deploy-20260806074626-904b945f` |
| Kod | `fabric-app\pulpit-spo` |

Pięć ekranów: zapytanie o procedurę własnymi słowami, checklista uruchomienia
z zegarami norm, dziennik decyzji z klauzulami, zadania roli, raport zamknięcia
z wnioskami. Encje zapisu zaaplikowane (`rayfin up db apply --force`), adres
dopisany do `allowedRedirectUris`. Szczegóły — `fabric-app\pulpit-spo\README.md`.

Sprawdzone automatycznie: kontrola typów, lint, 38 testów (w tym kotwica retrievera
wobec metryk z `retrieval_eval.json`), audyt kontrastu WCAG, odpowiedź serwisu
(HTTP 200), serwowanie sceny (0,92 MB) i jasnej palety rządowej w CSS (21 wystąpień
tokenów `--color-gov`).

**Do przeklikania przez człowieka w portalu:** logowanie brokerem Fabric i zapis
wiersza przez formularz. Ścieżka zapisu nie została wykonana ręcznie od końca do końca.

## 3. Zgodność wyszukiwania w aplikacji z retrieverem w Pythonie

`fabric-app\pulpit-spo\src\data\retrieval.ts` jest portem `corpus\retriever.py`.
Aplikacja liczy wyszukiwanie w przeglądarce — do klienta trafia korpus 513 fragmentów
i indeks TF-IDF 513 × 1816 zapisany rzadko (33 107 wartości niezerowych). Bez tego
odpowiedź wymagałaby połączenia z Fabric, a scenariusz zakłada pracę przy ograniczonej
łączności.

Testy kotwiczące porównują wskazania portu z metrykami policzonymi w notatniku 04
(`datasets\derived\retrieval_eval.json`): top-1 0,906, top-3 0,938, MRR 0,932 —
łącznie z pytaniami, które chybiły także w Pythonie. Rozjazd implementacji psuje test.

## 4. Stan danych po przeładowaniu

Historia została wyczyszczona i zaingestowana ponownie po naprawie transliteracji
polskich znaków. Liczności w Eventhouse (surowe i typowane zgadzają się co do wiersza,
brak duplikatów po ponownej ingestii):

| Tabela | Wierszy |
|---|---|
| `activation` | 986 |
| `step_execution` | 9 420 |
| `decision_log` | 2 002 |
| `assistant_query` | 4 200 |
| `corpus_chunk` | 513 |
| `dim_step` | 155 |
| `dim_document` | 49 |
| `dim_role` | 22 |
| `dim_hazard` | 20 |
| `dim_procedure` | 16 |

## 5. Defekty znalezione i usunięte podczas wdrożenia

1. **`NaN` w scenie.** `tools\build_scene.py` zapisywał puste komórki pandas jako
   literał `NaN`, którego `JSON.parse` nie przyjmuje — aplikacja nie wczytałaby się
   w ogóle. Naprawione zamianą pustych wartości na `""` przed zapisem oraz zaporą
   `allow_nan=False`, która zamienia cichy błąd w błąd głośny.
2. **Polski cudzysłów zamykający literał w JSX.** Znak `”` w atrybucie tekstowym kończył
   literał i psuł kompilację. Naprawione ujęciem tekstu w wyrażenie.

## 6. Automat uruchamiania notatników

`tools\run_notebooks.py` uruchamia notatniki przez Fabric Jobs API i czeka na wynik.
Przydatny we wszystkich repozytoriach programu — wcześniej notatniki trzeba było
uruchamiać ręcznie w portalu po każdym przeliczeniu zbiorów.
