# -*- coding: utf-8 -*-
"""Tresc korpusu procedur dla demo ol-spo-copilot.

UWAGA: wszystkie tresci sa SYNTETYCZNE i uproszczone. Odwzorowuja jedynie
strukture i logike Standardowych Procedur Operacyjnych opisanych w KPZK,
ale NIE sa odwzorowaniem rzeczywistych dokumentow zadnej instytucji i nie
moga byc wykorzystywane operacyjnie.

Struktura kroku:
    (nr, tytul, kod_roli, sla_minuty, dokument_wyjsciowy, krytyczny)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Role i instytucje
# ---------------------------------------------------------------------------

ROLES = [
    # role_code, nazwa roli, instytucja, poziom
    ("R_DYZ_RCB", "Oficer dyzurny RCB", "Rzadowe Centrum Bezpieczenstwa", "krajowy"),
    ("R_DYR_RCB", "Dyrektor RCB", "Rzadowe Centrum Bezpieczenstwa", "krajowy"),
    ("R_ANAL_RCB", "Zespol analiz RCB", "Rzadowe Centrum Bezpieczenstwa", "krajowy"),
    ("R_SEKR_RZZK", "Sekretarz RZZK", "Rzadowe Centrum Bezpieczenstwa", "krajowy"),
    ("R_RZECZ", "Rzecznik prasowy", "Rzadowe Centrum Bezpieczenstwa", "krajowy"),
    ("R_MIN_WIOD", "Minister wiodacy", "Ministerstwo wiodace", "krajowy"),
    ("R_MSWIA", "Departament ZK MSWiA", "Ministerstwo Spraw Wewnetrznych i Administracji", "krajowy"),
    ("R_MON", "Centrum Zarzadzania Kryzysowego MON", "Ministerstwo Obrony Narodowej", "krajowy"),
    ("R_MSZ", "Sztab Kryzysowy MSZ", "Ministerstwo Spraw Zagranicznych", "krajowy"),
    ("R_MF", "Departament Budzetu MF", "Ministerstwo Finansow", "krajowy"),
    ("R_MZ", "Centrum Zarzadzania Kryzysowego MZ", "Ministerstwo Zdrowia", "krajowy"),
    ("R_KGP", "Komenda Glowna Policji", "Policja", "krajowy"),
    ("R_KGPSP", "Komenda Glowna PSP", "Panstwowa Straz Pozarna", "krajowy"),
    ("R_KGSG", "Komenda Glowna Strazy Granicznej", "Straz Graniczna", "krajowy"),
    ("R_ABW", "Agencja Bezpieczenstwa Wewnetrznego", "ABW", "krajowy"),
    ("R_CSIRT", "CSIRT NASK / CSIRT GOV", "Zespoly reagowania na incydenty", "krajowy"),
    ("R_WOJ", "Wojewoda / WCZK", "Urzad Wojewodzki", "wojewodzki"),
    ("R_STAR", "Starosta / PCZK", "Starostwo Powiatowe", "powiatowy"),
    ("R_WOJT", "Wojt, burmistrz, prezydent miasta", "Urzad Gminy", "gminny"),
    ("R_OPER_IK", "Operator infrastruktury krytycznej", "Podmiot IK", "operatorski"),
    ("R_RCL", "Rzadowe Centrum Legislacji", "RCL", "krajowy"),
    ("R_KPRM", "Kancelaria Prezesa Rady Ministrow", "KPRM", "krajowy"),
]

# ---------------------------------------------------------------------------
# 16 Standardowych Procedur Operacyjnych
# ---------------------------------------------------------------------------

PROCEDURES = [
    {
        "code": "SPO-1",
        "name": "Organizacja posiedzenia Rzadowego Zespolu Zarzadzania Kryzysowego",
        "owner_role": "R_SEKR_RZZK",
        "hazards": ["Z01", "Z02", "Z04", "Z07", "Z17"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa z 26 kwietnia 2007 r. o zarzadzaniu kryzysowym, art. 8-9",
        "purpose": (
            "Zapewnienie sprawnego zwolania i obslugi posiedzenia RZZK jako organu "
            "opiniodawczo-doradczego Rady Ministrow w sprawach inicjowania i koordynowania "
            "dzialan podejmowanych w zakresie zarzadzania kryzysowego."
        ),
        "triggers": [
            "wniosek ministra wiodacego o zwolanie posiedzenia RZZK",
            "sytuacja kryzysowa angazujaca kilku ministrow",
            "wyczerpanie sil i srodkow ministra wiodacego",
            "rekomendacja Dyrektora RCB po analizie obrazu sytuacji",
        ],
        "keywords": ["RZZK", "posiedzenie", "premier", "zwolanie zespolu", "rekomendacje rzadowe"],
        "steps": [
            (1, "Przyjecie i rejestracja wniosku o zwolanie posiedzenia RZZK", "R_DYZ_RCB", 30, "Karta rejestracji wniosku", True),
            (2, "Weryfikacja przeslanek ustawowych i zakresu przedmiotowego posiedzenia", "R_DYR_RCB", 60, "", True),
            (3, "Uzgodnienie terminu i trybu posiedzenia: stacjonarny, zdalny lub obiegowy", "R_SEKR_RZZK", 60, "Decyzja o trybie posiedzenia", True),
            (4, "Powiadomienie czlonkow RZZK oraz uczestnikow zaproszonych", "R_SEKR_RZZK", 45, "Lista powiadomien", True),
            (5, "Przygotowanie raportu sytuacyjnego i projektu porzadku obrad", "R_ANAL_RCB", 120, "Raport sytuacyjny RCB", True),
            (6, "Uzgodnienie projektow rekomendacji z ministrem wiodacym", "R_DYR_RCB", 120, "Projekt rekomendacji", False),
            (7, "Zapewnienie warunkow organizacyjno-technicznych i lacznosci niejawnej", "R_KPRM", 90, "", False),
            (8, "Obsluga posiedzenia i protokolowanie przebiegu", "R_SEKR_RZZK", 180, "Protokol posiedzenia", True),
            (9, "Sporzadzenie i dystrybucja ustalen oraz wykazu zadan", "R_SEKR_RZZK", 240, "Wykaz zadan po posiedzeniu", True),
            (10, "Monitorowanie realizacji zadan i raport zwrotny do Przewodniczacego", "R_ANAL_RCB", 1440, "Raport z realizacji zadan", False),
        ],
    },
    {
        "code": "SPO-2",
        "name": "Uruchomienie dodatkowych srodkow finansowych",
        "owner_role": "R_MF",
        "hazards": ["Z02", "Z07", "Z08", "Z19"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o finansach publicznych - rezerwa celowa na zarzadzanie kryzysowe",
        "purpose": (
            "Uruchomienie srodkow z rezerwy celowej lub ogolnej budzetu panstwa na "
            "przeciwdzialanie skutkom sytuacji kryzysowej oraz usuwanie tych skutkow."
        ),
        "triggers": [
            "wniosek wojewody o srodki na usuwanie skutkow zdarzenia",
            "wyczerpanie limitu wydatkow ministra wiodacego",
            "koniecznosc zakupu zasobow z rezerw strategicznych",
            "decyzja RZZK o wsparciu finansowym samorzadow",
        ],
        "keywords": ["rezerwa celowa", "srodki finansowe", "promesa", "dotacja", "budzet kryzysowy"],
        "steps": [
            (1, "Przyjecie wniosku wojewody lub ministra o uruchomienie srodkow", "R_MF", 60, "Wniosek o srodki", True),
            (2, "Weryfikacja formalna wniosku i kompletnosci kosztorysu", "R_MF", 120, "Protokol weryfikacji", True),
            (3, "Ocena zasadnosci merytorycznej i zwiazku wydatku ze zdarzeniem", "R_MSWIA", 240, "Opinia merytoryczna", True),
            (4, "Uzgodnienie zrodla finansowania i limitu z Ministrem Finansow", "R_MF", 480, "", True),
            (5, "Przygotowanie projektu decyzji o zmianie w budzecie panstwa", "R_MF", 480, "Projekt decyzji budzetowej", True),
            (6, "Uzyskanie opinii RZZK, jesli wymagana zakresem zdarzenia", "R_SEKR_RZZK", 720, "Opinia RZZK", False),
            (7, "Wydanie decyzji i przekazanie jej dysponentowi czesci budzetowej", "R_MF", 240, "Decyzja o uruchomieniu srodkow", True),
            (8, "Uruchomienie transzy i powiadomienie beneficjenta", "R_WOJ", 240, "Zawiadomienie o transzy", False),
            (9, "Monitoring wydatkowania i sprawozdawczosc okresowa", "R_WOJ", 2880, "Sprawozdanie z wydatkowania", False),
            (10, "Rozliczenie koncowe i kontrola wykorzystania srodkow", "R_MF", 4320, "Protokol rozliczenia", False),
        ],
    },
    {
        "code": "SPO-3",
        "name": "Zasady informowania ludnosci o zagrozeniach - organizacja procesu komunikacji spolecznej w sytuacji kryzysowej",
        "owner_role": "R_RZECZ",
        "hazards": ["Z01", "Z02", "Z07", "Z13", "Z17", "Z20"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o zarzadzaniu kryzysowym; ustawa Prawo telekomunikacyjne - Alert RCB",
        "purpose": (
            "Zapewnienie ludnosci szybkiej, spojnej i zrozumialej informacji o zagrozeniu, "
            "zasadach postepowania i dzialaniach administracji oraz przeciwdzialanie panice "
            "i dezinformacji."
        ),
        "triggers": [
            "wystapienie zagrozenia zycia lub zdrowia ludnosci",
            "przekroczenie stanow alarmowych i koniecznosc ewakuacji",
            "rozpowszechnianie nieprawdziwych informacji o zdarzeniu",
            "decyzja RZZK o uruchomieniu komunikacji kryzysowej",
        ],
        "keywords": ["Alert RCB", "RSO", "komunikat", "rzecznik", "informowanie ludnosci", "dezinformacja"],
        "steps": [
            (1, "Ocena sytuacji informacyjnej i identyfikacja grup odbiorcow", "R_ANAL_RCB", 30, "Analiza odbiorcow", True),
            (2, "Wyznaczenie rzecznika wiodacego i wdrozenie zasady jednego glosu", "R_DYR_RCB", 30, "Decyzja o rzeczniku wiodacym", True),
            (3, "Przygotowanie komunikatu bazowego oraz wersji uproszczonej", "R_RZECZ", 45, "Komunikat ostrzegawczy", True),
            (4, "Przygotowanie wersji obcojezycznych i dostepnych dla osob z niepelnosprawnosciami", "R_RZECZ", 60, "Wersje jezykowe komunikatu", False),
            (5, "Dobor kanalow: Alert RCB, RSO, media, syreny, kanaly samorzadowe", "R_DYR_RCB", 30, "Plan dystrybucji", True),
            (6, "Zatwierdzenie tresci przez ministra wiodacego lub Dyrektora RCB", "R_MIN_WIOD", 30, "Akceptacja tresci", True),
            (7, "Emisja komunikatu i potwierdzenie dystrybucji w kanalach", "R_DYZ_RCB", 15, "Potwierdzenie emisji", True),
            (8, "Monitoring odbioru komunikatu oraz narracji dezinformacyjnych", "R_ANAL_RCB", 120, "Raport monitoringu", False),
            (9, "Publikacja sprostowan i aktualizacji cyklicznych", "R_RZECZ", 180, "Sprostowanie", False),
            (10, "Briefing prasowy lub konferencja z udzialem ministra wiodacego", "R_RZECZ", 240, "Notatka z briefingu", False),
            (11, "Archiwizacja komunikatow i ocena skutecznosci dotarcia", "R_ANAL_RCB", 1440, "Raport skutecznosci", False),
        ],
    },
    {
        "code": "SPO-4",
        "name": "Tymczasowe przywrocenie kontroli granicznej na granicach RP",
        "owner_role": "R_MSWIA",
        "hazards": ["Z04", "Z16", "Z18"],
        "phase": "reagowanie",
        "legal_basis": "Kodeks graniczny Schengen; ustawa o ochronie granicy panstwowej",
        "purpose": (
            "Przygotowanie i wdrozenie tymczasowego przywrocenia kontroli granicznej na "
            "granicach wewnetrznych w przypadku powaznego zagrozenia porzadku publicznego "
            "lub bezpieczenstwa wewnetrznego."
        ),
        "triggers": [
            "powazne zagrozenie porzadku publicznego lub bezpieczenstwa wewnetrznego",
            "masowy niekontrolowany naplyw osob przez granice wewnetrzna",
            "impreza masowa o charakterze miedzynarodowym wysokiego ryzyka",
            "zagrozenie terrorystyczne o charakterze transgranicznym",
        ],
        "keywords": ["kontrola graniczna", "Schengen", "granica wewnetrzna", "Straz Graniczna", "notyfikacja KE"],
        "steps": [
            (1, "Analiza przeslanek zagrozenia porzadku publicznego i bezpieczenstwa", "R_ABW", 240, "Ocena zagrozenia", True),
            (2, "Ocena skutkow dla ruchu granicznego, transportu i gospodarki", "R_MSWIA", 480, "Ocena skutkow", False),
            (3, "Uzgodnienie zakresu, odcinkow i czasu kontroli z KG SG", "R_KGSG", 240, "Plan rozwiniecia kontroli", True),
            (4, "Notyfikacja Komisji Europejskiej i panstw czlonkowskich", "R_MSZ", 480, "Notyfikacja KE", True),
            (5, "Opracowanie projektu rozporzadzenia MSWiA", "R_MSWIA", 480, "Projekt rozporzadzenia", True),
            (6, "Uzgodnienia miedzyresortowe i opinia RCL", "R_RCL", 720, "Opinia RCL", False),
            (7, "Przyjecie i publikacja rozporzadzenia", "R_KPRM", 240, "Rozporzadzenie", True),
            (8, "Rozwiniecie przejsc granicznych i sil Strazy Granicznej", "R_KGSG", 720, "Meldunek o gotowosci", True),
            (9, "Komunikacja do podroznych i przewoznikow w trybie SPO-3", "R_RZECZ", 120, "Komunikat dla podroznych", False),
            (10, "Cykliczna ocena zasadnosci utrzymania lub przedluzenia kontroli", "R_MSWIA", 2880, "Raport oceny", False),
        ],
    },
    {
        "code": "SPO-5",
        "name": "Wprowadzenie stanu kleski zywiolowej",
        "owner_role": "R_MSWIA",
        "hazards": ["Z01", "Z02", "Z07", "Z08", "Z10", "Z19"],
        "phase": "reagowanie",
        "legal_basis": "Konstytucja RP art. 228 i 232; ustawa z 18 kwietnia 2002 r. o stanie kleski zywiolowej",
        "purpose": (
            "Przygotowanie i wprowadzenie stanu kleski zywiolowej na obszarze dotknietym "
            "zdarzeniem, gdy zwykle srodki konstytucyjne sa niewystarczajace do zapobiezenia "
            "skutkom katastrofy naturalnej lub awarii technicznej."
        ),
        "triggers": [
            "niewystarczajace sily i srodki wojewody na obszarze zdarzenia",
            "katastrofa naturalna o zasiegu ponadwojewodzkim",
            "wniosek wojewody o wprowadzenie stanu kleski zywiolowej",
            "koniecznosc wprowadzenia ograniczen wolnosci i praw czlowieka",
        ],
        "keywords": ["stan kleski zywiolowej", "rozporzadzenie Rady Ministrow", "ograniczenia praw", "pelnomocnik"],
        "steps": [
            (1, "Przyjecie wniosku wojewody lub ministra o wprowadzenie stanu", "R_MSWIA", 120, "Wniosek o wprowadzenie stanu", True),
            (2, "Ocena, czy sily i srodki na nizszych poziomach sa niewystarczajace", "R_ANAL_RCB", 240, "Analiza sil i srodkow", True),
            (3, "Okreslenie obszaru obowiazywania i przewidywanego czasu trwania", "R_MSWIA", 240, "Zalacznik terytorialny", True),
            (4, "Opracowanie projektu rozporzadzenia Rady Ministrow", "R_MSWIA", 480, "Projekt rozporzadzenia RM", True),
            (5, "Okreslenie katalogu ograniczen wolnosci i praw czlowieka", "R_RCL", 240, "Katalog ograniczen", True),
            (6, "Rozpatrzenie projektu przez Rade Ministrow", "R_KPRM", 480, "Rozporzadzenie RM", True),
            (7, "Przekazanie rozporzadzenia Sejmowi RP", "R_KPRM", 120, "Pismo przewodnie do Sejmu", True),
            (8, "Publikacja i ogloszenie stanu w mediach w trybie SPO-3", "R_RZECZ", 60, "Komunikat o stanie", True),
            (9, "Wyznaczenie pelnomocnika i trybu kierowania dzialaniami", "R_MSWIA", 240, "Decyzja o pelnomocniku", False),
            (10, "Raportowanie okresowe i wniosek o zniesienie stanu", "R_WOJ", 2880, "Raport okresowy", False),
        ],
    },
    {
        "code": "SPO-6",
        "name": "Wprowadzenie stanu wyjatkowego",
        "owner_role": "R_MSWIA",
        "hazards": ["Z04", "Z16", "Z18"],
        "phase": "reagowanie",
        "legal_basis": "Konstytucja RP art. 230; ustawa z 21 czerwca 2002 r. o stanie wyjatkowym",
        "purpose": (
            "Przygotowanie wprowadzenia stanu wyjatkowego w razie zagrozenia konstytucyjnego "
            "ustroju panstwa, bezpieczenstwa obywateli lub porzadku publicznego."
        ),
        "triggers": [
            "zagrozenie konstytucyjnego ustroju panstwa",
            "masowe zaklocenia porzadku publicznego niemozliwe do opanowania",
            "dzialania o charakterze hybrydowym wymierzone w bezpieczenstwo wewnetrzne",
        ],
        "keywords": ["stan wyjatkowy", "porzadek publiczny", "Prezydent RP", "rozporzadzenie"],
        "steps": [
            (1, "Analiza zagrozenia i przeslanek konstytucyjnych", "R_ABW", 240, "Ocena zagrozenia", True),
            (2, "Przygotowanie wniosku Rady Ministrow do Prezydenta RP", "R_MSWIA", 480, "Wniosek RM", True),
            (3, "Okreslenie obszaru, czasu i zakresu ograniczen", "R_MSWIA", 240, "Zalacznik do wniosku", True),
            (4, "Opinia RCL i uzgodnienia miedzyresortowe", "R_RCL", 480, "Opinia RCL", False),
            (5, "Rozpatrzenie wniosku przez Rade Ministrow", "R_KPRM", 480, "Uchwala RM", True),
            (6, "Wydanie rozporzadzenia przez Prezydenta RP", "R_KPRM", 720, "Rozporzadzenie Prezydenta RP", True),
            (7, "Przedstawienie rozporzadzenia Sejmowi RP", "R_KPRM", 120, "Pismo do Sejmu", True),
            (8, "Komunikacja spoleczna i informowanie ludnosci w trybie SPO-3", "R_RZECZ", 60, "Komunikat", True),
            (9, "Monitoring stosowania ograniczen i raportowanie", "R_MSWIA", 2880, "Raport okresowy", False),
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
            "Przygotowanie wprowadzenia stanu wojennego w razie zewnetrznego zagrozenia "
            "panstwa, zbrojnej napasci lub zobowiazan sojuszniczych do wspolnej obrony."
        ),
        "triggers": [
            "zewnetrzne zagrozenie panstwa",
            "zbrojna napasc na terytorium RP",
            "zobowiazanie sojusznicze do wspolnej obrony przeciwko agresji",
        ],
        "keywords": ["stan wojenny", "Naczelny Dowodca", "obrona panstwa", "Prezydent RP"],
        "steps": [
            (1, "Ocena zagrozenia zewnetrznego i rekomendacja MON", "R_MON", 180, "Ocena zagrozenia", True),
            (2, "Przygotowanie wniosku Rady Ministrow do Prezydenta RP", "R_MON", 360, "Wniosek RM", True),
            (3, "Okreslenie obszaru objetego stanem wojennym", "R_MON", 240, "Zalacznik terytorialny", True),
            (4, "Uzgodnienia z MSWiA, MSZ i BBN", "R_MSZ", 360, "Protokol uzgodnien", False),
            (5, "Rozpatrzenie wniosku przez Rade Ministrow", "R_KPRM", 360, "Uchwala RM", True),
            (6, "Wydanie rozporzadzenia przez Prezydenta RP", "R_KPRM", 480, "Rozporzadzenie Prezydenta RP", True),
            (7, "Przedstawienie rozporzadzenia Sejmowi RP", "R_KPRM", 120, "Pismo do Sejmu", True),
            (8, "Uruchomienie systemu kierowania obrona panstwa", "R_MON", 720, "Meldunek o uruchomieniu", True),
            (9, "Informowanie ludnosci i sojusznikow", "R_RZECZ", 120, "Komunikat", True),
        ],
    },
    {
        "code": "SPO-8",
        "name": "Postepowanie w sytuacji uprowadzenia terrorystycznego obywatela polskiego poza obszarem RP",
        "owner_role": "R_MSZ",
        "hazards": ["Z16"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o dzialaniach antyterrorystycznych; prawo konsularne",
        "purpose": (
            "Skoordynowanie dzialan sluzb i resortow w przypadku uprowadzenia obywatela RP "
            "poza granicami kraju przez organizacje o charakterze terrorystycznym."
        ),
        "triggers": [
            "wiarygodna informacja o uprowadzeniu obywatela RP za granica",
            "zadanie okupu lub zadanie polityczne wobec RP",
            "wniosek rodziny lub pracodawcy o pomoc konsularna",
        ],
        "keywords": ["uprowadzenie", "zakladnik", "konsul", "antyterroryzm", "negocjacje"],
        "steps": [
            (1, "Weryfikacja informacji o uprowadzeniu i ustalenie tozsamosci", "R_MSZ", 120, "Notatka weryfikacyjna", True),
            (2, "Powiadomienie Zespolu do spraw Incydentow Krytycznych", "R_MSZ", 60, "Zawiadomienie ZIK", True),
            (3, "Powolanie sztabu kryzysowego MSZ i wyznaczenie koordynatora", "R_MSZ", 120, "Decyzja o powolaniu sztabu", True),
            (4, "Nawiazanie wspolpracy z placowka dyplomatyczna i sluzbami panstwa pobytu", "R_MSZ", 240, "Protokol wspolpracy", True),
            (5, "Ocena wiarygodnosci zadan i analiza zagrozenia", "R_ABW", 240, "Analiza zagrozenia", True),
            (6, "Ustalenie strategii postepowania i zasad kontaktu", "R_MSZ", 360, "Strategia postepowania", True),
            (7, "Opieka nad rodzina i zapewnienie wsparcia psychologicznego", "R_MSZ", 240, "Plan wsparcia rodziny", False),
            (8, "Zarzadzanie informacja publiczna i ochrona danych osoby uprowadzonej", "R_RZECZ", 120, "Zasady komunikacji", True),
            (9, "Przygotowanie i realizacja operacji uwolnienia lub przekazania", "R_MON", 1440, "Plan operacji", False),
            (10, "Powrot, pomoc medyczna i psychologiczna oraz raport koncowy", "R_MSZ", 2880, "Raport koncowy", False),
        ],
    },
    {
        "code": "SPO-9",
        "name": "Dzialania w przypadku masowego naplywu cudzoziemcow na terytorium RP",
        "owner_role": "R_MSWIA",
        "hazards": ["Z04", "Z09", "Z18"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o udzielaniu cudzoziemcom ochrony; ustawa o zarzadzaniu kryzysowym",
        "purpose": (
            "Zapewnienie przyjecia, rejestracji, zakwaterowania i obslugi socjalnej duzej "
            "liczby cudzoziemcow przekraczajacych granice RP w krotkim czasie."
        ),
        "triggers": [
            "gwaltowny wzrost liczby osob przekraczajacych granice",
            "konflikt zbrojny lub katastrofa w panstwie sasiednim",
            "instrumentalne wykorzystanie migracji jako element dzialan hybrydowych",
        ],
        "keywords": ["naplyw cudzoziemcow", "recepcja", "punkt przyjecia", "rejestracja", "zakwaterowanie"],
        "steps": [
            (1, "Monitoring i prognoza liczby osob przekraczajacych granice", "R_KGSG", 120, "Prognoza naplywu", True),
            (2, "Uruchomienie punktow recepcyjnych i rejestracji", "R_WOJ", 240, "Wykaz punktow recepcyjnych", True),
            (3, "Zapewnienie zakwaterowania, wyzywienia i opieki medycznej", "R_WOJ", 480, "Plan zabezpieczenia socjalnego", True),
            (4, "Wsparcie tlumaczy i informacji w jezykach obcych", "R_MSWIA", 240, "Plan wsparcia jezykowego", False),
            (5, "Weryfikacja tozsamosci i kontrola bezpieczenstwa", "R_ABW", 360, "Protokol weryfikacji", True),
            (6, "Koordynacja z organizacjami pozarzadowymi i samorzadami", "R_WOJ", 360, "Porozumienie o wspolpracy", False),
            (7, "Uruchomienie srodkow finansowych w trybie SPO-2", "R_MF", 720, "Wniosek o srodki", False),
            (8, "Ochrona osob maloletnich bez opieki i osob wrazliwych", "R_MSWIA", 360, "Rejestr osob wrazliwych", True),
            (9, "Komunikacja spoleczna i przeciwdzialanie dezinformacji", "R_RZECZ", 180, "Komunikat", False),
            (10, "Raportowanie dobowe i ocena wydolnosci systemu", "R_MSWIA", 1440, "Raport dobowy", False),
        ],
    },
    {
        "code": "SPO-10",
        "name": "Wspolpraca miedzy administracja publiczna a wlascicielami oraz posiadaczami obiektow infrastruktury krytycznej w zakresie jej ochrony",
        "owner_role": "R_DYR_RCB",
        "hazards": ["Z03", "Z04", "Z07", "Z12", "Z14", "Z16"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o zarzadzaniu kryzysowym, art. 6; Narodowy Program Ochrony Infrastruktury Krytycznej",
        "purpose": (
            "Zapewnienie wymiany informacji i skoordynowanych dzialan miedzy administracja a "
            "operatorami infrastruktury krytycznej w celu ochrony IK i szybkiego odtworzenia "
            "jej funkcji po zdarzeniu."
        ),
        "triggers": [
            "zagrozenie lub uszkodzenie obiektu infrastruktury krytycznej",
            "kaskadowa awaria wynikajaca ze wspolzaleznosci systemow IK",
            "podwyzszenie stopnia alarmowego CRP",
            "wniosek operatora IK o wsparcie administracji",
        ],
        "keywords": ["infrastruktura krytyczna", "operator IK", "NPOIK", "odtworzenie funkcji", "efekt domina"],
        "steps": [
            (1, "Przyjecie zgloszenia o zagrozeniu obiektu IK i jego rejestracja", "R_DYZ_RCB", 30, "Karta zgloszenia IK", True),
            (2, "Identyfikacja systemu IK i wlasciwego ministra odpowiedzialnego", "R_ANAL_RCB", 60, "Karta identyfikacji", True),
            (3, "Nawiazanie kontaktu z operatorem i wyznaczenie punktu styku", "R_OPER_IK", 60, "Lista punktow kontaktowych", True),
            (4, "Ocena skutkow wtornych i zaleznosci miedzysystemowych", "R_ANAL_RCB", 180, "Analiza wspolzaleznosci", True),
            (5, "Ustalenie priorytetow zasilania i przywracania funkcji", "R_MIN_WIOD", 240, "Lista priorytetow", True),
            (6, "Uzgodnienie wsparcia sil i srodkow administracji dla operatora", "R_WOJ", 240, "Protokol uzgodnien", False),
            (7, "Wprowadzenie ograniczen lub reglamentacji, jesli konieczne", "R_MIN_WIOD", 480, "Decyzja o ograniczeniach", False),
            (8, "Monitorowanie odtwarzania funkcji i raportowanie postepu", "R_OPER_IK", 720, "Raport odtworzenia", True),
            (9, "Informowanie odbiorcow uslug o przewidywanym czasie przywrocenia", "R_RZECZ", 120, "Komunikat dla odbiorcow", False),
            (10, "Wnioski i aktualizacja planu ochrony IK po zdarzeniu", "R_DYR_RCB", 4320, "Raport po zdarzeniu", False),
        ],
    },
    {
        "code": "SPO-11",
        "name": "Organizacja ewakuacji obywateli polskich spoza granic kraju",
        "owner_role": "R_MSZ",
        "hazards": ["Z04", "Z16", "Z15"],
        "phase": "reagowanie",
        "legal_basis": "Prawo konsularne; ustawa o zarzadzaniu kryzysowym",
        "purpose": (
            "Organizacja bezpiecznego powrotu obywateli RP przebywajacych na obszarze objetym "
            "konfliktem, katastrofa lub innym zagrozeniem, we wspolpracy z partnerami UE i NATO."
        ),
        "triggers": [
            "eskalacja konfliktu zbrojnego w panstwie pobytu obywateli RP",
            "katastrofa naturalna lub epidemia uniemozliwiajaca powrot",
            "zamkniecie przestrzeni powietrznej panstwa pobytu",
        ],
        "keywords": ["ewakuacja z zagranicy", "most powietrzny", "konsul", "rejestracja Odyseusz", "repatriacja"],
        "steps": [
            (1, "Ocena zagrozenia w panstwie pobytu i decyzja o ewakuacji", "R_MSZ", 240, "Ocena zagrozenia", True),
            (2, "Ustalenie liczby i lokalizacji obywateli RP", "R_MSZ", 360, "Wykaz osob do ewakuacji", True),
            (3, "Uruchomienie infolinii i kanalow zgloszeniowych", "R_MSZ", 120, "Procedura infolinii", True),
            (4, "Wybor wariantu transportu i tras ewakuacji", "R_MON", 360, "Plan transportu", True),
            (5, "Uzgodnienia z panstwem pobytu i panstwami tranzytu", "R_MSZ", 480, "Zgody dyplomatyczne", True),
            (6, "Koordynacja z mechanizmem ochrony ludnosci UE i sojusznikami", "R_MSZ", 480, "Wniosek do UCPM", False),
            (7, "Organizacja punktow zbornych i eskorty", "R_MON", 480, "Plan punktow zbornych", True),
            (8, "Realizacja przerzutu i odprawa po przylocie", "R_MON", 1440, "Meldunek z realizacji", True),
            (9, "Pomoc medyczna, socjalna i psychologiczna po powrocie", "R_MZ", 720, "Plan pomocy", False),
            (10, "Rozliczenie kosztow i raport koncowy", "R_MSZ", 4320, "Raport koncowy", False),
        ],
    },
    {
        "code": "SPO-12",
        "name": "Obieg informacji pomiedzy krajowymi organami i strukturami zarzadzania kryzysowego",
        "owner_role": "R_DYZ_RCB",
        "hazards": ["Z01", "Z02", "Z03", "Z04", "Z07", "Z12"],
        "phase": "przygotowanie",
        "legal_basis": "Ustawa o zarzadzaniu kryzysowym, art. 11 - zadania RCB",
        "purpose": (
            "Zapewnienie ciaglego, jednolitego i udokumentowanego obiegu informacji miedzy "
            "centrami zarzadzania kryzysowego wszystkich poziomow oraz sluzbami."
        ),
        "triggers": [
            "wystapienie zdarzenia o potencjale kryzysowym",
            "zapytanie ministra wiodacego o obraz sytuacji",
            "przekroczenie progu meldunkowego przez CZK nizszego szczebla",
        ],
        "keywords": ["meldunek", "raport dobowy", "obieg informacji", "CZK", "dyzur"],
        "steps": [
            (1, "Przyjecie meldunku z CZK i nadanie numeru ewidencyjnego", "R_DYZ_RCB", 15, "Meldunek wejsciowy", True),
            (2, "Weryfikacja i uzupelnienie danych u zrodla", "R_DYZ_RCB", 30, "", True),
            (3, "Klasyfikacja zdarzenia wg katalogu zagrozen Z01-Z20", "R_ANAL_RCB", 30, "Karta klasyfikacji", True),
            (4, "Sporzadzenie raportu sytuacyjnego dla kierownictwa", "R_ANAL_RCB", 60, "Raport sytuacyjny", True),
            (5, "Dystrybucja raportu do adresatow zgodnie z lista rozdzielnika", "R_DYZ_RCB", 30, "Rozdzielnik", True),
            (6, "Aktualizacja obrazu sytuacji i zasilenie COP", "R_ANAL_RCB", 60, "Aktualizacja COP", False),
            (7, "Sporzadzenie raportu dobowego", "R_ANAL_RCB", 1440, "Raport dobowy", False),
            (8, "Archiwizacja i zapewnienie sladu audytowego", "R_DYZ_RCB", 1440, "", False),
        ],
    },
    {
        "code": "SPO-13",
        "name": "Ostrzeganie i alarmowanie wojsk oraz ludnosci cywilnej o zagrozeniu uderzeniami z powietrza",
        "owner_role": "R_MON",
        "hazards": ["Z04", "Z16"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o obronie Ojczyzny; przepisy o systemie wykrywania i alarmowania",
        "purpose": (
            "Zapewnienie natychmiastowego ostrzezenia wojsk i ludnosci cywilnej o zagrozeniu "
            "uderzeniami z powietrza oraz uruchomienie zachowan ochronnych."
        ),
        "triggers": [
            "wykrycie obiektu powietrznego naruszajacego przestrzen powietrzna RP",
            "informacja sojusznicza o zagrozeniu z powietrza",
            "wykrycie bezzalogowego statku powietrznego nad obiektem chronionym",
        ],
        "keywords": ["alarm powietrzny", "syreny", "system wykrywania i alarmowania", "SWA", "przestrzen powietrzna"],
        "steps": [
            (1, "Przyjecie informacji o zagrozeniu z systemu obrony powietrznej", "R_MON", 5, "Meldunek o zagrozeniu", True),
            (2, "Weryfikacja i ocena wiarygodnosci sygnalu", "R_MON", 10, "", True),
            (3, "Okreslenie obszaru zagrozonego i sposobu alarmowania", "R_MON", 10, "Decyzja o zasiegu alarmu", True),
            (4, "Przekazanie sygnalu do wojewodzkich centrow zarzadzania kryzysowego", "R_MON", 5, "Sygnal alarmowy", True),
            (5, "Uruchomienie syren i systemow alarmowych na obszarze zagrozonym", "R_WOJ", 10, "Potwierdzenie uruchomienia", True),
            (6, "Emisja komunikatu do ludnosci w kanalach masowych", "R_RZECZ", 15, "Komunikat alarmowy", True),
            (7, "Koordynacja z operatorami lotnisk i zarzadca przestrzeni powietrznej", "R_MON", 30, "Protokol koordynacji", False),
            (8, "Odwolanie alarmu i komunikat o zakonczeniu zagrozenia", "R_MON", 15, "Sygnal odwolania alarmu", True),
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
            "wniosek panstwa sojuszniczego o tranzyt lub pobyt wojsk",
            "cwiczenie sojusznicze na terytorium RP",
            "wzmocnienie wschodniej flanki w reakcji na zagrozenie",
        ],
        "keywords": ["wojska sojusznicze", "HNS", "tranzyt", "NATO", "przekraczanie granicy"],
        "steps": [
            (1, "Przyjecie i weryfikacja wniosku panstwa wysylajacego", "R_MON", 480, "Wniosek o zgode", True),
            (2, "Uzgodnienia z MSZ i MSWiA w zakresie zgod i kontroli", "R_MSZ", 480, "Protokol uzgodnien", True),
            (3, "Przygotowanie projektu zgody wlasciwego organu", "R_MON", 720, "Projekt zgody", True),
            (4, "Ustalenie tras przemieszczania i harmonogramu", "R_MON", 480, "Plan przemieszczenia", True),
            (5, "Zapewnienie wsparcia panstwa gospodarza w zakresie HNS", "R_MON", 720, "Plan HNS", True),
            (6, "Koordynacja z zarzadcami drog i kolei oraz Policja", "R_KGP", 480, "Plan zabezpieczenia ruchu", False),
            (7, "Odprawa graniczna i kontrola dokumentow", "R_KGSG", 240, "Protokol odprawy", True),
            (8, "Monitorowanie przemieszczania i raportowanie", "R_MON", 720, "Meldunek biezacy", False),
            (9, "Rozliczenie pobytu i raport koncowy", "R_MON", 4320, "Raport koncowy", False),
        ],
    },
    {
        "code": "SPO-15",
        "name": "Organizacja medycznego mostu powietrznego w przypadku wystapienia zdarzenia masowego",
        "owner_role": "R_MZ",
        "hazards": ["Z01", "Z10", "Z13", "Z15", "Z16", "Z17"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o Panstwowym Ratownictwie Medycznym; ustawa o zarzadzaniu kryzysowym",
        "purpose": (
            "Zapewnienie transportu lotniczego poszkodowanych ze zdarzenia masowego do "
            "szpitali o odpowiednim profilu, w tym poza obszar dotkniety zdarzeniem."
        ),
        "triggers": [
            "zdarzenie masowe przekraczajace mozliwosci szpitali w regionie",
            "koniecznosc transportu pacjentow oparzeniowych lub skazonych",
            "prosba o wsparcie od wojewody lub dysponenta jednostki PRM",
        ],
        "keywords": ["most powietrzny", "zdarzenie masowe", "LPR", "triage", "MEDEVAC", "szpital docelowy"],
        "steps": [
            (1, "Przyjecie informacji o zdarzeniu masowym i ocena skali", "R_MZ", 30, "Meldunek o zdarzeniu", True),
            (2, "Ustalenie liczby poszkodowanych i wynikow segregacji medycznej", "R_MZ", 60, "Zestawienie triage", True),
            (3, "Identyfikacja szpitali docelowych i wolnych miejsc specjalistycznych", "R_MZ", 90, "Wykaz miejsc szpitalnych", True),
            (4, "Uruchomienie sil LPR i lotnictwa transportowego SZ RP", "R_MON", 120, "Zapotrzebowanie na statki powietrzne", True),
            (5, "Wyznaczenie lotnisk i ladowisk operacyjnych", "R_MON", 120, "Plan lotnisk", True),
            (6, "Koordynacja przestrzeni powietrznej i priorytetow lotow", "R_MON", 60, "Uzgodnienie z ATM", True),
            (7, "Organizacja transportu naziemnego na obu koncach mostu", "R_WOJ", 120, "Plan transportu naziemnego", False),
            (8, "Zabezpieczenie medyczne w trakcie transportu", "R_MZ", 60, "Karta transportu medycznego", True),
            (9, "Ewidencja pacjentow i informacja dla rodzin", "R_MZ", 240, "Rejestr pacjentow", False),
            (10, "Raport z realizacji i rozliczenie kosztow", "R_MZ", 2880, "Raport koncowy", False),
        ],
    },
    {
        "code": "SPO-16",
        "name": "Zwolanie i obsluga posiedzenia Zespolu do spraw Incydentow Krytycznych",
        "owner_role": "R_ABW",
        "hazards": ["Z03", "Z04", "Z16"],
        "phase": "reagowanie",
        "legal_basis": "Ustawa o dzialaniach antyterrorystycznych; ustawa o krajowym systemie cyberbezpieczenstwa",
        "purpose": (
            "Zapewnienie szybkiego zwolania i obslugi Zespolu do spraw Incydentow Krytycznych "
            "dla incydentow o charakterze terrorystycznym, hybrydowym lub cybernetycznym."
        ),
        "triggers": [
            "incydent krytyczny w rozumieniu ustawy o krajowym systemie cyberbezpieczenstwa",
            "zdarzenie o charakterze terrorystycznym na terytorium RP",
            "seria skorelowanych incydentow wskazujaca na dzialanie skoordynowane",
            "wniosek CSIRT o zwolanie zespolu",
        ],
        "keywords": ["ZIK", "incydent krytyczny", "cyberbezpieczenstwo", "CSIRT", "stopien alarmowy CRP"],
        "steps": [
            (1, "Przyjecie zgloszenia incydentu i wstepna kwalifikacja", "R_CSIRT", 30, "Karta incydentu", True),
            (2, "Ocena, czy incydent spelnia kryteria incydentu krytycznego", "R_ABW", 60, "Ocena kwalifikacyjna", True),
            (3, "Zwolanie Zespolu do spraw Incydentow Krytycznych", "R_ABW", 60, "Zawiadomienie o posiedzeniu", True),
            (4, "Przygotowanie materialu sytuacyjnego o incydencie", "R_CSIRT", 120, "Raport techniczny", True),
            (5, "Uzgodnienie rekomendacji dotyczacych stopni alarmowych", "R_ABW", 180, "Rekomendacja stopni alarmowych", True),
            (6, "Koordynacja dzialan z operatorami uslug kluczowych", "R_OPER_IK", 240, "Protokol koordynacji", True),
            (7, "Obsluga posiedzenia i protokolowanie ustalen", "R_ABW", 180, "Protokol posiedzenia", True),
            (8, "Przekazanie rekomendacji do RZZK lub Prezesa Rady Ministrow", "R_SEKR_RZZK", 120, "Rekomendacje", False),
            (9, "Komunikacja publiczna uzgodniona ze sluzbami", "R_RZECZ", 180, "Komunikat", False),
            (10, "Raport po incydencie i wnioski do procedur", "R_CSIRT", 4320, "Raport po incydencie", False),
        ],
    },
]

# ---------------------------------------------------------------------------
# Dokumenty towarzyszace: plany wojewodzkie, plany ochrony ludnosci, KPZK
# ---------------------------------------------------------------------------

VOIVODESHIPS = [
    ("02", "dolnoslaskie", "Wroclaw"),
    ("04", "kujawsko-pomorskie", "Bydgoszcz"),
    ("06", "lubelskie", "Lublin"),
    ("08", "lubuskie", "Gorzow Wielkopolski"),
    ("10", "lodzkie", "Lodz"),
    ("12", "malopolskie", "Krakow"),
    ("14", "mazowieckie", "Warszawa"),
    ("16", "opolskie", "Opole"),
    ("18", "podkarpackie", "Rzeszow"),
    ("20", "podlaskie", "Bialystok"),
    ("22", "pomorskie", "Gdansk"),
    ("24", "slaskie", "Katowice"),
    ("26", "swietokrzyskie", "Kielce"),
    ("28", "warminsko-mazurskie", "Olsztyn"),
    ("30", "wielkopolskie", "Poznan"),
    ("32", "zachodniopomorskie", "Szczecin"),
]

HAZARDS = [
    ("Z01", "Epidemia", "prawdopodobienstwo: mozliwe; skutki: katastrofalne"),
    ("Z02", "Powodz", "prawdopodobienstwo: prawdopodobne; skutki: duze"),
    ("Z03", "Zaklocenie funkcjonowania systemow i sieci teleinformatycznych", "prawdopodobienstwo: mozliwe; skutki: duze"),
    ("Z04", "Dzialania hybrydowe", "prawdopodobienstwo: mozliwe; skutki: duze"),
    ("Z05", "Susza i upal", "prawdopodobienstwo: prawdopodobne; skutki: srednie"),
    ("Z06", "Epizootia", "prawdopodobienstwo: prawdopodobne; skutki: srednie"),
    ("Z07", "Zaklocenie w systemie energetycznym", "prawdopodobienstwo: prawdopodobne; skutki: srednie"),
    ("Z08", "Silny wiatr", "prawdopodobienstwo: prawdopodobne; skutki: srednie"),
    ("Z09", "Zaklocenie w systemie paliwowym", "prawdopodobienstwo: mozliwe; skutki: srednie"),
    ("Z10", "Pozar wielkopowierzchniowy", "prawdopodobienstwo: mozliwe; skutki: srednie"),
    ("Z11", "Epifitoza", "prawdopodobienstwo: mozliwe; skutki: srednie"),
    ("Z12", "Zaklocenie funkcjonowania systemow i uslug telekomunikacyjnych", "prawdopodobienstwo: mozliwe; skutki: srednie"),
    ("Z13", "Skazenie chemiczne na ladzie", "prawdopodobienstwo: rzadkie; skutki: male"),
    ("Z14", "Zaklocenie w systemie gazowym", "prawdopodobienstwo: rzadkie; skutki: srednie"),
    ("Z15", "Katastrofa morska", "prawdopodobienstwo: rzadkie; skutki: srednie"),
    ("Z16", "Zdarzenie o charakterze terrorystycznym", "prawdopodobienstwo: bardzo rzadkie; skutki: duze"),
    ("Z17", "Skazenie promieniotworcze", "prawdopodobienstwo: bardzo rzadkie; skutki: duze"),
    ("Z18", "Zbiorowe zaklocenie porzadku publicznego", "prawdopodobienstwo: prawdopodobne; skutki: male"),
    ("Z19", "Silny mroz i intensywne opady sniegu", "prawdopodobienstwo: mozliwe; skutki: male"),
    ("Z20", "Dezinformacja", "prawdopodobienstwo: nieujete w matrycy; skutki: nieujete w matrycy"),
]

# Zestaw pytan ewaluacyjnych: pytanie -> oczekiwana procedura
EVAL_QUESTIONS = [
    ("Mamy skazenie chemiczne w porcie i wielu poszkodowanych. Co robimy?", "SPO-15"),
    ("Ilu poszkodowanych mozemy przetransportowac lotniczo do szpitali oparzeniowych?", "SPO-15"),
    ("Kto zwoluje posiedzenie Rzadowego Zespolu Zarzadzania Kryzysowego?", "SPO-1"),
    ("W jakim trybie mozna zwolac RZZK poza posiedzeniem stacjonarnym?", "SPO-1"),
    ("Wojewoda potrzebuje pieniedzy na usuwanie skutkow powodzi. Jaka procedura?", "SPO-2"),
    ("Skad wziac srodki na zakup lozek polowych dla ewakuowanych?", "SPO-2"),
    ("Jak szybko musimy wyemitowac komunikat ostrzegawczy dla ludnosci?", "SPO-3"),
    ("Kto zatwierdza tresc komunikatu Alert RCB?", "SPO-3"),
    ("W sieci krazy informacja, ze pekla tama. Jak reagujemy?", "SPO-3"),
    ("Czy mozemy tymczasowo przywrocic kontrole na granicy z powodu zagrozenia?", "SPO-4"),
    ("Kogo trzeba notyfikowac przed przywroceniem kontroli granicznej?", "SPO-4"),
    ("Kiedy wprowadza sie stan kleski zywiolowej i kto go oglasza?", "SPO-5"),
    ("Sily wojewody sa niewystarczajace przy powodzi. Jaki stan nadzwyczajny?", "SPO-5"),
    ("Jaka procedura dotyczy zagrozenia konstytucyjnego ustroju panstwa?", "SPO-6"),
    ("Kto wydaje rozporzadzenie o stanie wojennym?", "SPO-7"),
    ("Obywatel RP zostal uprowadzony za granica przez organizacje terrorystyczna. Co robimy?", "SPO-8"),
    ("Kto prowadzi sztab kryzysowy przy uprowadzeniu obywatela poza granicami kraju?", "SPO-8"),
    ("Gwaltownie rosnie liczba cudzoziemcow na granicy. Jaka procedura?", "SPO-9"),
    ("Gdzie uruchomic punkty recepcyjne przy masowym naplywie osob?", "SPO-9"),
    ("Awaria stacji energetycznej zagraza szpitalom i przepompowniom. Jak wspolpracowac z operatorem?", "SPO-10"),
    ("Kto ustala priorytety przywracania zasilania obiektow infrastruktury krytycznej?", "SPO-10"),
    ("Trzeba sprowadzic Polakow z kraju objetego konfliktem. Jaka procedura?", "SPO-11"),
    ("Jak zorganizowac punkty zborne dla ewakuowanych z zagranicy?", "SPO-11"),
    ("Jak ma wygladac obieg meldunkow miedzy WCZK a RCB?", "SPO-12"),
    ("W jakim czasie dyzurny rejestruje meldunek z centrum wojewodzkiego?", "SPO-12"),
    ("Wykryto obcy dron nad obiektem chronionym. Jak alarmujemy ludnosc?", "SPO-13"),
    ("Kto uruchamia syreny przy zagrozeniu uderzeniem z powietrza?", "SPO-13"),
    ("Panstwo sojusznicze chce przemiescic wojska przez terytorium RP. Co dalej?", "SPO-14"),
    ("Kto odpowiada za wsparcie panstwa gospodarza dla wojsk sojuszniczych?", "SPO-14"),
    ("Wystapil powazny incydent cyberbezpieczenstwa u operatora uslugi kluczowej. Kogo zwolac?", "SPO-16"),
    ("Kilka niezaleznych incydentow wyglada na dzialanie skoordynowane. Jaka procedura?", "SPO-16"),
    ("Kto rekomenduje wprowadzenie stopni alarmowych CRP?", "SPO-16"),
]
