"""
Run this to inspect your BigQuery table and verify column mapping.

    cd oos_agent_v3
    source venv/bin/activate
    python data/schema_check.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

BQ_PROJECT = os.getenv("BQ_PROJECT", "noonbigmktgsandbox")
BQ_DATASET = os.getenv("BQ_DATASET", "vinod")
BQ_TABLE   = os.getenv("BQ_TABLE",   "oos_sku_daily")

try:
    from google.cloud import bigquery
    client = bigquery.Client(project=BQ_PROJECT)
    table  = client.get_table(f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}")

    print(f"\n✅  Connected: {BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}")
    print(f"    Rows (approx): {table.num_rows:,}\n")

    actual_cols = {f.name.lower(): f.field_type for f in table.schema}

    print(f"{'─'*60}")
    print(f"  {'ACTUAL COLUMN':<35} {'TYPE'}")
    print(f"{'─'*60}")
    for col, typ in sorted(actual_cols.items()):
        print(f"  {col:<35} {typ}")

    from data.bigquery import COLUMN_ALIASES
    print(f"\n{'─'*60}")
    print("  MAPPING RESULTS (standard name → your column)")
    print(f"{'─'*60}")
    for std, aliases in COLUMN_ALIASES.items():
        matched = next((a for a in aliases if a.lower() in actual_cols), None)
        if matched:
            print(f"  ✅  {std:<25} → {matched}  ({actual_cols[matched.lower()]})")
        else:
            print(f"  ⚠️   {std:<25} → NOT FOUND (will be derived or defaulted)")

    print(f"\n{'─'*60}")
    print("  SAMPLE ROW (first 1 row)")
    print(f"{'─'*60}")
    row = client.query(
        f"SELECT * FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}` LIMIT 1"
    ).to_dataframe()
    for col in row.columns:
        print(f"  {col:<35} {repr(row[col].iloc[0])}")

except Exception as e:
    print(f"\n❌  Error: {e}")
    print("\nFix options:")
    print("  1. Run:  gcloud auth application-default login")
    print("  2. Set:  GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json  in .env")
