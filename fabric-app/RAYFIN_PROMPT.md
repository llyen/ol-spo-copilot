# Prompt do generatora Fabric App (Rayfin) — SPO Copilot

> Skopiuj poniższą treść do kreatora aplikacji w Microsoft Fabric.
> Aplikacja korzysta z tabel Lakehouse `OL_SPO_Copilot_LH` i Eventhouse `OL_SPO_Copilot_EH`
> utworzonych zgodnie z `SETUP_FABRIC.md`. Dane są syntetyczne (demo).

---

Zbuduj aplikację operacyjną dla oficera dyżurnego centrum zarządzania kryzysowego o nazwie
**„SPO Copilot"**. Aplikacja ma zamienić korpus procedur kryzysowych w narzędzie pracy:
wskazać właściwą procedurę, poprowadzić po jej krokach i zapisać ślad audytowy decyzji.
Interfejs w języku polskim, ciemny motyw operacyjny, duże elementy dotykowe.

**Źródła danych**

- Lakehouse `OL_SPO_Copilot_LH`: `dim_procedure`, `dim_step`, `dim_role`, `dim_hazard`,
  `dim_document`, `corpus_chunk`, `bridge_procedure_hazard`.
- Eventhouse `OL_SPO_Copilot_EH`: `step_execution`, `decision_log`, `assistant_query`, `activation`.
- Zapis zwrotny: nowe wiersze do `step_execution` i `decision_log` przez Eventstream.

**Ekran 1 „Zapytaj o procedurę"** (startowy)

- Jedno duże pole pytania w języku naturalnym + przycisk mikrofonu.
- Po zadaniu pytania pokaż kartę odpowiedzi: kod i nazwa procedury, właściciel, podstawa prawna,
  pewność dopasowania (0–1) oraz dwie procedury alternatywne jako klikalne przyciski.
- Wyróżnij blok „Pierwszy krok krytyczny" (tytuł + czas normatywny) największą czcionką na ekranie.
- Poniżej: checklista kroków z `dim_step` (nr, tytuł, odpowiedzialny, instytucja, czas normatywny,
  dokument wyjściowy, znacznik krytyczności) oraz lista kontaktowa z `dim_role`.
- Sekcja „Źródła": 4 fragmenty z `corpus_chunk` z identyfikatorem i wynikiem dopasowania.
  Nie pokazuj żadnej treści bez identyfikatora fragmentu.
- Sekcja „Jak nam szło": z `step_execution` policz dotrzymanie czasów normatywnych tej procedury
  i wskaż krok najczęściej przekraczający normę.
- Jeśli pewność dopasowania jest niższa niż 0,45, nie pokazuj jednej procedury — pokaż trzy
  kandydatki i poproś o doprecyzowanie.
- Przyciski: „Uruchom procedurę", „Pokaż pełny dokument", „Wyślij listę kontaktową",
  „To nie ta procedura" (zapisuje ocenę do `assistant_query`).

**Ekran 2 „Checklista uruchomienia"**

- Formularz uruchomienia: procedura, poziom (gminny/powiatowy/wojewódzki/krajowy), województwo,
  nazwa zdarzenia, uzasadnienie uruchomienia (pole wymagane).
- Tabela kroków z edytowalnym statusem: oczekuje, w toku, wykonany, zablokowany, pominięty.
- Przy każdym kroku licznik odliczający do czasu normatywnego; po przekroczeniu podświetl na
  bursztynowo, przy dwukrotnym przekroczeniu na czerwono.
- Pole „Blokada" z listą przyczyn zasilaną z historii oraz notatką.
- Odstąpienie od kroku wymaga roli właściciela procedury i uzasadnienia.
- Każda zmiana statusu zapisuje zdarzenie do `step_execution` z czasem i autorem.

**Ekran 3 „Dziennik decyzji"**

- Formularz: typ decyzji (lista wartości), przedmiot, uzasadnienie (wymagane),
  klauzula (jawne/zastrzeżone/poufne), powiązany krok.
- Lista wpisów w porządku chronologicznym, tylko do odczytu.
- Wpisów nie można edytować ani usuwać; korekta = nowy wpis odsyłający do poprzedniego.
- Wpisy z klauzulą inną niż „jawne" widoczne tylko dla ról uprawnionych.

**Ekran 4 „Moje zadania"**

- Lista kroków przypisanych do roli zalogowanego użytkownika we wszystkich otwartych
  uruchomieniach, sortowana po czasie pozostałym do przekroczenia normy.

**Ekran 5 „Po zdarzeniu"**

- Raport zamknięcia: przebieg kroków, przekroczenia, blokady, pełny dziennik decyzji.
- Automatyczne wnioski: dla każdego przekroczonego kroku podaj, ile razy wcześniej ten sam krok
  przekraczał normę i jaka przyczyna blokady powtarza się najczęściej.
- Przycisk „Zatwierdź wnioski" zapisuje je do rejestru wniosków.

**Zasady przekrojowe**

- Nie generuj treści procedur — wyłącznie cytuj korpus.
- Każdy zapis ma autora, czas i identyfikator uruchomienia.
- Aplikacja musi działać przy ograniczonej łączności: checklista i lista kontaktowa z cache.
- W stopce stała informacja: „Demo. Dane syntetyczne — nie stanowią dokumentacji operacyjnej."
