from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

STREAM_FILES = {
    "step_execution": "fact_step_execution.jsonl",
    "decision_log": "fact_decision_log.jsonl",
    "assistant_query": "fact_assistant_query.jsonl",
    "activation": "fact_activation.jsonl",
}
BASE = Path(__file__).resolve().parent
DATA = BASE / "datasets"
FLUSH_EVERY = 200
API = "https://api.fabric.microsoft.com/v1"

# Pola, ktore trzeba przesunac razem z osia czasu, zeby zachowac spojnosc
# (np. czas planowany kroku wzgledem faktycznego rozpoczecia).
TIME_FIELDS = ("event_time", "started_at", "closed_at", "planned_start",
               "completed_at", "decided_at", "asked_at")


def parse_time(value: str | None):
    return datetime.fromisoformat(value) if value else None


def shift_event(event: dict, offset: timedelta, speed: float, anchor: datetime) -> None:
    """Przesuwa znaczniki czasu zdarzenia na bieżący czas, sciskajac os o `speed`.
    Dzieki temu zdarzenie trafia do Eventhouse ze znacznikiem odpowiadajacym
    momentowi wyslania, a dashboard w oknie 'ostatnia godzina' zyje na oczach."""
    for field in TIME_FIELDS:
        raw = event.get(field)
        if not isinstance(raw, str):
            continue
        ts = parse_time(raw)
        event[field] = (anchor + (ts - anchor - offset) / speed).isoformat()


def eventhub_connection() -> tuple[str, str | None]:
    """Kolejnosc zrodel: zmienna srodowiskowa, config.json, API Fabric."""
    conn = os.environ.get("EVENTHUB_CONNECTION_STR")
    if conn:
        return conn, os.environ.get("EVENTHUB_NAME")

    cfg = json.load(open(BASE / "config.json", encoding="utf-8"))
    conn = cfg.get("eventstream", {}).get("connection_string")
    if conn:
        return conn, cfg["eventstream"].get("event_hub_name")

    import requests  # lazy import

    fab = cfg["fabric"]
    tok = subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, shell=True).stdout.strip()
    headers = {"Authorization": f"Bearer {tok}"}
    ws = fab["workspace_id"]
    name = cfg["eventstream"]["name"]
    streams = requests.get(f"{API}/workspaces/{ws}/eventstreams", headers=headers).json()["value"]
    es_id = next(s["id"] for s in streams if s["displayName"] == name)
    topo = requests.get(f"{API}/workspaces/{ws}/eventstreams/{es_id}/topology",
                        headers=headers).json()
    src = next(s for s in topo["sources"] if s["type"] == "CustomEndpoint")
    info = requests.get(
        f"{API}/workspaces/{ws}/eventstreams/{es_id}/sources/{src['id']}/connection",
        headers=headers).json()
    print(f"poswiadczenia pobrane z API (zrodlo: {src['name']})")
    return info["accessKeys"]["primaryConnectionString"], info["eventHubName"]


def iter_events(streams, start=None, end=None):
    for stream in streams:
        with (DATA / STREAM_FILES[stream]).open(encoding="utf-8") as f:
            for line in f:
                event = json.loads(line)
                event["_stream"] = stream
                ts = parse_time(event["event_time"])
                if start and ts < start:
                    continue
                if end and ts > end:
                    continue
                yield event


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wysylka strumieni realizacji procedur SPO do Fabric Eventstream / Event Hub."
    )
    parser.add_argument("--stream", action="append", choices=STREAM_FILES.keys(),
                        help="Nazwa strumienia, można podac wielokrotnie. Domyslnie: wszystkie.")
    parser.add_argument("--speed", type=float, default=120.0, help="Mnoznik przyspieszenia symulacji.")
    parser.add_argument("--from", dest="from_time", help="Filtr czasu ISO od.")
    parser.add_argument("--to", dest="to_time", help="Filtr czasu ISO do.")
    parser.add_argument("--limit", type=int, help="Maksymalna liczba zdarzen do wyslania.")
    parser.add_argument("--dry-run", action="store_true", help="Tryb offline, bez zależności i poswiadczen.")
    parser.add_argument("--shift-to-now", action="store_true",
                        help="Przesuwa znaczniki czasu na biezaca chwile - wymagane, "
                             "zeby dashboard pokazywal napływ danych w oknie ostatnich godzin.")
    parser.add_argument("--compress-to", type=float, metavar="GODZINY",
                        help="Dobiera --speed tak, zeby caly wybrany zakres zmiescil się "
                             "w podanej liczbie godzin. Wlacza --shift-to-now.")
    args = parser.parse_args()

    streams = args.stream or list(STREAM_FILES)
    events = sorted(iter_events(streams, parse_time(args.from_time), parse_time(args.to_time)),
                    key=lambda e: e["event_time"])
    if args.limit:
        events = events[: args.limit]
    if args.compress_to and events:
        span = (parse_time(events[-1]["event_time"]) - parse_time(events[0]["event_time"])).total_seconds()
        args.speed = max(span / (args.compress_to * 3600), 1.0)
        args.shift_to_now = True
        print(f"zakres {span / 86400:.1f} dni -> {args.compress_to} h, "
              f"kompresja {args.speed:.0f}x, {len(events)} zdarzen "
              f"(~{len(events) / (args.compress_to * 60):.1f}/min)")
    if args.dry_run:
        out = DATA / "derived" / ("dry_run_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jsonl")
        out.parent.mkdir(exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for event in events[:2000]:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        print(f"DRY RUN OK: wybrano {len(events)} zdarzen ze strumieni {streams}; probka w {out}")
        for event in events[:3]:
            print(json.dumps(event, ensure_ascii=False))
        return

    from azure.eventhub import EventData, EventHubProducerClient  # lazy import

    conn_str, hub_name = eventhub_connection()
    producer = EventHubProducerClient.from_connection_string(
        conn_str=conn_str, eventhub_name=hub_name,
    )
    anchor = datetime.now(timezone.utc)
    offset = parse_time(events[0]["event_time"]) - anchor if events else timedelta()
    if args.shift_to_now:
        print(f"przesuniecie osi czasu na teraz, kompresja {args.speed}x")
    prev = None
    sent = 0
    with producer:
        batch = producer.create_batch()
        pending = 0
        for event in events:
            ts = parse_time(event["event_time"])
            if prev:
                time.sleep(max(0, (ts - prev).total_seconds() / args.speed))
            prev = ts
            if args.shift_to_now:
                shift_event(event, offset, args.speed, anchor)
            # Eventstream (ProcessedIngestion) mapuje pola po nazwach kolumn tabeli
            # docelowej - tabele *_raw maja pojedyncza kolumne dynamic "payload".
            envelope = {"_stream": event["_stream"], "payload": event}
            payload = json.dumps(envelope, ensure_ascii=False)
            try:
                batch.add(EventData(payload))
                pending += 1
            except ValueError:
                producer.send_batch(batch)
                sent += pending
                batch = producer.create_batch()
                batch.add(EventData(payload))
                pending = 1
            if pending >= FLUSH_EVERY:
                producer.send_batch(batch)
                sent += pending
                print(f"... wyslano {sent} zdarzen", flush=True)
                batch = producer.create_batch()
                pending = 0
        if pending > 0:
            producer.send_batch(batch)
            sent += pending
    print(f"SENT OK: {sent} zdarzen")


if __name__ == "__main__":
    main()
