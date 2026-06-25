import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import centralized configurations
from config import (
    BASE_CONFIG,
    RETAIL_CONFIG,
    FINANCE_CONFIG,
    IOT_CONFIG
)

# For backward compatibility with existing retail code
CONFIG = BASE_CONFIG

# ── Stage 1: Ingestion ───────────────────────────────────────────────
def load_raw(filename: str, cfg: dict = CONFIG) -> pd.DataFrame:
    """Load raw data from the configured raw directory."""
    path = cfg["raw_dir"] / filename
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, encoding="latin-1")
    elif suffix == ".parquet":
        return pd.read_parquet(path)
    elif suffix in (".xlsx", ".xls"):
        sheet = cfg.get("sheet_name", 0)
        return pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

def audit(df: pd.DataFrame) -> dict:
    """Return a summary audit report for a raw DataFrame."""
    return {
        "shape":       df.shape,
        "dtypes":      df.dtypes.to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "null_pct":    (df.isnull().mean() * 100).round(2).to_dict(),
        "duplicates":  int(df.duplicated().sum()),
    }

# ── Stage 2: Cleaning ────────────────────────────────────────────────
def clean(df: pd.DataFrame, cfg: dict = CONFIG) -> pd.DataFrame:
    """Apply standard cleaning rules and return a clean DataFrame."""
    df = df.copy()

    # Drop exact duplicates
    before = len(df)
    df = df.drop_duplicates()

    # Drop rows with null values in critical columns
    critical = [c for c in [cfg["id_col"], cfg["date_col"]]
                if c in df.columns]
    df = df.dropna(subset=critical)

    # Coerce date column
    if cfg["date_col"] in df.columns:
        df[cfg["date_col"]] = pd.to_datetime(
            df[cfg["date_col"]], errors="coerce"
        )
        df = df.dropna(subset=[cfg["date_col"]])

    # Remove physically impossible values
    if "Quantity" in df.columns:
        df = df[df["Quantity"] >= cfg["min_quantity"]]
    if "UnitPrice" in df.columns:
        df = df[df["UnitPrice"] >= cfg["min_price"]]

    print(f"clean(): {before:,} → {len(df):,} rows "
          f"({before - len(df):,} removed)")
    return df

# ── Stage 3: Feature engineering ─────────────────────────────────────
def engineer(df: pd.DataFrame, cfg: dict = CONFIG) -> pd.DataFrame:
    """Derive analytical columns from clean data."""
    df = df.copy()

    if "Quantity" in df.columns and "UnitPrice" in df.columns:
        df["Revenue"] = df["Quantity"] * df["UnitPrice"]

    if cfg["date_col"] in df.columns:
        dt = df[cfg["date_col"]]
        df["Year"]       = dt.dt.year
        df["Month"]      = dt.dt.month
        df["DayOfWeek"]  = dt.dt.day_name()
        df["Hour"]       = dt.dt.hour
        df["YearMonth"]  = dt.dt.to_period("M").astype(str)

    return df

# ── Stage 4: Aggregation ─────────────────────────────────────────────
def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total revenue and order count by month."""
    return (
        df.groupby("YearMonth")
        .agg(revenue=("Revenue", "sum"),
             orders  =("Revenue", "count"),
             avg_order=("Revenue","mean"))
        .round(2)
        .reset_index()
    )

def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return the top n products by total revenue."""
    return (
        df.groupby("Description")["Revenue"]
        .sum()
        .nlargest(n)
        .reset_index()
        .rename(columns={"Revenue": "total_revenue"})
    )

def customer_rfm(df: pd.DataFrame, cfg: dict = CONFIG) -> pd.DataFrame:
    """Compute Recency, Frequency, Monetary (RFM) scores per customer."""
    snapshot = df[cfg["date_col"]].max() + pd.Timedelta(days=1)
    rfm = (
        df.groupby(cfg["id_col"])
        .agg(
            recency  =(cfg["date_col"],
                       lambda x: (snapshot - x.max()).days),
            frequency=("Invoice",     "nunique"),
            monetary =(cfg["amount_col"], "sum"),
        )
        .round(2)
        .reset_index()
    )
    return rfm

def finance_summary(prices: pd.DataFrame,
                    log_returns: pd.DataFrame,
                    tickers: list) -> pd.DataFrame:
    """Compute annualised return, volatility, Sharpe ratio, and max drawdown."""
    return pd.DataFrame({
        "ticker":         tickers,
        "ann_return":     (
            (prices.iloc[-1] / prices.iloc[0]) **
            (252 / len(prices)) - 1
        ).values,
        "ann_volatility": (log_returns.std() * np.sqrt(252)).values,
        "sharpe_ratio":   (
            log_returns.mean() * 252 /
            (log_returns.std() * np.sqrt(252))
        ).values,
        "max_drawdown":   (
            (prices / prices.cummax() - 1).min()
        ).values,
    }).round(3)

def detect_anomalies(series: pd.Series,
                     window: int,
                     threshold: float) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Return (roll_mean, roll_std, z_score, anomalies) for a sensor series."""
    roll_mean = series.rolling(window).mean()
    roll_std  = series.rolling(window).std()
    z_score   = (series - roll_mean) / roll_std
    anomalies = series[z_score.abs() > threshold]
    return roll_mean, roll_std, z_score, anomalies

# ── Stage 5: Saving ───────────────────────────────────────────────────
def save_processed(df: pd.DataFrame,
                   filename: str,
                   cfg: dict = CONFIG) -> None:
    """Save a processed DataFrame to the configured directory."""
    cfg["processed_dir"].mkdir(parents=True, exist_ok=True)
    path = cfg["processed_dir"] / filename
    df.to_parquet(path, index=False)
    print(f"Saved {len(df):,} rows → {path}")

# ── Visualisation: Retail ─────────────────────────────────────────────
def plot_monthly_revenue(monthly: pd.DataFrame,
                         title: str = "Monthly Revenue",
                         color: str = "#1565C0") -> go.Figure:
    """Return a Plotly bar+line combo chart for monthly revenue and orders."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly["YearMonth"], y=monthly["revenue"],
        name="Revenue", marker_color=color, opacity=0.7
    ))
    fig.add_trace(go.Scatter(
        x=monthly["YearMonth"], y=monthly["orders"],
        name="Orders", yaxis="y2",
        line=dict(color="#E53935", width=2),
        mode="lines+markers"
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Month",
        yaxis=dict(title="Revenue (£)"),
        yaxis2=dict(title="Orders", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="#FAFAFA",
        height=420,
    )
    return fig


def plot_top_products(top_n: pd.DataFrame,
                      title: str = "Top Products by Revenue") -> go.Figure:
    """Return a horizontal bar chart of top products by revenue."""
    fig = px.bar(
        top_n.sort_values("total_revenue"),
        x="total_revenue", y="Description",
        orientation="h",
        title=title,
        labels={"total_revenue": "Revenue (£)", "Description": "Product"},
        color="total_revenue",
        color_continuous_scale="Blues",
    )
    fig.update_layout(showlegend=False, plot_bgcolor="#FAFAFA", height=420)
    return fig

def plot_rfm_scatter(rfm: pd.DataFrame,
                     title: str = "RFM Customer Map — Frequency vs Monetary",
                     sample_n: int = 2000) -> go.Figure:
    """Return a scatter plot of Frequency vs Monetary coloured by Recency."""
    data = rfm.sample(min(sample_n, len(rfm)), random_state=42)
    hover = [c for c in ["Customer ID", "segment"] if c in data.columns]
    fig = px.scatter(
        data, x="frequency", y="monetary",
        color="recency", size="monetary",
        color_continuous_scale="RdYlGn_r",
        hover_data=hover or None,
        title=title,
        labels={"frequency": "Purchase Frequency",
                "monetary":  "Total Spend (£)",
                "recency":   "Recency (days)"},
        opacity=0.65, size_max=22,
    )
    fig.update_layout(plot_bgcolor="#FAFAFA", height=460)
    return fig

# ── Visualisation: Finance ────────────────────────────────────────────
def plot_price_with_ma(prices: pd.DataFrame,
                       ticker: str,
                       rolling_mean_20: pd.DataFrame,
                       rolling_mean_60: pd.DataFrame,
                       rolling_std_20: pd.DataFrame) -> go.Figure:
    """Return a two-panel Plotly chart: price + MAs (top), rolling volatility (bottom)."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=[f"{ticker} — Price and Rolling Averages",
                        f"{ticker} — 20-Day Rolling Volatility"],
        row_heights=[0.65, 0.35],
        vertical_spacing=0.08
    )
    fig.add_trace(go.Scatter(
        x=prices.index, y=prices[ticker],
        name="Close", line=dict(color="#1565C0", width=1.5)
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=rolling_mean_20.index, y=rolling_mean_20[ticker],
        name="20-day MA", line=dict(color="#FB8C00", width=1.5, dash="dot")
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=rolling_mean_60.index, y=rolling_mean_60[ticker],
        name="60-day MA", line=dict(color="#E53935", width=1.5, dash="dash")
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=rolling_std_20.index,
        y=rolling_std_20[ticker] * np.sqrt(252),
        name="Ann. Vol (20d)",
        line=dict(color="#6A1B9A", width=1.5),
        fill="tozeroy", fillcolor="rgba(106,27,154,0.1)"
    ), row=2, col=1)
    fig.update_layout(
        height=600, plot_bgcolor="#FAFAFA",
        margin=dict(t=80),
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.12,
            xanchor="center", x=0.5,
        ),
        yaxis_title="Price (USD)",
        yaxis2_title="Ann. Volatility",
    )
    return fig

def plot_return_distributions(log_returns: pd.DataFrame,
                              title: str = "Daily Log Return Distributions") -> go.Figure:
    """Return a Plotly overlaid histogram of log returns for all tickers."""
    lr_long = (
        log_returns.reset_index()
        .melt(id_vars="Date", var_name="Ticker", value_name="return")
    )
    fig = px.histogram(
        lr_long, x="return", color="Ticker",
        barmode="overlay", opacity=0.55, nbins=80,
        title=title,
        labels={"return": "Daily Log Return"}
    )
    fig.update_layout(plot_bgcolor="#FAFAFA", height=380)
    return fig

def plot_risk_return(summary: pd.DataFrame,
                     title: str = "Risk vs Return — 5-Year Annualised (2019–2023)") -> go.Figure:
    """Return a risk–return scatter sized and coloured by Sharpe ratio."""
    fig = px.scatter(
        summary,
        x="ann_volatility", y="ann_return",
        text="ticker",
        size="sharpe_ratio", size_max=30,
        color="sharpe_ratio",
        color_continuous_scale="RdYlGn",
        title=title,
        labels={"ann_volatility": "Annualised Volatility",
                "ann_return":     "Annualised Return",
                "sharpe_ratio":   "Sharpe Ratio"},
    )
    fig.update_traces(textposition="top center",
                      marker=dict(line=dict(width=1, color="white")))
    fig.update_layout(plot_bgcolor="#FAFAFA", height=420)
    return fig

# ── Visualisation: IoT ────────────────────────────────────────────────
def plot_anomaly_chart(series: pd.Series,
                       roll_mean: pd.Series,
                       roll_std: pd.Series,
                       anomalies: pd.Series,
                       threshold: float,
                       sensor: str) -> go.Figure:
    """Return a Plotly chart of sensor readings with anomaly bands and markers."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index, y=series.values,
        name=sensor, line=dict(color="#1565C0", width=1.2), opacity=0.8
    ))
    fig.add_trace(go.Scatter(
        x=roll_mean.index, y=roll_mean + threshold * roll_std,
        name=f"+{threshold:.1f}σ",
        line=dict(color="#FB8C00", dash="dot", width=1)
    ))
    fig.add_trace(go.Scatter(
        x=roll_mean.index, y=roll_mean - threshold * roll_std,
        name=f"-{threshold:.1f}σ",
        line=dict(color="#FB8C00", dash="dot", width=1),
        fill="tonexty", fillcolor="rgba(251,140,0,0.05)"
    ))
    if len(anomalies) > 0:
        fig.add_trace(go.Scatter(
            x=anomalies.index, y=anomalies.values,
            name="Anomaly", mode="markers",
            marker=dict(color="#E53935", size=7, symbol="x")
        ))
    fig.update_layout(
        title=f"{sensor} — Rolling ±{threshold:.1f}σ Anomaly Bands",
        xaxis_title="Datetime",
        yaxis_title=sensor,
        plot_bgcolor="#FAFAFA",
        height=440,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    return fig