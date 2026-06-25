import streamlit as st
import pandas as pd
import plotly.express as px
from watchdog.observers.polling import PollingObserver   # stable on Windows
from watchdog.events import FileSystemEventHandler
import queue, time, os

DATA_FILE = "../data/live_data.csv"

# ── Queue stored in session state ─────────────────────────────────────
if "change_queue" not in st.session_state:
    st.session_state["change_queue"] = queue.Queue()
_q: queue.Queue = st.session_state["change_queue"]

# ── Debounce state ────────────────────────────────────────────────────
_last_event: dict = {}
_DEBOUNCE = 0.3   # seconds

# ── File watcher handler ──────────────────────────────────────────────
class CSVChangeHandler(FileSystemEventHandler):
    def _handle_any(self):
        """Trigger reload if target file exists OR was removed."""
        now = time.monotonic()
        target = os.path.abspath(DATA_FILE)

        if now - _last_event.get(target, 0) < _DEBOUNCE:
            return

        _last_event[target] = now
        _q.put_nowait("changed")

    def on_any_event(self, event):
        # 👇 Key idea: DO NOT filter by exact file path anymore
        # Instead: check if target file exists or changed state
        self._handle_any()

# ── Safe data loader ──────────────────────────────────────────────────
def load_data() -> pd.DataFrame | None:
    if not os.path.exists(DATA_FILE):
        return None
    try:
        return pd.read_csv(DATA_FILE, parse_dates=["timestamp"])
    except Exception as e:
        st.session_state["load_error"] = str(e)
        return None

# ── Start observer once ───────────────────────────────────────────────
if "observer_started" not in st.session_state:
    watch_dir = os.path.dirname(os.path.abspath(DATA_FILE)) or "."
    obs = PollingObserver(timeout=0.25)
    obs.schedule(CSVChangeHandler(), watch_dir, recursive=False)
    obs.start()
    st.session_state["observer_started"] = True

# ── Initial load ──────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state["df"] = load_data()
    st.session_state["last_loaded"] = time.time()

# ── Watcher fragment (poll queue every 200 ms) ────────────────────────
@st.fragment(run_every="200ms")
def _watcher():
    try:
        _q.get_nowait()

        # drain duplicates
        while not _q.empty():
            _q.get_nowait()

        st.session_state["df"] = load_data()
        st.session_state["last_loaded"] = time.time()
        st.session_state.pop("load_error", None)

        st.rerun()

    except queue.Empty:
        pass

_watcher()

# ── UI ────────────────────────────────────────────────────────────────
st.title("🐶 Watchdog — Real-Time Monitor")

# show error if any
if err := st.session_state.get("load_error"):
    st.error(f"Reload failed: {err}")

df = st.session_state["df"]

if df is not None and not df.empty:

    loaded_at = st.session_state.get("last_loaded")
    if loaded_at:
        st.caption(
            f"Last updated: {time.strftime('%H:%M:%S', time.localtime(loaded_at))}  •  {len(df)} rows"
        )

    fig = px.line(df, x="timestamp", y="value", title="Live Value — Event-Driven Refresh")
    st.plotly_chart(fig, width="stretch")

    col1, col2 = st.columns(2)
    col1.metric(
        "Latest value",
        f"{df['value'].iloc[-1]:.2f}",
        f"{df['value'].diff().iloc[-1]:+.2f}" if len(df) > 1 else "0.00"
    )
    col2.metric("Row count", len(df))

else:
    st.warning(f"⚠️ Waiting for data file: {DATA_FILE}")