# -*- coding: utf-8 -*-
"""Treść korpusu procedur dla demo ol-spo-copilot.

UWAGA: wszystkie treści są SYNTETYCZNE i uproszczone. Odwzorowują jedynie
strukturę i logikę Standardowych Procedur Operacyjnych opisanych w KPZK,
ale NIE są odwzorowaniem rzeczywistych dokumentów żadnej instytucji i nie
mogą być wykorzystywane operacyjnie.

Struktura kroku:
    (nr, tytuł, kod_roli, sla_minuty, dokument_wyjściowy, krytyczny)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Role i instytucje
# ---------------------------------------------------------------------------

ROLES = [
    # role_code, nazwa roli, instytucja, poziom
    ("R_DYZ_RCB", "Oficer dyżurny RCB", "Rządowe Centrum Bezpieczeństwa", "krajowy"),
    ("R_DYR_RCB", "Dyrektor RCB", "Rządowe Centrum Bezpieczeństwa", "krajowy"),
    ("R_ANAL_RCB", "Zespół analiz RCB", "Rządowe Centrum Bezpieczeństwa", "krajowy"),
    ("R_SEKR_RZZK", "Sekretarz RZZK", "Rządowe Centrum Bezpieczeństwa", "krajowy"),
    ("R_RZECZ", "Rzecznik prasowy", "Rządowe Centrum Bezpieczeństwa", "krajowy"),
    ("R_MIN_WIOD", "Minister wiodący", "Ministerstwo wiodące", "krajowy"),
    ("R_MSWIA", "Departament ZK MSWiA", "Ministerstwo Spraw Wewnętrznych i Administracji", "krajowy"),
    ("R_MON", "Centrum Zarządzania Kryzysowego MON", "Ministerstwo Obrony Narodowej", "krajowy"),
    ("R_MSZ", "Sztab Kryzysowy MSZ", "Ministerstwo Spraw Zagranicznych", "krajowy"),
    ("R_MF", "Departament Budżetu MF", "Ministerstwo Finansów", "krajowy"),
    ("R_MZ", "Centrum Zarządzania Kryzysowego MZ", "Ministerstwo Zdrowia", "krajowy"),
    ("R_KGP", "Komenda Główna Policji", "Policja", "krajowy"),
    ("R_KGPSP", "Komenda Główna PSP", "Państwowa Straż Pożarna", "krajowy"),
    ("R_KGSG", "Komenda Główna Straży Granicznej", "Straż Graniczna", "krajowy"),
    ("R_ABW", "Agencja Bezpieczeństwa Wewnętrznego", "ABW", "krajowy"),
    ("R_CSIRT", "CSIRT NASK / CSIRT GOV", "Zespoły reagowania na incydenty", "krajowy"),
    ("R_WOJ", "Wojewoda / WCZK", "Urząd Wojewódzki", "wojewódzki"),
    ("R_STAR", "Starosta / PCZK", "Starostwo Powiatowe", "powiatowy"),
    ("R_WOJT", "Wójt, burmistrz, prezydent miasta", "Urząd Gminy", "gminny"),
    ("R_OPER_IK", "Operator infrastruktury krytycznej", "Podmiot IK", "operatorski"),
    ("R_RCL", "Rządowe Centrum Legislacji", "RCL", "krajowy"),
    ("R_KPRM", "Kancelaria Prezesa Rady Ministrów", "KPRM", "krajowy"),
]

# ---------------------------------------------------------------------------
# 16 Standardowych Procedur Operacyjnych
# ---------------------------------------------------------------------------

PROCEDURES = [
    {
        "code": "SPO-1",
        "name": "Organizacja posiedzenia Rządowego Zespołu Zarządzania Kryzysowego",
        "owner_role": "R_SEKR_RZZK",
        "hazards": ["Z01", "Z02", "Z04", "Z07", "Z17"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa z 26 kwietnia 2007 r. o zarządzaniu kryzysowym, art. 8-9",
        "purpose": (
            "Zapewnienie sprawnego zwołania i obsługi posiedzenia RZZK jako organu "
            "opiniodawczo-doradczego Rady Ministrów w sprawach inicjowania i koordynowania "
            "działań podejmowanych w zakresie zarządzania kryzysowego."
        ),
        "triggers": [
            "wniosek ministra wiodącego o zwołanie posiedzenia RZZK",
            "sytuacja kryzysowa angażująca kilku ministrów",
            "wyczerpanie sił i środków ministra wiodącego",
            "rekomendacja Dyrektora RCB po analizie obrazu sytuacji",
        ],
        "keywords": ["RZZK", "posiedzenie", "premier", "zwołanie zespołu", "rekomendacje rządowe"],
        "steps": [
            (1, "Przyjęcie i rejestracja wniosku o zwołanie posiedzenia RZZK", "R_DYZ_RCB", 30, "Karta rejestracji wniosku", True),
            (2, "Weryfikacja przesłanek ustawowych i zakresu przedmiotowego posiedzenia", "R_DYR_RCB", 60, "", True),
            (3, "Uzgodnienie terminu i trybu posiedzenia: stacjonarny, zdalny lub obiegowy", "R_SEKR_RZZK", 60, "Decyzja o trybie posiedzenia", True),
            (4, "Powiadomienie członków RZZK oraz uczestników zaproszonych", "R_SEKR_RZZK", 45, "Lista powiadomień", True),
            (5, "Przygotowanie raportu sytuacyjnego i projektu porządku obrad", "R_ANAL_RCB", 120, "Raport sytuacyjny RCB", True),
            (6, "Uzgodnienie projektów rekomendacji z ministrem wiodącym", "R_DYR_RCB", 120, "Projekt rekomendacji", False),
            (7, "Zapewnienie warunków organizacyjno-technicznych i łączności niejawnej", "R_KPRM", 90, "", False),
            (8, "Obsługa posiedzenia i protokołowanie przebiegu", "R_SEKR_RZZK", 180, "Protokół posiedzenia", True),
            (9, "Sporządzenie i dystrybucja ustaleń oraz wykazu zadań", "R_SEKR_RZZK", 240, "Wykaz zadań po posiedzeniu", True),
            (10, "Monitorowanie realizacji zadań i raport zwrotny do Przewodniczącego", "R_ANAL_RCB", 1440, "Raport z realizacji zadań", False),
        ],
    },
    {
        "code": "SPO-2",
        "name": "Uruchomienie dodatkowych środków finansowych",
        "owner_role": "R_MF",
        "hazards": ["Z02", "Z07", "Z08", "Z19"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o finansach publicznych - rezerwa celowa na zarządzanie kryzysowe",
        "purpose": (
            "Uruchomienie środków z rezerwy celowej lub ogolnej budżetu państwa na "
            "przeciwdziałanie skutkom sytuacji kryzysowej oraz usuwanie tych skutków."
        ),
        "triggers": [
            "wniosek wojewody o środki na usuwanie skutków zdarzenia",
            "wyczerpanie limitu wydatków ministra wiodącego",
            "konieczność zakupu zasobów z rezerw strategicznych",
            "decyzja RZZK o wsparciu finansowym samorządów",
        ],
        "keywords": ["rezerwa celowa", "środki finansowe", "promesa", "dotacja", "budżet kryzysowy"],
        "steps": [
            (1, "Przyjęcie wniosku wojewody lub ministra o uruchomienie środków", "R_MF", 60, "Wniosek o środki", True),
            (2, "Weryfikacja formalna wniosku i kompletności kosztorysu", "R_MF", 120, "Protokół weryfikacji", True),
            (3, "Ocena zasadności merytorycznej i związku wydatku ze zdarzeniem", "R_MSWIA", 240, "Opinia merytoryczna", True),
            (4, "Uzgodnienie źródła finansowania i limitu z Ministrem Finansów", "R_MF", 480, "", True),
            (5, "Przygotowanie projektu decyzji o zmianie w budżecie państwa", "R_MF", 480, "Projekt decyzji budżetowej", True),
            (6, "Uzyskanie opinii RZZK, jeśli wymagana zakresem zdarzenia", "R_SEKR_RZZK", 720, "Opinia RZZK", False),
            (7, "Wydanie decyzji i przekazanie jej dysponentowi części budżetowej", "R_MF", 240, "Decyzja o uruchomieniu środków", True),
            (8, "Uruchomienie transzy i powiadomienie beneficjenta", "R_WOJ", 240, "Zawiadomienie o transzy", False),
            (9, "Monitoring wydatkowania i sprawozdawczość okresowa", "R_WOJ", 2880, "Sprawozdanie z wydatkowania", False),
            (10, "Rozliczenie końcowe i kontrola wykorzystania środków", "R_MF", 4320, "Protokół rozliczenia", False),
        ],
    },
    {
        "code": "SPO-3",
        "name": "Zasady informowania ludności o zagrożeniach - organizacja procesu komunikacji społecznej w sytuacji kryzysowej",
        "owner_role": "R_RZECZ",
        "hazards": ["Z01", "Z02", "Z07", "Z13", "Z17", "Z20"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o zarządzaniu kryzysowym; ustawa Prawo telekomunikacyjne - Alert RCB",
        "purpose": (
            "Zapewnienie ludności szybkiej, spójnej i zrozumiałej informacji o zagrożeniu, "
            "zasadach postępowania i działaniach administracji oraz przeciwdziałanie panice "
            "i dezinformacji."
        ),
        "triggers": [
            "wystąpienie zagrożenia życia lub zdrowia ludności",
            "przekroczenie stanów alarmowych i konieczność ewakuacji",
            "rozpowszechnianie nieprawdziwych informacji o zdarzeniu",
            "decyzja RZZK o uruchomieniu komunikacji kryzysowej",
        ],
        "keywords": ["Alert RCB", "RSO", "komunikat", "rzecznik", "informowanie ludności", "dezinformacja"],
        "steps": [
            (1, "Ocena sytuacji informacyjnej i identyfikacja grup odbiorców", "R_ANAL_RCB", 30, "Analiza odbiorców", True),
            (2, "Wyznaczenie rzecznika wiodącego i wdrożenie zasady jednego głosu", "R_DYR_RCB", 30, "Decyzja o rzeczniku wiodącym", True),
            (3, "Przygotowanie komunikatu bazowego oraz wersji uproszczonej", "R_RZECZ", 45, "Komunikat ostrzegawczy", True),
            (4, "Przygotowanie wersji obcojęzycznych i dostępnych dla osób z niepełnosprawnościami", "R_RZECZ", 60, "Wersje językowe komunikatu", False),
            (5, "Dobór kanałów: Alert RCB, RSO, media, syreny, kanały samorządowe", "R_DYR_RCB", 30, "Plan dystrybucji", True),
            (6, "Zatwierdzenie treści przez ministra wiodącego lub Dyrektora RCB", "R_MIN_WIOD", 30, "Akceptacja treści", True),
            (7, "Emisja komunikatu i potwierdzenie dystrybucji w kanałach", "R_DYZ_RCB", 15, "Potwierdzenie emisji", True),
            (8, "Monitoring odbioru komunikatu oraz narracji dezinformacyjnych", "R_ANAL_RCB", 120, "Raport monitoringu", False),
            (9, "Publikacja sprostowań i aktualizacji cyklicznych", "R_RZECZ", 180, "Sprostowanie", False),
            (10, "Briefing prasowy lub konferencja z udziałem ministra wiodącego", "R_RZECZ", 240, "Notatka z briefingu", False),
            (11, "Archiwizacja komunikatów i ocena skuteczności dotarcia", "R_ANAL_RCB", 1440, "Raport skuteczności", False),
        ],
    },
    {
        "code": "SPO-4",
        "name": "Tymczasowe przywrócenie kontroli granicznej na granicach RP",
        "owner_role": "R_MSWIA",
        "hazards": ["Z04", "Z16", "Z18"],
        "phase": "reagowanie",
        "legal_basis": "Kodeks graniczny Schengen; ustawa o ochronie granicy państwowej",
        "purpose": (
            "Przygotowanie i wdrożenie tymczasowego przywrócenia kontroli granicznej na "
            "granicach wewnętrznych w przypadku poważnego zagrożenia porządku publicznego "
            "lub bezpieczeństwa wewnętrznego."
        ),
        "triggers": [
            "poważne zagrożenie porządku publicznego lub bezpieczeństwa wewnętrznego",
            "masowy niekontrolowany napływ osób przez granicę wewnętrzną",
            "impreza masowa o charakterze międzynarodowym wysokiego ryzyka",
            "zagrożenie terrorystyczne o charakterze transgranicznym",
        ],
        "keywords": ["kontrola graniczna", "Schengen", "granica wewnętrzna", "Straż Graniczna", "notyfikacja KE"],
        "steps": [
            (1, "Analiza przesłanek zagrożenia porządku publicznego i bezpieczeństwa", "R_ABW", 240, "Ocena zagrożenia", True),
            (2, "Ocena skutków dla ruchu granicznego, transportu i gospodarki", "R_MSWIA", 480, "Ocena skutków", False),
            (3, "Uzgodnienie zakresu, odcinków i czasu kontroli z KG SG", "R_KGSG", 240, "Plan rozwinięcia kontroli", True),
            (4, "Notyfikacja Komisji Europejskiej i państw członkowskich", "R_MSZ", 480, "Notyfikacja KE", True),
            (5, "Opracowanie projektu rozporządzenia MSWiA", "R_MSWIA", 480, "Projekt rozporządzenia", True),
            (6, "Uzgodnienia międzyresortowe i opinia RCL", "R_RCL", 720, "Opinia RCL", False),
            (7, "Przyjęcie i publikacja rozporządzenia", "R_KPRM", 240, "Rozporządzenie", True),
            (8, "Rozwinięcie przejść granicznych i sił Straży Granicznej", "R_KGSG", 720, "Meldunek o gotowości", True),
            (9, "Komunikacja do podróżnych i przewoźników w trybie SPO-3", "R_RZECZ", 120, "Komunikat dla podróżnych", False),
            (10, "Cykliczna ocena zasadności utrzymania lub przedłużenia kontroli", "R_MSWIA", 2880, "Raport oceny", False),
        ],
    },
    {
        "code": "SPO-5",
        "name": "Wprowadzenie stanu klęski żywiołowej",
        "owner_role": "R_MSWIA",
        "hazards": ["Z01", "Z02", "Z07", "Z08", "Z10", "Z19"],
        "phase": "reagowanie",
        "legal_basis": "Konstytucja RP art. 228 i 232; ustawa z 18 kwietnia 2002 r. o stanie klęski żywiołowej",
        "purpose": (
            "Przygotowanie i wprowadzenie stanu klęski żywiołowej na obszarze dotkniętym "
            "zdarzeniem, gdy zwykle środki konstytucyjne są niewystarczające do zapobieżenia "
            "skutkom katastrofy naturalnej lub awarii technicznej."
        ),
        "triggers": [
            "niewystarczające siły i środki wojewody na obszarze zdarzenia",
            "katastrofa naturalna o zasięgu ponadwojewódzkim",
            "wniosek wojewody o wprowadzenie stanu klęski żywiołowej",
            "konieczność wprowadzenia ograniczeń wolności i praw człowieka",
        ],
        "keywords": ["stan klęski żywiołowej", "rozporządzenie Rady Ministrów", "ograniczenia praw", "pełnomocnik"],
        "steps": [
            (1, "Przyjęcie wniosku wojewody lub ministra o wprowadzenie stanu", "R_MSWIA", 120, "Wniosek o wprowadzenie stanu", True),
            (2, "Ocena, czy siły i środki na niższych poziomach są niewystarczające", "R_ANAL_RCB", 240, "Analiza sił i środków", True),
            (3, "Określenie obszaru obowiązywania i przewidywanego czasu trwania", "R_MSWIA", 240, "Załącznik terytorialny", True),
            (4, "Opracowanie projektu rozporządzenia Rady Ministrów", "R_MSWIA", 480, "Projekt rozporządzenia RM", True),
            (5, "Określenie katalogu ograniczeń wolności i praw człowieka", "R_RCL", 240, "Katalog ograniczeń", True),
            (6, "Rozpatrzenie projektu przez Rade Ministrów", "R_KPRM", 480, "Rozporządzenie RM", True),
            (7, "Przekazanie rozporządzenia Sejmowi RP", "R_KPRM", 120, "Pismo przewodnie do Sejmu", True),
            (8, "Publikacja i ogłoszenie stanu w mediach w trybie SPO-3", "R_RZECZ", 60, "Komunikat o stanie", True),
            (9, "Wyznaczenie pełnomocnika i trybu kierowania działaniami", "R_MSWIA", 240, "Decyzja o pełnomocniku", False),
            (10, "Raportowanie okresowe i wniosek o zniesienie stanu", "R_WOJ", 2880, "Raport okresowy", False),
        ],
    },
    {
        "code": "SPO-6",
        "name": "Wprowadzenie stanu wyjątkowego",
        "owner_role": "R_MSWIA",
        "hazards": ["Z04", "Z16", "Z18"],
        "phase": "reagowanie",
        "legal_basis": "Konstytucja RP art. 230; ustawa z 21 czerwca 2002 r. o stanie wyjątkowym",
        "purpose": (
            "Przygotowanie wprowadzenia stanu wyjątkowego w razie zagrożenia konstytucyjnego "
            "ustroju państwa, bezpieczeństwa obywateli lub porządku publicznego."
        ),
        "triggers": [
            "zagrożenie konstytucyjnego ustroju państwa",
            "masowe zakłócenia porządku publicznego niemożliwe do opanowania",
            "działania o charakterze hybrydowym wymierzone w bezpieczeństwo wewnętrzne",
        ],
        "keywords": ["stan wyjątkowy", "porządek publiczny", "Prezydent RP", "rozporządzenie"],
        "steps": [
            (1, "Analiza zagrożenia i przesłanek konstytucyjnych", "R_ABW", 240, "Ocena zagrożenia", True),
            (2, "Przygotowanie wniosku Rady Ministrów do Prezydenta RP", "R_MSWIA", 480, "Wniosek RM", True),
            (3, "Określenie obszaru, czasu i zakresu ograniczeń", "R_MSWIA", 240, "Załącznik do wniosku", True),
            (4, "Opinia RCL i uzgodnienia międzyresortowe", "R_RCL", 480, "Opinia RCL", False),
            (5, "Rozpatrzenie wniosku przez Rade Ministrów", "R_KPRM", 480, "Uchwała RM", True),
            (6, "Wydanie rozporządzenia przez Prezydenta RP", "R_KPRM", 720, "Rozporządzenie Prezydenta RP", True),
            (7, "Przedstawienie rozporządzenia Sejmowi RP", "R_KPRM", 120, "Pismo do Sejmu", True),
            (8, "Komunikacja społeczna i informowanie ludności w trybie SPO-3", "R_RZECZ", 60, "Komunikat", True),
            (9, "Monitoring stosowania ograniczeń i raportowanie", "R_MSWIA", 2880, "Raport okresowy", False),
        ],
    },
    {
        "code": "SPO-7",
        "name": "Wprowadzenie stanu wojennego",
        "owner_role": "R_MON",
        "hazards": ["Z04", "Z16"],
        "phase": "reagowanie",
        "legal_basis": "Konstytucja RP art. 229; ustawa z 29 sierpnia 2002 r. o stanie wojennym",
        "purpose": (
            "Przygotowanie wprowadzenia stanu wojennego w razie zewnętrznego zagrożenia "
            "państwa, zbrojnej napaści lub zobowiązań sojuszniczych do wspólnej obrony."
        ),
        "triggers": [
            "zewnętrzne zagrożenie państwa",
            "zbrojna napaść na terytorium RP",
            "zobowiązanie sojusznicze do wspólnej obrony przeciwko agresji",
        ],
        "keywords": ["stan wojenny", "Naczelny Dowódca", "obrona państwa", "Prezydent RP"],
        "steps": [
            (1, "Ocena zagrożenia zewnętrznego i rekomendacja MON", "R_MON", 180, "Ocena zagrożenia", True),
            (2, "Przygotowanie wniosku Rady Ministrów do Prezydenta RP", "R_MON", 360, "Wniosek RM", True),
            (3, "Określenie obszaru objętego stanem wojennym", "R_MON", 240, "Załącznik terytorialny", True),
            (4, "Uzgodnienia z MSWiA, MSZ i BBN", "R_MSZ", 360, "Protokół uzgodnień", False),
            (5, "Rozpatrzenie wniosku przez Rade Ministrów", "R_KPRM", 360, "Uchwała RM", True),
            (6, "Wydanie rozporządzenia przez Prezydenta RP", "R_KPRM", 480, "Rozporządzenie Prezydenta RP", True),
            (7, "Przedstawienie rozporządzenia Sejmowi RP", "R_KPRM", 120, "Pismo do Sejmu", True),
            (8, "Uruchomienie systemu kierowania obrona państwa", "R_MON", 720, "Meldunek o uruchomieniu", True),
            (9, "Informowanie ludności i sojuszników", "R_RZECZ", 120, "Komunikat", True),
        ],
    },
    {
        "code": "SPO-8",
        "name": "Postępowanie w sytuacji uprowadzenia terrorystycznego obywatela polskiego poza obszarem RP",
        "owner_role": "R_MSZ",
        "hazards": ["Z16"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o działaniach antyterrorystycznych; prawo konsularne",
        "purpose": (
            "Skoordynowanie działań służb i resortów w przypadku uprowadzenia obywatela RP "
            "poza granicami kraju przez organizację o charakterze terrorystycznym."
        ),
        "triggers": [
            "wiarygodna informacja o uprowadzeniu obywatela RP za granica",
            "zadanie okupu lub zadanie polityczne wobec RP",
            "wniosek rodziny lub pracodawcy o pomoc konsularna",
        ],
        "keywords": ["uprowadzenie", "zakładnik", "konsul", "antyterroryzm", "negocjacje"],
        "steps": [
            (1, "Weryfikacja informacji o uprowadzeniu i ustalenie tożsamości", "R_MSZ", 120, "Notatka weryfikacyjna", True),
            (2, "Powiadomienie Zespołu do spraw Incydentów Krytycznych", "R_MSZ", 60, "Zawiadomienie ZIK", True),
            (3, "Powołanie sztabu kryzysowego MSZ i wyznaczenie koordynatora", "R_MSZ", 120, "Decyzja o powołaniu sztabu", True),
            (4, "Nawiązanie współpracy z placówka dyplomatyczna i służbami państwa pobytu", "R_MSZ", 240, "Protokół współpracy", True),
            (5, "Ocena wiarygodności zadań i analiza zagrożenia", "R_ABW", 240, "Analiza zagrożenia", True),
            (6, "Ustalenie strategii postępowania i zasad kontaktu", "R_MSZ", 360, "Strategia postępowania", True),
            (7, "Opieka nad rodzina i zapewnienie wsparcia psychologicznego", "R_MSZ", 240, "Plan wsparcia rodziny", False),
            (8, "Zarządzanie informacja publiczna i ochrona danych osoby uprowadzonej", "R_RZECZ", 120, "Zasady komunikacji", True),
            (9, "Przygotowanie i realizacja operacji uwolnienia lub przekazania", "R_MON", 1440, "Plan operacji", False),
            (10, "Powrót, pomoc medyczna i psychologiczna oraz raport końcowy", "R_MSZ", 2880, "Raport końcowy", False),
        ],
    },
    {
        "code": "SPO-9",
        "name": "Działania w przypadku masowego napływu cudzoziemców na terytorium RP",
        "owner_role": "R_MSWIA",
        "hazards": ["Z04", "Z09", "Z18"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o udzielaniu cudzoziemcom ochrony; ustawa o zarządzaniu kryzysowym",
        "purpose": (
            "Zapewnienie przyjęcia, rejestracji, zakwaterowania i obsługi socjalnej dużej "
            "liczby cudzoziemców przekraczających granicę RP w krótkim czasie."
        ),
        "triggers": [
            "gwałtowny wzrost liczby osób przekraczających granicę",
            "konflikt zbrojny lub katastrofa w państwie sąsiednim",
            "instrumentalne wykorzystanie migracji jako element działań hybrydowych",
        ],
        "keywords": ["napływ cudzoziemców", "recepcja", "punkt przyjęcia", "rejestracja", "zakwaterowanie"],
        "steps": [
            (1, "Monitoring i prognoza liczby osób przekraczających granicę", "R_KGSG", 120, "Prognoza napływu", True),
            (2, "Uruchomienie punktów recepcyjnych i rejestracji", "R_WOJ", 240, "Wykaz punktów recepcyjnych", True),
            (3, "Zapewnienie zakwaterowania, wyżywienia i opieki medycznej", "R_WOJ", 480, "Plan zabezpieczenia socjalnego", True),
            (4, "Wsparcie tłumaczy i informacji w językach obcych", "R_MSWIA", 240, "Plan wsparcia językowego", False),
            (5, "Weryfikacja tożsamości i kontrola bezpieczeństwa", "R_ABW", 360, "Protokół weryfikacji", True),
            (6, "Koordynacja z organizacjami pozarządowymi i samorządami", "R_WOJ", 360, "Porozumienie o współpracy", False),
            (7, "Uruchomienie środków finansowych w trybie SPO-2", "R_MF", 720, "Wniosek o środki", False),
            (8, "Ochrona osób małoletnich bez opieki i osób wrażliwych", "R_MSWIA", 360, "Rejestr osób wrażliwych", True),
            (9, "Komunikacja społeczna i przeciwdziałanie dezinformacji", "R_RZECZ", 180, "Komunikat", False),
            (10, "Raportowanie dobowe i ocena wydolności systemu", "R_MSWIA", 1440, "Raport dobowy", False),
        ],
    },
    {
        "code": "SPO-10",
        "name": "Współpraca między administracja publiczna a właścicielami oraz posiadaczami obiektów infrastruktury krytycznej w zakresie jej ochrony",
        "owner_role": "R_DYR_RCB",
        "hazards": ["Z03", "Z04", "Z07", "Z12", "Z14", "Z16"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o zarządzaniu kryzysowym, art. 6; Narodowy Program Ochrony Infrastruktury Krytycznej",
        "purpose": (
            "Zapewnienie wymiany informacji i skoordynowanych działań między administracja a "
            "operatorami infrastruktury krytycznej w celu ochrony IK i szybkiego odtworzenia "
            "jej funkcji po zdarzeniu."
        ),
        "triggers": [
            "zagrożenie lub uszkodzenie obiektu infrastruktury krytycznej",
            "kaskadowa awaria wynikająca ze współzależności systemów IK",
            "podwyższenie stopnia alarmowego CRP",
            "wniosek operatora IK o wsparcie administracji",
        ],
        "keywords": ["infrastruktura krytyczna", "operator IK", "NPOIK", "odtworzenie funkcji", "efekt domina"],
        "steps": [
            (1, "Przyjęcie zgłoszenia o zagrożeniu obiektu IK i jego rejestracja", "R_DYZ_RCB", 30, "Karta zgłoszenia IK", True),
            (2, "Identyfikacja systemu IK i właściwego ministra odpowiedzialnego", "R_ANAL_RCB", 60, "Karta identyfikacji", True),
            (3, "Nawiązanie kontaktu z operatorem i wyznaczenie punktu styku", "R_OPER_IK", 60, "Lista punktów kontaktowych", True),
            (4, "Ocena skutków wtórnych i zależności międzysystemowych", "R_ANAL_RCB", 180, "Analiza współzależności", True),
            (5, "Ustalenie priorytetów zasilania i przywracania funkcji", "R_MIN_WIOD", 240, "Lista priorytetów", True),
            (6, "Uzgodnienie wsparcia sił i środków administracji dla operatora", "R_WOJ", 240, "Protokół uzgodnień", False),
            (7, "Wprowadzenie ograniczeń lub reglamentacji, jeśli konieczne", "R_MIN_WIOD", 480, "Decyzja o ograniczeniach", False),
            (8, "Monitorowanie odtwarzania funkcji i raportowanie postępu", "R_OPER_IK", 720, "Raport odtworzenia", True),
            (9, "Informowanie odbiorców usług o przewidywanym czasie przywrócenia", "R_RZECZ", 120, "Komunikat dla odbiorców", False),
            (10, "Wnioski i aktualizacja planu ochrony IK po zdarzeniu", "R_DYR_RCB", 4320, "Raport po zdarzeniu", False),
        ],
    },
    {
        "code": "SPO-11",
        "name": "Organizacja ewakuacji obywateli polskich spoza granic kraju",
        "owner_role": "R_MSZ",
        "hazards": ["Z04", "Z16", "Z15"],
        "phase": "reagowanie",
        "legal_basis": "Prawo konsularne; ustawa o zarządzaniu kryzysowym",
        "purpose": (
            "Organizacja bezpiecznego powrotu obywateli RP przebywających na obszarze objętym "
            "konfliktem, katastrofa lub innym zagrożeniem, we współpracy z partnerami UE i NATO."
        ),
        "triggers": [
            "eskalacja konfliktu zbrojnego w państwie pobytu obywateli RP",
            "katastrofa naturalna lub epidemia uniemożliwiająca powrót",
            "zamknięcie przestrzeni powietrznej państwa pobytu",
        ],
        "keywords": ["ewakuacja z zagranicy", "most powietrzny", "konsul", "rejestracja Odyseusz", "repatriacja"],
        "steps": [
            (1, "Ocena zagrożenia w państwie pobytu i decyzja o ewakuacji", "R_MSZ", 240, "Ocena zagrożenia", True),
            (2, "Ustalenie liczby i lokalizacji obywateli RP", "R_MSZ", 360, "Wykaz osób do ewakuacji", True),
            (3, "Uruchomienie infolinii i kanałów zgłoszeniowych", "R_MSZ", 120, "Procedura infolinii", True),
            (4, "Wybór wariantu transportu i tras ewakuacji", "R_MON", 360, "Plan transportu", True),
            (5, "Uzgodnienia z państwem pobytu i państwami tranzytu", "R_MSZ", 480, "Zgody dyplomatyczne", True),
            (6, "Koordynacja z mechanizmem ochrony ludności UE i sojusznikami", "R_MSZ", 480, "Wniosek do UCPM", False),
            (7, "Organizacja punktów zbornych i eskorty", "R_MON", 480, "Plan punktów zbornych", True),
            (8, "Realizacja przerzutu i odprawa po przylocie", "R_MON", 1440, "Meldunek z realizacji", True),
            (9, "Pomoc medyczna, socjalna i psychologiczna po powrocie", "R_MZ", 720, "Plan pomocy", False),
            (10, "Rozliczenie kosztów i raport końcowy", "R_MSZ", 4320, "Raport końcowy", False),
        ],
    },
    {
        "code": "SPO-12",
        "name": "Obieg informacji pomiedzy krajowymi organami i strukturami zarządzania kryzysowego",
        "owner_role": "R_DYZ_RCB",
        "hazards": ["Z01", "Z02", "Z03", "Z04", "Z07", "Z12"],
        "phase": "przygotowanie",
        "legal_basis": "Ustawa o zarządzaniu kryzysowym, art. 11 - zadania RCB",
        "purpose": (
            "Zapewnienie ciągłego, jednolitego i udokumentowanego obiegu informacji między "
            "centrami zarządzania kryzysowego wszystkich poziomów oraz służbami."
        ),
        "triggers": [
            "wystąpienie zdarzenia o potencjale kryzysowym",
            "zapytanie ministra wiodącego o obraz sytuacji",
            "przekroczenie progu meldunkowego przez CZK niższego szczebla",
        ],
        "keywords": ["meldunek", "raport dobowy", "obieg informacji", "CZK", "dyżur"],
        "steps": [
            (1, "Przyjęcie meldunku z CZK i nadanie numeru ewidencyjnego", "R_DYZ_RCB", 15, "Meldunek wejściowy", True),
            (2, "Weryfikacja i uzupełnienie danych u źródła", "R_DYZ_RCB", 30, "", True),
            (3, "Klasyfikacja zdarzenia wg katalogu zagrożeń Z01-Z20", "R_ANAL_RCB", 30, "Karta klasyfikacji", True),
            (4, "Sporządzenie raportu sytuacyjnego dla kierownictwa", "R_ANAL_RCB", 60, "Raport sytuacyjny", True),
            (5, "Dystrybucja raportu do adresatów zgodnie z lista rozdzielnika", "R_DYZ_RCB", 30, "Rozdzielnik", True),
            (6, "Aktualizacja obrazu sytuacji i zasilenie COP", "R_ANAL_RCB", 60, "Aktualizacja COP", False),
            (7, "Sporządzenie raportu dobowego", "R_ANAL_RCB", 1440, "Raport dobowy", False),
            (8, "Archiwizacja i zapewnienie śladu audytowego", "R_DYZ_RCB", 1440, "", False),
        ],
    },
    {
        "code": "SPO-13",
        "name": "Ostrzeganie i alarmowanie wojsk oraz ludności cywilnej o zagrożeniu uderzeniami z powietrza",
        "owner_role": "R_MON",
        "hazards": ["Z04", "Z16"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o obronie Ojczyzny; przepisy o systemie wykrywania i alarmowania",
        "purpose": (
            "Zapewnienie natychmiastowego ostrzeżenia wojsk i ludności cywilnej o zagrożeniu "
            "uderzeniami z powietrza oraz uruchomienie zachowań ochronnych."
        ),
        "triggers": [
            "wykrycie obiektu powietrznego naruszającego przestrzeń powietrzna RP",
            "informacja sojusznicza o zagrożeniu z powietrza",
            "wykrycie bezzałogowego statku powietrznego nad obiektem chronionym",
        ],
        "keywords": ["alarm powietrzny", "syreny", "system wykrywania i alarmowania", "SWA", "przestrzeń powietrzna"],
        "steps": [
            (1, "Przyjęcie informacji o zagrożeniu z systemu obrony powietrznej", "R_MON", 5, "Meldunek o zagrożeniu", True),
            (2, "Weryfikacja i ocena wiarygodności sygnału", "R_MON", 10, "", True),
            (3, "Określenie obszaru zagrożonego i sposobu alarmowania", "R_MON", 10, "Decyzja o zasięgu alarmu", True),
            (4, "Przekazanie sygnału do wojewódzkich centrów zarządzania kryzysowego", "R_MON", 5, "Sygnał alarmowy", True),
            (5, "Uruchomienie syren i systemów alarmowych na obszarze zagrożonym", "R_WOJ", 10, "Potwierdzenie uruchomienia", True),
            (6, "Emisja komunikatu do ludności w kanałach masowych", "R_RZECZ", 15, "Komunikat alarmowy", True),
            (7, "Koordynacja z operatorami lotnisk i zarządca przestrzeni powietrznej", "R_MON", 30, "Protokół koordynacji", False),
            (8, "Odwołanie alarmu i komunikat o zakończeniu zagrożenia", "R_MON", 15, "Sygnał odwołania alarmu", True),
            (9, "Analiza przebiegu alarmowania i wnioski", "R_MON", 1440, "Raport z alarmowania", False),
        ],
    },
    {
        "code": "SPO-14",
        "name": "Przekraczanie granic RP przez wojska sojusznicze w celu pobytu lub tranzytu",
        "owner_role": "R_MON",
        "hazards": ["Z04", "Z16"],
        "phase": "przygotowanie",
        "legal_basis": "Ustawa o zasadach pobytu wojsk obcych na terytorium RP; NATO SOFA",
        "purpose": (
            "Zapewnienie sprawnego i zgodnego z prawem przekraczania granicy RP przez wojska "
            "sojusznicze oraz ich pobytu lub przemieszczania po terytorium kraju."
        ),
        "triggers": [
            "wniosek państwa sojuszniczego o tranzyt lub pobyt wojsk",
            "ćwiczenie sojusznicze na terytorium RP",
            "wzmocnienie wschodniej flanki w reakcji na zagrożenie",
        ],
        "keywords": ["wojska sojusznicze", "HNS", "tranzyt", "NATO", "przekraczanie granicy"],
        "steps": [
            (1, "Przyjęcie i weryfikacja wniosku państwa wysyłającego", "R_MON", 480, "Wniosek o zgodę", True),
            (2, "Uzgodnienia z MSZ i MSWiA w zakresie zgód i kontroli", "R_MSZ", 480, "Protokół uzgodnień", True),
            (3, "Przygotowanie projektu zgody właściwego organu", "R_MON", 720, "Projekt zgody", True),
            (4, "Ustalenie tras przemieszczania i harmonogramu", "R_MON", 480, "Plan przemieszczenia", True),
            (5, "Zapewnienie wsparcia państwa gospodarza w zakresie HNS", "R_MON", 720, "Plan HNS", True),
            (6, "Koordynacja z zarządcami dróg i kolei oraz Policja", "R_KGP", 480, "Plan zabezpieczenia ruchu", False),
            (7, "Odprawa graniczna i kontrola dokumentów", "R_KGSG", 240, "Protokół odprawy", True),
            (8, "Monitorowanie przemieszczania i raportowanie", "R_MON", 720, "Meldunek bieżący", False),
            (9, "Rozliczenie pobytu i raport końcowy", "R_MON", 4320, "Raport końcowy", False),
        ],
    },
    {
        "code": "SPO-15",
        "name": "Organizacja medycznego mostu powietrznego w przypadku wystąpienia zdarzenia masowego",
        "owner_role": "R_MZ",
        "hazards": ["Z01", "Z10", "Z13", "Z15", "Z16", "Z17"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o Państwowym Ratownictwie Medycznym; ustawa o zarządzaniu kryzysowym",
        "purpose": (
            "Zapewnienie transportu lotniczego poszkodowanych ze zdarzenia masowego do "
            "szpitali o odpowiednim profilu, w tym poza obszar dotknięty zdarzeniem."
        ),
        "triggers": [
            "zdarzenie masowe przekraczające możliwości szpitali w regionie",
            "konieczność transportu pacjentów oparzeniowych lub skażonych",
            "prośba o wsparcie od wojewody lub dysponenta jednostki PRM",
        ],
        "keywords": ["most powietrzny", "zdarzenie masowe", "LPR", "triage", "MEDEVAC", "szpital docelowy"],
        "steps": [
            (1, "Przyjęcie informacji o zdarzeniu masowym i ocena skali", "R_MZ", 30, "Meldunek o zdarzeniu", True),
            (2, "Ustalenie liczby poszkodowanych i wyników segregacji medycznej", "R_MZ", 60, "Zestawienie triage", True),
            (3, "Identyfikacja szpitali docelowych i wolnych miejsc specjalistycznych", "R_MZ", 90, "Wykaz miejsc szpitalnych", True),
            (4, "Uruchomienie sił LPR i lotnictwa transportowego SZ RP", "R_MON", 120, "Zapotrzebowanie na statki powietrzne", True),
            (5, "Wyznaczenie lotnisk i lądowisk operacyjnych", "R_MON", 120, "Plan lotnisk", True),
            (6, "Koordynacja przestrzeni powietrznej i priorytetów lotów", "R_MON", 60, "Uzgodnienie z ATM", True),
            (7, "Organizacja transportu naziemnego na obu końcach mostu", "R_WOJ", 120, "Plan transportu naziemnego", False),
            (8, "Zabezpieczenie medyczne w trakcie transportu", "R_MZ", 60, "Karta transportu medycznego", True),
            (9, "Ewidencja pacjentów i informacja dla rodzin", "R_MZ", 240, "Rejestr pacjentów", False),
            (10, "Raport z realizacji i rozliczenie kosztów", "R_MZ", 2880, "Raport końcowy", False),
        ],
    },
    {
        "code": "SPO-16",
        "name": "Zwołanie i obsługa posiedzenia Zespołu do spraw Incydentów Krytycznych",
        "owner_role": "R_ABW",
        "hazards": ["Z03", "Z04", "Z16"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o działaniach antyterrorystycznych; ustawa o krajowym systemie cyberbezpieczeństwa",
        "purpose": (
            "Zapewnienie szybkiego zwołania i obsługi Zespołu do spraw Incydentów Krytycznych "
            "dla incydentów o charakterze terrorystycznym, hybrydowym lub cybernetycznym."
        ),
        "triggers": [
            "incydent krytyczny w rozumieniu ustawy o krajowym systemie cyberbezpieczeństwa",
            "zdarzenie o charakterze terrorystycznym na terytorium RP",
            "seria skorelowanych incydentów wskazująca na działanie skoordynowane",
            "wniosek CSIRT o zwołanie zespołu",
        ],
        "keywords": ["ZIK", "incydent krytyczny", "cyberbezpieczeństwo", "CSIRT", "stopień alarmowy CRP"],
        "steps": [
            (1, "Przyjęcie zgłoszenia incydentu i wstępna kwalifikacja", "R_CSIRT", 30, "Karta incydentu", True),
            (2, "Ocena, czy incydent spełnia kryteria incydentu krytycznego", "R_ABW", 60, "Ocena kwalifikacyjna", True),
            (3, "Zwołanie Zespołu do spraw Incydentów Krytycznych", "R_ABW", 60, "Zawiadomienie o posiedzeniu", True),
            (4, "Przygotowanie materiału sytuacyjnego o incydencie", "R_CSIRT", 120, "Raport techniczny", True),
            (5, "Uzgodnienie rekomendacji dotyczących stopni alarmowych", "R_ABW", 180, "Rekomendacja stopni alarmowych", True),
            (6, "Koordynacja działań z operatorami usług kluczowych", "R_OPER_IK", 240, "Protokół koordynacji", True),
            (7, "Obsługa posiedzenia i protokołowanie ustaleń", "R_ABW", 180, "Protokół posiedzenia", True),
            (8, "Przekazanie rekomendacji do RZZK lub Prezesa Rady Ministrów", "R_SEKR_RZZK", 120, "Rekomendacje", False),
            (9, "Komunikacja publiczna uzgodniona ze służbami", "R_RZECZ", 180, "Komunikat", False),
            (10, "Raport po incydencie i wnioski do procedur", "R_CSIRT", 4320, "Raport po incydencie", False),
        ],
    },
]

# ---------------------------------------------------------------------------
# Dokumenty towarzyszace: plany wojewodzkie, plany ochrony ludnosci, KPZK
# ---------------------------------------------------------------------------

VOIVODESHIPS = [
    ("02", "dolnośląskie", "Wrocław"),
    ("04", "kujawsko-pomorskie", "Bydgoszcz"),
    ("06", "lubelskie", "Lublin"),
    ("08", "lubuskie", "Gorzów Wielkopolski"),
    ("10", "łódzkie", "Łódź"),
    ("12", "małopolskie", "Kraków"),
    ("14", "mazowieckie", "Warszawa"),
    ("16", "opolskie", "Opole"),
    ("18", "podkarpackie", "Rzeszów"),
    ("20", "podlaskie", "Białystok"),
    ("22", "pomorskie", "Gdańsk"),
    ("24", "śląskie", "Katowice"),
    ("26", "świętokrzyskie", "Kielce"),
    ("28", "warmińsko-mazurskie", "Olsztyn"),
    ("30", "wielkopolskie", "Poznań"),
    ("32", "zachodniopomorskie", "Szczecin"),
]

HAZARDS = [
    ("Z01", "Epidemia", "prawdopodobieństwo: możliwe; skutki: katastrofalne"),
    ("Z02", "Powódź", "prawdopodobieństwo: prawdopodobne; skutki: duże"),
    ("Z03", "Zakłócenie funkcjonowania systemów i sieci teleinformatycznych", "prawdopodobieństwo: możliwe; skutki: duże"),
    ("Z04", "Działania hybrydowe", "prawdopodobieństwo: możliwe; skutki: duże"),
    ("Z05", "Susza i upał", "prawdopodobieństwo: prawdopodobne; skutki: średnie"),
    ("Z06", "Epizootia", "prawdopodobieństwo: prawdopodobne; skutki: średnie"),
    ("Z07", "Zakłócenie w systemie energetycznym", "prawdopodobieństwo: prawdopodobne; skutki: średnie"),
    ("Z08", "Silny wiatr", "prawdopodobieństwo: prawdopodobne; skutki: średnie"),
    ("Z09", "Zakłócenie w systemie paliwowym", "prawdopodobieństwo: możliwe; skutki: średnie"),
    ("Z10", "Pożar wielkopowierzchniowy", "prawdopodobieństwo: możliwe; skutki: średnie"),
    ("Z11", "Epifitoza", "prawdopodobieństwo: możliwe; skutki: średnie"),
    ("Z12", "Zakłócenie funkcjonowania systemów i usług telekomunikacyjnych", "prawdopodobieństwo: możliwe; skutki: średnie"),
    ("Z13", "Skażenie chemiczne na lądzie", "prawdopodobieństwo: rzadkie; skutki: małe"),
    ("Z14", "Zakłócenie w systemie gazowym", "prawdopodobieństwo: rzadkie; skutki: średnie"),
    ("Z15", "Katastrofa morska", "prawdopodobieństwo: rzadkie; skutki: średnie"),
    ("Z16", "Zdarzenie o charakterze terrorystycznym", "prawdopodobieństwo: bardzo rzadkie; skutki: duże"),
    ("Z17", "Skażenie promieniotwórcze", "prawdopodobieństwo: bardzo rzadkie; skutki: duże"),
    ("Z18", "Zbiorowe zakłócenie porządku publicznego", "prawdopodobieństwo: prawdopodobne; skutki: małe"),
    ("Z19", "Silny mróz i intensywne opady śniegu", "prawdopodobieństwo: możliwe; skutki: małe"),
    ("Z20", "Dezinformacja", "prawdopodobieństwo: nieujęte w matrycy; skutki: nieujęte w matrycy"),
]

# Zestaw pytan ewaluacyjnych: pytanie -> oczekiwana procedura
EVAL_QUESTIONS = [
    ("Mamy skażenie chemiczne w porcie i wielu poszkodowanych. Co robimy?", "SPO-15"),
    ("Ilu poszkodowanych możemy przetransportować lotniczo do szpitali oparzeniowych?", "SPO-15"),
    ("Kto zwołuje posiedzenie Rządowego Zespołu Zarządzania Kryzysowego?", "SPO-1"),
    ("W jakim trybie można zwołać RZZK poza posiedzeniem stacjonarnym?", "SPO-1"),
    ("Wojewoda potrzebuje pieniędzy na usuwanie skutków powodzi. Jaka procedura?", "SPO-2"),
    ("Skad wziąć środki na zakup łóżek polowych dla ewakuowanych?", "SPO-2"),
    ("Jak szybko musimy wyemitować komunikat ostrzegawczy dla ludności?", "SPO-3"),
    ("Kto zatwierdza treść komunikatu Alert RCB?", "SPO-3"),
    ("W sieci krąży informacja, że pękła tama. Jak reagujemy?", "SPO-3"),
    ("Czy możemy tymczasowo przywrócić kontrolę na granicy z powodu zagrożenia?", "SPO-4"),
    ("Kogo trzeba notyfikować przed przywróceniem kontroli granicznej?", "SPO-4"),
    ("Kiedy wprowadza się stan klęski żywiołowej i kto go ogłasza?", "SPO-5"),
    ("Siły wojewody są niewystarczające przy powodzi. Jaki stan nadzwyczajny?", "SPO-5"),
    ("Jaka procedura dotyczy zagrożenia konstytucyjnego ustroju państwa?", "SPO-6"),
    ("Kto wydaje rozporządzenie o stanie wojennym?", "SPO-7"),
    ("Obywatel RP został uprowadzony za granica przez organizację terrorystyczną. Co robimy?", "SPO-8"),
    ("Kto prowadzi sztab kryzysowy przy uprowadzeniu obywatela poza granicami kraju?", "SPO-8"),
    ("Gwałtownie rośnie liczba cudzoziemców na granicy. Jaka procedura?", "SPO-9"),
    ("Gdzie uruchomić punkty recepcyjne przy masowym napływie osób?", "SPO-9"),
    ("Awaria stacji energetycznej zagraża szpitalom i przepompowniom. Jak współpracować z operatorem?", "SPO-10"),
    ("Kto ustala priorytety przywracania zasilania obiektów infrastruktury krytycznej?", "SPO-10"),
    ("Trzeba sprowadzić Polaków z kraju objętego konfliktem. Jaka procedura?", "SPO-11"),
    ("Jak zorganizować punkty zborne dla ewakuowanych z zagranicy?", "SPO-11"),
    ("Jak ma wyglądać obieg meldunków między WCZK a RCB?", "SPO-12"),
    ("W jakim czasie dyżurny rejestruje meldunek z centrum wojewódzkiego?", "SPO-12"),
    ("Wykryto obcy dron nad obiektem chronionym. Jak alarmujemy ludność?", "SPO-13"),
    ("Kto uruchamia syreny przy zagrożeniu uderzeniem z powietrza?", "SPO-13"),
    ("Państwo sojusznicze chce przemieścić wojska przez terytorium RP. Co dalej?", "SPO-14"),
    ("Kto odpowiada za wsparcie państwa gospodarza dla wojsk sojuszniczych?", "SPO-14"),
    ("Wystąpił poważny incydent cyberbezpieczeństwa u operatora usługi kluczowej. Kogo zwołać?", "SPO-16"),
    ("Kilka niezależnych incydentów wygląda na działanie skoordynowane. Jaka procedura?", "SPO-16"),
    ("Kto rekomenduje wprowadzenie stopni alarmowych CRP?", "SPO-16"),
]
