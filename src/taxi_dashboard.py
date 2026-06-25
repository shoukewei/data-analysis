# taxi_dashboard.py
# Run with: streamlit run taxi_dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import urllib.request
import os

# ── Page configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="NYC Taxi Dashboard",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Data loading ─────────────────────────────────────────────────────
@st.cache_data
def load_data():
    path = "yellow_tripdata_2023-01.parquet"
    if not os.path.exists(path):
        url = ("https://d37ci6vzurychx.cloudfront.net/"
               "trip-data/yellow_tripdata_2023-01.parquet")
        urllib.request.urlretrieve(url, path)

    df = pd.read_parquet(
        path,
        columns=["tpep_pickup_datetime", "trip_distance",
                 "fare_amount", "tip_amount",
                 "total_amount", "payment_type"]
    )
    df = df[(df["trip_distance"] > 0) & (df["fare_amount"] > 0)].copy()
    df["hour"]        = df["tpep_pickup_datetime"].dt.hour
    df["date"]        = df["tpep_pickup_datetime"].dt.date
    df["tip_pct"]     = (df["tip_amount"] / df["fare_amount"] * 100).round(1)
    df["payment_label"] = df["payment_type"].map(
        {1:"Credit Card", 2:"Cash",
         3:"No Charge",   4:"Dispute", 0:"Unknown"}
    )
    return df

df = load_data()

# ── Sidebar filters ──────────────────────────────────────────────────
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/"
                 "thumb/4/47/NYC_Taxi_waiting_for_customers.jpg/"
                 "320px-NYC_Taxi_waiting_for_customers.jpg",
                 use_container_width=True)
st.sidebar.title("🚕 NYC Taxi — Jan 2023")
st.sidebar.header("Filters")

# Date range
min_date = df["date"].min()
max_date = df["date"].max()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Payment type
all_payments = sorted(df["payment_label"].dropna().unique())
selected_payments = st.sidebar.multiselect(
    "Payment type",
    options=all_payments,
    default=all_payments
)

# Fare range
fare_min, fare_max = st.sidebar.slider(
    "Fare range ($)",
    float(df["fare_amount"].min()),
    float(df["fare_amount"].quantile(0.99)),
    (float(df["fare_amount"].min()),
     float(df["fare_amount"].quantile(0.99))),
    step=0.5
)

show_raw = st.sidebar.toggle("Show raw data table", value=False)

# ── Apply filters ────────────────────────────────────────────────────
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]

filtered = df[
    (df["date"] >= start_date) &
    (df["date"] <= end_date) &
    (df["payment_label"].isin(selected_payments)) &
    (df["fare_amount"] >= fare_min) &
    (df["fare_amount"] <= fare_max)
]

# ── Title and description ────────────────────────────────────────────
st.title("🚕 NYC Yellow Taxi — January 2023")
st.markdown(
    "Interactive dashboard for the NYC TLC Yellow Taxi "
    "trip records. Use the sidebar to filter by date, "
    "payment type, and fare range."
)

if filtered.empty:
    st.warning("No trips match the current filters. "
               "Please adjust the sidebar controls.")
    st.stop()

# ── KPI row ─────────────────────────────────────────────────────────
st.subheader("Key Performance Indicators")
k1, k2, k3, k4, k5 = st.columns(5)

total_trips  = len(filtered)
total_rev    = filtered["total_amount"].sum()
avg_fare     = filtered["fare_amount"].mean()
avg_tip_pct  = filtered["tip_pct"].mean()
avg_distance = filtered["trip_distance"].mean()

k1.metric("Total Trips",    f"{total_trips:,}")
k2.metric("Total Revenue",  f"${total_rev:,.0f}")
k3.metric("Avg Fare",       f"${avg_fare:.2f}")
k4.metric("Avg Tip %",      f"{avg_tip_pct:.1f}%")
k5.metric("Avg Distance",   f"{avg_distance:.2f} mi")

st.divider()

# ── Charts row 1 ────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Trips by Hour of Day")
    hourly = (
        filtered.groupby("hour")
        .agg(n_trips=("fare_amount","count"),
             avg_fare=("fare_amount","mean"))
        .reset_index()
    )
    fig_hourly = px.bar(
        hourly, x="hour", y="n_trips",
        color="avg_fare",
        color_continuous_scale="Blues",
        labels={"hour":"Hour","n_trips":"Trips",
                "avg_fare":"Mean Fare ($)"},
        title="Trip Volume by Hour (colour = mean fare)"
    )
    fig_hourly.update_layout(coloraxis_colorbar_title="Fare ($)")
    st.plotly_chart(fig_hourly, use_container_width=True)

with col2:
    st.subheader("Payment Type Distribution")
    payment_counts = (
        filtered["payment_label"]
        .value_counts().reset_index()
        .rename(columns={"payment_label":"payment",
                          "count":"n_trips"})
    )
    fig_pay = px.pie(
        payment_counts, values="n_trips", names="payment",
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Share by Payment Type"
    )
    fig_pay.update_traces(textposition="inside",
                           textinfo="percent+label")
    st.plotly_chart(fig_pay, use_container_width=True)

# ── Charts row 2 ────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Fare vs Distance")
    sample = filtered.sample(min(20_000, len(filtered)),
                              random_state=42)
    fig_scatter = px.scatter(
        sample,
        x="trip_distance", y="fare_amount",
        color="payment_label",
        opacity=0.3,
        range_x=[0, 25], range_y=[0, 80],
        labels={"trip_distance":"Distance (mi)",
                "fare_amount":"Fare ($)",
                "payment_label":"Payment"},
        title="Fare vs Distance (20k sample)"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col4:
    st.subheader("Daily Trip Volume")
    daily = (
        filtered.groupby("date")
        .size().reset_index(name="n_trips")
    )
    daily["date"] = pd.to_datetime(daily["date"])
    fig_daily = px.line(
        daily, x="date", y="n_trips",
        labels={"date":"Date","n_trips":"Trips"},
        title="Daily Trips over January 2023"
    )
    fig_daily.update_traces(line_color="#1565C0", line_width=2)
    st.plotly_chart(fig_daily, use_container_width=True)

# ── Hourly profile by payment type ──────────────────────────────────
st.subheader("Hourly Tip % by Payment Type")
hourly_tip = (
    filtered[filtered["payment_label"].isin(
        ["Credit Card","Cash"]
    )]
    .groupby(["hour","payment_label"])
    .agg(avg_tip_pct=("tip_pct","mean"))
    .reset_index()
)
fig_tip = px.line(
    hourly_tip,
    x="hour", y="avg_tip_pct",
    color="payment_label",
    markers=True,
    labels={"hour":"Hour","avg_tip_pct":"Mean Tip (%)","payment_label":"Payment"},
    color_discrete_map={"Credit Card":"#1565C0","Cash":"#2E7D32"},
    title="Mean Tip % by Hour — Credit Card vs Cash"
)
st.plotly_chart(fig_tip, use_container_width=True)

# ── Raw data table (optional) ────────────────────────────────────────
if show_raw:
    st.subheader("Raw Data")
    st.dataframe(
        filtered[["date","hour","trip_distance","fare_amount",
                  "tip_pct","payment_label"]]
        .sort_values("date")
        .head(5_000),
        use_container_width=True
    )

# ── Footer ───────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Data: NYC TLC Yellow Taxi Trip Records, January 2023. "
    "Source: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"
)