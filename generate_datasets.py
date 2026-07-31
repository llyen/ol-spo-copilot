# -*- coding: utf-8 -*-
"""Generator danych syntetycznych dla demo "SPO Copilot" (ol-spo-copilot).

Wszystkie dane sa w 100% syntetyczne i powtarzalne (seed=42).
Uruchomienie:  python generate_datasets.py
"""

from __future__ import annotations

import csv
import json
import random
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from corpus.spo_content import (
    EVAL_QUESTIONS,
    HAZARDS,
    PROCEDURES,
    ROLES,
    VOIVODESHIPS,
)

SEED = 42
random.seed(SEED)
rng = np.random.default_rng(SEED)

BASE = Path(__file__).resolve().parent
DATA = BASE / "datasets"
DERIVED = DATA / "derived"
DATA.mkdir(exist_ok=True)
DERIVED.mkdir(exist_ok=True)

TZ = timezone(timedelta(hours=2))
D0 = datetime(2026, 9, 15, 6, 0, tzinfo=TZ)          # przekroczenie stanow alarmowych
WINDOW_START = D0 - timedelta(days=3)                 # D-3
WINDOW_END = D0 + timedelta(days=10)                  # D+10
HISTORY_START = datetime(2023, 1, 2, 8, 0, tzinfo=TZ)

ROLE_BY_CODE = {r[0]: r for r in ROLES}
PROC_BY_CODE = {p["code"]: p for p in PROCEDURES}
HAZARD_NAME = {h[0]: h[1] for h in HAZARDS}

# Kroki, ktore w tym demo systematycznie przekraczaja czas normatywny.
# To zamierzone: buduje wniosek "lessons learned" widoczny w raporcie.
CHRONIC_BREACHES = {
    ("SPO-3", 4): 0.86,   # wersje jezykowe komunikatu
    ("SPO-2", 3): 0.71,   # opinia merytoryczna do wniosku o srodki
    ("SPO-10", 3): 0.78,  # kontakt z operatorem IK - nieaktualne punkty styku
    ("SPO-9", 4): 0.63,   # wsparcie tlumaczy
    ("SPO-15", 3): 0.58,  # wykaz wolnych miejsc szpitalnych
}

IK_CONTACT_BLOCKER = "Nieaktualna lista punktow kontaktowych operatorow infrastruktury krytycznej"

# Wagi dobrane tak, by jedna przyczyna dominowala przez cale 4 lata historii -
# to jest material na wniosek "lessons learned" w raporcie i w Data Agencie.
BLOCKERS = [
    (IK_CONTACT_BLOCKER, 26),
    ("Brak potwierdzenia odbioru meldunku przez adresata", 14),
    ("Oczekiwanie na decyzje ministra wiodacego", 12),
    ("Brak wyznaczonego zastepcy osoby odpowiedzialnej", 11),
    ("Oczekiwanie na opinie prawna", 9),
    ("Niekompletny kosztorys we wniosku o srodki", 8),
    ("Rozbieznosc danych miedzy WCZK a sluzba", 7),
    ("Brak dostepu do lacznosci niejawnej w lokalizacji zapasowej", 5),
    ("Brak tlumacza jezyka obcego o wymaganej specjalnosci", 4),
    ("Przeciazenie infolinii i kanalu zgloszeniowego", 4),
]
BLOCKER_NAMES = [b[0] for b in BLOCKERS]
BLOCKER_WEIGHTS = [b[1] for b in BLOCKERS]


def pick_blocker(procedure_code: str) -> str:
    """Procedury oparte na kontakcie z operatorami IK i na obiegu meldunkow
    czesciej wpadaja na te sama, systemowa przeszkode."""
    if procedure_code in ("SPO-10", "SPO-12") and rng.random() < 0.5:
        return IK_CONTACT_BLOCKER
    return random.choices(BLOCKER_NAMES, weights=BLOCKER_WEIGHTS)[0]

DECISION_TYPES = [
    "uruchomienie procedury",
    "eskalacja poziomu reagowania",
    "zatwierdzenie tresci komunikatu",
    "uruchomienie srodkow finansowych",
    "skierowanie sil i srodkow",
    "wprowadzenie ograniczen",
    "odstapienie od kroku procedury",
    "zamkniecie procedury",
]

CLASSIFICATIONS = ["jawne", "zastrzezone", "poufne"]

LEVELS = ["gminny", "powiatowy", "wojewodzki", "krajowy"]

USER_ROLES = [
    "Oficer dyzurny WCZK",
    "Oficer dyzurny RCB",
    "Dyzurny PCZK",
    "Analityk RCB",
    "Rzecznik prasowy wojewody",
    "Dyrektor wydzialu ZK",
    "Sekretarz RZZK",
    "Oficer lacznikowy MON",
]


# ---------------------------------------------------------------------------
# Pomocnicze
# ---------------------------------------------------------------------------

def iso(dt: datetime) -> str:
    return dt.isoformat()


def slug(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", norm.lower()).strip("-")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def sla_label(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} minut"
    if minutes < 1440:
        hours = minutes / 60
        return f"{hours:.0f} godzin" if hours == int(hours) else f"{hours:.1f} godziny"
    return f"{minutes / 1440:.0f} doby" if minutes / 1440 < 2 else f"{minutes / 1440:.0f} dni"


# ---------------------------------------------------------------------------
# 1. Wymiary
# ---------------------------------------------------------------------------

def build_dimensions():
    roles = [
        {"role_code": c, "role_name": n, "institution": i, "level": lv}
        for c, n, i, lv in ROLES
    ]
    hazards = [
        {"hazard_code": c, "hazard_name": n, "risk_matrix": m}
        for c, n, m in HAZARDS
    ]
    procedures, steps = [], []
    for idx, proc in enumerate(PROCEDURES, start=1):
        procedures.append({
            "procedure_id": f"P{idx:03d}",
            "procedure_code": proc["code"],
            "procedure_name": proc["name"],
            "owner_role": proc["owner_role"],
            "owner_institution": ROLE_BY_CODE[proc["owner_role"]][2],
            "phase": proc["phase"],
            "hazard_codes": "|".join(proc["hazards"]),
            "legal_basis": proc["legal_basis"],
            "step_count": len(proc["steps"]),
            "total_sla_minutes": sum(s[3] for s in proc["steps"]),
            "critical_step_count": sum(1 for s in proc["steps"] if s[5]),
            "keywords": "|".join(proc["keywords"]),
        })
        for no, title, role_code, sla, doc, critical in proc["steps"]:
            steps.append({
                "step_id": f"{proc['code']}-{no:02d}",
                "procedure_code": proc["code"],
                "step_no": no,
                "step_title": title,
                "role_code": role_code,
                "role_name": ROLE_BY_CODE[role_code][1],
                "institution": ROLE_BY_CODE[role_code][2],
                "sla_minutes": sla,
                "output_document": doc,
                "is_critical": int(critical),
            })
    return roles, hazards, procedures, steps


# ---------------------------------------------------------------------------
# 2. Korpus dokumentow i chunki dla wyszukiwania semantycznego
# ---------------------------------------------------------------------------

def build_corpus():
    documents, chunks = [], []

    def add_chunk(doc_id, doc_type, proc_code, section, title, text, hazards, roles):
        chunks.append({
            "chunk_id": f"C{len(chunks) + 1:05d}",
            "document_id": doc_id,
            "doc_type": doc_type,
            "procedure_code": proc_code or "",
            "section": section,
            "chunk_title": title,
            "text": " ".join(text.split()),
            "hazard_codes": "|".join(hazards),
            "role_codes": "|".join(roles),
            "char_count": len(" ".join(text.split())),
        })

    # --- 16 SPO ---
    for proc in PROCEDURES:
        code = proc["code"]
        doc_id = f"DOC-{code}"
        owner = ROLE_BY_CODE[proc["owner_role"]]
        hz_names = ", ".join(f"{h} {HAZARD_NAME[h]}" for h in proc["hazards"])
        start_len = len(chunks)

        add_chunk(doc_id, "spo", code, "1. Cel procedury", f"{code} - cel procedury",
                  f"{code} {proc['name']}. Cel procedury: {proc['purpose']} Procedura jest wlasciwa dla fazy "
                  f"{proc['phase']} zarzadzania kryzysowego. Wlasciciel procedury: {owner[1]} ({owner[2]}). "
                  f"Zagrozenia powiazane: {hz_names}.",
                  proc["hazards"], [proc["owner_role"]])

        add_chunk(doc_id, "spo", code, "2. Podstawa prawna", f"{code} - podstawa prawna",
                  f"Podstawa prawna procedury {code}: {proc['legal_basis']}. Procedura stanowi element Krajowego "
                  f"Planu Zarzadzania Kryzysowego i jest uruchamiana w powiazaniu z siatka bezpieczenstwa, ktora "
                  f"wskazuje dzialy administracji rzadowej odpowiedzialne za poszczegolne moduly zadaniowe.",
                  proc["hazards"], [proc["owner_role"]])

        trig = " ".join(f"Przeslanka {i}: {t}." for i, t in enumerate(proc["triggers"], start=1))
        add_chunk(doc_id, "spo", code, "3. Przeslanki uruchomienia", f"{code} - kiedy uruchomic",
                  f"Procedure {code} uruchamia sie, gdy wystapi co najmniej jedna z przeslanek. {trig} "
                  f"W razie watpliwosci o uruchomieniu decyduje {owner[1]}. Uruchomienie procedury odnotowuje sie "
                  f"w dzienniku decyzji wraz z uzasadnieniem i godzina.",
                  proc["hazards"], [proc["owner_role"]])

        participants = sorted({s[2] for s in proc["steps"]})
        part_txt = " ".join(
            f"{ROLE_BY_CODE[r][1]} ({ROLE_BY_CODE[r][2]}) - poziom {ROLE_BY_CODE[r][3]}."
            for r in participants
        )
        add_chunk(doc_id, "spo", code, "4. Uczestnicy i odpowiedzialnosci", f"{code} - kto odpowiada",
                  f"W realizacji procedury {code} uczestnicza: {part_txt} Koordynacje calosci prowadzi {owner[1]}. "
                  f"Kazdy uczestnik potwierdza przyjecie zadania i raportuje wykonanie kroku.",
                  proc["hazards"], participants)

        for no, title, role_code, sla, doc, critical in proc["steps"]:
            role = ROLE_BY_CODE[role_code]
            crit = "Krok krytyczny - jego niewykonanie blokuje dalsze etapy procedury." if critical else \
                   "Krok wspierajacy - moze byc realizowany rownolegle z innymi krokami."
            out = f"Produkt kroku: {doc}." if doc else "Krok nie wytwarza odrebnego dokumentu; wynik odnotowuje sie w dzienniku."
            add_chunk(doc_id, "spo", code, "5. Przebieg - kroki", f"{code} krok {no}: {title}",
                      f"{code} krok {no}. {title}. Odpowiedzialny: {role[1]} ({role[2]}), poziom {role[3]}. "
                      f"Czas normatywny realizacji: {sla_label(sla)} od uruchomienia procedury. {out} {crit} "
                      f"Po wykonaniu kroku odpowiedzialny wprowadza status i godzine wykonania do rejestru realizacji "
                      f"procedury {code}.",
                      proc["hazards"], [role_code])

        docs_out = [s[4] for s in proc["steps"] if s[4]]
        add_chunk(doc_id, "spo", code, "6. Dokumenty wytwarzane", f"{code} - dokumenty",
                  f"W toku realizacji procedury {code} powstaja nastepujace dokumenty: {'; '.join(docs_out)}. "
                  f"Dokumenty przechowuje sie w rejestrze procedury wraz z identyfikatorem uruchomienia, co zapewnia "
                  f"slad audytowy na potrzeby pozniejszego rozliczenia i wnioskow po zdarzeniu.",
                  proc["hazards"], [proc["owner_role"]])

        total = sum(s[3] for s in proc["steps"])
        crit_total = sum(s[3] for s in proc["steps"] if s[5])
        add_chunk(doc_id, "spo", code, "7. Wskazniki i czasy normatywne", f"{code} - SLA i wskazniki",
                  f"Laczny czas normatywny sciezki procedury {code} wynosi {sla_label(total)}, w tym "
                  f"{sla_label(crit_total)} przypada na kroki krytyczne. Mierzone wskazniki: odsetek krokow wykonanych "
                  f"w czasie normatywnym, czas do wykonania pierwszego kroku krytycznego, liczba blokad oraz liczba "
                  f"decyzji odnotowanych w dzienniku.",
                  proc["hazards"], [proc["owner_role"]])

        related = [p["code"] for p in PROCEDURES if p["code"] != code and set(p["hazards"]) & set(proc["hazards"])]
        add_chunk(doc_id, "spo", code, "8. Powiazania", f"{code} - powiazania z innymi procedurami",
                  f"Procedura {code} jest powiazana z: {', '.join(related) if related else 'brak powiazan bezposrednich'}. "
                  f"Powiazanie oznacza, ze procedury dotycza tych samych zagrozen ({', '.join(proc['hazards'])}) i moga "
                  f"byc uruchamiane rownolegle. Slowa kluczowe: {', '.join(proc['keywords'])}.",
                  proc["hazards"], [proc["owner_role"]])

        documents.append({
            "document_id": doc_id,
            "doc_type": "spo",
            "title": f"{code} {proc['name']}",
            "procedure_code": code,
            "voivodeship_code": "",
            "owner_institution": owner[2],
            "section_count": 8,
            "chunk_count": len(chunks) - start_len,
            "char_count": sum(c["char_count"] for c in chunks[start_len:]),
        })

    # --- Wojewodzkie plany zarzadzania kryzysowego ---
    top_hazards = ["Z02", "Z07", "Z19", "Z08", "Z01", "Z12"]
    for wc, wname, capital in VOIVODESHIPS:
        doc_id = f"DOC-WZK-{wc}"
        start_len = len(chunks)
        add_chunk(doc_id, "plan_wojewodzki", "", "1. Charakterystyka wojewodztwa",
                  f"WPZK {wname} - charakterystyka",
                  f"Wojewodzki Plan Zarzadzania Kryzysowego dla wojewodztwa {wname} (kod TERYT {wc}, siedziba "
                  f"wojewody: {capital}). Plan okresla zadania wojewody, sluzb zespolonych i jednostek samorzadu "
                  f"terytorialnego w czterech fazach zarzadzania kryzysowego: zapobieganie, przygotowanie, reagowanie "
                  f"i odbudowa. Plan uruchamia sie zgodnie z procedurami krajowymi SPO-1 do SPO-16.",
                  top_hazards, ["R_WOJ"])
        for hz in top_hazards:
            related_spo = [p["code"] for p in PROCEDURES if hz in p["hazards"]]
            add_chunk(doc_id, "plan_wojewodzki", "", f"2. Zagrozenie {hz}",
                      f"WPZK {wname} - {HAZARD_NAME[hz]}",
                      f"Zagrozenie {hz} {HAZARD_NAME[hz]} w wojewodztwie {wname}. Wojewoda uruchamia Wojewodzki Zespol "
                      f"Zarzadzania Kryzysowego i WCZK w trybie calodobowym. Jesli sily i srodki powiatu sa "
                      f"niewystarczajace, wojewoda przejmuje koordynacje, a przy wyczerpaniu wlasnych mozliwosci "
                      f"kieruje wniosek do ministra wiodacego. Procedury krajowe wlasciwe dla tego zagrozenia: "
                      f"{', '.join(related_spo)}. Informowanie ludnosci realizuje sie w trybie SPO-3, a wnioski "
                      f"o srodki finansowe w trybie SPO-2.",
                      [hz], ["R_WOJ", "R_STAR"])
        add_chunk(doc_id, "plan_wojewodzki", "", "3. Zasady wspolpracy",
                  f"WPZK {wname} - wspolpraca i lacznosc",
                  f"W wojewodztwie {wname} obowiazuje calodobowy dyzur WCZK, ktory przekazuje meldunki do RCB zgodnie "
                  f"z SPO-12. Wymiana informacji z operatorami infrastruktury krytycznej odbywa sie zgodnie z SPO-10. "
                  f"Lista punktow kontaktowych podlega aktualizacji kwartalnej.",
                  ["Z07", "Z12"], ["R_WOJ", "R_OPER_IK"])
        documents.append({
            "document_id": doc_id, "doc_type": "plan_wojewodzki",
            "title": f"Wojewodzki Plan Zarzadzania Kryzysowego - {wname}",
            "procedure_code": "", "voivodeship_code": wc,
            "owner_institution": f"Urzad Wojewodzki w {capital}",
            "section_count": 3, "chunk_count": len(chunks) - start_len,
            "char_count": sum(c["char_count"] for c in chunks[start_len:]),
        })

    # --- Plany ochrony ludnosci ---
    for wc, wname, capital in VOIVODESHIPS:
        doc_id = f"DOC-OL-{wc}"
        start_len = len(chunks)
        sections = [
            ("1. Ewakuacja ludnosci",
             f"Plan ochrony ludnosci wojewodztwa {wname}: zasady ewakuacji I, II i III stopnia, wyznaczenie miejsc "
             f"zbiorki, tras i punktow przyjecia. Ewakuacja z terenow zalewowych realizowana jest we wspolpracy z PSP "
             f"i Policja, a informowanie mieszkancow w trybie SPO-3.", ["Z02", "Z08"]),
            ("2. Schronienie i pomoc socjalna",
             f"Zabezpieczenie miejsc tymczasowego schronienia w wojewodztwie {wname}, wyzywienia i pomocy socjalnej dla "
             f"osob ewakuowanych, w tym osob wrazliwych: seniorow samotnych, osob z niepelnosprawnosciami i pacjentow "
             f"wymagajacych zasilania medycznego. Finansowanie w trybie SPO-2.", ["Z02", "Z19"]),
            ("3. Zaopatrzenie i rezerwy",
             f"Zasady wydawania agregatow pradotworczych, wody butelkowanej i srodkow ratunkowych z zasobow wojewody "
             f"{wname}. Uruchomienie rezerw strategicznych nastepuje na wniosek wojewody.", ["Z07", "Z09"]),
            ("4. Ostrzeganie i alarmowanie",
             f"System wykrywania i alarmowania w wojewodztwie {wname}: syreny, Alert RCB, RSO oraz kanaly samorzadowe. "
             f"Alarmowanie o zagrozeniu z powietrza realizuje sie zgodnie z SPO-13, a informowanie ludnosci zgodnie "
             f"z SPO-3.", ["Z04", "Z16"]),
            ("5. Osoby wymagajace szczegolnego wsparcia",
             f"Rejestr osob wymagajacych szczegolnego wsparcia w wojewodztwie {wname} prowadza gminy. Dane sa "
             f"przetwarzane z zachowaniem minimalizacji i udostepniane wylacznie uprawnionym sluzbom.", ["Z19", "Z07"]),
            ("6. Odbudowa i powrot do normalnosci",
             f"Zasady szacowania strat, odtwarzania infrastruktury i wsparcia mieszkancow wojewodztwa {wname} po "
             f"ustaniu zagrozenia, w tym rozliczenie srodkow uruchomionych w trybie SPO-2.", ["Z02"]),
        ]
        for sec_title, text, hz in sections:
            add_chunk(doc_id, "plan_ol", "", sec_title, f"Plan OL {wname} - {sec_title[3:]}", text, hz, ["R_WOJ", "R_WOJT"])
        documents.append({
            "document_id": doc_id, "doc_type": "plan_ol",
            "title": f"Plan Ochrony Ludnosci - wojewodztwo {wname}",
            "procedure_code": "", "voivodeship_code": wc,
            "owner_institution": f"Urzad Wojewodzki w {capital}",
            "section_count": len(sections), "chunk_count": len(chunks) - start_len,
            "char_count": sum(c["char_count"] for c in chunks[start_len:]),
        })

    # --- Karty zagrozen KPZK ---
    doc_id = "DOC-KPZK"
    start_len = len(chunks)
    for hz_code, hz_name, matrix in HAZARDS:
        related_spo = [p["code"] for p in PROCEDURES if hz_code in p["hazards"]]
        add_chunk(doc_id, "kpzk", "", f"Karta zagrozenia {hz_code}",
                  f"KPZK - {hz_code} {hz_name}",
                  f"Karta zagrozenia {hz_code} {hz_name} z Krajowego Planu Zarzadzania Kryzysowego. Pozycja w matrycy "
                  f"ryzyka: {matrix}. Procedury operacyjne wlasciwe dla tego zagrozenia: "
                  f"{', '.join(related_spo) if related_spo else 'brak dedykowanej SPO - stosuje sie SPO-12 i SPO-3'}. "
                  f"Poziomy reagowania: gmina, powiat, wojewoda, minister wiodacy, Rzadowy Zespol Zarzadzania "
                  f"Kryzysowego.",
                  [hz_code], ["R_DYR_RCB"])
    add_chunk(doc_id, "kpzk", "", "Siatka bezpieczenstwa",
              "KPZK - siatka bezpieczenstwa",
              "Siatka bezpieczenstwa przypisuje kazdemu z 20 zagrozen dzialy administracji rzadowej odpowiedzialne za "
              "moduly zadaniowe w fazie reagowania (R) i odbudowy (O). Minister wiodacy koordynuje realizacje zadan, a "
              "przy zaangazowaniu kilku ministrow lub wyczerpaniu sil i srodkow sprawa trafia na posiedzenie RZZK "
              "w trybie SPO-1.", [h[0] for h in HAZARDS], ["R_DYR_RCB"])
    add_chunk(doc_id, "kpzk", "", "Poziomy reagowania",
              "KPZK - poziomy reagowania i eskalacja",
              "Eskalacja przebiega w kolejnosci: gmina, powiat, wojewoda, minister wiodacy, Rzadowy Zespol Zarzadzania "
              "Kryzysowego. Wojewoda przejmuje koordynacje, gdy brakuje sil i srodkow w powiecie. RZZK zwoluje sie, gdy "
              "w dzialania zaangazowanych jest kilku ministrow albo minister wiodacy wyczerpal wlasne mozliwosci. "
              "Obieg informacji miedzy poziomami reguluje SPO-12.",
              [h[0] for h in HAZARDS], ["R_DYR_RCB", "R_WOJ"])
    documents.append({
        "document_id": doc_id, "doc_type": "kpzk",
        "title": "Krajowy Plan Zarzadzania Kryzysowego - karty zagrozen i siatka bezpieczenstwa",
        "procedure_code": "", "voivodeship_code": "",
        "owner_institution": "Rzadowe Centrum Bezpieczenstwa",
        "section_count": len(HAZARDS) + 2, "chunk_count": len(chunks) - start_len,
        "char_count": sum(c["char_count"] for c in chunks[start_len:]),
    })

    return documents, chunks


def attach_doc_titles(documents, chunks):
    titles = {d["document_id"]: d["title"] for d in documents}
    for c in chunks:
        c["doc_title"] = titles.get(c["document_id"], "")
    return chunks


# ---------------------------------------------------------------------------
# 3. Uruchomienia procedur, wykonania krokow, dziennik decyzji
# ---------------------------------------------------------------------------

def pick_procedure_for_history() -> dict:
    weights = {
        "SPO-12": 26, "SPO-3": 18, "SPO-10": 12, "SPO-2": 9, "SPO-1": 7,
        "SPO-16": 6, "SPO-13": 5, "SPO-9": 4, "SPO-15": 4, "SPO-5": 2,
        "SPO-14": 2, "SPO-11": 2, "SPO-4": 1, "SPO-8": 1, "SPO-6": 0.5, "SPO-7": 0.5,
    }
    codes = list(weights)
    probs = np.array([weights[c] for c in codes], dtype=float)
    probs = probs / probs.sum()
    return PROC_BY_CODE[str(rng.choice(codes, p=probs))]


def build_activations():
    activations, executions, decisions = [], [], []
    seq = {"a": 0, "e": 0, "d": 0}

    def run_activation(proc, started_at, level, wc, wname, event_name, stress):
        """stress 0..1 - im wyzszy, tym wieksza presja czasowa i ryzyko blokad."""
        seq["a"] += 1
        act_id = f"ACT-{seq['a']:05d}"
        trigger = random.choice(proc["triggers"])
        owner = ROLE_BY_CODE[proc["owner_role"]]
        cursor = started_at
        completed_steps = 0
        blocked = 0
        breaches = 0

        for no, title, role_code, sla, doc, critical in proc["steps"]:
            seq["e"] += 1
            planned_start = cursor
            # opoznienie startu kroku jest proporcjonalne do czasu normatywnego
            start_delay = max(0.0, rng.normal(0.06 * sla * (1.0 + stress), 0.05 * sla))
            started = planned_start + timedelta(minutes=float(start_delay))
            base_ratio = rng.gamma(shape=4.0, scale=0.13)  # srednio ~0.52 czasu normatywnego
            ratio = base_ratio * (1.0 + 0.45 * stress)
            chronic = CHRONIC_BREACHES.get((proc["code"], no))
            if chronic is not None and rng.random() < chronic:
                ratio = max(ratio, float(rng.uniform(1.15, 2.6)))
            duration = max(3.0, sla * ratio)

            status = "wykonany"
            blocker = ""
            if rng.random() < 0.025 + 0.06 * stress:
                status = "zablokowany" if critical else "pominiety"
                blocker = pick_blocker(proc["code"])
                if status == "zablokowany":
                    duration *= 1.9
                    blocked += 1
            completed = started + timedelta(minutes=float(duration))
            elapsed = (completed - planned_start).total_seconds() / 60.0
            sla_met = int(elapsed <= sla and status != "zablokowany")
            if not sla_met:
                breaches += 1
            if status != "pominiety":
                completed_steps += 1

            executions.append({
                "execution_id": f"EXE-{seq['e']:06d}",
                "activation_id": act_id,
                "procedure_code": proc["code"],
                "step_id": f"{proc['code']}-{no:02d}",
                "step_no": no,
                "step_title": title,
                "role_code": role_code,
                "institution": ROLE_BY_CODE[role_code][2],
                "level": level,
                "voivodeship_code": wc,
                "event_name": event_name,
                "planned_start": iso(planned_start),
                "started_at": iso(started),
                "completed_at": iso(completed),
                "sla_minutes": sla,
                "elapsed_minutes": round(elapsed, 1),
                "sla_met": sla_met,
                "is_critical": int(critical),
                "status": status,
                "blocker_reason": blocker,
                "output_document": doc,
                "event_time": iso(completed),
            })

            # dziennik decyzji dla wybranych krokow
            if critical and rng.random() < 0.34:
                seq["d"] += 1
                decisions.append({
                    "decision_id": f"DEC-{seq['d']:05d}",
                    "activation_id": act_id,
                    "procedure_code": proc["code"],
                    "step_no": no,
                    "decided_at": iso(completed + timedelta(minutes=float(rng.integers(2, 25)))),
                    "decision_type": random.choice(DECISION_TYPES),
                    "decided_by_role": role_code,
                    "decided_by_name": ROLE_BY_CODE[role_code][1],
                    "subject": f"{proc['code']} krok {no}: {title}",
                    "rationale": f"Decyzja podjeta na podstawie ustalen kroku {no} procedury {proc['code']} "
                                 f"w ramach zdarzenia {event_name}.",
                    "classification": random.choices(CLASSIFICATIONS, weights=[0.72, 0.22, 0.06])[0],
                    "event_time": iso(completed + timedelta(minutes=float(rng.integers(2, 25)))),
                })

            cursor = completed - timedelta(minutes=float(max(0.0, rng.normal(sla * 0.18, sla * 0.1))))
            cursor = max(cursor, planned_start + timedelta(minutes=1))

        closed_at = max(datetime.fromisoformat(e["completed_at"]) for e in executions[-len(proc["steps"]):])
        activations.append({
            "activation_id": act_id,
            "procedure_code": proc["code"],
            "procedure_name": proc["name"],
            "event_name": event_name,
            "hazard_code": random.choice(proc["hazards"]),
            "level": level,
            "voivodeship_code": wc,
            "voivodeship_name": wname,
            "initiated_by_role": proc["owner_role"],
            "initiated_by_institution": owner[2],
            "trigger_text": trigger,
            "started_at": iso(started_at),
            "closed_at": iso(closed_at),
            "duration_minutes": round((closed_at - started_at).total_seconds() / 60.0, 1),
            "steps_total": len(proc["steps"]),
            "steps_completed": completed_steps,
            "steps_blocked": blocked,
            "steps_sla_breached": breaches,
            "sla_compliance_pct": round(100.0 * (len(proc["steps"]) - breaches) / len(proc["steps"]), 1),
            "status": "zamkniete",
            "event_time": iso(started_at),
        })

    # --- Historia 2023-01 .. 2026-09-11 ---
    span_minutes = int((WINDOW_START - HISTORY_START).total_seconds() / 60)
    for _ in range(960):
        proc = pick_procedure_for_history()
        started_at = HISTORY_START + timedelta(minutes=int(rng.integers(0, span_minutes)))
        level = random.choices(LEVELS, weights=[0.12, 0.2, 0.38, 0.3])[0]
        wc, wname, _ = VOIVODESHIPS[int(rng.integers(0, len(VOIVODESHIPS)))]
        # zimowe i wiosenne szczyty stresu
        month = started_at.month
        stress = 0.25 + (0.3 if month in (1, 2, 7, 9) else 0.0) + float(rng.random()) * 0.3
        run_activation(proc, started_at, level, wc, wname, "historia operacyjna", min(stress, 1.0))

    # --- Scenariusz osiowy: POWODZ WRZESIEN (D-3 .. D+10) ---
    flood_plan = [
        ("SPO-12", -3.0, "wojewodzki", "02"), ("SPO-12", -2.6, "wojewodzki", "16"),
        ("SPO-3", -2.2, "wojewodzki", "02"), ("SPO-10", -1.8, "krajowy", "02"),
        ("SPO-12", -1.2, "krajowy", "14"), ("SPO-3", -0.6, "krajowy", "14"),
        ("SPO-1", 0.1, "krajowy", "14"), ("SPO-3", 0.3, "krajowy", "14"),
        ("SPO-10", 0.5, "krajowy", "02"), ("SPO-2", 0.8, "krajowy", "14"),
        ("SPO-5", 1.1, "krajowy", "14"), ("SPO-15", 1.4, "wojewodzki", "16"),
        ("SPO-12", 1.6, "krajowy", "14"), ("SPO-3", 2.0, "krajowy", "14"),
        ("SPO-2", 2.4, "wojewodzki", "16"), ("SPO-10", 2.8, "wojewodzki", "24"),
        ("SPO-16", 3.2, "krajowy", "14"), ("SPO-1", 3.6, "krajowy", "14"),
        ("SPO-9", 4.1, "wojewodzki", "08"), ("SPO-3", 4.5, "krajowy", "14"),
        ("SPO-2", 5.2, "krajowy", "14"), ("SPO-12", 6.0, "krajowy", "14"),
        ("SPO-10", 6.6, "wojewodzki", "32"), ("SPO-3", 7.2, "krajowy", "14"),
        ("SPO-2", 8.4, "wojewodzki", "02"), ("SPO-12", 9.5, "krajowy", "14"),
    ]
    voiv_by_code = {v[0]: v for v in VOIVODESHIPS}
    for code, day_offset, level, wc in flood_plan:
        proc = PROC_BY_CODE[code]
        started_at = D0 + timedelta(days=day_offset)
        stress = 0.55 + 0.4 * max(0.0, 1.0 - abs(day_offset) / 6.0)
        wname = voiv_by_code[wc][1]
        run_activation(proc, started_at, level, wc, wname, "POWODZ WRZESIEN", min(stress, 1.0))

    return activations, executions, decisions


# ---------------------------------------------------------------------------
# 4. Zapytania do asystenta (telemetria Copilota)
# ---------------------------------------------------------------------------

def build_queries(chunks):
    chunks_by_proc = {}
    for c in chunks:
        if c["procedure_code"]:
            chunks_by_proc.setdefault(c["procedure_code"], []).append(c["chunk_id"])

    queries = []
    span_minutes = int((WINDOW_END - HISTORY_START).total_seconds() / 60)
    for i in range(4200):
        question, expected = EVAL_QUESTIONS[int(rng.integers(0, len(EVAL_QUESTIONS)))]
        asked_at = HISTORY_START + timedelta(minutes=int(rng.integers(0, span_minutes)))
        confidence = float(np.clip(rng.normal(0.82, 0.12), 0.15, 0.99))
        hit = confidence > 0.45 and rng.random() < 0.94
        top_proc = expected if hit else random.choice([p["code"] for p in PROCEDURES if p["code"] != expected])
        cited = random.sample(chunks_by_proc[top_proc], k=min(3, len(chunks_by_proc[top_proc])))
        queries.append({
            "query_id": f"Q-{i + 1:06d}",
            "asked_at": iso(asked_at),
            "user_role": random.choice(USER_ROLES),
            "channel": random.choices(["Fabric App", "Teams", "Data Agent"], weights=[0.5, 0.3, 0.2])[0],
            "question": question,
            "expected_procedure": expected,
            "top_procedure": top_proc,
            "confidence": round(confidence, 3),
            "is_correct": int(top_proc == expected),
            "cited_chunk_ids": "|".join(cited),
            "latency_ms": int(np.clip(rng.normal(1450, 420), 380, 6000)),
            "feedback": random.choices(["pomocne", "brak oceny", "niepomocne"], weights=[0.46, 0.47, 0.07])[0],
            "event_time": iso(asked_at),
        })
    return queries


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    roles, hazards, procedures, steps = build_dimensions()
    write_csv(DATA / "dim_role.csv", roles, list(roles[0]))
    write_csv(DATA / "dim_hazard.csv", hazards, list(hazards[0]))
    write_csv(DATA / "dim_procedure.csv", procedures, list(procedures[0]))
    write_csv(DATA / "dim_step.csv", steps, list(steps[0]))

    documents, chunks = build_corpus()
    chunks = attach_doc_titles(documents, chunks)
    write_csv(DATA / "dim_document.csv", documents, list(documents[0]))
    write_jsonl(DATA / "corpus_chunks.jsonl", chunks)

    activations, executions, decisions = build_activations()
    write_jsonl(DATA / "fact_activation.jsonl", activations)
    write_jsonl(DATA / "fact_step_execution.jsonl", executions)
    write_jsonl(DATA / "fact_decision_log.jsonl", decisions)

    queries = build_queries(chunks)
    write_jsonl(DATA / "fact_assistant_query.jsonl", queries)

    write_csv(DATA / "eval_questions.csv",
              [{"question_id": f"EVQ-{i + 1:03d}", "question": q, "expected_procedure": p}
               for i, (q, p) in enumerate(EVAL_QUESTIONS)],
              ["question_id", "question", "expected_procedure"])

    counts = {
        "dim_role": len(roles),
        "dim_hazard": len(hazards),
        "dim_procedure": len(procedures),
        "dim_step": len(steps),
        "dim_document": len(documents),
        "corpus_chunks": len(chunks),
        "corpus_chars": sum(c["char_count"] for c in chunks),
        "fact_activation": len(activations),
        "fact_step_execution": len(executions),
        "fact_decision_log": len(decisions),
        "fact_assistant_query": len(queries),
        "eval_questions": len(EVAL_QUESTIONS),
    }
    (DATA / "record_counts.json").write_text(json.dumps(counts, indent=2, ensure_ascii=False), encoding="utf-8")

    for name, value in counts.items():
        print(f"{name:24s} {value:>8}")
    print(f"\nOK: dane zapisane w {DATA}")


if __name__ == "__main__":
    main()
