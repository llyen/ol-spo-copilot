# Asystent SPO — Fabric App scenariusza „Copilot procedur SPO"

Aplikacja odpowiada na pytanie, które oficer dyżurny zadaje sobie w pierwszych minutach
zdarzenia: **którą procedurę uruchomić i co zrobić najpierw**. Powstała dla scenariusza
demonstracyjnego `ol-spo-copilot`.

Dane są w całości syntetyczne. Procedury, dokumenty i historia uruchomień to rekordy
wygenerowane — żaden nie odpowiada rzeczywistej procedurze SPO.

## Ekrany

| Ścieżka | Ekran | Do czego służy |
|---|---|---|
| `/` | Zapytaj o procedurę | Pytanie własnymi słowami → wskazanie procedury z pewnością, cytatami z korpusu i pierwszym krokiem krytycznym. Kończy się uruchomieniem procedury albo oceną odpowiedzi. |
| `/checklista` | Checklista uruchomienia | Kroki z zegarami norm czasu, blokady, odstąpienia. Kończy się zamknięciem kroku albo zgłoszeniem blokady. |
| `/dziennik` | Dziennik decyzji | Ślad audytowy uruchomienia z klauzulami. Kończy się wpisem decyzji albo sprostowaniem. |
| `/zadania` | Moje zadania | Kroki przypisane do roli zalogowanego, posortowane wg pilności. Kończy się przejęciem kroku. |
| `/po-zdarzeniu` | Po zdarzeniu | Raport zamknięcia, przekroczenia norm, wnioski wyliczone z historii. Kończy się przyjęciem wniosku i zamknięciem uruchomienia. |

## Role

| Rola | Widzi wpisy z klauzulą | Może zapisywać | Zamyka procedurę i wnioski |
|---|---|---|---|
| oficer dyżurny | tak | tak | nie |
| właściciel procedury | tak | tak | tak |
| kierownictwo RCB | tak | tak | tak |
| analityk | **nie** | **nie** | nie |

Analitykowi maskowana jest treść, ale **nie sam fakt decyzji** — wpis zostaje na liście
z klauzulą i znacznikiem czasu. Gdyby znikał, liczba decyzji w raporcie byłaby
nieprawdziwa, a to jest gorsze niż zasłonięta treść.

## Skąd bierze się odpowiedź

Aplikacja **nie odpytuje backendu o odpowiedź**. Do przeglądarki trafia korpus 513
fragmentów i indeks TF-IDF 513 × 1816 zapisany rzadko (33 107 wartości niezerowych,
0,92 MB zamiast ok. 25 MB gęsto). Wyszukiwanie liczy `src/data/retrieval.ts` — port
`corpus/retriever.py`. To jest warunek pracy przy ograniczonej łączności: dyżurny dostaje
wskazanie procedury także wtedy, gdy nie ma połączenia z Fabric.

Reguły, których nie wolno zmienić bez zmiany retrievera w Pythonie:

- **transliteracja przed normalizacją Unicode** — `ł` nie rozkłada się w NFKD, więc samo
  odsianie znaków spoza ASCII zamienia „ludności" w „udnoci" i psuje trafność;
- tokenizacja dwupoziomowa: pełny wyraz plus prefiks 5 znaków dla wyrazów dłuższych —
  odmiana „ewakuacji"/„ewakuacja" ma trafiać w ten sam term;
- fragment przypisany do SPO wnosi wynik wprost, fragment KPZK lub planu wymieniający kod
  SPO wnosi 45% — działa jak odsyłacz, a nie jak źródło;
- pewność to udział wyniku najlepszej procedury w sumie wyników, nie wartość kosinusa;
- poniżej progu pewności aplikacja **nie wskazuje jednej procedury**, tylko pokazuje
  kandydatki. Wskazanie z niską pewnością jest gorsze niż przyznanie się do niepewności.

Testy w `src/__tests__/retrieval.test.ts` porównują wskazania portu z metrykami
policzonymi w Fabric (`datasets/derived/retrieval_eval.json`: top-1 0,906, top-3 0,938,
MRR 0,932) — łącznie z pytaniami, które chybiły. Rozjazd portu i Pythona psuje test,
zanim zdąży trafić na ekran.

## Czas w scenie jest względny

Scena nie niesie dat, tylko przesunięcia `offsetMin` od chwili wejścia do aplikacji
(ujemne = przeszłość). Dzięki temu demonstracja o dowolnej porze i po dowolnie długim
czasie od zbudowania sceny wygląda jak trwający dyżur, a nie jak archiwum. Zegary kroków
odświeża `tick` w `ScenarioContext` co 60 sekund.

Historia w zbiorach zawiera wyłącznie uruchomienia zamknięte (986 z 986), więc
`tools/build_scene.py` dokłada 6 uruchomień w toku (ziarno 42). Bez nich ekrany
checklisty, dziennika, zadań i raportu nie miałyby czego pokazać.

## Uruchomienie

```powershell
npm install
python tools/build_scene.py     # public/data/scene.json, ok. 0,92 MB
npm run dev
```

Testy, kontrola typów i lint:

```powershell
npm run test
npx tsc -b
npm run lint
```

## Wdrożenie na Fabric

```powershell
..\..\deploy\ensure_capacity.ps1
npx rayfin up -y --workspace-id <ID obszaru roboczego>
npx rayfin up db apply --force
```

Zapis z formularzy trafia do bazy Rayfin (`rayfin/data/`): `Activation`, `StepExecution`,
`DecisionLog`, `AssistantFeedback`, `LessonLearned`. Gdy baza jest niedostępna, zapis
zostaje w pamięci sesji i aplikacja pokazuje ostrzeżenie — demonstracja nie przerywa się
z powodu backendu.
