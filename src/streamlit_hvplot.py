import streamlit as st
import pandas as pd
import hvplot.pandas
import holoviews as hv
from streamlit_bokeh import streamlit_bokeh  # pip install streamlit-bokeh

@st.cache_data
def load_hourly_df():
    df = pd.read_parquet(
        "../data/taxi/yellow_tripdata_2023-01.parquet",
        columns=["tpep_pickup_datetime","fare_amount"]
    )
    df = df[df["fare_amount"] > 0].copy()
    df["hour"] = df["tpep_pickup_datetime"].dt.hour
    return df.groupby("hour")["fare_amount"].mean().reset_index()

hourly = load_hourly_df()

hv_plot = hourly.hvplot.line(
    x="hour", y="fare_amount",
    title="Mean Fare by Hour",
    xlabel="Hour", ylabel="Fare (USD)",
    color="#1565C0", width=700, height=350
)
bokeh_fig = hv.render(hv_plot, backend="bokeh")
streamlit_bokeh(bokeh_fig, use_container_width=True)