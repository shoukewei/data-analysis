import streamlit as st

st.sidebar.header("Filters")

# Text
name = st.sidebar.text_input("Search", placeholder="Type here…")

# Numeric
threshold = st.sidebar.number_input("Min fare ($)", 0.0, 500.0, 5.0)

# Slider
distance = st.sidebar.slider("Max distance (mi)", 0.0, 50.0, 20.0)

# Selectbox (single choice)
payment = st.sidebar.selectbox(
    "Payment type",
    ["All", "Credit Card", "Cash", "No Charge"]
)

# Multiselect (multiple choices)
boroughs = st.sidebar.multiselect(
    "Boroughs",
    ["Manhattan", "Queens", "Brooklyn", "Bronx", "Staten Island"],
    default=["Manhattan", "Queens"]
)

# Date range
import datetime
date_range = st.sidebar.date_input(
    "Date range",
    value=(datetime.date(2023, 1, 1), datetime.date(2023, 1, 31))
)

# Toggle
show_raw = st.sidebar.toggle("Show raw data", value=False)