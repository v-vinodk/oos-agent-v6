import pandas as pd
import random
from datetime import datetime, timedelta

CATEGORIES = ["Electronics", "Sports", "Fashion", "Beauty", "Grocery", "Home", "Toys", "Automotive"]
REGIONS = ["AE", "SA", "EG"]
CHANNELS = ["retail", "marketplace"]
SUPPLIERS = ["Supplier_Alpha", "Supplier_Beta", "Supplier_Gamma", "Supplier_Delta", "Supplier_Epsilon"]
ROOT_CAUSES = ["supplier_delay", "demand_spike", "forecast_miss", "replenishment_lag", "planogram_gap"]

random.seed(42)

def _make_inventory():
    rows = []
    for i in range(1, 101):
        stock = random.randint(0, 300)
        sales = random.randint(8, 60)
        price = round(random.uniform(15, 800), 2)
        channel = random.choice(CHANNELS)
        region = random.choice(REGIONS)
        category = random.choice(CATEGORIES)
        rows.append({
            "sku_id": f"SKU-{i:04d}",
            "sku_name": f"{category} Product {i}",
            "category": category,
            "region": region,
            "channel": channel,
            "store_id": f"STR-{random.randint(1,20):02d}",
            "current_stock": stock,
            "daily_sales_rate": sales,
            "days_of_supply": round(stock / sales, 1) if sales > 0 else 0,
            "unit_price_aed": price,
            "gmv_daily": round(sales * price, 2),
            "supplier": random.choice(SUPPLIERS),
            "supplier_eta_days": random.randint(2, 21),
            "last_reorder_date": (datetime.now() - timedelta(days=random.randint(1, 45))).strftime("%Y-%m-%d"),
            "root_cause": random.choice(ROOT_CAUSES),
        })
    return pd.DataFrame(rows)

def _make_history():
    rows = []
    for i in range(1, 31):
        date = datetime.now() - timedelta(days=i)
        for region in REGIONS:
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "region": region,
                "oos_count": random.randint(5, 25),
                "oos_rate": round(random.uniform(0.04, 0.28), 3),
                "lost_gmv_aed": round(random.uniform(8000, 75000), 2),
                "actioned": random.randint(2, 15),
                "unactioned": random.randint(1, 10),
            })
    return pd.DataFrame(rows)

INVENTORY_DF = _make_inventory()
HISTORY_DF = _make_history()
