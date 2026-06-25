import streamlit as st

# --- Columns ---
col1, col2 = st.columns([2, 1])   # 2:1 width ratio
with col1:
    st.subheader("Main chart")
with col2:
    st.subheader("Summary")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["Overview", "Details", "Raw Data"])
with tab1:
    st.write("Overview content here")
with tab2:
    st.write("Detailed analysis here")
with tab3:
    st.write("Raw data table here")

# --- Expander (collapsible section) ---
with st.expander("Show methodology"):
    st.markdown("""
    Data is filtered to trips with positive fare and distance.
    All monetary values are in USD.
    """)

# --- Sidebar ---
with st.sidebar:
    st.header("Controls")
    st.write("Sidebar content here")