"""
Run once to regenerate oos_data.csv with realistic OOS patterns.

    cd ~/Downloads/oos_agent_v6
    python3 data/generate_data.py

Covers all agent questions:
  ✅ 14-day GMV loss trend  (varying OOS each day)
  ✅ OOS SKUs today
  ✅ At-risk SKUs  (0 < days_of_supply ≤ 7)
  ✅ Root cause mix  (supplier_delay / replenishment_lag / no_inbound_stock)
  ✅ Supplier lead time > 14 days  (Apple=21d, Sony=18d, IKEA=16d)
  ✅ Brand comparisons  (Apple vs Samsung vs Sony, Nike vs Puma vs Adidas)
  ✅ Category comparisons  (Electronics, Fashion, Home, Beauty)
  ✅ SKUs going OOS before supplier delivers
"""

import os, pandas as pd, numpy as np
from datetime import date, timedelta

np.random.seed(42)

# ── SKU master  (sku_id, category, brand, price, avg_daily_sales, lead_time_days)
SKUS = [
    ("SKU001", "Electronics", "Apple",       1200,  6, 21),
    ("SKU002", "Electronics", "Samsung",      800, 10, 14),
    ("SKU003", "Electronics", "Sony",         650,  8, 18),
    ("SKU004", "Fashion",     "Nike",         180, 20,  7),
    ("SKU005", "Fashion",     "Puma",         150, 16, 10),
    ("SKU006", "Fashion",     "Adidas",       160, 18, 12),
    ("SKU007", "Home",        "IKEA",         300, 12, 16),
    ("SKU008", "Home",        "HomeCentre",   250, 14,  8),
    ("SKU009", "Beauty",      "Loreal",        60, 40,  5),
    ("SKU010", "Beauty",      "Maybelline",    45, 32,  6),
]

START = date(2026, 1, 1)
END   = date(2026, 4, 14)   # latest date / "today"
DATES = [START + timedelta(days=i) for i in range((END - START).days + 1)]

# ── Restock cycles per SKU  [(restock_date, opening_stock), ...]
# Stock depletes daily by ~avg_sales; hits 0 → OOS until next restock_date.
CYCLES = {
    "SKU001": [  # Apple — long lead time, OOS from ~Apr 8
        (date(2026, 1,  1), 180),
        (date(2026, 2, 12), 160),
        (date(2026, 3, 20), 140),
        (date(2026, 4, 18), 150),   # restock arrives 18 Apr → OOS Apr 8–14
    ],
    "SKU002": [  # Samsung — OOS from ~Apr 12
        (date(2026, 1,  1), 300),
        (date(2026, 2,  5), 280),
        (date(2026, 3,  8), 250),
        (date(2026, 4,  5), 220),
        (date(2026, 4, 22), 230),   # OOS ~Apr 12–14
    ],
    "SKU003": [  # Sony — OOS from ~Apr 10, at-risk earlier
        (date(2026, 1,  1), 200),
        (date(2026, 2,  1), 190),
        (date(2026, 3,  1), 180),
        (date(2026, 4,  2), 160),
        (date(2026, 4, 25), 170),   # OOS ~Apr 10–14
    ],
    "SKU004": [  # Nike — OOS mid-Apr, at risk now
        (date(2026, 1,  1), 500),
        (date(2026, 1, 28), 480),
        (date(2026, 2, 25), 460),
        (date(2026, 3, 25), 440),
        (date(2026, 4, 10), 150),
        (date(2026, 4, 20), 400),   # low stock Apr 10, OOS ~Apr 18
    ],
    "SKU005": [  # Puma — low stock, at risk (dos ≈ 2 d)
        (date(2026, 1,  1), 400),
        (date(2026, 2, 10), 380),
        (date(2026, 3, 15), 350),
        (date(2026, 4,  8), 120),   # ~36 units left → dos ≈ 2 d
        (date(2026, 4, 22), 360),
    ],
    "SKU006": [  # Adidas — critically low, OOS by Apr 15
        (date(2026, 1,  1), 480),
        (date(2026, 2,  8), 460),
        (date(2026, 3, 10), 440),
        (date(2026, 4,  6), 130),   # ~2 units left Apr 14 → dos < 1
        (date(2026, 4, 21), 450),
    ],
    "SKU007": [  # IKEA — OOS from ~Apr 8 (long lead)
        (date(2026, 1,  1), 300),
        (date(2026, 2, 15), 280),
        (date(2026, 3, 22), 260),
        (date(2026, 4, 17), 270),   # OOS Apr 8–17
    ],
    "SKU008": [  # HomeCentre — OOS Apr 13–14
        (date(2026, 1,  1), 350),
        (date(2026, 2,  5), 330),
        (date(2026, 3,  5), 310),
        (date(2026, 4,  4), 280),
        (date(2026, 4, 16), 290),   # OOS Apr 13–16
    ],
    "SKU009": [  # Loreal — OOS Apr 13–14, restock incoming
        (date(2026, 1,  1), 800),
        (date(2026, 1, 22), 780),
        (date(2026, 2, 15), 760),
        (date(2026, 3,  8), 740),
        (date(2026, 4,  1), 500),
        (date(2026, 4, 15), 700),   # OOS Apr 13–14
    ],
    "SKU010": [  # Maybelline — OOS Apr 1–9, restocked Apr 14
        (date(2026, 1,  1), 700),
        (date(2026, 1, 25), 680),
        (date(2026, 2, 20), 660),
        (date(2026, 3, 18), 640),
        (date(2026, 4,  3), 350),   # OOS Apr ~8–12
        (date(2026, 4, 14), 600),   # restocked today
    ],
}

# ── Incoming stock windows  {(sku_id, from, to): qty}
INCOMING = {
    ("SKU001", date(2026, 4,  8), date(2026, 4, 17)): 150,
    ("SKU002", date(2026, 4, 10), date(2026, 4, 21)): 230,
    ("SKU003", date(2026, 4,  9), date(2026, 4, 24)): 170,
    ("SKU007", date(2026, 4,  5), date(2026, 4, 16)): 270,
    ("SKU008", date(2026, 4, 11), date(2026, 4, 15)): 290,
    ("SKU009", date(2026, 4, 10), date(2026, 4, 14)): 700,
    # SKU004, SKU005, SKU006 → no_inbound_stock root cause
}


def _stock(sku_id: str, d: date) -> int:
    avg_s = next(s[4] for s in SKUS if s[0] == sku_id)
    active_start, active_stock = None, 0
    for rd, stk in CYCLES[sku_id]:
        if rd <= d:
            active_start, active_stock = rd, stk
        else:
            break
    if active_start is None:
        return 0
    rng   = np.random.RandomState(hash((sku_id, str(d))) % (2 ** 31))
    sales = max(1, avg_s + rng.randint(-2, 3))
    return max(0, int(active_stock - (d - active_start).days * sales))


def _incoming(sku_id: str, d: date) -> int:
    for (sid, fd, td), qty in INCOMING.items():
        if sid == sku_id and fd <= d <= td:
            return qty
    return 0


rows = []
for d in DATES:
    for sku_id, category, brand, price, avg_sales, lead_time in SKUS:
        rng         = np.random.RandomState(hash((sku_id, str(d), "s")) % (2 ** 31))
        daily_sales = max(1, avg_sales + rng.randint(-3, 4))
        stock_avail = _stock(sku_id, d)
        incoming    = _incoming(sku_id, d)
        last_restock = max(
            (rd for rd, _ in CYCLES[sku_id] if rd <= d), default=d
        )
        rows.append({
            "date":               d.strftime("%Y-%m-%d"),
            "sku_id":             sku_id,
            "category":           category,
            "brand":              brand,
            "stock_available":    stock_avail,
            "stock_incoming":     incoming,
            "daily_sales":        daily_sales,
            "last_restock_date":  last_restock.strftime("%Y-%m-%d"),
            "supplier_lead_time": lead_time,
            "price":              price,
        })

df = pd.DataFrame(rows)

# ── Validate ──────────────────────────────────────────────────────────────────
latest  = pd.to_datetime(df.date).max()
last14s = latest - pd.Timedelta(days=13)
l14     = df[pd.to_datetime(df.date) >= last14s]
oos14   = l14[l14.stock_available == 0].groupby("date").size()

print(f"✅ Rows generated : {len(df)}")
print(f"   Date range     : {df.date.min()} → {df.date.max()}")
print(f"\n📊 OOS count — last 14 days:")
if oos14.empty:
    print("   ⚠️  No OOS! Check cycles.")
else:
    for dt, cnt in oos14.items():
        print(f"   {dt}  →  {cnt} SKU(s) OOS")

snap = df[df.date == latest.strftime("%Y-%m-%d")]
oos_today = snap[snap.stock_available == 0]
print(f"\n🔴 OOS today ({latest.date()}): {len(oos_today)} SKU(s)")
for _, r in oos_today.iterrows():
    print(f"   {r.sku_id} {r.brand} ({r.category})  incoming={r.stock_incoming}  lead={r.supplier_lead_time}d")

# ── Save ──────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), "oos_data.csv")
df.to_csv(out, index=False)
print(f"\n💾 Saved → {out}")
