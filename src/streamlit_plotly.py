import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_payment():
    df = pd.read_parquet(
        "../data/taxi/yellow_tripdata_2023-01.parquet",
        columns=["fare_amount", "payment_type"]
    )
    df = df[df["fare_amount"] > 0].copy()
    payment_map = {1:"Credit Card", 2:"Cash",
                   3:"No Charge",   4:"Dispute", 0:"Unknown"}
    return (
        df["payment_type"].map(payment_map)
        .value_counts().reset_index()
        .rename(columns={"payment_type":"payment","count":"n_trips"})
    )

payment_df = load_payment()

fig = px.pie(
    payment_df, values="n_trips", names="payment",
    title="Payment Type Distribution — January 2023",
    color_discrete_sequence=px.colors.qualitative.Set2
)
st.plotly_chart(fig, use_container_width=True)