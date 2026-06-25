# iot_dashboard.py — streamlit run iot_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import datetime

from pipeline import detect_anomalies, plot_anomaly_chart
from config import IOT_CONFIG

st.set_page_config(
    page_title="IoT Sensor Monitor",
    page_icon="🌡️",
    layout="wide"
)

# Auto-refresh every 30 seconds
refresh_count = st_autorefresh(interval=30_000, key="iot_refresh")

st.title("🌡️ IoT Sensor Monitor — AirQuality UCI")
st.caption(
    f"Last updated: {datetime.datetime.now():%H:%M:%S}  "
    f"| Refresh #{refresh_count}"
)

# ── Data loading ─────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_sensor_data():
    df_raw = pd.read_csv(
        IOT_CONFIG["raw_dir"] / IOT_CONFIG["filename"],
        sep=";", decimal=","
    )
    df_raw = df_raw.dropna(how="all", axis=1).dropna(how="all", axis=0)
    df_raw["datetime"] = pd.to_datetime(
        df_raw["Date"].astype(str) + " " + df_raw["Time"].astype(str),
        format="%d/%m/%Y %H.%M.%S", errors="coerce"
    )
    df = df_raw[["datetime"] + IOT_CONFIG["sensors"]].copy()
    df = df.set_index("datetime").sort_index().replace(-200, np.nan)
    df = df.fillna(method="ffill", limit=IOT_CONFIG["ffill_limit"])
    df = df.dropna(how="all")
    return df

df = load_sensor_data()

# ── Sidebar controls ─────────────────────────────────────────────────
sel_sensor  = st.sidebar.selectbox("Sensor channel", IOT_CONFIG["sensors"])
window_size = st.sidebar.slider(
    "Rolling window (hours)", 6, 168, IOT_CONFIG["window"]
)
threshold   = st.sidebar.slider(
    "Anomaly threshold (σ)", 1.5, 5.0, IOT_CONFIG["threshold"], 0.5
)
lookback    = st.sidebar.slider("Lookback (days)", 7, 60, 30)

# Restrict to lookback period
cutoff = df.index.max() - pd.Timedelta(days=lookback)
view   = df[[sel_sensor]].loc[cutoff:].dropna()

# ── Anomaly detection ────────────────────────────────────────────────
roll_mean, roll_std, z_score, anomalies = detect_anomalies(
    view[sel_sensor], window=window_size, threshold=threshold
)

# ── KPI row ──────────────────────────────────────────────────────────
latest   = view[sel_sensor].iloc[-1]
mean_val = view[sel_sensor].mean()
n_anom   = len(anomalies)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Latest Reading",  f"{latest:.2f}")
k2.metric("Period Mean",     f"{mean_val:.2f}")
k3.metric("Anomalies Found", f"{n_anom}",
          delta=f"{n_anom/len(view)*100:.1f}%")
k4.metric("Data Points",     f"{len(view):,}")

st.divider()

# ── Main sensor chart ─────────────────────────────────────────────────
fig = plot_anomaly_chart(
    view[sel_sensor], roll_mean, roll_std, anomalies,
    threshold=threshold, sensor=sel_sensor
)
fig.update_layout(
    title=(f"{sel_sensor} — Last {lookback} Days  "
           f"({window_size}h rolling ±{threshold:.1f}σ bands)")
)
st.plotly_chart(fig, use_container_width=True)

# ── Correlation heatmap and anomaly log ──────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Sensor Correlation Heatmap")
    corr = df.loc[cutoff:].corr()
    fig_c, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(corr, annot=True, fmt=".2f",
                cmap="RdYlGn", vmin=-1, vmax=1,
                linewidths=0.5, ax=ax)
    ax.set_title(f"Sensor Correlations — Last {lookback} Days")
    st.pyplot(fig_c)

with col2:
    st.subheader("Anomaly Log")
    if len(anomalies) > 0:
        anom_df = (anomalies.reset_index()
                   .rename(columns={"datetime": "Timestamp",
                                    sel_sensor: "Value"}))
        anom_df["z_score"] = z_score[anomalies.index].round(2).values
        st.dataframe(
            anom_df.sort_values("Timestamp", ascending=False).head(20),
            use_container_width=True
        )
    else:
        st.success("No anomalies detected in the selected window.")

# ── Footer ────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Dataset: UCI Air Quality — "
    "https://archive.ics.uci.edu/dataset/360/air+quality"
)