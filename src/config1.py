# src/config.py
from pathlib import Path
from typing import Dict, Any

# ── Base configuration ─────────────────────────────────────────────────────
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

# ── Retail (Case Study 1) ───────────────────────────────────────────────────
RETAIL_CONFIG: Dict[str, Any] = {
    **BASE_CONFIG,
    "filename":      "online_retail_II.xlsx",
    "sheet_name":    "Year 2010-2011",
    "id_col":        "Customer ID",      # actual column name in dataset
}

# ── Finance (Case Study 2) ──────────────────────────────────────────────────
FINANCE_CONFIG: Dict[str, Any] = {
    **BASE_CONFIG,
    "tickers":       ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
    "start_date":    "2019-01-01",
    "end_date":      "2023-12-31",
    "raw_filename":  "tech_stocks.parquet",
    # Finance-specific defaults
    "window_short":  20,
    "window_long":   60,
    "trading_days":  252,
}

# ── IoT / AirQuality (Case Study 3) ─────────────────────────────────────────
IOT_CONFIG: Dict[str, Any] = {
    **BASE_CONFIG,
    "raw_filename":       "AirQualityUCI.csv",
    "sensors":            ["CO(GT)", "PT08.S1(CO)", "C6H6(GT)", "T", "RH"],
    "error_code":         -200,
    "window":             24,          # hours for rolling statistics
    "threshold":          3.0,         # z-score threshold
    "ffill_limit":        3,
    "lookback_days":      30,
}

# Export all configs
__all__ = ["BASE_CONFIG", "RETAIL_CONFIG", "FINANCE_CONFIG", "IOT_CONFIG"]