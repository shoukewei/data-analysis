# realtime_watchdog.py
import streamlit as st
import pandas as pd
import plotly.express as px
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time

DATA_FILE = "../data/live_data.csv"

# ── Shared flag (thread-safe: GIL is enough for a single bool) ───────
_change_flag = threading.Event()

# ── Watchdog event handler ───────────────────────────────────────────
class CSVChangeHandler(FileSystemEventHandler):
    """Set a threading.Event when the CSV is modified."""
    def on_modified(self, event):
        if event.src_path.endswith(DATA_FILE):
            _change_flag.set()          # signal main thread

def load_data():
    return pd.read_csv(DATA_FILE, parse_dates=["timestamp"])

# ── Start watchdog observer in a background thread ───────────────────
def start_watching():
    observer = Observer()
    observer.schedule(CSVChangeHandler(), ".", recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except Exception:
        observer.stop()
    observer.join()

if "observer_started" not in st.session_state:
    threading.Thread(target=start_watching, daemon=True).start()
    st.session_state["observer_started"] = True

# ── Initial data load ────────────────────────────────────────────────
if "df" not in st.session_state:
    try:
        st.session_state["df"] = load_data()
    except FileNotFoundError:
        st.session_state["df"] = None

# ── Poll the shared flag and rerun when the file changes ─────────────
# st.fragment + st.rerun runs only this block, keeping the rest stable.
@st.fragment(run_every=1)          # re-executes every second
def poll_for_changes():
    if _change_flag.is_set():
        _change_flag.clear()
        try:
            st.session_state["df"] = load_data()
        except Exception as e:
            st.error(f"Reload failed: {e}")
        st.rerun()                 # wake up the full app

poll_for_changes()

# ── Dashboard ────────────────────────────────────────────────────────
st.title("🐶 Watchdog — Real-Time Monitor")
st.caption("Dashboard updates instantly when the CSV file changes.")

if st.session_state["df"] is not None:
    df = st.session_state["df"]
    fig = px.line(df, x="timestamp", y="value",
                  title="Live Value — Event-Driven Refresh")
    st.plotly_chart(fig, width="stretch")           # ← use_container_width replaced
    st.metric("Latest value",
              f"{df['value'].iloc[-1]:.2f}",
              f"{df['value'].diff().iloc[-1]:+.2f}")
else:
    st.warning(f"Waiting for {DATA_FILE}…")
