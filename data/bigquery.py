"""
BigQuery data layer — noonbigmktgsandbox.vinod.oos_sku_daily

Confirmed schema:
  date                DATE
  sku_id              STRING
  category            STRING
  brand               STRING
  stock_available     INTEGER
  stock_incoming      INTEGER
  daily_sales         INTEGER
  last_restock_date   DATE
  supplier_lead_time  INTEGER
  price               FLOAT
"""

import os
import streamlit as st
import pandas as pd

BQ_PROJECT = os.getenv("BQ_PROJECT", "noonbigmktgsandbox")
BQ_DATASET = os.getenv("BQ_DATASET", "vinod")
BQ_TABLE   = os.getenv("BQ_TABLE",   "oos_sku_daily")
FULL_TABLE = f"`{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`"


@st.cache_resource(show_spinner=False)
def _get_client():
    try:
        from google.cloud import bigquery
        # Try Streamlit Cloud service account secret first
        try:
            sa = dict(st.secrets["gcp_service_account"])
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_info(
                sa, scopes=["https://www.googleapis.com/auth/bigquery"])
            return bigquery.Client(project=BQ_PROJECT, credentials=creds)
        except Exception:
            pass
        # Fall back to ADC (gcloud auth application-default login)
        return bigquery.Client(project=BQ_PROJECT)
    except Exception:
        return None


def _run_query(sql: str) -> pd.DataFrame:
    client = _get_client()
    if client is None:
        return pd.DataFrame()
    try:
        return client.query(sql).to_dataframe()
    except Exception as e:
        st.warning(f"BQ query failed — using mock data. Error: {e}")
        return pd.DataFrame()


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all derived columns from the raw BQ columns."""
    df = df.copy()

    # 1. Ensure numeric types for all numeric columns
    for col in ["stock_available", "stock_incoming", "daily_sales", "supplier_lead_time", "price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0  # safe default if column somehow missing

    # 2. days_of_supply = stock_available / daily_sales (0 if daily_sales is 0)
    df["days_of_supply"] = 0.0
    mask = df["daily_sales"] > 0
    df.loc[mask, "days_of_supply"] = (
        df.loc[mask, "stock_available"] / df.loc[mask, "daily_sales"]
    ).round(1)

    # 3. gmv_daily = daily_sales * price
    df["gmv_daily"] = (df["daily_sales"] * df["price"]).round(2)

    # 4. Root cause — clean logic using actual columns
    def _root_cause(row):
        if row["stock_available"] > 0:
            return "in_stock"
        if row["supplier_lead_time"] > 14:
            return "supplier_delay"
        if row["stock_incoming"] > 0:
            return "replenishment_lag"
        return "no_inbound_stock"

    df["root_cause"] = df.apply(_root_cause, axis=1)

    # 5. Alias columns tools reference by other names
    df["sku_name"]      = df["sku_id"]
    df["unit_price_aed"] = df["price"]
    df["supplier"]      = df["brand"]
    df["channel"]       = "retail"
    df["region"]        = "AE"

    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_inventory() -> pd.DataFrame:
    sql = f"""
        SELECT
            date, sku_id, category, brand,
            stock_available, stock_incoming,
            daily_sales, last_restock_date,
            supplier_lead_time, price
        FROM {FULL_TABLE}
        WHERE date = (SELECT MAX(date) FROM {FULL_TABLE})
        LIMIT 10000
    """
    df = _run_query(sql)
    if df.empty:
        from data.mock_data import INVENTORY_DF
        return INVENTORY_DF
    return _enrich(df)


@st.cache_data(ttl=300, show_spinner=False)
def load_history() -> pd.DataFrame:
    sql = f"""
        SELECT
            CAST(date AS STRING)                                AS date,
            'AE'                                                AS region,
            COUNTIF(stock_available = 0)                        AS oos_count,
            SAFE_DIVIDE(COUNTIF(stock_available = 0), COUNT(*)) AS oos_rate,
            SUM(IF(stock_available = 0, daily_sales * price, 0)) AS lost_gmv_aed,
            0 AS actioned,
            0 AS unactioned
        FROM {FULL_TABLE}
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        GROUP BY date
        ORDER BY date DESC
    """
    df = _run_query(sql)
    if df.empty:
        from data.mock_data import HISTORY_DF
        return HISTORY_DF
    return df


def get_inventory_df() -> pd.DataFrame:
    return load_inventory()

def get_history_df() -> pd.DataFrame:
    return load_history()

def _get_actual_columns() -> list:
    client = _get_client()
    if client is None:
        return []
    try:
        table = client.get_table(f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}")
        return [f.name for f in table.schema]
    except Exception:
        return []
