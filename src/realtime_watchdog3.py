# realtime_watchdog.py
import streamlit as st
import pandas as pd
import plotly.express as px
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import queue
import time
import os

DATA_FILE = "../data/live_data.csv"

# ── Thread-safe queue: watchdog pushes, main thread drains ───────────
if "change_queue" not in st.session_state:
    st.session_state["change_queue"] = queue.Queue()

_change_queue: queue.Queue = st.session_state["change_queue"]

# ── Debounce: ignore duplicate events within 0.2 s ───────────────────
_last_event_time: dict = {}
_DEBOUNCE_SEC = 0.2

class CSVChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        abs_data = os.path.abspath(DATA_FILE)
        abs_src  = os.path.abspath(event.src_path)
        if abs_src != abs_data:
            return
        now = time.monotonic()
        if now - _last_event_time.get(abs_src, 0) < _DEBOUNCE_SEC:
            return                          # swallow duplicate OS events
        _last_event_time[abs_src] = now
        _change_queue.put_nowait("changed") # non-blocking, never raises

def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_FILE, parse_dates=["timestamp"])

# ── Start observer once per process (survives Streamlit reruns) ───────
if "observer_started" not in st.session_state:
    watch_dir = os.path.dirname(os.path.abspath(DATA_FILE)) or "."
    observer = Observer()
    observer.schedule(CSVChangeHandler(), watch_dir, recursive=False)
    observer.start()
    st.session_state["observer_started"] = True

# ── Initial data load ─────────────────────────────────────────────────
if "df" not in st.session_state:
    try:
        st.session_state["df"] = load_data()
    except FileNotFoundError:
        st.session_state["df"] = None

# ── Drain the queue — reload + rerun as soon as a change arrives ──────
@st.fragment(run_every="200ms")     # tight poll: negligible CPU cost
def _watch_fragment():
    try:
        _change_queue.get_nowait()  # raises Empty if nothing queued
        # Drain any further duplicates that piled up
        while not _change_queue.empty():
            _change_queue.get_nowait()
        try:
            st.session_state["df"] = load_data()
        except Exception as e:
            st.session_state["load_error"] = str(e)
        st.rerun()                  # kick the full app immediately
    except queue.Empty:
        pass                        # nothing changed, do nothing

_watch_fragment()

# ── Dashboard ─────────────────────────────────────────────────────────
st.title("🐶 Watchdog — Real-Time Monitor")
st.caption("Updates within ~200 ms of file change.")

if err := st.session_state.get("load_error"):
    st.error(f"Reload failed: {err}")
    st.session_state.pop("load_error", None)

if st.session_state["df"] is not None:
    df = st.session_state["df"]
    fig = px.line(df, x="timestamp", y="value",
                  title="Live Value — Event-Driven Refresh")
    st.plotly_chart(fig, width="stretch")
    st.metric(
        "Latest value",
        f"{df['value'].iloc[-1]:.2f}",
        f"{df['value'].diff().iloc[-1]:+.2f}",
    )
else:
    st.warning(f"Waiting for {DATA_FILE}…")
