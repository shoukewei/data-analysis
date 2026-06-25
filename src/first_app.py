import streamlit as st
import pandas as pd
import numpy as np

# Page configuration — must be the first Streamlit call
st.set_page_config(
    page_title="My First App",
    page_icon="🚀",
    layout="wide"
)

st.title("My First Streamlit App 🚀")
st.markdown("A quick tour of the core building blocks.")

# --- Text elements ---
st.header("1. Text Elements")
st.subheader("Subheader")
st.write("**Bold**, *italic*, and `code` via st.write()")
st.code('print("Hello, Streamlit!")', language="python")

# --- Widgets ---
st.header("2. Widgets")
name    = st.text_input("Your name", placeholder="Enter name…")
age     = st.slider("Your age", 0, 100, 25)
options = st.multiselect("Favourite colours",
                          ["Red","Green","Blue","Yellow"])

if name:
    st.success(f"Hello, {name}! You are {age} years old.")

# --- Layout ---
st.header("3. Columns Layout")
col1, col2, col3 = st.columns(3)
col1.metric("Trips",    "2,959,680",  "+3.2%")
col2.metric("Avg Fare", "$15.98",     "-0.4%")
col3.metric("Avg Tip",  "$3.14",      "+1.1%")

# --- Chart ---
st.header("4. Quick Chart")
data = pd.DataFrame(np.random.randn(30, 2), columns=["A", "B"])
st.line_chart(data)

