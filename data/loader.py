"""
Data loader — reads from oos_data.csv (no BigQuery or credentials needed).

CSV columns (exact):
  date, sku_id, category, brand, stock_available, stock_incoming,
  daily_sales, last_restock_date, supplier_lead_time, price

All derived columns are computed here and cached for the session.
"""

import os
import pandas as pd
import streamlit as st

# Path to CSV — works both locally and on Streamlit Cloud
CSV_PATH = os.path.join(os.path.dirname(__file__), "oos_data.csv")


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all derived columns the agent tools need."""
    df = df.copy()

    # Parse dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Numeric safety
    for col in ["stock_available", "stock_incoming", "daily_sales",
                "supplier_lead_time", "price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # days_of_supply = stock_available / daily_sales (0 when daily_sales=0)
    df["days_of_supply"] = 0.0
    mask = df["daily_sales"] > 0
    df.loc[mask, "days_of_supply"] = (
        df.loc[mask, "stock_available"] / df.loc[mask, "daily_sales"]
    ).round(1)

    # gmv_daily = daily_sales * price
    df["gmv_daily"] = (df["daily_sales"] * df["price"]).round(2)

    # root_cause
    def _rc(row):
        if row["stock_available"] > 0:
            return "in_stock"
        if row["supplier_lead_time"] > 14:
            return "supplier_delay"
        if row["stock_incoming"] > 0:
            return "replenishment_lag"
        return "no_inbound_stock"
    df["root_cause"] = df.apply(_rc, axis=1)

    # Alias columns so agent tools work unchanged
    df["sku_name"]       = df["sku_id"]
    df["unit_price_aed"] = df["price"]
    df["supplier"]       = df["brand"]
    df["channel"]        = "retail"
    df["region"]         = "AE"

    return df


@st.cache_data(show_spinner=False)
def _load_raw() -> pd.DataFrame:
    """Load and enrich full CSV (cached for the session)."""
    df = pd.read_csv(CSV_PATH)
    return _enrich(df)


@st.cache_data(show_spinner=False)
def get_inventory_df() -> pd.DataFrame:
    """Latest snapshot — most recent date in the CSV."""
    df = _load_raw()
    latest = df["date"].max()
    return df[df["date"] == latest].copy().reset_index(drop=True)


@st.cache_data(show_spinner=False)
def get_history_df() -> pd.DataFrame:
    """Daily aggregated history for trend charts."""
    df = _load_raw()
    agg = df.groupby("date").apply(lambda g: pd.Series({
        "date":         g.name.strftime("%Y-%m-%d"),
        "region":       "AE",
        "oos_count":    int((g["stock_available"] == 0).sum()),
        "oos_rate":     round((g["stock_available"] == 0).mean(), 4),
        "lost_gmv_aed": round(
            g.loc[g["stock_available"] == 0, "gmv_daily"].sum(), 2
        ),
        "actioned":   0,
        "unactioned": 0,
    }), include_groups=False).reset_index(drop=True)
    return agg.sort_values("date").reset_index(drop=True)


def get_csv_info() -> dict:
    """Meta info shown in the debug panel."""
    df = _load_raw()
    return {
        "total_rows":  len(df),
        "date_range":  f"{df['date'].min().date()} → {df['date'].max().date()}",
        "skus":        sorted(df["sku_id"].unique().tolist()),
        "categories":  sorted(df["category"].unique().tolist()),
        "brands":      sorted(df["brand"].unique().tolist()),
        "latest_date": df["date"].max().date(),
    }


# Keep old BQ function names as aliases so nothing else needs to change
def _get_actual_columns() -> list:
    return list(pd.read_csv(CSV_PATH, nrows=0).columns)
