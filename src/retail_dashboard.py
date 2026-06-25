import streamlit as st
import pandas as pd

from pipeline import (plot_monthly_revenue, plot_top_products,
                      plot_rfm_scatter, top_products)

st.set_page_config(page_title="Retail Analytics",
                   page_icon="🛍️", layout="wide")
st.title("🛍️ Online Retail — Sales Analytics Dashboard")

@st.cache_data
def load():
    df      = pd.read_parquet("../data/processed/retail_clean.parquet")
    monthly = pd.read_parquet("../data/processed/retail_monthly.parquet")
    rfm     = pd.read_parquet("../data/processed/retail_rfm.parquet")
    return df, monthly, rfm

df, monthly, rfm = load()

# Sidebar filter
countries   = ["All"] + sorted(df["Country"].unique().tolist())
sel_country = st.sidebar.selectbox("Country", countries)
if sel_country != "All":
    df = df[df["Country"] == sel_country]

# KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue",   f"£{df['Revenue'].sum():,.0f}")
k2.metric("Orders",          f"{df['Invoice'].nunique():,}")
k3.metric("Customers",       f"{df['Customer ID'].nunique():,}")
k4.metric("Avg Order Value", f"£{df.groupby('Invoice')['Revenue'].sum().mean():,.2f}")

# Charts — all figures built by pipeline functions
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        plot_monthly_revenue(monthly, title="Monthly Revenue"),
        use_container_width=True
    )
with col2:
    top10 = top_products(df, n=10)
    st.plotly_chart(
        plot_top_products(top10, title="Top 10 Products"),
        use_container_width=True
    )

st.plotly_chart(
    plot_rfm_scatter(rfm, title="RFM Customer Map"),
    use_container_width=True
)