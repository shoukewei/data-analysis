# finance_dashboard.py — streamlit run finance_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from pipeline import (plot_price_with_ma, plot_return_distributions,
                      plot_risk_return, finance_summary)
from config import FINANCE_CONFIG

st.set_page_config(page_title="Equity Analytics",
                   page_icon="📈", layout="wide")
st.title("📈 Tech Equity Analytics — 2019–2023")

@st.cache_data
def load():
    prices  = pd.read_parquet(FINANCE_CONFIG["raw_path"])
    log_ret = np.log(prices / prices.shift(1)).dropna()
    return prices, log_ret

prices, log_returns = load()
tickers = list(prices.columns)

# Sidebar
selected = st.sidebar.multiselect(
    "Select tickers", tickers, default=tickers
)
window = st.sidebar.slider(
    "Rolling window (days)", 5, 120, FINANCE_CONFIG["window_20"]
)

prices_sel = prices[selected]
lr_sel     = log_returns[selected]
roll_mean  = prices_sel.rolling(window).mean()
roll_std   = prices_sel.rolling(window).std()

# KPIs
st.subheader("5-Year Performance Summary")
cols = st.columns(len(selected))
for col, ticker in zip(cols, selected):
    total_ret = prices_sel[ticker].iloc[-1] / prices_sel[ticker].iloc[0] - 1
    vol       = lr_sel[ticker].std() * np.sqrt(252)
    col.metric(ticker,
               f"{total_ret:.1%} return",
               f"σ = {vol:.1%}")

# Tabs
tab1, tab2, tab3 = st.tabs(["Prices", "Return Distribution", "Correlation"])

with tab1:
    # plot_price_with_ma expects a single ticker; show the first selected
    ticker = selected[0] if selected else tickers[0]
    fig_p = plot_price_with_ma(
        prices_sel, ticker=ticker,
        rolling_mean_20=roll_mean,
        rolling_mean_60=prices_sel.rolling(FINANCE_CONFIG["window_60"]).mean(),
        rolling_std_20=roll_std,
    )
    st.plotly_chart(fig_p, use_container_width=True)

with tab2:
    st.plotly_chart(
        plot_return_distributions(lr_sel),
        use_container_width=True
    )

with tab3:
    summary = finance_summary(prices_sel, lr_sel, selected)
    st.plotly_chart(
        plot_risk_return(summary, title="Risk vs Return — Selected Tickers"),
        use_container_width=True
    )
    corr = lr_sel.corr()
    fig_c, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(corr, annot=True, fmt=".2f",
                cmap="RdYlGn", vmin=-1, vmax=1,
                linewidths=0.5, ax=ax)
    ax.set_title("Return Correlation Matrix")
    st.pyplot(fig_c)