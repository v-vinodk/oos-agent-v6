"""
Agent tools — exact columns: stock_available, daily_sales, price,
brand, category, supplier_lead_time, stock_incoming, days_of_supply, gmv_daily

Key design:
  • Snapshot tools  (get_oos_skus, get_gmv_loss, get_root_cause_breakdown,
                     get_category_summary, get_brand_analysis, get_at_risk_skus)
    → use get_inventory_df()  = latest date in CSV only
    → answer "right now / today" questions

  • Historical tools (get_oos_trend, get_historical_oos_events)
    → use _load_raw()  = all rows across all dates
    → always anchored to the CSV's own max date (never datetime.now())
    → answer "last N days / trend / which SKUs were OOS" questions
"""
import pandas as pd
from data.loader import get_inventory_df, _load_raw


def _safe_str(val) -> str:
    return str(val) if val is not None else ""


# ── Snapshot tools ─────────────────────────────────────────────────────────────

def get_oos_skus(category=None, brand=None, days_of_supply_threshold=0, limit=20):
    """Returns SKUs OOS or critically low as of the latest date in the dataset."""
    df = get_inventory_df().copy()
    if category:
        df = df[df["category"].str.lower() == category.lower()]
    if brand:
        df = df[df["brand"].str.lower().str.contains(brand.lower(), na=False)]
    oos = df[df["days_of_supply"] <= float(days_of_supply_threshold)].copy()
    oos = oos.sort_values("gmv_daily", ascending=False)
    cols = [c for c in ["sku_id","category","brand","stock_available","stock_incoming",
                         "days_of_supply","gmv_daily","root_cause"] if c in oos.columns]
    return {
        "count": int(len(oos)),
        "skus": oos[cols].head(int(limit)).to_dict("records"),
    }


def get_gmv_loss(category=None, brand=None):
    """Calculates daily GMV loss from OOS as of the latest date."""
    df = get_inventory_df().copy()
    if category:
        df = df[df["category"].str.lower() == category.lower()]
    if brand:
        df = df[df["brand"].str.lower().str.contains(brand.lower(), na=False)]
    oos = df[df["stock_available"] == 0].copy()
    if oos.empty:
        return {"total_daily_gmv_loss_aed": 0, "oos_sku_count": 0,
                "loss_by_category": {}, "loss_by_brand": {}, "top_5_impacted_skus": [],
                "unactioned_gmv_loss_aed": 0, "actioned_gmv_loss_aed": 0}
    total      = round(float(oos["gmv_daily"].sum()), 2)
    unactioned = round(float(oos[oos["stock_incoming"] == 0]["gmv_daily"].sum()), 2)
    by_cat   = oos.groupby("category")["gmv_daily"].sum().sort_values(ascending=False).round(2).to_dict()
    by_brand = oos.groupby("brand")["gmv_daily"].sum().sort_values(ascending=False).round(2).head(10).to_dict()
    top_cols = [c for c in ["sku_id","category","brand","gmv_daily"] if c in oos.columns]
    top_skus = oos.nlargest(5, "gmv_daily")[top_cols].to_dict("records")
    return {
        "total_daily_gmv_loss_aed": total,
        "unactioned_gmv_loss_aed": unactioned,
        "actioned_gmv_loss_aed": round(total - unactioned, 2),
        "loss_by_category": by_cat,
        "loss_by_brand": by_brand,
        "top_5_impacted_skus": top_skus,
        "oos_sku_count": int(len(oos)),
    }


def get_root_cause_breakdown(category=None, brand=None):
    """Root cause analysis of current OOS events (supplier_delay / no_inbound_stock / replenishment_lag)."""
    df = get_inventory_df().copy()
    if category:
        df = df[df["category"].str.lower() == category.lower()]
    if brand:
        df = df[df["brand"].str.lower().str.contains(brand.lower(), na=False)]
    oos = df[df["stock_available"] == 0].copy()
    if oos.empty:
        return {"breakdown": [], "total_oos_skus": 0,
                "avg_supplier_lead_time_days": 0, "skus_with_incoming_stock": 0}

    total_oos = len(oos)
    supplier_delay = oos[oos["supplier_lead_time"] > 14]
    no_inbound     = oos[(oos["stock_incoming"] == 0) & (oos["supplier_lead_time"] <= 14)]
    replen_lag     = oos[(oos["stock_incoming"] > 0)  & (oos["supplier_lead_time"] <= 14)]

    breakdown = [
        {"root_cause": "Supplier delay (LT > 14d)",
         "sku_count": int(len(supplier_delay)),
         "gmv_impact_aed": round(float(supplier_delay["gmv_daily"].sum()), 2),
         "pct_of_total": round(len(supplier_delay) / total_oos * 100, 1)},
        {"root_cause": "No inbound stock",
         "sku_count": int(len(no_inbound)),
         "gmv_impact_aed": round(float(no_inbound["gmv_daily"].sum()), 2),
         "pct_of_total": round(len(no_inbound) / total_oos * 100, 1)},
        {"root_cause": "Replenishment lag",
         "sku_count": int(len(replen_lag)),
         "gmv_impact_aed": round(float(replen_lag["gmv_daily"].sum()), 2),
         "pct_of_total": round(len(replen_lag) / total_oos * 100, 1)},
    ]
    avg_lt = round(float(oos["supplier_lead_time"].mean()), 1)
    return {
        "breakdown": breakdown,
        "total_oos_skus": int(total_oos),
        "avg_supplier_lead_time_days": avg_lt,
        "skus_with_incoming_stock": int((oos["stock_incoming"] > 0).sum()),
    }


def get_at_risk_skus(days_threshold=7, category=None):
    """SKUs projected to go OOS within N days (days_of_supply ≤ threshold, but > 0)."""
    df = get_inventory_df().copy()
    if category:
        df = df[df["category"].str.lower() == category.lower()]
    at_risk = df[
        (df["days_of_supply"] > 0) & (df["days_of_supply"] <= float(days_threshold))
    ].sort_values("gmv_daily", ascending=False).copy()

    will_oos = int(
        (at_risk["days_of_supply"] < at_risk["supplier_lead_time"]).sum()
    ) if len(at_risk) else 0

    cols = [c for c in ["sku_id","category","brand","stock_available","stock_incoming",
                          "daily_sales","days_of_supply","supplier_lead_time","gmv_daily"]
            if c in at_risk.columns]
    return {
        "count": int(len(at_risk)),
        "skus": at_risk[cols].head(15).to_dict("records"),
        "total_at_risk_gmv_aed": round(float(at_risk["gmv_daily"].sum()), 2),
        "will_oos_before_restock": will_oos,
    }


def get_category_summary(category=None):
    """OOS rate, GMV loss and avg days of supply per category (current snapshot)."""
    df = get_inventory_df().copy()
    if category:
        df = df[df["category"].str.lower() == category.lower()]
    if df.empty:
        return {"categories": [], "total_categories": 0}
    result = []
    for cat, grp in df.groupby("category"):
        oos = grp[grp["stock_available"] == 0]
        result.append({
            "category": str(cat),
            "total_skus": int(len(grp)),
            "oos_skus": int(len(oos)),
            "oos_rate_pct": round(len(oos) / len(grp) * 100, 1) if len(grp) else 0,
            "gmv_loss_aed": round(float(oos["gmv_daily"].sum()), 2),
            "avg_days_of_supply": round(float(grp["days_of_supply"].mean()), 1),
            "avg_supplier_lead_time": round(float(grp["supplier_lead_time"].mean()), 1),
        })
    result.sort(key=lambda x: x["gmv_loss_aed"], reverse=True)
    return {"categories": result, "total_categories": len(result)}


def get_brand_analysis(category=None, top_n=10):
    """Top brands by OOS GMV loss (current snapshot)."""
    df = get_inventory_df().copy()
    if category:
        df = df[df["category"].str.lower() == category.lower()]
    oos = df[df["stock_available"] == 0].copy()
    if oos.empty:
        return {"brands": [], "total_oos_brands": 0}
    brand_gmv   = oos.groupby("brand")["gmv_daily"].sum().sort_values(ascending=False).head(int(top_n))
    brand_count = oos.groupby("brand").size()
    result = [
        {"brand": str(b),
         "oos_skus": int(brand_count.get(b, 0)),
         "gmv_loss_aed": round(float(brand_gmv[b]), 2)}
        for b in brand_gmv.index
    ]
    return {"brands": result, "total_oos_brands": int(oos["brand"].nunique())}


# ── Historical tools ───────────────────────────────────────────────────────────

def get_oos_trend(days=14):
    """
    OOS rate and GMV loss trend over the last N days.
    Anchored to the CSV's own max date — never the server clock.
    Use for 'is OOS getting better or worse?' trend questions.
    """
    df = _load_raw().copy()
    if df.empty:
        return {"error": "No history data available"}

    # Anchor to the data's own max date (not datetime.now())
    max_date = pd.to_datetime(df["date"]).max()
    cutoff   = max_date - pd.Timedelta(days=int(days) - 1)

    window = df[df["date"] >= cutoff].copy()
    if window.empty:
        return {"error": f"No data found in last {days} days of the dataset"}

    # Aggregate per day
    agg = (
        window.groupby("date")
        .apply(lambda g: pd.Series({
            "date":         g.name.strftime("%Y-%m-%d"),
            "oos_count":    int((g["stock_available"] == 0).sum()),
            "oos_rate":     round((g["stock_available"] == 0).mean(), 4),
            "lost_gmv_aed": round(g.loc[g["stock_available"] == 0, "gmv_daily"].sum(), 2),
        }), include_groups=False)
        .reset_index(drop=True)
        .sort_values("date")
    )

    first_rate = float(agg["oos_rate"].iloc[0])
    last_rate  = float(agg["oos_rate"].iloc[-1])
    trend_dir  = "improving" if last_rate < first_rate else "worsening"

    return {
        "trend_direction":       trend_dir,
        "period_days":           int(days),
        "data_up_to":            max_date.strftime("%Y-%m-%d"),
        "avg_daily_lost_gmv_aed": round(float(agg["lost_gmv_aed"].mean()), 2),
        "total_lost_gmv_aed":    round(float(agg["lost_gmv_aed"].sum()), 2),
        "avg_oos_rate_pct":      round(float(agg["oos_rate"].mean()) * 100, 2),
        "peak_oos_count":        int(agg["oos_count"].max()),
        "daily_data":            agg[["date","oos_count","oos_rate","lost_gmv_aed"]].to_dict("records"),
    }


def get_historical_oos_events(days=14, category=None, brand=None):
    """
    Scans ALL rows (not just today's snapshot) across the last N days and returns
    every SKU×date combination where stock_available = 0.
    Use for questions like:
      • 'Which SKUs were OOS in the last 14 days?'
      • 'How many days was Apple OOS this month?'
      • 'Show me the OOS history for Electronics'
      • 'What was the cumulative GMV lost over the past 2 weeks?'
    Always anchored to the CSV's own max date.
    """
    df = _load_raw().copy()
    if df.empty:
        return {"error": "No data available"}

    # Anchor window to CSV's own max date
    max_date = pd.to_datetime(df["date"]).max()
    cutoff   = max_date - pd.Timedelta(days=int(days) - 1)
    window   = df[df["date"] >= cutoff].copy()

    # Optional filters
    if category:
        window = window[window["category"].str.lower() == category.lower()]
    if brand:
        window = window[window["brand"].str.lower().str.contains(brand.lower(), na=False)]

    oos_rows = window[window["stock_available"] == 0].copy()

    if oos_rows.empty:
        return {
            "total_oos_events": 0,
            "unique_oos_skus": 0,
            "cumulative_gmv_loss_aed": 0,
            "period_days": int(days),
            "data_up_to": max_date.strftime("%Y-%m-%d"),
            "oos_events": [],
            "summary_by_sku": [],
        }

    # Per-SKU summary: how many days OOS + total GMV lost
    sku_summary = (
        oos_rows.groupby(["sku_id","brand","category"])
        .agg(
            days_oos=("date", "count"),
            total_gmv_loss_aed=("gmv_daily", "sum"),
            first_oos_date=("date", "min"),
            last_oos_date=("date",  "max"),
        )
        .reset_index()
    )
    sku_summary["total_gmv_loss_aed"] = sku_summary["total_gmv_loss_aed"].round(2)
    sku_summary["first_oos_date"] = sku_summary["first_oos_date"].dt.strftime("%Y-%m-%d")
    sku_summary["last_oos_date"]  = sku_summary["last_oos_date"].dt.strftime("%Y-%m-%d")
    sku_summary = sku_summary.sort_values("total_gmv_loss_aed", ascending=False)

    # Detailed event rows
    event_cols = [c for c in ["date","sku_id","brand","category",
                               "stock_available","stock_incoming",
                               "days_of_supply","gmv_daily","root_cause"]
                  if c in oos_rows.columns]
    events = oos_rows[event_cols].copy()
    events["date"] = events["date"].dt.strftime("%Y-%m-%d")
    events = events.sort_values(["date","gmv_daily"], ascending=[True, False])

    return {
        "period_days":              int(days),
        "data_up_to":               max_date.strftime("%Y-%m-%d"),
        "total_oos_events":         int(len(oos_rows)),
        "unique_oos_skus":          int(oos_rows["sku_id"].nunique()),
        "cumulative_gmv_loss_aed":  round(float(oos_rows["gmv_daily"].sum()), 2),
        "avg_daily_gmv_loss_aed":   round(float(oos_rows["gmv_daily"].sum()) / int(days), 2),
        "summary_by_sku":           sku_summary.to_dict("records"),
        "oos_events":               events.head(50).to_dict("records"),
    }


# ── Tool schemas ──────────────────────────────────────────────────────────────
TOOL_DEFINITIONS = [
    {
        "name": "get_oos_skus",
        "description": (
            "Returns SKUs that are currently OOS (stock_available=0) or below a "
            "days-of-supply threshold AS OF TODAY (the latest date in the dataset). "
            "Filter by category or brand. Use for 'what is OOS right now' questions."
        ),
        "input_schema": {"type": "object", "properties": {
            "category":                 {"type": "string", "description": "Product category (e.g. Electronics, Fashion, Home, Beauty)"},
            "brand":                    {"type": "string", "description": "Brand name (e.g. Apple, Samsung, Nike)"},
            "days_of_supply_threshold": {"type": "number",  "default": 0,  "description": "Include SKUs with days_of_supply <= this value. 0 = strictly OOS only."},
            "limit":                    {"type": "integer", "default": 20},
        }}
    },
    {
        "name": "get_gmv_loss",
        "description": (
            "Calculates CURRENT daily GMV loss from OOS SKUs (today's snapshot). "
            "Breaks down by category and brand. For 'how much revenue are we losing today' questions."
        ),
        "input_schema": {"type": "object", "properties": {
            "category": {"type": "string"},
            "brand":    {"type": "string"},
        }}
    },
    {
        "name": "get_root_cause_breakdown",
        "description": (
            "Root cause analysis of CURRENT OOS events. Classifies each OOS SKU as: "
            "supplier_delay (lead_time>14d), no_inbound_stock, or replenishment_lag. "
            "Use for 'why are SKUs OOS' questions."
        ),
        "input_schema": {"type": "object", "properties": {
            "category": {"type": "string"},
            "brand":    {"type": "string"},
        }}
    },
    {
        "name": "get_oos_trend",
        "description": (
            "OOS rate and GMV loss TREND over the last N days (default 14). "
            "Scans all historical rows — anchored to the CSV's own max date, not the server clock. "
            "Use for 'is OOS getting better or worse', 'show me the trend', '14-day GMV loss' questions."
        ),
        "input_schema": {"type": "object", "properties": {
            "days": {"type": "integer", "default": 14, "description": "Number of days to look back from the dataset's latest date"},
        }}
    },
    {
        "name": "get_historical_oos_events",
        "description": (
            "Scans ALL historical rows across the last N days and returns every SKU×date "
            "combination where stock_available=0. Anchored to the CSV's own max date. "
            "Use for: 'which SKUs were OOS in the last 14 days', 'how many days was X OOS', "
            "'cumulative GMV lost over past 2 weeks', 'OOS history for a brand/category'."
        ),
        "input_schema": {"type": "object", "properties": {
            "days":     {"type": "integer", "default": 14, "description": "Number of days to look back"},
            "category": {"type": "string",  "description": "Filter by category"},
            "brand":    {"type": "string",  "description": "Filter by brand"},
        }}
    },
    {
        "name": "get_at_risk_skus",
        "description": (
            "SKUs projected to go OOS within N days (days_of_supply > 0 but ≤ threshold). "
            "Flags SKUs where days_of_supply < supplier_lead_time (will go OOS before restock arrives)."
        ),
        "input_schema": {"type": "object", "properties": {
            "days_threshold": {"type": "integer", "default": 7},
            "category":       {"type": "string"},
        }}
    },
    {
        "name": "get_category_summary",
        "description": (
            "OOS rate, GMV loss, avg days of supply per category (current snapshot). "
            "For category comparison questions."
        ),
        "input_schema": {"type": "object", "properties": {
            "category": {"type": "string"},
        }}
    },
    {
        "name": "get_brand_analysis",
        "description": (
            "Top brands by OOS GMV loss (current snapshot). "
            "For brand-level comparison questions like Apple vs Samsung vs Sony."
        ),
        "input_schema": {"type": "object", "properties": {
            "category": {"type": "string"},
            "top_n":    {"type": "integer", "default": 10},
        }}
    },
]

TOOL_MAP = {
    "get_oos_skus":               get_oos_skus,
    "get_gmv_loss":               get_gmv_loss,
    "get_root_cause_breakdown":   get_root_cause_breakdown,
    "get_oos_trend":              get_oos_trend,
    "get_historical_oos_events":  get_historical_oos_events,
    "get_at_risk_skus":           get_at_risk_skus,
    "get_category_summary":       get_category_summary,
    "get_brand_analysis":         get_brand_analysis,
}


def execute_tool(name: str, inputs: dict) -> dict:
    fn = TOOL_MAP.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    try:
        import inspect
        sig   = inspect.signature(fn)
        valid = {k: v for k, v in inputs.items() if k in sig.parameters}
        return fn(**valid)
    except Exception as e:
        return {"error": f"Tool '{name}' failed: {str(e)}"}
