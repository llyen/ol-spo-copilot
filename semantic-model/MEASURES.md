# Miary DAX — SPO Copilot

> Konwencja: miary w folderze `_Miary`, formaty procentowe z jednym miejscem po przecinku,
> czasy w minutach lub godzinach zależnie od rzędu wielkości.

## 1. Wolumen i przebieg

```dax
Uruchomienia procedur = DISTINCTCOUNT ( fact_activation[activation_id] )

Wykonania kroków = COUNTROWS ( fact_step_execution )

Decyzje w dzienniku = COUNTROWS ( fact_decision_log )

Mediana czasu trwania procedury (h) =
MEDIANX ( fact_activation, fact_activation[duration_minutes] ) / 60
```

## 2. Dotrzymanie czasów normatywnych (SLA)

```dax
Kroki w normie = CALCULATE ( [Wykonania kroków], fact_step_execution[sla_met] = TRUE () )

Dotrzymanie SLA % =
DIVIDE ( [Kroki w normie], [Wykonania kroków] )

Przekroczenia SLA % = 1 - [Dotrzymanie SLA %]

Mediana przekroczenia (min) =
MEDIANX (
    FILTER ( fact_step_execution, fact_step_execution[overdue_minutes] > 0 ),
    fact_step_execution[overdue_minutes]
)

Stosunek czasu do normy =
DIVIDE (
    MEDIANX ( fact_step_execution, fact_step_execution[elapsed_minutes] ),
    MEDIANX ( fact_step_execution, fact_step_execution[sla_minutes] )
)
```

## 3. Reakcja i krytyczność

```dax
Czas do 1. kroku krytycznego (min) =
VAR PierwszeKrytyczne =
    SUMMARIZE (
        FILTER ( fact_step_execution, fact_step_execution[is_critical] = TRUE () ),
        fact_step_execution[activation_id],
        "Zakonczenie", MIN ( fact_step_execution[completed_at] )
    )
VAR ZeStartem =
    ADDCOLUMNS (
        PierwszeKrytyczne,
        "Reakcja",
        DATEDIFF (
            LOOKUPVALUE (
                fact_activation[started_at],
                fact_activation[activation_id], fact_step_execution[activation_id]
            ),
            [Zakonczenie],
            MINUTE
        )
    )
RETURN
    MEDIANX ( ZeStartem, [Reakcja] )

Dotrzymanie SLA kroków krytycznych % =
CALCULATE ( [Dotrzymanie SLA %], fact_step_execution[is_critical] = TRUE () )
```

## 4. Blokady i wnioski systemowe

```dax
Kroki zablokowane = CALCULATE ( [Wykonania kroków], fact_step_execution[status] = "zablokowany" )

Udzial blokad % = DIVIDE ( [Kroki zablokowane], [Wykonania kroków] )

Lata wystepowania blokady =
CALCULATE (
    DISTINCTCOUNT ( dim_date[Rok] ),
    FILTER ( fact_step_execution, fact_step_execution[blocker_reason] <> "" )
)

Blokada powtarzalna =
VAR Wystąpienia = [Kroki zablokowane]
VAR Lata = [Lata wystepowania blokady]
RETURN IF ( Wystąpienia >= 10 && Lata >= 3, "wniosek systemowy", "incydentalna" )
```

## 5. Jakość asystenta

```dax
Zapytania do asystenta = COUNTROWS ( fact_assistant_query )

Trafnosc routingu % =
DIVIDE (
    CALCULATE ( [Zapytania do asystenta], fact_assistant_query[is_correct] = TRUE () ),
    [Zapytania do asystenta]
)

Mediana czasu odpowiedzi (ms) =
MEDIANX ( fact_assistant_query, fact_assistant_query[latency_ms] )

P95 czasu odpowiedzi (ms) =
PERCENTILEX.INC ( fact_assistant_query, fact_assistant_query[latency_ms], 0.95 )

Ocena pomocne % =
DIVIDE (
    CALCULATE ( [Zapytania do asystenta], fact_assistant_query[feedback] = "pomocne" ),
    CALCULATE ( [Zapytania do asystenta], fact_assistant_query[feedback] <> "brak oceny" )
)

Zapytania niskiej pewnosci =
CALCULATE ( [Zapytania do asystenta], fact_assistant_query[confidence] < 0.45 )
```

## 6. Pokrycie korpusu i gotowość dokumentacyjna

```dax
Procedury w korpusie = DISTINCTCOUNT ( dim_procedure[procedure_code] )

Fragmenty korpusu = COUNTROWS ( corpus_chunk )

Kroki bez dokumentu wyjsciowego =
CALCULATE ( COUNTROWS ( dim_step ), dim_step[output_document] = "" )

Pokrycie zagrożeń procedurami % =
DIVIDE (
    CALCULATE ( DISTINCTCOUNT ( bridge_procedure_hazard[hazard_code] ) ),
    DISTINCTCOUNT ( dim_hazard[hazard_code] )
)
```

## 7. Scenariusz osiowy

```dax
Uruchomienia POWODZ WRZESIEN =
CALCULATE ( [Uruchomienia procedur], fact_activation[event_name] = "POWODZ WRZESIEN" )

Dotrzymanie SLA - powódź % =
CALCULATE ( [Dotrzymanie SLA %], fact_step_execution[event_name] = "POWODZ WRZESIEN" )

Roznica SLA powódź vs historia (p.p.) =
( [Dotrzymanie SLA - powódź %]
  - CALCULATE ( [Dotrzymanie SLA %], fact_step_execution[event_name] <> "POWODZ WRZESIEN" ) ) * 100
```
