"""
Agent tools — exact columns: stock_available, daily_sales, price,
brand, category, supplier_lead_time, stock_incoming, days_of_supply, gmv_daily
"""
import json
import pandas as pd
from data.loader import get_inventory_df, get_history_df


def _safe_str(val) -> str:
    return str(val) if val is not None else ""


def get_oos_skus(category=None, brand=None, days_of_supply_threshold=0, limit=20):
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


def get_oos_trend(days=7):
    import datetime
    df = get_history_df().copy()
    if df.empty:
        return {"error": "No history data available"}
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=int(days))).strftime("%Y-%m-%d")
    df = df[df["date"] >= cutoff].sort_values("date")
    if df.empty:
        return {"error": f"No trend data for last {days} days"}
    first_rate = float(df["oos_rate"].iloc[0])
    last_rate  = float(df["oos_rate"].iloc[-1])
    trend_dir  = "improving" if last_rate < first_rate else "worsening"
    return {
        "trend_direction": trend_dir,
        "period_days": int(days),
        "avg_daily_lost_gmv_aed": round(float(df["lost_gmv_aed"].mean()), 2),
        "avg_oos_rate_pct": round(float(df["oos_rate"].mean()) * 100, 2),
        "daily_data": df[["date","oos_count","oos_rate","lost_gmv_aed"]].to_dict("records"),
    }


def get_at_risk_skus(days_threshold=7, category=None):
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


# ── Tool schemas ──────────────────────────────────────────────────────────────
TOOL_DEFINITIONS = [
    {"name": "get_oos_skus",
     "description": "Returns SKUs currently OOS or below a days-of-supply threshold. Filter by category or brand.",
     "input_schema": {"type": "object", "properties": {
         "category":               {"type": "string", "description": "Product category"},
         "brand":                  {"type": "string", "description": "Brand name"},
         "days_of_supply_threshold": {"type": "number", "default": 0},
         "limit":                  {"type": "integer", "default": 20},
     }}},
    {"name": "get_gmv_loss",
     "description": "Calculates daily GMV loss from OOS, broken down by category and brand.",
     "input_schema": {"type": "object", "properties": {
         "category": {"type": "string"},
         "brand":    {"type": "string"},
     }}},
    {"name": "get_root_cause_breakdown",
     "description": "Root cause analysis of OOS using supplier_lead_time and stock_incoming. Use for 'why' questions.",
     "input_schema": {"type": "object", "properties": {
         "category": {"type": "string"},
         "brand":    {"type": "string"},
     }}},
    {"name": "get_oos_trend",
     "description": "OOS rate and GMV loss trend over N days. Use for better/worse/trend questions.",
     "input_schema": {"type": "object", "properties": {
         "days": {"type": "integer", "default": 7},
     }}},
    {"name": "get_at_risk_skus",
     "description": "SKUs projected to go OOS within N days. Flags where days_of_supply < supplier_lead_time.",
     "input_schema": {"type": "object", "properties": {
         "days_threshold": {"type": "integer", "default": 7},
         "category":       {"type": "string"},
     }}},
    {"name": "get_category_summary",
     "description": "OOS rate, GMV loss, avg days of supply per category. For category comparison questions.",
     "input_schema": {"type": "object", "properties": {
         "category": {"type": "string"},
     }}},
    {"name": "get_brand_analysis",
     "description": "Top brands by OOS GMV loss. For brand-level questions.",
     "input_schema": {"type": "object", "properties": {
         "category": {"type": "string"},
         "top_n":    {"type": "integer", "default": 10},
     }}},
]

TOOL_MAP = {
    "get_oos_skus":            get_oos_skus,
    "get_gmv_loss":            get_gmv_loss,
    "get_root_cause_breakdown": get_root_cause_breakdown,
    "get_oos_trend":           get_oos_trend,
    "get_at_risk_skus":        get_at_risk_skus,
    "get_category_summary":    get_category_summary,
    "get_brand_analysis":      get_brand_analysis,
}


def execute_tool(name: str, inputs: dict) -> dict:
    fn = TOOL_MAP.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    try:
        # Only pass kwargs the function actually accepts
        import inspect
        sig = inspect.signature(fn)
        valid = {k: v for k, v in inputs.items() if k in sig.parameters}
        return fn(**valid)
    except Exception as e:
        return {"error": f"Tool '{name}' failed: {str(e)}"}
