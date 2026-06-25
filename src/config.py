# src/config.py
from pathlib import Path
from typing import Dict, Any

# ── Base configuration (shared defaults) ──────────────────────────────────
BASE_CONFIG: Dict[str, Any] = {
    "raw_dir":       Path("../data/raw"),
    "processed_dir": Path("../data/processed"),
    "figures_dir":   Path("../figures"),
    "date_col":      "InvoiceDate",
    "amount_col":    "Revenue",
    "id_col":        "CustomerID",
    "min_quantity":  1,
    "min_price":     0.01,
}

# ── Retail (Case Study 1) ──────────────────────────────────────────────────
RETAIL_CONFIG: Dict[str, Any] = {
    **BASE_CONFIG,
    "filename":   "online_retail_II.xlsx",
    "sheet_name": "Year 2010-2011",
    "id_col":     "Customer ID",      # exact column name in this dataset
}

# ── Finance (Case Study 2) ─────────────────────────────────────────────────
FINANCE_CONFIG: Dict[str, Any] = {
    **BASE_CONFIG,
    "tickers":      ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
    "start_date":   "2019-01-01",
    "end_date":     "2023-12-31",
    "filename":     "tech_stocks.parquet",
    "raw_path":     Path("../data/raw/tech_stocks.parquet"),
    "window_20":    20,    # short rolling window (days)
    "window_60":    60,    # long rolling window (days)
    "trading_days": 252,
}

# ── IoT / AirQuality (Case Study 3) ───────────────────────────────────────
IOT_CONFIG: Dict[str, Any] = {
    **BASE_CONFIG,
    "filename":      "AirQualityUCI.csv",
    "date_col":      "datetime",
    "sensors":       ["CO(GT)", "PT08.S1(CO)", "C6H6(GT)", "T", "RH"],
    "error_code":    -200,
    "window":        24,    # rolling window in hours
    "threshold":     3.0,   # z-score anomaly threshold
    "ffill_limit":   3,
    "lookback_days": 30,
}

__all__ = ["BASE_CONFIG", "RETAIL_CONFIG", "FINANCE_CONFIG", "IOT_CONFIG"]
