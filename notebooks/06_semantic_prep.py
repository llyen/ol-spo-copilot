"""Przygotowanie warstwy semantycznej w Lakehouse (notatnik uruchamiany wyłącznie w Fabric).

Model semantyczny działa w trybie Direct Lake, ktory nie obsluguje kolumn wyliczanych DAX.
Wszystkie kolumny opisane w semantic-model/MODEL.md jako "kolumny wyliczane" materializujemy
tutaj w tabelach Delta. Dodatkowo budujemy wymiar czasu dim_date.
"""

from pyspark.sql import functions as F  # noqa: F401  (dostepne tylko w Fabric)

spark = spark  # noqa: F821  (sesja Spark dostarczana przez Fabric)

TS = "yyyy-MM-dd'T'HH:mm:ss"


def to_ts(col):
    return F.to_timestamp(F.substring(F.col(col), 1, 19), TS)


# --- fakty: kolumny dat + kolumny wyliczane ------------------------------------

act = spark.read.table("fact_activation")
act = (act
       .withColumn("started_ts", to_ts("started_at"))
       .withColumn("started_date", F.to_date(to_ts("started_at")))
       .withColumn("duration_hours", F.col("duration_minutes") / F.lit(60.0))
       .withColumn("is_flood_scenario", (F.col("event_name") == F.lit("POWODZ WRZESIEN")).cast("int")))
act.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_activation")

step = spark.read.table("fact_step_execution")
step = (step
        .withColumn("event_ts", to_ts("event_time"))
        .withColumn("event_date", F.to_date(to_ts("event_time")))
        .withColumn("completed_ts", to_ts("completed_at"))
        .withColumn("started_ts", to_ts("started_at"))
        .withColumn("overdue_minutes", F.col("elapsed_minutes") - F.col("sla_minutes"))
        .withColumn("sla_bucket",
                    F.when(F.col("elapsed_minutes").isNull(), F.lit("brak danych"))
                     .when(F.col("elapsed_minutes") <= F.col("sla_minutes"), F.lit("w normie"))
                     .when(F.col("elapsed_minutes") <= 2 * F.col("sla_minutes"), F.lit("do 2x normy"))
                     .otherwise(F.lit("powyzej 2x normy"))))
step.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_step_execution")

dec = spark.read.table("fact_decision_log")
dec = (dec
       .withColumn("decided_ts", to_ts("decided_at"))
       .withColumn("decided_date", F.to_date(to_ts("decided_at"))))
dec.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_decision_log")

qry = spark.read.table("fact_assistant_query")
qry = (qry
       .withColumn("asked_ts", to_ts("asked_at"))
       .withColumn("asked_date", F.to_date(to_ts("asked_at")))
       .withColumn("latency_s", F.col("latency_ms") / F.lit(1000.0)))
qry.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_assistant_query")

proc = spark.read.table("dim_procedure")
proc = proc.withColumn("sla_path_hours", F.col("total_sla_minutes") / F.lit(60.0))
proc.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_procedure")

# --- wymiar czasu --------------------------------------------------------------

bounds = (act.select(F.min("started_date").alias("lo"), F.max("started_date").alias("hi"))
             .union(step.select(F.min("event_date"), F.max("event_date")))
             .union(dec.select(F.min("decided_date"), F.max("decided_date")))
             .union(qry.select(F.min("asked_date"), F.max("asked_date")))
             .agg(F.min("lo").alias("lo"), F.max("hi").alias("hi")).collect()[0])

lo = bounds["lo"].replace(month=1, day=1)
hi = bounds["hi"].replace(month=12, day=31)

MONTHS = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
          "lipca", "sierpnia", "wrzesnia", "pazdziernika", "listopada", "grudnia"]
DAYS = ["poniedzialek", "wtorek", "sroda", "czwartek", "piatek", "sobota", "niedziela"]

dates = (spark.sql(f"SELECT explode(sequence(to_date('{lo}'), to_date('{hi}'), interval 1 day)) AS date")
         .withColumn("year", F.year("date"))
         .withColumn("quarter", F.concat(F.lit("K"), F.quarter("date")))
         .withColumn("month_no", F.month("date"))
         .withColumn("month_name", F.element_at(F.array(*[F.lit(m) for m in MONTHS]), F.month("date")))
         .withColumn("year_month", F.date_format("date", "yyyy-MM"))
         .withColumn("day_of_month", F.dayofmonth("date"))
         .withColumn("day_name", F.element_at(F.array(*[F.lit(d) for d in DAYS]),
                                              F.dayofweek(F.col("date")) - 1 + F.when(F.dayofweek("date") == 1, 7).otherwise(0)))
         .withColumn("is_weekend", (F.dayofweek("date").isin(1, 7)).cast("int"))
         .withColumn("date_key", F.date_format("date", "yyyyMMdd").cast("int")))
dates.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_date")

print("dim_date:", dates.count(), "wierszy;", lo, "->", hi)
for t in ("fact_activation", "fact_step_execution", "fact_decision_log",
          "fact_assistant_query", "dim_procedure", "dim_date"):
    print(t, spark.read.table(t).count())
