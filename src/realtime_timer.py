# realtime_timer.py
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Live Monitor", layout="wide")

# Refresh every 10 seconds (10_000 ms)
# Returns the number of refreshes so far
refresh_count = st_autorefresh(interval=10_000, key="datarefresh")

st.title("🔴 Live Data Monitor")
st.caption(f"Auto-refreshes every 10 seconds | "
           f"Refresh count: {refresh_count} | "
           f"Last updated: {datetime.datetime.now():%H:%M:%S}")

# Load your data — re-read on every refresh
@st.cache_data(ttl=10)   # cache expires after 10 seconds
def load_latest():
    return pd.read_csv("../data/live_data.csv", parse_dates=["timestamp"])

try:
    df = load_latest()
    fig = px.line(df, x="timestamp", y="value",
                  title="Live Value Over Time")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.tail(20), use_container_width=True)
except FileNotFoundError:
    st.warning("Waiting for data file… (live_data.csv not found)")