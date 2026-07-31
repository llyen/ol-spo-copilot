# Architektura — SPO Copilot

> ⚠️ Rozwiązanie demonstracyjne na danych syntetycznych. Nie jest systemem operacyjnym
> ani źródłem obowiązujących procedur.

## 1. Problem

Dyżurny w centrum zarządzania kryzysowego w momencie zdarzenia ma do dyspozycji
kilkadziesiąt dokumentów: standardowe procedury operacyjne, plan zarządzania kryzysowego
województwa, plan ochrony ludności, siatkę bezpieczeństwa. Odnalezienie właściwego
kroku — pod presją czasu, często w nocy, przez telefon — trwa minuty, których nie ma.
Skutki widać w danych: **23,9% kroków wykonywanych jest po czasie normatywnym**,
a w scenariuszu powodziowym niemal **co trzeci**.

Drugi, cichszy problem: te same blokady wracają latami. Jedna przyczyna
(nieaktualna lista punktów kontaktowych operatorów infrastruktury krytycznej)
zablokowała kroki **201 razy w ciągu czterech lat** w kilkunastu różnych procedurach.
Nikt tego nie widział, bo każde zdarzenie rozliczane jest osobno.

## 2. Odpowiedź

Asystent procedur (RAG nad korpusem SPO) połączony z warstwą analityczną, która
z tych samych zdarzeń wyciąga wnioski systemowe:

1. **Warstwa wiedzy** — korpus 49 dokumentów pocięty na 513 fragmentów, indeks TF-IDF,
   routing pytania → procedura → konkretne kroki z cytowaniami.
2. **Warstwa działania** — karta odpowiedzi: procedura, rola odpowiedzialna, checklista
   kroków z czasami normatywnymi, dokumenty do wytworzenia, wpis do dziennika decyzji.
3. **Warstwa uczenia się** — analityka dotrzymania czasów, chronicznie przekraczane kroki,
   powtarzające się blokady, telemetria trafności asystenta.

## 3. Przepływ danych

```mermaid
%% zawartosc pliku architecture.mmd
```

Pełny diagram: [`architecture.mmd`](architecture.mmd).

### 3.1 Ścieżka wsadowa (korpus)

`corpus/spo_content.py` → `generate_datasets.py` → `datasets/*.csv|jsonl` →
**Lakehouse** (`Files/raw` → tabele delta) → notatnik `02_build_vector_index.py`
buduje indeks TF-IDF i zapisuje go z powrotem do Lakehouse (`Files/derived`).
Indeks jest artefaktem wersjonowanym — przebudowa jest deterministyczna.

### 3.2 Ścieżka strumieniowa (zdarzenia)

`simulate_realtime.py` publikuje cztery strumienie do **Eventstream**:

| Strumień | Tabela KQL | Częstotliwość w demo |
|---|---|---|
| uruchomienia procedur | `activation_stream` | rzadka, punkty zwrotne scenariusza |
| wykonania kroków | `step_execution_stream` | najgęstszy, źródło alertów SLA |
| wpisy dziennika decyzji | `decision_log_stream` | średnia |
| zapytania do asystenta | `assistant_query_stream` | gęsta, telemetria |

Eventstream → **Eventhouse** (`kql/01_create_tables.kql`), zasady aktualizacji
(`kql/02_update_policies.kql`) materializują widoki analityczne w locie.

### 3.3 Ścieżka odpowiedzi asystenta

```
pytanie użytkownika
  → tokenizacja (pełny wyraz + prefiks 5 znaków — odporność na fleksję)
  → cosine similarity nad indeksem TF-IDF (513 fragmentów, 1816 termów)
  → agregacja fragmentów do procedury
       fragment z procedury            → waga 1,00
       fragment planu/KPZK z „SPO-n"   → waga 0,45
       tłumienie rangi                 → 1 / (1 + 0,25 · rank)
  → karta odpowiedzi: procedura, checklista kroków, cytowania (chunk_id)
  → log do assistant_query_stream (pytanie, trafność, latencja, ocena)
```

Jakość mierzona zestawem 32 pytań kontrolnych: **top-1 90,6%**, **top-3 93,8%**,
**MRR 0,932**. Trzy pytania trafiają poza cel — świadomie zostawione, bo pokazują
zachowanie asystenta przy niskiej pewności (prezentacja trzech alternatyw zamiast
jednej błędnej odpowiedzi).

## 4. Komponenty Fabric

| Komponent | Nazwa | Rola w rozwiązaniu |
|---|---|---|
| Lakehouse | `spo_copilot_lh` | wymiary, korpus, indeks, karty odpowiedzi |
| Eventhouse / KQL DB | `spo_copilot_kql` | strumienie operacyjne, zapytania dashboardu |
| Eventstream | `es-spo-copilot` | ingest czterech strumieni |
| Notebooks | `01`–`05` | ładowanie, indeks, odpowiedzi, ewaluacja, analityka |
| Model semantyczny | `spo_copilot_sm` | gwiazda + 28 miar DAX |
| Raport | `SPO Copilot` | 6 stron (przegląd, procedura, SLA, blokady, asystent, decyzje) |
| Activator | 9 reguł `A1`–`A9` | alerty o przekroczeniach i blokadach krytycznych |
| Data Agent | `spo-copilot-agent` | pytania w języku naturalnym o stan realizacji |
| Fabric App | `SPO Copilot` | interfejs dyżurnego: pytanie → karta → checklista → decyzja |

## 5. Decyzje projektowe

| Decyzja | Uzasadnienie |
|---|---|
| TF-IDF zamiast embeddingów | brak zależności od modelu i sieci, deterministyczne wyniki, pełna wyjaśnialność cytowań; w produkcji warstwa wektorowa Fabric zastępuje ten moduł bez zmiany interfejsu `Retriever.route()` |
| Fragment = sekcja lub pojedynczy krok | cytowanie musi wskazywać konkretny krok, nie „gdzieś w procedurze" |
| Waga 0,45 dla wzmianek `SPO-n` | plany wojewódzkie odsyłają do procedur; sygnał jest realny, ale słabszy niż treść samej procedury |
| Tokenizacja dwupoziomowa | prefiks 7 znaków gubił fleksję („zbornych" vs „zborne"); pełny wyraz + prefiks 5 podniósł top-1 z 87,5% do 90,6% |
| Treść korpusu bez znaków diakrytycznych | odporność na kodowanie przy ingest i w konsoli; dokumentacja pozostaje pełną polszczyzną |
| Dziennik decyzji jako osobny fakt | uzasadnienie decyzji jest wymogiem formalnym i jednocześnie najcenniejszym materiałem do analizy po zdarzeniu |
| Blokady ważone, z jedną przyczyną dominującą | równomierny rozkład blokad nie generuje wniosku; realne dane mają „długi ogon" i jeden gruby przypadek |

## 6. Granice rozwiązania

- Dane są syntetyczne; wnioski ilustrują **metodę**, nie stan faktyczny.
- Model nie rozstrzyga o klasyfikacji informacji — pole `classification` jest atrybutem
  wejściowym, a nie wynikiem analizy.
- Asystent wspiera decyzję, nie zastępuje osoby uprawnionej; każda karta odpowiedzi
  kończy się wskazaniem roli, która podejmuje decyzję.
