# ─────────────────────────────────────────────────────────────────────────────
# StudentLife Visual Analytics Dashboard
# Light + Dark Theme  |  Mobile + Desktop Responsive
# Author: Rohith Elanchezhian | Newcastle University
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(
    page_title="StudentLife Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Session state: theme ──────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

dark = st.session_state.dark_mode

# ── Theme colour tokens ───────────────────────────────────────────────────────
if dark:
    BG        = "#0F0F15"
    SURFACE   = "#1A1A24"
    SURFACE2  = "#22222E"
    BORDER    = "#2A2A3E"
    TEXT      = "#E8E8F0"
    MUTED     = "#8888AA"
    ACCENT    = "#60A5FA"
    PLOT_BG   = "#1A1A24"
    PLOT_PAPER= "#0F0F15"
    GRID      = "#2A2A3E"
    SIDEBAR_BG= "#13131C"
else:
    BG        = "#F4F6FA"
    SURFACE   = "#FFFFFF"
    SURFACE2  = "#F8FAFF"
    BORDER    = "#E0E6F0"
    TEXT      = "#111827"
    MUTED     = "#6B7280"
    ACCENT    = "#1F4E79"
    PLOT_BG   = "#FFFFFF"
    PLOT_PAPER= "#F9FAFB"
    GRID      = "#E5E7EB"
    SIDEBAR_BG= "#FFFFFF"

# Chart colours (same for both themes)
C = {
    'stress':   '#E05C5C',
    'sleep':    '#4ECDC4',
    'mood':     '#7C6AF7',
    'exercise': '#50C878',
    'social':   '#F0A050',
    'neutral':  '#8888AA',
    'ml':       '#FF6B9D',
    'blue':     ACCENT,
}

# Plotly template
PLOT = dict(
    paper_bgcolor=PLOT_PAPER,
    plot_bgcolor=PLOT_BG,
    font=dict(color=TEXT, family='Inter, sans-serif', size=12),
    margin=dict(l=40, r=20, t=40, b=40),
)

DAY_NAMES = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
WEEKS     = list(range(1, 11))
DATA_DIR  = 'data'

# ── CSS: theme + responsive ───────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {{ font-family: 'Inter', sans-serif !important; }}

/* ── Page background ── */
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {{
    background-color: {BG} !important;
}}
[data-testid="stHeader"] {{
    background-color: {BG} !important;
}}
.block-container {{
    padding: 0.8rem 1rem 2rem 1rem !important;
    max-width: 1400px;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background-color: {SIDEBAR_BG} !important;
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {{
    color: {TEXT} !important;
}}

/* ── All text ── */
p, span, div, h1, h2, h3, label {{ color: {TEXT}; }}

/* ── Metric cards ── */
.metric-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 1rem 0.75rem;
    text-align: center;
    box-shadow: 0 1px 6px rgba(0,0,0,{"0.25" if dark else "0.06"});
    height: 100%;
}}
.metric-val  {{ font-size: 1.6rem; font-weight: 700; line-height: 1.1; }}
.metric-lbl  {{ font-size: 0.7rem; font-weight: 600; color: {MUTED};
                text-transform: uppercase; letter-spacing: 0.07em; margin-top: 5px; }}
.metric-sub  {{ font-size: 0.7rem; color: {MUTED}; margin-top: 2px; }}

/* ── Finding cards ── */
.find-card {{
    background: {SURFACE};
    border-left: 4px solid {ACCENT};
    border-radius: 0 12px 12px 0;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
    box-shadow: 0 1px 4px rgba(0,0,0,{"0.2" if dark else "0.05"});
}}
.find-card.red    {{ border-left-color: #E05C5C; }}
.find-card.teal   {{ border-left-color: #4ECDC4; }}
.find-card.orange {{ border-left-color: #F0A050; }}
.find-title {{ font-size: 0.85rem; font-weight: 600; color: {TEXT}; margin-bottom: 3px; }}
.find-text  {{ font-size: 0.8rem; color: {MUTED}; line-height: 1.5; }}

/* ── Section title ── */
.sec-title {{
    font-size: 0.95rem; font-weight: 700; color: {ACCENT};
    border-bottom: 2px solid {BORDER};
    padding-bottom: 5px; margin: 0.8rem 0 0.5rem;
}}

/* ── Chart card wrapper ── */
.chart-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,{"0.2" if dark else "0.04"});
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: {SURFACE};
    border-radius: 12px;
    padding: 4px;
    gap: 2px;
    box-shadow: 0 1px 4px rgba(0,0,0,{"0.25" if dark else "0.08"});
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 500;
    color: {MUTED} !important;
    padding: 0.4rem 0.8rem;
    white-space: nowrap;
    background: transparent;
}}
.stTabs [aria-selected="true"] {{
    background: {ACCENT} !important;
    color: #FFFFFF !important;
}}

/* ── Buttons ── */
.stButton > button {{
    background: {ACCENT};
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-weight: 600;
}}

/* ── Selectbox / inputs ── */
.stSelectbox > div > div {{
    background: {SURFACE} !important;
    border-color: {BORDER} !important;
    color: {TEXT} !important;
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    background: {SURFACE};
    border-radius: 10px;
}}

/* ── Expander ── */
.streamlit-expanderHeader {{
    background: {SURFACE} !important;
    color: {TEXT} !important;
    border-radius: 8px;
}}

/* ── Plotly charts ── */
.js-plotly-plot {{ border-radius: 10px; }}
.plot-container {{ border-radius: 10px; }}

/* ── ══════════ RESPONSIVE GRID ══════════ ── */

/* Metric grid: 3 per row on phones, 6 on desktop */
.metric-grid {{
    display: grid;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    grid-template-columns: repeat(3, 1fr);
}}
@media (min-width: 768px) {{
    .metric-grid {{ grid-template-columns: repeat(6, 1fr); }}
}}

/* Full width on mobile, 50% on desktop */
.chart-grid {{
    display: grid;
    gap: 0.75rem;
    grid-template-columns: 1fr;
}}
@media (min-width: 640px) {{
    .chart-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}

/* Tabs wrap on small screens */
@media (max-width: 640px) {{
    .block-container {{ padding-left: 0.5rem !important; padding-right: 0.5rem !important; }}
    .metric-val {{ font-size: 1.2rem; }}
    .stTabs [data-baseweb="tab"] {{
        font-size: 0.72rem;
        padding: 0.3rem 0.5rem;
    }}
}}

/* Alert / info boxes */
.stAlert {{ border-radius: 10px; }}
div[data-testid="stMarkdownContainer"] p {{ color: {TEXT}; }}

/* Caption text */
.stCaption {{ color: {MUTED} !important; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def safe_mean(df, col):
    if col in df.columns and df[col].notna().any():
        return df[col].mean()
    return None

def apply_plot(fig, height=320, **extra):
    fig.update_layout(**PLOT, height=height, **extra)
    fig.update_xaxes(gridcolor=GRID, linecolor=BORDER, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, linecolor=BORDER, zerolinecolor=GRID)
    return fig

def metric_html(label, value, sub='', color=None):
    col = color or ACCENT
    return f"""<div class="metric-card">
        <div class="metric-val" style="color:{col}">{value}</div>
        <div class="metric-lbl">{label}</div>
        <div class="metric-sub">{sub}</div>
    </div>"""

def metric_card(label, value, sub='', color=None):
    st.markdown(metric_html(label, value, sub, color), unsafe_allow_html=True)

def find_card(icon, title, text, style=''):
    st.markdown(f"""<div class="find-card {style}">
        <div class="find-title">{icon} {title}</div>
        <div class="find-text">{text}</div>
    </div>""", unsafe_allow_html=True)

def sec(title):
    st.markdown(f'<div class="sec-title">{title}</div>', unsafe_allow_html=True)

def quality_check(df):
    if 'uid' not in df.columns or 'stress_avg' not in df.columns:
        return {}
    counts = df.groupby('uid')['stress_avg'].count()
    return {uid: (int(n), n < 5) for uid, n in counts.items()}

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def load_master():
    df = pd.read_csv(os.path.join(DATA_DIR, 'daily_master.csv'))
    if 'student_id' in df.columns:
        df.rename(columns={'student_id': 'uid'}, inplace=True)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    if 'is_weekend' in df.columns:
        df['is_weekend'] = df['is_weekend'].astype(str).str.lower().isin(['true','1','yes'])
    if 'stress_avg' in df.columns:
        df['high_stress'] = (df['stress_avg'] >= 4).astype(float)
        df.loc[df['stress_avg'].isna(), 'high_stress'] = np.nan
    return df

@st.cache_data
def load_ml(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    if 'student_id' in df.columns:
        df.rename(columns={'student_id': 'uid'}, inplace=True)
    return df

if not os.path.exists(os.path.join(DATA_DIR, 'daily_master.csv')):
    st.title("🎓 StudentLife Dashboard")
    st.error("Data not found — add `daily_master.csv` to the `data/` folder.")
    st.stop()

df         = load_master()
pred_df    = load_ml('ml_predictions.csv')
cluster_df = load_ml('ml_clusters.csv')
fi_df      = load_ml('ml_feature_importance.csv')
perf_df    = load_ml('ml_performance.csv')

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"<h3 style='color:{TEXT}'>🎓 StudentLife</h3>", unsafe_allow_html=True)
    st.caption("Visual Analytics for Digital Health")
    st.caption("Rohith Elanchezhian · Newcastle University")
    st.divider()

    # ── Theme toggle ──────────────────────────────────────────────
    st.markdown(f"<b style='color:{TEXT}'>Theme</b>", unsafe_allow_html=True)
    col_l, col_d = st.columns(2)
    with col_l:
        if st.button("☀️ Light", use_container_width=True,
                     type="primary" if not dark else "secondary"):
            st.session_state.dark_mode = False
            st.rerun()
    with col_d:
        if st.button("🌙 Dark", use_container_width=True,
                     type="primary" if dark else "secondary"):
            st.session_state.dark_mode = True
            st.rerun()

    st.divider()

    # ── Filters ───────────────────────────────────────────────────
    st.markdown(f"<b style='color:{TEXT}'>Filters</b>", unsafe_allow_html=True)
    week_filter = st.selectbox("Study week",
                               ["All weeks"] + [f"Week {w}" for w in WEEKS])
    day_filter  = st.selectbox("Day type",
                               ["All days","Weekdays only","Weekends only"])

    st.divider()

    # ── Data status ───────────────────────────────────────────────
    st.markdown(f"<b style='color:{TEXT}'>Data Status</b>", unsafe_allow_html=True)
    st.success("✅ daily_master.csv")
    for fname, lbl in [
        ('ml_predictions.csv',       'ml_predictions'),
        ('ml_clusters.csv',          'ml_clusters'),
        ('ml_feature_importance.csv','ml_feature_importance'),
        ('ml_performance.csv',       'ml_performance'),
    ]:
        if load_ml(fname) is not None:
            st.success(f"✅ {lbl}")
        else:
            st.caption(f"⬜ {lbl}")

    st.divider()
    st.caption("📊 49 students · 10 weeks · Spring 2013")

# ─────────────────────────────────────────────────────────────────────────────
# FILTER
# ─────────────────────────────────────────────────────────────────────────────

filtered = df.copy()
if week_filter != "All weeks":
    filtered = filtered[filtered['study_week'] == int(week_filter.split()[1])]
if day_filter == "Weekdays only":
    filtered = filtered[filtered['is_weekend'] == False]
elif day_filter == "Weekends only":
    filtered = filtered[filtered['is_weekend'] == True]

quality = quality_check(df)
sparse  = [u for u,(n,sp) in quality.items() if sp]

# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style='background:{ACCENT};border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:0.8rem'>
    <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem'>
        <div>
            <h1 style='color:#FFFFFF;font-size:clamp(1.1rem,3vw,1.6rem);font-weight:700;margin:0'>
                🎓 StudentLife Visual Analytics
            </h1>
            <p style='color:rgba(255,255,255,0.75);font-size:0.82rem;margin:4px 0 0'>
                Digital Health · 49 students · 10 weeks · Newcastle University
            </p>
        </div>
        <div style='color:rgba(255,255,255,0.6);font-size:0.75rem;text-align:right'>
            {"🌙 Dark mode" if dark else "☀️ Light mode"}<br>
            <span style='font-size:0.68rem'>Toggle in sidebar →</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.caption(
    f"Showing **{len(filtered):,} rows** · "
    f"**{filtered['uid'].nunique()} students** · "
    f"{week_filter} | {day_filter}"
)
if sparse:
    st.warning(f"⚠️ {len(sparse)} students have sparse data (<5 responses).")

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────

tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
    "📊 Overview",
    "📈 Trends",
    "🔗 Correlations",
    "🌡️ Heatmap",
    "👤 Student",
    "⚖️ Compare",
    "🤖 ML",
])

# ══════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════
with tab1:
    sm  = safe_mean(filtered, 'stress_avg')
    slm = safe_mean(filtered, 'sleep_hours')
    mm  = safe_mean(filtered, 'mood_score_avg')
    tm  = safe_mean(filtered, 'total_talking_minutes')
    hp  = (filtered['high_stress'].mean()*100
           if 'high_stress' in filtered.columns else None)
    dep = filtered['sleep_hours'].dropna() if 'sleep_hours' in filtered.columns else pd.Series([])
    dp  = ((dep<7).mean()*100) if len(dep) else None

    # Finding cards
    sec("📌 Key Findings")
    f1,f2,f3 = st.columns(3)
    with f1:
        if sm and hp:
            find_card("😟","Stress",
                      f"Avg <b>{sm:.2f}/5</b> · <b>{hp:.0f}%</b> days high stress","red")
    with f2:
        if dp and slm:
            find_card("😴","Sleep",
                      f"Avg <b>{slm:.1f}h</b> · <b>{dp:.0f}%</b> nights under 7h","teal")
    with f3:
        wd = df[df['is_weekend']==False]['stress_avg'].mean() if 'is_weekend' in df.columns else np.nan
        we = df[df['is_weekend']==True]['stress_avg'].mean()  if 'is_weekend' in df.columns else np.nan
        if pd.notna(wd) and pd.notna(we):
            find_card("😮","Surprise",
                      f"Weekend stress <b>{we:.2f}</b> {'>' if we>wd else '<'} "
                      f"weekday <b>{wd:.2f}</b>  (p=0.007)","orange")

    st.divider()

    # Metric cards — 6-column HTML grid (auto-responsive)
    sec("Key Metrics")
    metrics = [
        ("Avg Stress",      f"{sm:.2f}/5"  if sm  else "—","out of 5",    C['stress']),
        ("High Stress",     f"{hp:.0f}%"   if hp  else "—","level 4–5",   C['social']),
        ("Avg Sleep",       f"{slm:.1f}h"  if slm else "—","per night",   C['sleep']),
        ("Under 7h Nights", f"{dp:.0f}%"   if dp  else "—","deprived",    C['mood']),
        ("Avg Mood",        f"{mm:.2f}"    if mm  else "—","−4 to +4",    C['exercise']),
        ("Avg Talking",     f"{tm:.0f}m"   if tm  else "—","per day",     C['neutral']),
    ]
    cards_html = "".join(metric_html(l,v,s,c) for l,v,s,c in metrics)
    st.markdown(f'<div class="metric-grid">{cards_html}</div>', unsafe_allow_html=True)

    st.divider()

    # Charts
    c1,c2 = st.columns(2)
    with c1:
        sec("Stress Distribution")
        if 'stress_avg' in filtered.columns:
            v = filtered['stress_avg'].dropna()
            labels = ['1','2','3','4','5']
            full_labels = ['1 Not stressed','2','3 Moderate','4','5 Very stressed']
            counts = pd.cut(v,bins=[0.5,1.5,2.5,3.5,4.5,5.5],
                            labels=full_labels).value_counts().sort_index()
            fig = go.Figure(go.Bar(
                x=counts.index.tolist(), y=counts.values,
                marker_color=[C['sleep'],C['sleep'],C['neutral'],C['stress'],C['stress']],
                text=[f"{val/len(v)*100:.0f}%" for val in counts.values],
                textposition='outside'))
            apply_plot(fig,height=270,showlegend=False,
                       yaxis=dict(title='Responses',gridcolor=GRID))
            st.plotly_chart(fig,use_container_width=True)

    with c2:
        sec("Sleep Categories")
        if 'sleep_hours' in filtered.columns:
            v = filtered['sleep_hours'].dropna()
            cats = pd.cut(v,bins=[-np.inf,5,7,9,np.inf],
                          labels=['Under 5h','5–7h','7–9h','Over 9h'])
            cc   = cats.value_counts().sort_index()
            fig  = go.Figure(go.Pie(
                labels=cc.index.tolist(), values=cc.values,
                marker_colors=[C['stress'],C['social'],C['sleep'],C['mood']],
                hole=0.45, textinfo='label+percent', textfont_size=11))
            apply_plot(fig,height=270,showlegend=False)
            st.plotly_chart(fig,use_container_width=True)

    c3,c4 = st.columns(2)
    with c3:
        sec("Physical Activity")
        act = {'Stationary':'fraction_stationary',
               'Walking':'fraction_walking','Running':'fraction_running'}
        vals = {k:filtered[v].mean()*100 for k,v in act.items()
                if v in filtered.columns and filtered[v].notna().any()}
        if vals:
            fig = go.Figure(go.Bar(
                x=list(vals.keys()), y=list(vals.values()),
                marker_color=[C['neutral'],C['sleep'],C['exercise']],
                text=[f"{v:.1f}%" for v in vals.values()],
                textposition='outside'))
            apply_plot(fig,height=250,showlegend=False,
                       yaxis=dict(title='% of readings',range=[0,105],gridcolor=GRID))
            st.plotly_chart(fig,use_container_width=True)

    with c4:
        sec("Talking Time by Day")
        if all(x in filtered.columns for x in ['total_talking_minutes','day_of_week']):
            dow = filtered.groupby('day_of_week')['total_talking_minutes'].mean().reindex(range(7))
            fig = go.Figure(go.Bar(
                x=DAY_NAMES, y=dow.values,
                marker_color=[C['social'] if i>=5 else C['mood'] for i in range(7)],
                text=[f"{v:.0f}m" if pd.notna(v) else "" for v in dow.values],
                textposition='outside'))
            apply_plot(fig,height=250,showlegend=False,
                       yaxis=dict(title='Minutes',gridcolor=GRID))
            st.plotly_chart(fig,use_container_width=True)


# ══════════════════════════════════════════════════════
# TAB 2 — TRENDS
# ══════════════════════════════════════════════════════
with tab2:
    sec("📈 Key Variables Across the 10-Week Term")
    st.caption("🔴 shaded area = finals week (Week 10)")

    weekly = df.groupby('study_week').agg(
        stress  =('stress_avg','mean'),
        sleep   =('sleep_hours','mean'),
        mood    =('mood_score_avg','mean'),
        talking =('total_talking_minutes','mean'),
        walking =('fraction_walking','mean'),
        devices =('unique_devices_nearby','mean'),
    ).reindex(WEEKS)

    fig = make_subplots(rows=2,cols=2,
        subplot_titles=['Stress Level (1–5)','Sleep Hours',
                        'Mood Score','Talking Time (min)'],
        vertical_spacing=0.2, horizontal_spacing=0.1)

    for row,col,key,color,yr in [
        (1,1,'stress', C['stress'],[1,5]),
        (1,2,'sleep',  C['sleep'], [3,12]),
        (2,1,'mood',   C['mood'],  [-2,2.5]),
        (2,2,'talking',C['social'],[0,70]),
    ]:
        y = weekly[key] if key in weekly.columns else [None]*10
        fig.add_scatter(x=WEEKS,y=y,mode='lines+markers',
                        line=dict(color=color,width=2.5),
                        marker=dict(size=7,color=color),row=row,col=col)
        fig.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,
                      line_width=0,row=row,col=col)
        fig.update_yaxes(range=yr,gridcolor=GRID,row=row,col=col)
        fig.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS],
                         gridcolor=GRID,row=row,col=col)

    fig.update_layout(height=480,paper_bgcolor=PLOT_PAPER,plot_bgcolor=PLOT_BG,
                      font=dict(color=TEXT,size=11),showlegend=False,
                      margin=dict(l=40,r=20,t=60,b=40))
    st.plotly_chart(fig,use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        sec("Social Proximity by Week")
        if 'devices' in weekly.columns:
            fig2 = go.Figure(go.Bar(x=[f'W{w}' for w in WEEKS],
                                    y=weekly['devices'].values,
                                    marker_color=C['mood']))
            apply_plot(fig2,height=240,
                       yaxis=dict(title='Unique BT devices',gridcolor=GRID))
            st.plotly_chart(fig2,use_container_width=True)
    with c2:
        sec("Walking Activity by Week")
        if 'walking' in weekly.columns:
            fig3 = go.Figure(go.Bar(x=[f'W{w}' for w in WEEKS],
                                    y=(weekly['walking']*100).values,
                                    marker_color=C['exercise']))
            apply_plot(fig3,height=240,
                       yaxis=dict(title='% time walking',gridcolor=GRID))
            st.plotly_chart(fig3,use_container_width=True)


# ══════════════════════════════════════════════════════
# TAB 3 — CORRELATIONS
# ══════════════════════════════════════════════════════
with tab3:
    sec("🔗 How Variables Relate to Each Other")
    st.caption("Each dot = one student on one day · Dashed line = trend")

    candidates = [
        ('sleep_hours','stress_avg','Sleep hours','Stress level',C['stress']),
        ('sleep_hours','mood_score_avg','Sleep hours','Mood score',C['mood']),
        ('fraction_walking','stress_avg','Walking fraction','Stress level',C['exercise']),
        ('total_talking_minutes','mood_score_avg','Talking (min)','Mood',C['social']),
        ('unique_devices_nearby','stress_avg','BT devices nearby','Stress level',C['neutral']),
        ('sleep_rate','stress_avg','Sleep quality','Stress level',C['sleep']),
    ]
    scatter_opts = {}
    for xc,yc,xl,yl,color in candidates:
        if xc in filtered.columns and yc in filtered.columns:
            scatter_opts[f"{xl}  vs  {yl}"] = (xc,yc,xl,yl,color)

    if scatter_opts:
        keys = list(scatter_opts.keys())
        s1 = st.selectbox("First chart",  keys, index=0)
        s2 = st.selectbox("Second chart", keys, index=min(1,len(keys)-1))

        def make_scatter(key):
            xc,yc,xl,yl,color = scatter_opts[key]
            d = filtered[[xc,yc]].dropna()
            if len(d)<5: return None
            r   = d[xc].corr(d[yc])
            m,b = np.polyfit(d[xc],d[yc],1)
            xs  = np.linspace(d[xc].min(),d[xc].max(),100)
            fig = go.Figure()
            fig.add_scatter(x=d[xc],y=d[yc],mode='markers',
                            marker=dict(color=color,size=5,opacity=0.35))
            fig.add_scatter(x=xs,y=m*xs+b,mode='lines',
                            line=dict(color=TEXT,width=2,dash='dash'))
            fig.add_annotation(text=f"r = {r:.3f}",
                               xref="paper",yref="paper",x=0.05,y=0.95,
                               showarrow=False,font=dict(size=13,color=TEXT),
                               bgcolor=SURFACE2,bordercolor=BORDER,
                               borderwidth=1,borderpad=6)
            apply_plot(fig,height=300,showlegend=False,
                       xaxis=dict(title=xl,gridcolor=GRID),
                       yaxis=dict(title=yl,gridcolor=GRID))
            return fig

        c1,c2 = st.columns(2)
        f1,f2 = make_scatter(s1), make_scatter(s2)
        if f1: c1.plotly_chart(f1,use_container_width=True)
        if f2: c2.plotly_chart(f2,use_container_width=True)

    sec("Correlation Matrix")
    corr_map = {'stress_avg':'Stress','sleep_hours':'Sleep hrs',
                'sleep_rate':'Sleep quality','mood_score_avg':'Mood',
                'fraction_walking':'Walking','total_talking_minutes':'Talking',
                'unique_devices_nearby':'BT devices'}
    avail = {k:v for k,v in corr_map.items() if k in filtered.columns}
    if len(avail)>=3:
        corr_df = filtered[list(avail.keys())].rename(columns=avail).corr()
        mask    = np.triu(np.ones(corr_df.shape,dtype=bool),k=1)
        corr_df[mask] = None
        fig_c = px.imshow(corr_df,color_continuous_scale='RdBu_r',
                          zmin=-1,zmax=1,text_auto='.2f',aspect='auto')
        fig_c.update_traces(textfont_size=11)
        apply_plot(fig_c,height=360)
        st.plotly_chart(fig_c,use_container_width=True)


# ══════════════════════════════════════════════════════
# TAB 4 — HEATMAP
# ══════════════════════════════════════════════════════
with tab4:
    sec("🌡️ Student × Week Stress Heatmap")
    st.caption("🟢 Green = calm · 🔴 Red = high stress · ⬜ White = no data")

    if 'stress_avg' in df.columns and 'uid' in df.columns:
        pivot = (df.groupby(['uid','study_week'])['stress_avg']
                 .mean().unstack(fill_value=np.nan).reindex(columns=WEEKS))
        fig_hm = px.imshow(pivot,
            color_continuous_scale=[
                [0.0,'#059669'],[0.25,'#6EE7B7'],
                [0.5,'#FCD34D'],[0.75,'#F87171'],[1.0,'#991B1B']],
            zmin=1,zmax=5,text_auto='.1f',aspect='auto',
            labels=dict(x='Study Week',y='Student ID',color='Avg Stress'))
        fig_hm.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
        fig_hm.update_traces(textfont_size=9)
        fig_hm.update_layout(
            height=max(420,len(pivot)*18),
            paper_bgcolor=PLOT_PAPER, font=dict(color=TEXT,size=11),
            margin=dict(l=80,r=20,t=40,b=40))
        st.plotly_chart(fig_hm,use_container_width=True)

        sm_s = df.groupby('uid')['stress_avg'].mean().dropna()
        c1,c2,c3 = st.columns(3)
        c1.metric("Most stressed",  sm_s.idxmax(), f"{sm_s.max():.2f}/5")
        c2.metric("Least stressed", sm_s.idxmin(), f"{sm_s.min():.2f}/5")
        c3.metric("Range", f"{sm_s.max()-sm_s.min():.2f} units")

    with st.expander("📋 Response count per student"):
        q_df = (pd.DataFrame([(uid,n,"⚠️ sparse" if sp else "✓ ok")
                               for uid,(n,sp) in quality.items()],
                              columns=["Student","Responses","Quality"])
                .sort_values("Responses",ascending=False))
        st.dataframe(q_df,use_container_width=True,hide_index=True)


# ══════════════════════════════════════════════════════
# TAB 5 — STUDENT EXPLORER
# ══════════════════════════════════════════════════════
with tab5:
    sec("👤 Individual Student Explorer")
    st.caption("🟢 low · 🟡 medium · 🔴 high  |  ⚠️ = fewer than 5 responses")

    all_students  = sorted(df['uid'].unique()) if 'uid' in df.columns else []
    student_means = df.groupby('uid')['stress_avg'].mean().dropna()

    def slabel(uid):
        m  = student_means.get(uid)
        sp = quality.get(uid,(0,False))[1]
        if m is None: return uid
        return f"{'🔴' if m>=3.5 else '🟡' if m>=2.5 else '🟢'} {uid}  ({m:.1f}){' ⚠️' if sp else ''}"

    if not all_students:
        st.warning("No student data found.")
    else:
        selected = st.selectbox("Select student", all_students, format_func=slabel)
        s   = df[df['uid']==selected]
        s_n = int(s['stress_avg'].notna().sum())
        s_stress = s['stress_avg'].mean()
        s_sleep  = s['sleep_hours'].mean()   if 'sleep_hours'    in s.columns else np.nan
        s_mood   = s['mood_score_avg'].mean() if 'mood_score_avg' in s.columns else np.nan

        cards_html = "".join([
            metric_html("Avg Stress",    f"{s_stress:.2f}/5" if pd.notna(s_stress) else "—","",C['stress']),
            metric_html("Avg Sleep",     f"{s_sleep:.1f}h"   if pd.notna(s_sleep)  else "—","",C['sleep']),
            metric_html("Avg Mood",      f"{s_mood:.2f}"     if pd.notna(s_mood)   else "—","",C['mood']),
            metric_html("Responses",     str(s_n),"stress surveys",C['neutral']),
        ])
        st.markdown(f'<div class="metric-grid" style="grid-template-columns:repeat(4,1fr)">{cards_html}</div>',
                    unsafe_allow_html=True)

        if s_n < 5:
            st.warning(f"⚠️ Only {s_n} responses — treat with caution.")
        if cluster_df is not None and 'uid' in cluster_df.columns:
            row = cluster_df[cluster_df['uid']==selected]
            if len(row):
                st.info(f"🔵 Cluster **{int(row.iloc[0]['cluster'])}**")

        s_weekly = (s.groupby('study_week')
                    .agg(stress=('stress_avg','mean'),sleep=('sleep_hours','mean'))
                    .reindex(WEEKS))
        group_w  = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)

        sec(f"{selected} — Stress vs Group Average")
        fig1 = go.Figure()
        fig1.add_scatter(x=WEEKS,y=s_weekly['stress'],mode='lines+markers',
                         name=selected,line=dict(color=C['stress'],width=2.5),
                         marker=dict(size=8,color=C['stress']))
        fig1.add_scatter(x=WEEKS,y=group_w,mode='lines',name='Group avg',
                         line=dict(color=MUTED,width=1.5,dash='dash'))
        fig1.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,line_width=0)
        fig1.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
        apply_plot(fig1,height=240,yaxis=dict(range=[0,5.5],title='Stress',gridcolor=GRID),
                   legend=dict(orientation='h',y=-0.3,font=dict(color=TEXT)))
        st.plotly_chart(fig1,use_container_width=True)

        if 'sleep' in s_weekly.columns:
            sec(f"{selected} — Sleep by Week")
            sv = s_weekly['sleep'].values
            sc = [C['sleep'] if pd.notna(v) and v>=7
                  else C['social'] if pd.notna(v) and v>=5
                  else C['stress'] if pd.notna(v)
                  else BORDER for v in sv]
            fig2 = go.Figure(go.Bar(x=[f'W{w}' for w in WEEKS],y=sv,marker_color=sc))
            fig2.add_hline(y=7,line_dash='dash',line_color=C['sleep'],
                           annotation_text='7h recommended',
                           annotation_position='top right',
                           annotation_font_color=TEXT)
            apply_plot(fig2,height=220,yaxis=dict(range=[0,14],title='Hours',gridcolor=GRID))
            st.plotly_chart(fig2,use_container_width=True)

        if pred_df is not None and 'uid' in pred_df.columns:
            sp_data = pred_df[pred_df['uid']==selected]
            if len(sp_data) and 'stress_predicted' in sp_data.columns:
                sec(f"{selected} — Actual vs Predicted Stress")
                sp_w = sp_data.groupby('study_week').agg(
                    actual=('stress_avg','mean'),
                    predicted=('stress_predicted','mean')).reindex(WEEKS)
                fig3 = go.Figure()
                fig3.add_scatter(x=WEEKS,y=sp_w['actual'],mode='lines+markers',
                                 name='Actual',line=dict(color=C['stress'],width=2))
                fig3.add_scatter(x=WEEKS,y=sp_w['predicted'],mode='lines+markers',
                                 name='Predicted',line=dict(color=C['ml'],width=2,dash='dot'))
                fig3.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
                apply_plot(fig3,height=220,
                           yaxis=dict(range=[0,5.5],title='Stress',gridcolor=GRID),
                           legend=dict(orientation='h',y=-0.3,font=dict(color=TEXT)))
                st.plotly_chart(fig3,use_container_width=True)


# ══════════════════════════════════════════════════════
# TAB 6 — COMPARE
# ══════════════════════════════════════════════════════
with tab6:
    sec("⚖️ Compare Two Students")
    st.caption("Select two students to compare their patterns")

    all_students = sorted(df['uid'].unique()) if 'uid' in df.columns else []
    if len(all_students) < 2:
        st.info("Not enough data.")
    else:
        ca_col, cb_col = st.columns(2)
        sa = ca_col.selectbox("Student A", all_students, index=0,                      key="csa")
        sb = cb_col.selectbox("Student B", all_students, index=min(1,len(all_students)-1), key="csb")

        da = df[df['uid']==sa]
        db = df[df['uid']==sb]

        rows = []
        for lbl,col,unit,is_pct in [
            ("Avg Stress",   'stress_avg',           "",   False),
            ("Avg Sleep",    'sleep_hours',           "h",  False),
            ("Avg Mood",     'mood_score_avg',        "",   False),
            ("Walking %",    'fraction_walking',      "%",  True),
            ("Talking",      'total_talking_minutes', "m",  False),
        ]:
            if col not in df.columns: continue
            va = da[col].mean(); vb = db[col].mean()
            def fmt(v,u,p): return f"{v*100:.1f}{u}" if p and pd.notna(v) else f"{v:.2f}{u}" if pd.notna(v) else "—"
            rows.append({"Metric":lbl, sa:fmt(va,unit,is_pct), sb:fmt(vb,unit,is_pct)})
        if rows:
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

        st.divider()
        c1,c2 = st.columns(2)
        for col,student,data,color in [(c1,sa,da,C['stress']),(c2,sb,db,C['mood'])]:
            with col:
                sec(f"{student}")
                sw = data.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)
                ga = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)
                fig = go.Figure()
                fig.add_scatter(x=WEEKS,y=sw,mode='lines+markers',
                                name=student,line=dict(color=color,width=2.5),
                                marker=dict(size=7,color=color))
                fig.add_scatter(x=WEEKS,y=ga,mode='lines',name='Avg',
                                line=dict(color=MUTED,width=1.5,dash='dash'))
                fig.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,line_width=0)
                fig.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
                apply_plot(fig,height=250,
                           yaxis=dict(range=[0,5.5],gridcolor=GRID),
                           legend=dict(orientation='h',y=-0.3,font=dict(color=TEXT)))
                st.plotly_chart(fig,use_container_width=True)


# ══════════════════════════════════════════════════════
# TAB 7 — ML
# ══════════════════════════════════════════════════════
with tab7:
    sec("🤖 Machine Learning Results")

    if all(f is None for f in [pred_df,cluster_df,fi_df,perf_df]):
        st.info("Upload ML files to the `data/` folder to unlock this tab.")
        st.stop()

    if perf_df is not None and 'task' in perf_df.columns:
        sec("Model Performance")
        c1,c2 = st.columns(2)
        with c1:
            st.caption("Regression — lower MAE = better")
            reg = perf_df[(perf_df['task']=='regression') & (perf_df['metric']=='MAE')]
            if not reg.empty:
                reg = reg.sort_values('value')
                fig = go.Figure(go.Bar(
                    x=reg['model'],y=reg['value'],
                    marker_color=[ACCENT if i==0 else BORDER for i in range(len(reg))],
                    text=[f"{v:.3f}" for v in reg['value']],textposition='outside'))
                apply_plot(fig,height=250,showlegend=False,
                           yaxis=dict(title='MAE',gridcolor=GRID))
                st.plotly_chart(fig,use_container_width=True)
                st.success(f"✅ Best: **{reg.iloc[0]['model']}**  (MAE={reg.iloc[0]['value']:.3f})")
        with c2:
            st.caption("Classification — higher AUC = better")
            cls = perf_df[(perf_df['task']=='classification') & (perf_df['metric']=='AUC')]
            if not cls.empty:
                cls = cls.sort_values('value',ascending=False)
                fig = go.Figure(go.Bar(
                    x=cls['model'],y=cls['value'],
                    marker_color=[ACCENT if i==0 else BORDER for i in range(len(cls))],
                    text=[f"{v:.3f}" for v in cls['value']],textposition='outside'))
                fig.add_hline(y=0.5,line_dash='dash',line_color=MUTED,annotation_text='Random')
                apply_plot(fig,height=250,showlegend=False,
                           yaxis=dict(title='AUC',range=[0,1.1],gridcolor=GRID))
                st.plotly_chart(fig,use_container_width=True)
                st.success(f"✅ Best: **{cls.iloc[0]['model']}**  (AUC={cls.iloc[0]['value']:.3f})")
        st.divider()

    if pred_df is not None and all(c in pred_df.columns for c in ['stress_avg','stress_predicted']):
        sec("Predicted vs Actual Stress")
        c1,c2 = st.columns(2)
        with c1:
            d   = pred_df[['stress_avg','stress_predicted']].dropna()
            mae = (d['stress_avg']-d['stress_predicted']).abs().mean()
            fig = go.Figure()
            fig.add_scatter(x=d['stress_avg'],y=d['stress_predicted'],mode='markers',
                            marker=dict(color=ACCENT,size=5,opacity=0.3))
            fig.add_scatter(x=[1,5],y=[1,5],mode='lines',
                            line=dict(color=TEXT,width=1.5,dash='dash'))
            fig.add_annotation(text=f"MAE = {mae:.3f}",xref="paper",yref="paper",
                               x=0.05,y=0.95,showarrow=False,
                               font=dict(size=13,color=TEXT),
                               bgcolor=SURFACE2,bordercolor=BORDER,borderwidth=1,borderpad=6)
            apply_plot(fig,height=280,showlegend=False,
                       xaxis=dict(title='Actual stress',range=[0.5,5.5],gridcolor=GRID),
                       yaxis=dict(title='Predicted',range=[0.5,5.5],gridcolor=GRID))
            st.plotly_chart(fig,use_container_width=True)
        with c2:
            if 'high_stress_prob' in pred_df.columns and 'study_week' in pred_df.columns:
                pw = pred_df.groupby('study_week')['high_stress_prob'].mean().reindex(WEEKS)
                fig = go.Figure(go.Bar(
                    x=[f'W{w}' for w in WEEKS],y=pw.values,
                    marker_color=[C['stress'] if (pd.notna(v) and v>=0.4)
                                  else C['social'] if (pd.notna(v) and v>=0.25)
                                  else C['sleep'] for v in pw.values],
                    text=[f"{v:.0%}" if pd.notna(v) else "" for v in pw.values],
                    textposition='outside'))
                fig.add_hline(y=0.25,line_dash='dash',line_color=C['social'],
                              annotation_text='25% risk',annotation_font_color=TEXT)
                apply_plot(fig,height=280,
                           yaxis=dict(title='High-stress probability',
                                      tickformat=',.0%',range=[0,0.85],gridcolor=GRID))
                st.plotly_chart(fig,use_container_width=True)
        st.divider()

    if fi_df is not None:
        sec("Feature Importance")
        lc = 'label' if 'label' in fi_df.columns else 'feature'
        if lc in fi_df.columns and 'importance' in fi_df.columns:
            fi_s = fi_df.sort_values('importance',ascending=True).tail(10)
            colors = []
            for feat in fi_s[lc]:
                fl = str(feat).lower()
                colors.append(C['sleep'] if 'sleep' in fl else
                               C['exercise'] if 'walk' in fl else
                               C['social'] if 'talk' in fl else
                               C['mood'] if 'device' in fl or 'bt' in fl else ACCENT)
            fig = go.Figure(go.Bar(
                x=fi_s['importance'],y=fi_s[lc],orientation='h',
                marker_color=colors,
                text=[f"{v:.4f}" for v in fi_s['importance']],textposition='outside'))
            apply_plot(fig,height=350,showlegend=False,
                       xaxis=dict(title='Importance',gridcolor=GRID))
            st.plotly_chart(fig,use_container_width=True)
            top3 = fi_df.sort_values('importance',ascending=False).head(3)
            st.markdown(f"**Top 3 predictors of stress:**")
            for _,row in top3.iterrows():
                st.markdown(f"- **{row[lc]}** — {row['importance']:.4f}")
        st.divider()

    if cluster_df is not None and 'cluster' in cluster_df.columns:
        sec("Student Behaviour Clusters")
        counts = cluster_df['cluster'].value_counts().sort_index()
        c1,c2 = st.columns(2)
        with c1:
            fig = go.Figure(go.Pie(
                labels=[f"Cluster {i}" for i in counts.index],
                values=counts.values,
                marker_colors=[C['stress'],C['sleep'],C['mood'],C['exercise']][:len(counts)],
                hole=0.4,textinfo='label+value'))
            apply_plot(fig,height=260,showlegend=False)
            st.plotly_chart(fig,use_container_width=True)
        with c2:
            if 'uid' in df.columns:
                df_c = df.merge(cluster_df[['uid','cluster']],on='uid',how='left')
                pcols = [x for x in ['stress_avg','sleep_hours','fraction_walking',
                                      'total_talking_minutes','unique_devices_nearby']
                         if x in df_c.columns]
                if pcols:
                    profile = df_c.groupby('cluster')[pcols].mean()
                    pn = ((profile-profile.min())/(profile.max()-profile.min()+1e-9))
                    pn = pn.rename(columns={'stress_avg':'Stress','sleep_hours':'Sleep',
                                            'fraction_walking':'Walking',
                                            'total_talking_minutes':'Talking',
                                            'unique_devices_nearby':'BT devices'})
                    fig = go.Figure()
                    for i,(idx,row) in enumerate(pn.iterrows()):
                        fig.add_bar(name=f"Cluster {idx}",
                                    x=row.index.tolist(),y=row.values,
                                    marker_color=[C['stress'],C['sleep'],C['mood'],C['exercise']][i%4])
                    apply_plot(fig,height=260,barmode='group',
                               yaxis=dict(title='Score (0–1)',range=[0,1.2],gridcolor=GRID),
                               legend=dict(orientation='h',y=-0.25,font=dict(color=TEXT)))
                    st.plotly_chart(fig,use_container_width=True)

        cols = st.columns(min(cluster_df['cluster'].nunique(),3))
        for col,(cl,grp) in zip(cols,cluster_df.groupby('cluster')):
            with col:
                st.markdown(f"**Cluster {cl}** ({len(grp)} students)")
                st.write(", ".join(sorted(grp['uid'].tolist())))
