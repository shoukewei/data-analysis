import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

@st.cache_data
def load_hourly():
    df = pd.read_parquet(
        "../data/taxi/yellow_tripdata_2023-01.parquet",
        columns=["tpep_pickup_datetime", "fare_amount"]
    )
    df = df[df["fare_amount"] > 0].copy()
    df["hour"] = df["tpep_pickup_datetime"].dt.hour
    return df.groupby("hour")["fare_amount"].mean().reset_index()

hourly = load_hourly()

fig, ax = plt.subplots(figsize=(9, 4))
sns.barplot(data=hourly, x="hour", y="fare_amount",
            color="#1565C0", ax=ax)
ax.set_title("Mean Fare by Hour — January 2023")
ax.set_xlabel("Hour of Day")
ax.set_ylabel("Mean Fare (USD)")
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()

st.pyplot(fig)