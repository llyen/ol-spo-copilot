# Skrypty wdrożeniowe Fabric

Skrypty tworzą elementy Fabric przez REST API. Uwierzytelnianie: `az login`
(tokeny pobierane przez `az account get-access-token`). Wszystkie czytają
`config.json` z katalogu głównego repozytorium — plik nie jest wersjonowany,
wzorzec znajduje się w `config.example.json`.

| Skrypt | Co robi |
|---|---|
| [`../deploy_fabric.py`](../deploy_fabric.py) | OneLake, notatniki, skrypty KQL, ingest historii |
| [`get_schemas.py`](get_schemas.py) | odczytuje schematy tabel Delta z dziennika transakcji i zapisuje `lakehouse_schemas.json` |
| [`create_semantic_model.py`](create_semantic_model.py) | model semantyczny Direct Lake (TMDL): 13 tabel, relacje, 28 miar |
| [`create_report.py`](create_report.py) | raport Power BI (PBIR): 6 stron, ciemny motyw operacyjny |

Kolejność uruchomienia:

```powershell
python deploy_fabric.py --config config.json --step all
# uruchom notatniki 01-05, potem 06_semantic_prep (w portalu Fabric)
python fabric\get_schemas.py
python fabric\create_semantic_model.py
# uzupelnij semantic_model_id w config.json
python fabric\create_report.py
```

Skrypty są idempotentne: jeśli element o danej nazwie istnieje, wywołują
`updateDefinition` zamiast tworzyć duplikat. Wyjątkiem jest
`deploy_fabric.py --step history` — ingest do Eventhouse **nie** jest idempotentny.

Szczegóły, ograniczenia platformy i typowe błędy: [`../SETUP_FABRIC.md`](../SETUP_FABRIC.md).
