# bokeh_dashboard.py
# Run with: bokeh serve github_dashboard.py --show

import pandas as pd
import numpy as np
import requests
from datetime import datetime
from bokeh.plotting import figure, curdoc
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource, Select, CheckboxGroup,
    HoverTool, Div
)
from bokeh.palettes import Category10
from bokeh.transform import factor_cmap
from bokeh.io import output_file, save

# ── Data acquisition ──────────────────────────────────
def fetch_github_data(repos=None):
    """Fetch repository statistics from the GitHub public API."""
    if repos is None:
        repos = [
            "python/cpython", "microsoft/vscode",
            "facebook/react", "tensorflow/tensorflow",
            "nodejs/node"
        ]
    records = []
    for repo in repos:
        try:
            r = requests.get(f"https://api.github.com/repos/{repo}",
                             timeout=10)
            if r.status_code == 200:
                d = r.json()
                records.append({
                    "name":       d["name"],
                    "full_name":  d["full_name"],
                    "stars":      d["stargazers_count"],
                    "forks":      d["forks_count"],
                    "issues":     d["open_issues_count"],
                    "size":       d["size"],
                    "language":   d["language"] or "Unknown",
                    "created_at": pd.to_datetime(d["created_at"]),
                    "updated_at": pd.to_datetime(d["updated_at"]),
                    "description": d.get("description","")[:60],
                })
        except Exception as e:
            print(f"Error fetching {repo}: {e}")
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df["age_days"] = (datetime.now() - df["created_at"]).dt.days
    days_since = (datetime.now() - df["updated_at"]).dt.days
    df["activity_level"] = pd.cut(
        days_since,
        bins=[0, 7, 30, 90, float("inf")],
        labels=["Very Active","Active","Moderate","Low"]
    ).astype(str)
    df["star_category"] = pd.cut(
        df["stars"],
        bins=[0, 1000, 10000, 50000, float("inf")],
        labels=["Small","Medium","Large","Huge"]
    ).astype(str)
    return df

github_df = fetch_github_data()

# ── Data source ──────────────────────────────────────
source = ColumnDataSource(github_df)

# ── Scatter plot: stars vs forks ─────────────────────
languages = github_df["language"].unique().tolist()
colors = factor_cmap("language",
                      palette=Category10[max(3, len(languages))],
                      factors=languages)

p_scatter = figure(
    title="⭐ Repository Stars vs Forks Analysis",
    x_axis_label="Stars",
    y_axis_label="Forks",
    width=700, height=450,
    tools="pan,wheel_zoom,box_zoom,reset,save"
)
scatter = p_scatter.circle(
    "stars", "forks",
    source=source,
    size=14, color=colors, alpha=0.75, line_color="white"
)
hover_scatter = HoverTool(tooltips=[
    ("Repository",  "@full_name"),
    ("Language",    "@language"),
    ("Stars",       "@stars{0,0}"),
    ("Forks",       "@forks{0,0}"),
    ("Issues",      "@issues"),
    ("Description", "@description"),
])
p_scatter.add_tools(hover_scatter)
p_scatter.title.text_font_size = "15pt"
p_scatter.background_fill_color = "#FAFAFA"

# ── Bar chart: language distribution ─────────────────
lang_counts = github_df["language"].value_counts()
p_bar = figure(
    x_range=lang_counts.index.tolist(),
    title="📊 Languages Distribution",
    x_axis_label="Language",
    y_axis_label="Repositories",
    width=380, height=320,
    tools="save"
)
p_bar.vbar(
    x=lang_counts.index.tolist(),
    top=lang_counts.values.tolist(),
    width=0.7,
    color=Category10[max(3, len(lang_counts))][:len(lang_counts)]
)
p_bar.xgrid.grid_line_color = None
p_bar.background_fill_color = "#FAFAFA"
p_bar.title.text_font_size = "13pt"

# ── Time series: repository creation ────────────────
df_sorted = github_df.sort_values("created_at").copy()
df_sorted["cumulative"] = range(1, len(df_sorted) + 1)
ts_source = ColumnDataSource(df_sorted)

p_ts = figure(
    title="📅 Repository Timeline",
    x_axis_label="Creation Date",
    y_axis_label="Cumulative Repositories",
    x_axis_type="datetime",
    width=380, height=320,
    tools="save"
)
p_ts.line("created_at", "cumulative", source=ts_source,
           line_width=3, color="#E53935")
p_ts.circle("created_at", "cumulative", source=ts_source,
             size=8, color="#E53935", alpha=0.8)
p_ts.background_fill_color = "#FAFAFA"
p_ts.title.text_font_size = "13pt"

# ── Interactive widgets ─────────────────────────────
language_select = Select(
    title="Programming Language:",
    value="All",
    options=["All"] + sorted(github_df["language"].unique().tolist())
)
category_select = Select(
    title="Repository Size:",
    value="All",
    options=["All"] + github_df["star_category"].unique().tolist()
)
activity_group = CheckboxGroup(
    labels=github_df["activity_level"].unique().tolist(),
    active=list(range(len(github_df["activity_level"].unique())))
)

# ── Callback ───────────────────────────────────────
def update(attr, old, new):
    filt = github_df.copy()
    if language_select.value != "All":
        filt = filt[filt["language"] == language_select.value]
    if category_select.value != "All":
        filt = filt[filt["star_category"] == category_select.value]
    selected_levels = [activity_group.labels[i]
                       for i in activity_group.active]
    if selected_levels:
        filt = filt[filt["activity_level"].isin(selected_levels)]
    source.data = ColumnDataSource(filt).data

language_select.on_change("value", update)
category_select.on_change("value", update)
activity_group.on_change("active", update)

# ── Layout ──────────────────────────────────────────
header = Div(text="""
<div style="background:linear-gradient(135deg,#1565C0,#0D47A1);
            color:white;padding:18px 24px;border-radius:8px;
            margin-bottom:12px;">
  <h2 style="margin:0;">📦 GitHub Repository Analytics</h2>
  <p style="margin:4px 0 0;">Interactive Dashboard for Repository Analysis</p>
</div>
""")

controls = column(
    Div(text="<h3>Dashboard Controls</h3>"),
    language_select,
    category_select,
    Div(text="<b>Activity Level:</b>"),
    activity_group,
    width=220
)
charts = column(p_scatter, row(p_bar, p_ts))
dashboard = column(header, row(controls, charts))

curdoc().add_root(dashboard)
curdoc().title = "GitHub Repository Dashboard"