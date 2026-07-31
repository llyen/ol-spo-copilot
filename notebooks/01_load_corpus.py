# CELL
# 01 - zaladowanie korpusu procedur i wymiarow do Lakehouse
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "datasets"

# CELL
CSV_TABLES = ["dim_role", "dim_hazard", "dim_procedure", "dim_step", "dim_document", "eval_questions"]
JSONL_TABLES = ["corpus_chunks", "fact_activation", "fact_step_execution", "fact_decision_log", "fact_assistant_query"]

for name in CSV_TABLES:
    df = pd.read_csv(DATA / f"{name}.csv", dtype={"voivodeship_code": str})
    print(f"{name:24s} {df.shape}")

for name in JSONL_TABLES:
    df = pd.read_json(DATA / f"{name}.jsonl", lines=True)
    print(f"{name:24s} {df.shape}")

# CELL
# Mostek procedura -> zagrozenie (hazard_codes to lista rozdzielona znakiem |)
proc = pd.read_csv(DATA / "dim_procedure.csv")
bridge = (
    proc.assign(hazard_code=proc.hazard_codes.str.split("|"))
        .explode("hazard_code")[["procedure_code", "hazard_code"]]
        .reset_index(drop=True)
)
OUT = DATA / "derived"
OUT.mkdir(exist_ok=True)
bridge.to_csv(OUT / "bridge_procedure_hazard.csv", index=False)
print(f"bridge_procedure_hazard  {bridge.shape}")

# CELL
# W Microsoft Fabric ta komorka zapisuje tabele Delta w Lakehouse:
#
# for name in CSV_TABLES:
#     spark.createDataFrame(pd.read_csv(f"/lakehouse/default/Files/datasets/{name}.csv")) \
#          .write.mode("overwrite").saveAsTable(name)
# for name in JSONL_TABLES:
#     spark.read.json(f"Files/datasets/{name}.jsonl") \
#          .write.mode("overwrite").saveAsTable(name)
#
# Tabela corpus_chunks jest zrodlem dla indeksu wektorowego (notatnik 02)
# oraz dla Data Agenta (grounding).
print("OK - korpus gotowy do zaladowania")
