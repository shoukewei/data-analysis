# realtime_watchdog.py
import streamlit as st
import pandas as pd
import plotly.express as px
from watchdog.observers.polling import PollingObserver   # reliable on Windows & network drives
from watchdog.events import FileSystemEventHandler
import queue, time, os

DATA_FILE = "../data/live_data.csv"

# ── Thread-safe queue stored in session state (survives reruns) ───────
if "change_queue" not in st.session_state:
    st.session_state["change_queue"] = queue.Queue()
_q: queue.Queue = st.session_state["change_queue"]

# ── Debounce state (module-level, shared across reruns) ───────────────
_last_event: dict = {}
_DEBOUNCE = 0.3   # seconds — absorbs duplicate OS events on Windows

class CSVChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        target = os.path.abspath(DATA_FILE)
        if os.path.abspath(event.src_path) != target:
            return
        now = time.monotonic()
        if now - _last_event.get(target, 0) < _DEBOUNCE:
            return
        _last_event[target] = now
        _q.put_nowait("changed")

def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_FILE, parse_dates=["timestamp"])

# ── Start PollingObserver once (250 ms poll — fast but light) ─────────
if "observer_started" not in st.session_state:
    watch_dir = os.path.dirname(os.path.abspath(DATA_FILE)) or "."
    obs = PollingObserver(timeout=0.25)   # checks every 250 ms
    obs.schedule(CSVChangeHandler(), watch_dir, recursive=False)
    obs.start()
    st.session_state["observer_started"] = True

# ── Initial data load ─────────────────────────────────────────────────
if "df" not in st.session_state:
    try:
        st.session_state["df"] = load_data()
        st.session_state["last_loaded"] = time.time()
    except FileNotFoundError:
        st.session_state["df"] = None
        st.session_state["last_loaded"] = None

# ── Fragment polls queue every 200 ms ─────────────────────────────────
@st.fragment(run_every="200ms")
def _watcher():
    try:
        _q.get_nowait()
        while not _q.empty():          # drain duplicates
            _q.get_nowait()
        try:
            st.session_state["df"] = load_data()
            st.session_state["last_loaded"] = time.time()
            st.session_state.pop("load_error", None)
        except Exception as e:
            st.session_state["load_error"] = str(e)
        st.rerun()
    except queue.Empty:
        pass

_watcher()

# ── Dashboard ─────────────────────────────────────────────────────────
st.title("🐶 Watchdog — Real-Time Monitor")

if err := st.session_state.get("load_error"):
    st.error(f"Reload failed: {err}")

if st.session_state["df"] is not None:
    df = st.session_state["df"]

    loaded_at = st.session_state.get("last_loaded")
    if loaded_at:
        st.caption(f"Last updated: {time.strftime('%H:%M:%S', time.localtime(loaded_at))}  •  {len(df)} rows")

    fig = px.line(df, x="timestamp", y="value", title="Live Value — Event-Driven Refresh")
    st.plotly_chart(fig, width="stretch")

    col1, col2 = st.columns(2)
    col1.metric("Latest value",  f"{df['value'].iloc[-1]:.2f}",
                                 f"{df['value'].diff().iloc[-1]:+.2f}")
    col2.metric("Row count", len(df))
else:
    st.warning(f"Waiting for {DATA_FILE}…")
