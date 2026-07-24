# ─────────────────────────────────────────────────────────────────────────────
# StudentLife Visual Analytics Dashboard  — Fixed Version
# Dark Theme  |  Mobile + Desktop  |  All alignment bugs fixed
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

# ── Colour tokens ─────────────────────────────────────────────────────────────
BG       = "#0E0E16"
SURFACE  = "#161625"
CARD     = "#1C1C2E"
CARD2    = "#21213A"
BORDER   = "#2D2D4A"
BORDER2  = "#3A3A5C"
TEXT     = "#F0F0F8"
TEXT2    = "#C8C8E8"
MUTED    = "#7878A0"
ACCENT   = "#818CF8"
ACCENT2  = "#6366F1"
GRID     = "#252540"
PLOT_BG  = "#1C1C2E"
PLOT_PAP = "#161625"

C = {
    'stress':   '#F87171',
    'sleep':    '#34D399',
    'mood':     '#A78BFA',
    'exercise': '#4ADE80',
    'social':   '#FBBF24',
    'neutral':  '#94A3B8',
    'ml':       '#F472B6',
}

# ─────────────────────────────────────────────────────────────────────────────
# CSS — NO broken div wrappers. Chart styling done via CSS selectors only.
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*, *::before, *::after {{ font-family:'Inter',sans-serif !important; box-sizing:border-box; }}

/* ── Page ── */
html, body, [data-testid="stApp"],
[data-testid="stAppViewContainer"] {{ background:{BG} !important; }}
[data-testid="stHeader"] {{ background:{BG} !important; border-bottom:1px solid {BORDER}; }}
.block-container {{ padding:0.75rem 1rem 3rem !important; max-width:1440px; }}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{ background:{SURFACE} !important; border-right:1px solid {BORDER}; }}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {{ color:{TEXT2} !important; }}

/* ── Global text ── */
p, span, div, h1, h2, h3, label {{ color:{TEXT}; }}
.stMarkdown p {{ color:{TEXT2}; line-height:1.6; }}
.stCaption, .stCaption p {{ color:{MUTED} !important; font-size:0.8rem !important; }}

/* ── FIX: Override Streamlit's ugly default alert colors for dark theme ── */
.stAlert,
[data-testid="stAlertContainer"],
div.stAlert > div {{
    background:{CARD2} !important;
    border:1px solid {BORDER2} !important;
    border-radius:10px !important;
    color:{TEXT2} !important;
}}
div.stAlert p, div.stAlert span {{ color:{TEXT2} !important; }}

/* ── FIX: Style ALL plotly chart containers — no broken div wrappers needed ── */
[data-testid="stPlotlyChart"] {{
    background:{CARD};
    border:1px solid {BORDER};
    border-radius:14px;
    padding:0.6rem 0.5rem 0.25rem;
    margin-bottom:0.5rem;
}}

/* ── FIX: Style dataframe containers ── */
[data-testid="stDataFrame"] {{
    background:{CARD};
    border:1px solid {BORDER};
    border-radius:10px;
}}
[data-testid="stDataFrame"] * {{ color:{TEXT2} !important; }}
[data-testid="stDataFrameResizable"] {{ background:{CARD} !important; }}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > label {{ color:{TEXT2} !important; font-size:0.82rem; margin-bottom:2px; }}
[data-testid="stSelectbox"] > div > div {{
    background:{CARD} !important;
    border:1px solid {BORDER} !important;
    border-radius:8px !important;
    color:{TEXT} !important;
}}
[data-testid="stSelectbox"] svg {{ color:{MUTED} !important; }}

/* ── Metric cards (custom HTML) ── */
.m-grid {{
    display:grid; gap:0.55rem; margin-bottom:0.75rem;
    grid-template-columns:repeat(3,1fr);
}}
@media(min-width:768px) {{ .m-grid {{ grid-template-columns:repeat(6,1fr); }} }}
.m-card {{
    background:linear-gradient(135deg,{CARD},{CARD2});
    border:1px solid {BORDER};
    border-radius:14px;
    padding:1rem 0.6rem;
    text-align:center;
    transition:border-color .2s,transform .2s;
    cursor:default;
}}
.m-card:hover {{ border-color:{ACCENT}; transform:translateY(-2px); }}
.m-val {{ font-size:clamp(1rem,2.5vw,1.6rem); font-weight:700; line-height:1.1; }}
.m-lbl {{ font-size:0.65rem; font-weight:600; color:{MUTED};
          text-transform:uppercase; letter-spacing:.08em; margin-top:4px; }}
.m-sub {{ font-size:0.65rem; color:{MUTED}; margin-top:2px; }}

/* ── Finding cards ── */
.f-card {{
    background:linear-gradient(135deg,{CARD},{CARD2});
    border:1px solid {BORDER}; border-left:3px solid {ACCENT};
    border-radius:0 12px 12px 0;
    padding:0.75rem 1rem; margin-bottom:0.6rem;
}}
.f-card.red    {{ border-left-color:{C['stress']}; }}
.f-card.teal   {{ border-left-color:{C['sleep']};  }}
.f-card.orange {{ border-left-color:{C['social']}; }}
.f-title {{ font-size:0.85rem; font-weight:600; color:{TEXT};  margin-bottom:3px; }}
.f-text  {{ font-size:0.78rem; color:{TEXT2}; line-height:1.55; }}

/* ── Section label ── */
.sec-lbl {{
    font-size:0.78rem; font-weight:600; color:{MUTED};
    text-transform:uppercase; letter-spacing:.09em;
    border-bottom:1px solid {BORDER};
    padding-bottom:5px; margin:1rem 0 0.5rem;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background:{SURFACE} !important; border:1px solid {BORDER};
    border-radius:12px; padding:4px; gap:2px;
    flex-wrap:wrap; margin-bottom:0.6rem;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius:8px; font-size:0.78rem; font-weight:500;
    color:{MUTED} !important; padding:0.35rem 0.7rem; background:transparent;
}}
.stTabs [aria-selected="true"] {{
    background:{ACCENT2} !important; color:#fff !important;
}}

/* ── Expander ── */
details summary {{
    background:{CARD} !important; color:{TEXT} !important;
    border-radius:8px; border:1px solid {BORDER};
}}
details {{ background:{CARD}; border-radius:8px; border:1px solid {BORDER}; }}

/* ── Buttons ── */
.stButton>button {{
    background:{ACCENT2}; color:#fff; border:none;
    border-radius:8px; font-weight:600;
}}
.stButton>button:hover {{ background:{ACCENT}; }}

/* ── Metric widget (native st.metric) ── */
[data-testid="stMetric"] {{
    background:{CARD}; border:1px solid {BORDER};
    border-radius:12px; padding:0.75rem 1rem;
}}
[data-testid="stMetricLabel"] span {{ color:{MUTED} !important; font-size:0.78rem !important; }}
[data-testid="stMetricValue"]       {{ color:{TEXT}  !important; }}
[data-testid="stMetricDelta"]       {{ color:{MUTED} !important; }}

/* ── Divider ── */
hr {{ border:none; border-top:1px solid {BORDER}; margin:0.6rem 0; }}

/* ── Mobile ── */
@media(max-width:640px) {{
    .block-container {{ padding-left:0.5rem !important; padding-right:0.5rem !important; }}
    .m-val {{ font-size:1.1rem; }}
    .stTabs [data-baseweb="tab"] {{ font-size:0.7rem; padding:0.28rem 0.42rem; }}
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def safe_mean(df, col):
    if col in df.columns and df[col].notna().any():
        return df[col].mean()
    return None

def pf(fig, height=300, **kw):
    """Apply dark plot theme."""
    fig.update_layout(
        paper_bgcolor=PLOT_PAP, plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT2, family='Inter,sans-serif', size=11),
        height=height, margin=dict(l=44,r=20,t=36,b=36), **kw)
    fig.update_xaxes(gridcolor=GRID, linecolor=BORDER, color=TEXT2, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, linecolor=BORDER, color=TEXT2, zerolinecolor=GRID)
    return fig

def m_html(lbl, val, sub='', color=ACCENT):
    return (f'<div class="m-card">'
            f'<div class="m-val" style="color:{color}">{val}</div>'
            f'<div class="m-lbl">{lbl}</div>'
            f'<div class="m-sub">{sub}</div></div>')

def f_card(icon, title, text, cls=''):
    st.markdown(
        f'<div class="f-card {cls}">'
        f'<div class="f-title">{icon} {title}</div>'
        f'<div class="f-text">{text}</div></div>',
        unsafe_allow_html=True)

def sec(t):
    st.markdown(f'<div class="sec-lbl">{t}</div>', unsafe_allow_html=True)

def warn_badge(msg):
    st.markdown(
        f'<div style="background:#2D1B00;border:1px solid #78350F;border-radius:8px;'
        f'padding:6px 12px;font-size:0.8rem;color:#FBBF24;margin:0.4rem 0">⚠️ {msg}</div>',
        unsafe_allow_html=True)

def quality_check(df):
    if 'uid' not in df.columns or 'stress_avg' not in df.columns:
        return {}
    return {u:(int(n),n<5) for u,n in df.groupby('uid')['stress_avg'].count().items()}

def only_data(series):
    """Return x, y for a series, skipping NaN gaps so lines don't break."""
    mask = series.notna()
    return list(series.index[mask]), list(series[mask])

DAY_NAMES = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
WEEKS     = list(range(1,11))
DATA_DIR  = 'data'

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def load_master():
    df = pd.read_csv(os.path.join(DATA_DIR,'daily_master.csv'))
    if 'student_id' in df.columns: df.rename(columns={'student_id':'uid'}, inplace=True)
    if 'date'       in df.columns: df['date'] = pd.to_datetime(df['date'], errors='coerce')
    if 'is_weekend' in df.columns:
        df['is_weekend'] = df['is_weekend'].astype(str).str.lower().isin(['true','1','yes'])
    if 'stress_avg' in df.columns:
        df['high_stress'] = (df['stress_avg']>=4).astype(float)
        df.loc[df['stress_avg'].isna(),'high_stress'] = np.nan
    return df

@st.cache_data
def load_ml(fname):
    p = os.path.join(DATA_DIR, fname)
    if not os.path.exists(p): return None
    d = pd.read_csv(p)
    if 'student_id' in d.columns: d.rename(columns={'student_id':'uid'}, inplace=True)
    return d

# Gate
if not os.path.exists(os.path.join(DATA_DIR,'daily_master.csv')):
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
    st.markdown(
        f"<div style='padding:0.4rem 0 0.8rem'>"
        f"<div style='font-size:1.1rem;font-weight:700;color:{TEXT}'>🎓 StudentLife</div>"
        f"<div style='font-size:0.76rem;color:{MUTED}'>Visual Analytics · Newcastle University</div>"
        f"<div style='font-size:0.74rem;color:{MUTED};margin-top:1px'>Rohith Elanchezhian</div>"
        f"</div>", unsafe_allow_html=True)
    st.divider()

    # Filters — with proper labels (not collapsed)
    st.markdown(f"<div style='font-size:0.76rem;font-weight:600;color:{MUTED};text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px'>Filters</div>", unsafe_allow_html=True)
    week_filter = st.selectbox("Study week", ["All weeks"]+[f"Week {w}" for w in WEEKS])
    day_filter  = st.selectbox("Day type",   ["All days","Weekdays only","Weekends only"])

    st.divider()
    st.markdown(f"<div style='font-size:0.76rem;font-weight:600;color:{MUTED};text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px'>Data Files</div>", unsafe_allow_html=True)
    st.success("✅ daily_master.csv")
    for fname,lbl in [
        ('ml_predictions.csv','ml_predictions'),
        ('ml_clusters.csv','ml_clusters'),
        ('ml_feature_importance.csv','ml_feature_importance'),
        ('ml_performance.csv','ml_performance'),
    ]:
        if load_ml(fname) is not None: st.success(f"✅ {lbl}")
        else:                          st.caption(f"⬜ {lbl}")
    st.divider()
    st.caption("📊 49 students · 10 weeks · Spring 2013")

# ─────────────────────────────────────────────────────────────────────────────
# FILTER
# ─────────────────────────────────────────────────────────────────────────────

filtered = df.copy()
if week_filter != "All weeks":
    filtered = filtered[filtered['study_week']==int(week_filter.split()[1])]
if day_filter == "Weekdays only":
    filtered = filtered[filtered['is_weekend']==False]
elif day_filter == "Weekends only":
    filtered = filtered[filtered['is_weekend']==True]

quality = quality_check(df)
sparse  = [u for u,(_,sp) in quality.items() if sp]

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:linear-gradient(135deg,#1E1B4B 0%,#312E81 50%,#1E1B4B 100%);
            border:1px solid {BORDER2};border-radius:16px;
            padding:1.2rem 1.5rem;margin-bottom:0.75rem;
            box-shadow:0 4px 24px rgba(99,102,241,.18)'>
  <h1 style='color:#FFF;font-size:clamp(1rem,3.5vw,1.65rem);font-weight:700;margin:0;line-height:1.3'>
    🎓 StudentLife Visual Analytics Dashboard
  </h1>
  <p style='color:rgba(255,255,255,.6);font-size:0.8rem;margin:5px 0 0'>
    Digital Health &nbsp;·&nbsp; 49 students &nbsp;·&nbsp;
    10 weeks &nbsp;·&nbsp; Newcastle University
  </p>
</div>
""", unsafe_allow_html=True)

# Status bar
st.markdown(f"""
<div style='display:flex;gap:1rem;flex-wrap:wrap;align-items:center;margin-bottom:0.6rem'>
  <span style='font-size:0.8rem;color:{MUTED}'>
    <b style='color:{TEXT}'>{len(filtered):,} rows</b> &nbsp;·&nbsp;
    <b style='color:{TEXT}'>{filtered['uid'].nunique()} students</b> &nbsp;·&nbsp;
    {week_filter} | {day_filter}
  </span>
  {"<span style='font-size:0.76rem;background:#2D1B00;color:#FBBF24;border:1px solid #78350F;border-radius:6px;padding:2px 10px'>⚠️ " + str(len(sparse)) + " students have sparse data (&lt;5 responses)</span>" if sparse else ""}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────

tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
    "📊  Overview","📈  Trends","🔗  Correlations",
    "🌡️  Heatmap","👤  Student","⚖️  Compare","🤖  ML",
])

# ════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════
with tab1:
    sm  = safe_mean(filtered,'stress_avg')
    slm = safe_mean(filtered,'sleep_hours')
    mm  = safe_mean(filtered,'mood_score_avg')
    tm  = safe_mean(filtered,'total_talking_minutes')
    hp  = filtered['high_stress'].mean()*100 if 'high_stress' in filtered.columns else None
    dep = filtered['sleep_hours'].dropna()   if 'sleep_hours' in filtered.columns else pd.Series([])
    dp  = (dep<7).mean()*100 if len(dep) else None

    # Finding cards
    sec("Key Findings")
    c1,c2,c3 = st.columns(3)
    with c1:
        if sm and hp:
            f_card("😟","Stress",f"Average <b>{sm:.2f}/5</b> · <b>{hp:.0f}%</b> of days high stress","red")
    with c2:
        if dp and slm:
            f_card("😴","Sleep",f"Average <b>{slm:.1f}h</b> · <b>{dp:.0f}%</b> nights under 7h","teal")
    with c3:
        wd = df[df['is_weekend']==False]['stress_avg'].mean() if 'is_weekend' in df.columns else np.nan
        we = df[df['is_weekend']==True]['stress_avg'].mean()  if 'is_weekend' in df.columns else np.nan
        if pd.notna(wd) and pd.notna(we):
            f_card("😮","Surprise",f"Weekend <b>{we:.2f}</b> {'>' if we>wd else '<'} weekday <b>{wd:.2f}</b> (p=0.007)","orange")

    st.divider()

    # Metric grid
    sec("Key Metrics")
    metrics = [
        ("Avg Stress",  f"{sm:.2f}/5"  if sm  else "—","out of 5",  C['stress']),
        ("High Stress", f"{hp:.0f}%"   if hp  else "—","days 4–5",  C['social']),
        ("Avg Sleep",   f"{slm:.1f}h"  if slm else "—","per night", C['sleep']),
        ("Under 7h",    f"{dp:.0f}%"   if dp  else "—","deprived",  C['mood']),
        ("Avg Mood",    f"{mm:.2f}"    if mm  else "—","−4 to +4",  C['exercise']),
        ("Talking",     f"{tm:.0f}m"   if tm  else "—","per day",   C['neutral']),
    ]
    st.markdown(f'<div class="m-grid">{"".join(m_html(l,v,s,c) for l,v,s,c in metrics)}</div>',
                unsafe_allow_html=True)

    st.divider()
    col1,col2 = st.columns(2)

    with col1:
        sec("Stress Distribution")
        if 'stress_avg' in filtered.columns:
            v   = filtered['stress_avg'].dropna()
            lbs = ['1 Not stressed','2','3 Moderate','4','5 Very stressed']
            cts = pd.cut(v,bins=[.5,1.5,2.5,3.5,4.5,5.5],labels=lbs).value_counts().sort_index()
            fig = go.Figure(go.Bar(
                x=cts.index.tolist(), y=cts.values,
                marker_color=[C['sleep'],C['sleep'],C['neutral'],C['stress'],C['stress']],
                text=[f"{n/len(v)*100:.0f}%" for n in cts.values], textposition='outside'))
            pf(fig,height=260,showlegend=False,
               yaxis=dict(title='Responses',gridcolor=GRID))
            st.plotly_chart(fig,use_container_width=True)

    with col2:
        sec("Sleep Categories")
        if 'sleep_hours' in filtered.columns:
            v   = filtered['sleep_hours'].dropna()
            cats= pd.cut(v,bins=[-np.inf,5,7,9,np.inf],
                         labels=['Under 5h','5–7h','7–9h','Over 9h'])
            cc  = cats.value_counts().sort_index()
            fig = go.Figure(go.Pie(
                labels=cc.index.tolist(), values=cc.values,
                marker_colors=[C['stress'],C['social'],C['sleep'],C['mood']],
                hole=0.46, textinfo='label+percent', textfont_size=11,
                textfont_color=TEXT))
            pf(fig,height=260,showlegend=False)
            st.plotly_chart(fig,use_container_width=True)

    col3,col4 = st.columns(2)
    with col3:
        sec("Physical Activity")
        act = {'Stationary':'fraction_stationary',
               'Walking':'fraction_walking','Running':'fraction_running'}
        vals = {k:filtered[v].mean()*100 for k,v in act.items()
                if v in filtered.columns and filtered[v].notna().any()}
        if vals:
            fig = go.Figure(go.Bar(
                x=list(vals.keys()), y=list(vals.values()),
                marker_color=[C['neutral'],C['sleep'],C['exercise']],
                text=[f"{v:.1f}%" for v in vals.values()], textposition='outside'))
            pf(fig,height=250,showlegend=False,
               yaxis=dict(title='% of readings',range=[0,105],gridcolor=GRID))
            st.plotly_chart(fig,use_container_width=True)

    with col4:
        sec("Talking Time by Day of Week")
        if all(x in filtered.columns for x in ['total_talking_minutes','day_of_week']):
            dow = filtered.groupby('day_of_week')['total_talking_minutes'].mean().reindex(range(7))
            fig = go.Figure(go.Bar(
                x=DAY_NAMES, y=dow.values,
                marker_color=[C['social'] if i>=5 else ACCENT for i in range(7)],
                text=[f"{v:.0f}m" if pd.notna(v) else "" for v in dow.values],
                textposition='outside'))
            pf(fig,height=250,showlegend=False,
               yaxis=dict(title='Minutes',gridcolor=GRID))
            st.plotly_chart(fig,use_container_width=True)


# ════════════════════════════════════════
# TAB 2 — TRENDS
# ════════════════════════════════════════
with tab2:
    sec("Key Variables Across the 10-Week Term")
    st.caption("🔴 shaded = finals week (W10)  ·  Missing points = no data collected that week")

    weekly = df.groupby('study_week').agg(
        stress  =('stress_avg','mean'),
        sleep   =('sleep_hours','mean'),
        mood    =('mood_score_avg','mean'),
        talking =('total_talking_minutes','mean'),
        walking =('fraction_walking','mean'),
        devices =('unique_devices_nearby','mean'),
    ).reindex(WEEKS)

    fig = make_subplots(rows=2,cols=2,
        subplot_titles=['Stress Level (1–5)','Sleep Hours','Mood Score','Talking Time (min)'],
        vertical_spacing=0.22, horizontal_spacing=0.1)

    for row,col,key,color,yr in [
        (1,1,'stress', C['stress'],[1,5]),
        (1,2,'sleep',  C['sleep'], [3,12]),
        (2,1,'mood',   C['mood'],  [-2.5,2.5]),
        (2,2,'talking',C['social'],[0,70]),
    ]:
        if key in weekly.columns:
            x,y = only_data(weekly[key])
            if x:
                fig.add_scatter(x=x,y=y,mode='lines+markers',
                                line=dict(color=color,width=2.5),
                                marker=dict(size=8,color=color,
                                           line=dict(color=PLOT_BG,width=1.5)),
                                row=row,col=col)
        fig.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.08,line_width=0,row=row,col=col)
        fig.update_yaxes(range=yr,gridcolor=GRID,linecolor=BORDER,color=TEXT2,row=row,col=col)
        fig.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS],
                         gridcolor=GRID,linecolor=BORDER,color=TEXT2,row=row,col=col)

    for ann in fig['layout']['annotations']:
        ann['font'] = dict(color=TEXT2,size=12)

    fig.update_layout(height=460,paper_bgcolor=PLOT_PAP,plot_bgcolor=PLOT_BG,
                      font=dict(color=TEXT2,size=11),showlegend=False,
                      margin=dict(l=44,r=20,t=50,b=36))
    st.plotly_chart(fig,use_container_width=True)

    col1,col2 = st.columns(2)
    with col1:
        sec("BT Social Proximity by Week")
        if 'devices' in weekly.columns:
            x,y = only_data(weekly['devices'])
            if x:
                fig2 = go.Figure(go.Bar(x=[f'W{w}' for w in x],y=y,
                    marker_color=C['mood'],marker_line_color=PLOT_BG,marker_line_width=1))
                pf(fig2,height=230,yaxis=dict(title='Unique BT devices',gridcolor=GRID))
                st.plotly_chart(fig2,use_container_width=True)

    with col2:
        sec("Walking Activity by Week")
        if 'walking' in weekly.columns:
            x,y = only_data(weekly['walking'])
            if x:
                fig3 = go.Figure(go.Bar(x=[f'W{w}' for w in x],y=[v*100 for v in y],
                    marker_color=C['exercise'],marker_line_color=PLOT_BG,marker_line_width=1))
                pf(fig3,height=230,yaxis=dict(title='% time walking',gridcolor=GRID))
                st.plotly_chart(fig3,use_container_width=True)


# ════════════════════════════════════════
# TAB 3 — CORRELATIONS
# ════════════════════════════════════════
with tab3:
    sec("How Variables Relate to Each Other")
    st.caption("Each dot = one student on one day  ·  Dashed line = overall trend")

    cands = [
        ('sleep_hours','stress_avg','Sleep hours','Stress level',C['stress']),
        ('sleep_hours','mood_score_avg','Sleep hours','Mood score',C['mood']),
        ('fraction_walking','stress_avg','Walking fraction','Stress level',C['exercise']),
        ('total_talking_minutes','mood_score_avg','Talking (min)','Mood score',C['social']),
        ('unique_devices_nearby','stress_avg','BT devices','Stress level',C['neutral']),
        ('sleep_rate','stress_avg','Sleep quality','Stress level',C['sleep']),
    ]
    opts = {}
    for xc,yc,xl,yl,col in cands:
        if xc in filtered.columns and yc in filtered.columns:
            opts[f"{xl} vs {yl}"] = (xc,yc,xl,yl,col)

    if opts:
        keys   = list(opts.keys())
        # FIX: put dropdowns in columns so they align properly
        dc1,dc2 = st.columns(2)
        s1 = dc1.selectbox("First scatter plot",  keys, index=0)
        s2 = dc2.selectbox("Second scatter plot", keys, index=min(1,len(keys)-1))

        def mk_scatter(key):
            xc,yc,xl,yl,color = opts[key]
            d = filtered[[xc,yc]].dropna()
            if len(d)<5: return None
            r   = d[xc].corr(d[yc])
            m,b = np.polyfit(d[xc],d[yc],1)
            xs  = np.linspace(d[xc].min(),d[xc].max(),100)
            fig = go.Figure()
            fig.add_scatter(x=d[xc],y=d[yc],mode='markers',
                            marker=dict(color=color,size=5,opacity=0.4))
            fig.add_scatter(x=xs,y=m*xs+b,mode='lines',
                            line=dict(color=TEXT,width=2,dash='dash'))
            fig.add_annotation(text=f"r = {r:.3f}",
                               xref="paper",yref="paper",x=0.05,y=0.95,
                               showarrow=False,font=dict(size=13,color=TEXT),
                               bgcolor=CARD2,bordercolor=BORDER2,borderwidth=1,borderpad=8)
            pf(fig,height=300,showlegend=False,
               xaxis=dict(title=xl,gridcolor=GRID),
               yaxis=dict(title=yl,gridcolor=GRID))
            return fig

        sc1,sc2 = st.columns(2)
        f1 = mk_scatter(s1)
        f2 = mk_scatter(s2)
        if f1: sc1.plotly_chart(f1,use_container_width=True)
        if f2: sc2.plotly_chart(f2,use_container_width=True)

    sec("Full Correlation Matrix")
    cm  = {'stress_avg':'Stress','sleep_hours':'Sleep hrs','sleep_rate':'Sleep qlty',
           'mood_score_avg':'Mood','fraction_walking':'Walking',
           'total_talking_minutes':'Talking','unique_devices_nearby':'BT devices'}
    avl = {k:v for k,v in cm.items() if k in filtered.columns}
    if len(avl)>=3:
        corr = filtered[list(avl.keys())].rename(columns=avl).corr()
        mask = np.triu(np.ones(corr.shape,dtype=bool),k=1)
        corr[mask] = None
        fig_c = px.imshow(corr,color_continuous_scale='RdBu_r',zmin=-1,zmax=1,
                          text_auto='.2f',aspect='auto')
        fig_c.update_traces(textfont_size=11,textfont_color=TEXT)
        pf(fig_c,height=360)
        st.plotly_chart(fig_c,use_container_width=True)


# ════════════════════════════════════════
# TAB 4 — HEATMAP
# ════════════════════════════════════════
with tab4:
    sec("Student × Week Stress Heatmap")
    st.caption("🟢 Green = calm  ·  🔴 Red = high stress  ·  ⬜ White = no data that week")
    if 'stress_avg' in df.columns and 'uid' in df.columns:
        pivot = (df.groupby(['uid','study_week'])['stress_avg']
                 .mean().unstack(fill_value=np.nan).reindex(columns=WEEKS))
        fig_hm = px.imshow(pivot,
            color_continuous_scale=[[0,'#059669'],[.25,'#6EE7B7'],
                                    [.5,'#FCD34D'],[.75,'#F87171'],[1,'#991B1B']],
            zmin=1,zmax=5,text_auto='.1f',aspect='auto',
            labels=dict(x='Study Week',y='Student ID',color='Avg Stress'))
        fig_hm.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS],color=TEXT2)
        fig_hm.update_yaxes(color=TEXT2)
        fig_hm.update_traces(textfont_size=9)
        fig_hm.update_layout(
            height=max(440,len(pivot)*18),
            paper_bgcolor=PLOT_PAP, font=dict(color=TEXT2,size=11),
            margin=dict(l=80,r=20,t=36,b=36))
        st.plotly_chart(fig_hm,use_container_width=True)

        sm_s = df.groupby('uid')['stress_avg'].mean().dropna()
        c1,c2,c3 = st.columns(3)
        c1.metric("Most stressed",  sm_s.idxmax(), f"{sm_s.max():.2f}/5")
        c2.metric("Least stressed", sm_s.idxmin(), f"{sm_s.min():.2f}/5")
        c3.metric("Range",f"{sm_s.max()-sm_s.min():.2f} units")

    with st.expander("📋 Response count per student"):
        q_df = (pd.DataFrame([(u,n,"⚠️ sparse" if sp else "✓ ok")
                               for u,(n,sp) in quality.items()],
                              columns=["Student","Responses","Quality"])
                .sort_values("Responses",ascending=False))
        st.dataframe(q_df,use_container_width=True,hide_index=True)


# ════════════════════════════════════════
# TAB 5 — STUDENT EXPLORER
# ════════════════════════════════════════
with tab5:
    sec("Individual Student Explorer")
    st.caption("🟢 low  ·  🟡 moderate  ·  🔴 high stress  ·  ⚠️ = sparse data")

    all_s   = sorted(df['uid'].unique()) if 'uid' in df.columns else []
    s_means = df.groupby('uid')['stress_avg'].mean().dropna() if 'uid' in df.columns else pd.Series([])

    def slbl(u):
        m  = s_means.get(u)
        sp = quality.get(u,(0,False))[1]
        if m is None: return u
        return f"{'🔴' if m>=3.5 else '🟡' if m>=2.5 else '🟢'} {u}  ({m:.1f}){' ⚠️' if sp else ''}"

    if not all_s:
        st.warning("No student data found.")
    else:
        sel = st.selectbox("Select student", all_s, format_func=slbl)
        s   = df[df['uid']==sel]
        s_n = int(s['stress_avg'].notna().sum())
        s_s = s['stress_avg'].mean()
        s_l = s['sleep_hours'].mean()    if 'sleep_hours'    in s.columns else np.nan
        s_m = s['mood_score_avg'].mean() if 'mood_score_avg' in s.columns else np.nan

        # 4-card mini stats grid
        html4 = (m_html("Avg Stress",   f"{s_s:.2f}/5" if pd.notna(s_s) else "—","",C['stress']) +
                 m_html("Avg Sleep",    f"{s_l:.1f}h"  if pd.notna(s_l) else "—","",C['sleep']) +
                 m_html("Avg Mood",     f"{s_m:.2f}"   if pd.notna(s_m) else "—","",C['mood']) +
                 m_html("Surveys",      str(s_n),"responses",C['neutral']))
        st.markdown(
            f'<div class="m-grid" style="grid-template-columns:repeat(4,1fr)">{html4}</div>',
            unsafe_allow_html=True)

        if s_n < 5:
            warn_badge(f"Only {s_n} responses — treat with caution.")
        if cluster_df is not None and 'uid' in cluster_df.columns:
            row_c = cluster_df[cluster_df['uid']==sel]
            if len(row_c):
                cl = int(row_c.iloc[0]['cluster'])
                st.markdown(
                    f'<div style="display:inline-block;background:{CARD2};border:1px solid {BORDER};'
                    f'border-radius:8px;padding:4px 14px;font-size:0.82rem;color:{ACCENT};margin:4px 0">'
                    f'🔵 Cluster {cl}</div>', unsafe_allow_html=True)

        s_wk = s.groupby('study_week').agg(
            stress=('stress_avg','mean'), sleep=('sleep_hours','mean')).reindex(WEEKS)
        g_wk  = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)

        # Stress vs group
        sec(f"{sel} — Stress vs Group Average")
        fig1 = go.Figure()
        sx,sy = only_data(s_wk['stress'])
        gx,gy = only_data(g_wk)
        if sx:
            fig1.add_scatter(x=sx,y=sy,mode='lines+markers',name=sel,
                             line=dict(color=C['stress'],width=2.5),
                             marker=dict(size=8,color=C['stress'],line=dict(color=PLOT_BG,width=1.5)))
        if gx:
            fig1.add_scatter(x=gx,y=gy,mode='lines',name='Group avg',
                             line=dict(color=MUTED,width=1.5,dash='dash'))
        fig1.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,line_width=0)
        fig1.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
        pf(fig1,height=240,yaxis=dict(range=[0,5.5],title='Stress',gridcolor=GRID),
           legend=dict(orientation='h',y=-0.3,font=dict(color=TEXT2,size=11)))
        st.plotly_chart(fig1,use_container_width=True)

        # Sleep by week
        if 'sleep' in s_wk.columns:
            sec(f"{sel} — Sleep by Week")
            sv = s_wk['sleep'].values
            sc = [C['sleep'] if pd.notna(v) and v>=7
                  else C['social'] if pd.notna(v) and v>=5
                  else C['stress'] if pd.notna(v)
                  else BORDER for v in sv]
            fig2 = go.Figure(go.Bar(x=[f'W{w}' for w in WEEKS],y=sv,
                                    marker_color=sc,marker_line_color=PLOT_BG,marker_line_width=1))
            fig2.add_hline(y=7,line_dash='dash',line_color=C['sleep'],
                           annotation_text='7h recommended',
                           annotation_position='top right',annotation_font_color=TEXT2)
            pf(fig2,height=220,yaxis=dict(range=[0,14],title='Hours',gridcolor=GRID))
            st.plotly_chart(fig2,use_container_width=True)

        # Actual vs predicted
        if pred_df is not None and 'uid' in pred_df.columns:
            sp_d = pred_df[pred_df['uid']==sel]
            if len(sp_d) and 'stress_predicted' in sp_d.columns:
                sec(f"{sel} — Actual vs Predicted Stress")
                sp_w = sp_d.groupby('study_week').agg(
                    actual=('stress_avg','mean'),
                    predicted=('stress_predicted','mean')).reindex(WEEKS)
                fig3 = go.Figure()
                ax,ay = only_data(sp_w['actual'])
                px2,py2 = only_data(sp_w['predicted'])
                if ax: fig3.add_scatter(x=ax,y=ay,mode='lines+markers',name='Actual',
                                        line=dict(color=C['stress'],width=2))
                if px2: fig3.add_scatter(x=px2,y=py2,mode='lines+markers',name='Predicted',
                                         line=dict(color=C['ml'],width=2,dash='dot'))
                fig3.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
                pf(fig3,height=220,yaxis=dict(range=[0,5.5],title='Stress',gridcolor=GRID),
                   legend=dict(orientation='h',y=-0.3,font=dict(color=TEXT2,size=11)))
                st.plotly_chart(fig3,use_container_width=True)


# ════════════════════════════════════════
# TAB 6 — COMPARE
# ════════════════════════════════════════
with tab6:
    sec("Compare Two Students")
    all_s = sorted(df['uid'].unique()) if 'uid' in df.columns else []
    if len(all_s) < 2:
        st.info("Not enough data to compare.")
    else:
        # FIX: dropdowns in same row, properly aligned
        ca,cb = st.columns(2)
        sa = ca.selectbox("Student A", all_s, index=0,                         key="csa")
        sb = cb.selectbox("Student B", all_s, index=min(1,len(all_s)-1),       key="csb")

        da,db = df[df['uid']==sa], df[df['uid']==sb]

        # Comparison table
        rows = []
        for lbl,col,unit,pct in [
            ("Avg Stress",'stress_avg',"",False),
            ("Avg Sleep",'sleep_hours',"h",False),
            ("Avg Mood",'mood_score_avg',"",False),
            ("Walking %",'fraction_walking',"%",True),
            ("Talking",'total_talking_minutes',"m",False),
        ]:
            if col not in df.columns: continue
            va,vb = da[col].mean(), db[col].mean()
            def fmt(v,u,p):
                return (f"{v*100:.1f}{u}" if p and pd.notna(v) else
                        f"{v:.2f}{u}"     if pd.notna(v) else "—")
            rows.append({"Metric":lbl, sa:fmt(va,unit,pct), sb:fmt(vb,unit,pct)})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Side by side stress charts
        st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        for col_o,student,data,color in [
            (c1,sa,da,C['stress']),
            (c2,sb,db,C['mood']),
        ]:
            with col_o:
                sec(student)
                sw = data.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)
                ga = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)
                fig = go.Figure()
                sx,sy = only_data(sw)
                gx,gy = only_data(ga)
                if sx: fig.add_scatter(x=sx,y=sy,mode='lines+markers',name=student,
                                       line=dict(color=color,width=2.5),
                                       marker=dict(size=7,color=color,line=dict(color=PLOT_BG,width=1.5)))
                if gx: fig.add_scatter(x=gx,y=gy,mode='lines',name='Group avg',
                                       line=dict(color=MUTED,width=1.5,dash='dash'))
                fig.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,line_width=0)
                fig.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
                pf(fig,height=250,yaxis=dict(range=[0,5.5],gridcolor=GRID),
                   legend=dict(orientation='h',y=-0.3,font=dict(color=TEXT2,size=11)))
                st.plotly_chart(fig,use_container_width=True)


# ════════════════════════════════════════
# TAB 7 — ML
# ════════════════════════════════════════
with tab7:
    sec("Machine Learning Results")

    # FIX: use if/else instead of st.stop() inside a tab
    if all(f is None for f in [pred_df,cluster_df,fi_df,perf_df]):
        st.markdown(
            f'<div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;'
            f'padding:2rem;text-align:center;color:{MUTED}">'
            f'Upload the 4 ML CSV files to the <code>data/</code> folder to unlock this tab.<br>'
            f'<small>ml_predictions · ml_clusters · ml_feature_importance · ml_performance</small>'
            f'</div>', unsafe_allow_html=True)
    else:
        # Model performance
        if perf_df is not None and 'task' in perf_df.columns:
            sec("Model Performance")
            c1,c2 = st.columns(2)
            with c1:
                st.caption("Regression — lower MAE = better")
                reg = perf_df[(perf_df['task']=='regression')&(perf_df['metric']=='MAE')]
                if not reg.empty:
                    reg = reg.sort_values('value')
                    fig = go.Figure(go.Bar(
                        x=reg['model'],y=reg['value'],
                        marker_color=[ACCENT if i==0 else BORDER2 for i in range(len(reg))],
                        text=[f"{v:.3f}" for v in reg['value']],textposition='outside'))
                    pf(fig,height=250,showlegend=False,yaxis=dict(title='MAE',gridcolor=GRID))
                    st.plotly_chart(fig,use_container_width=True)
                    st.success(f"✅ Best: **{reg.iloc[0]['model']}** (MAE={reg.iloc[0]['value']:.3f})")

            with c2:
                st.caption("Classification — higher AUC = better")
                cls = perf_df[(perf_df['task']=='classification')&(perf_df['metric']=='AUC')]
                if not cls.empty:
                    cls = cls.sort_values('value',ascending=False)
                    fig = go.Figure(go.Bar(
                        x=cls['model'],y=cls['value'],
                        marker_color=[ACCENT if i==0 else BORDER2 for i in range(len(cls))],
                        text=[f"{v:.3f}" for v in cls['value']],textposition='outside'))
                    fig.add_hline(y=0.5,line_dash='dash',line_color=MUTED,
                                  annotation_text='Random (0.5)',annotation_font_color=MUTED)
                    pf(fig,height=250,showlegend=False,
                       yaxis=dict(title='AUC',range=[0,1.1],gridcolor=GRID))
                    st.plotly_chart(fig,use_container_width=True)
                    st.success(f"✅ Best: **{cls.iloc[0]['model']}** (AUC={cls.iloc[0]['value']:.3f})")

        # Predictions
        if pred_df is not None and all(c in pred_df.columns for c in ['stress_avg','stress_predicted']):
            sec("Predicted vs Actual Stress")
            c1,c2 = st.columns(2)
            with c1:
                d   = pred_df[['stress_avg','stress_predicted']].dropna()
                mae = (d['stress_avg']-d['stress_predicted']).abs().mean()
                fig = go.Figure()
                fig.add_scatter(x=d['stress_avg'],y=d['stress_predicted'],mode='markers',
                                marker=dict(color=ACCENT,size=5,opacity=0.35))
                fig.add_scatter(x=[1,5],y=[1,5],mode='lines',
                                line=dict(color=TEXT2,width=1.5,dash='dash'))
                fig.add_annotation(text=f"MAE = {mae:.3f}",xref="paper",yref="paper",
                                   x=0.05,y=0.95,showarrow=False,
                                   font=dict(size=13,color=TEXT),
                                   bgcolor=CARD2,bordercolor=BORDER2,borderwidth=1,borderpad=8)
                pf(fig,height=280,showlegend=False,
                   xaxis=dict(title='Actual stress',range=[.5,5.5],gridcolor=GRID),
                   yaxis=dict(title='Predicted',range=[.5,5.5],gridcolor=GRID))
                st.plotly_chart(fig,use_container_width=True)
            with c2:
                if 'high_stress_prob' in pred_df.columns and 'study_week' in pred_df.columns:
                    pw = pred_df.groupby('study_week')['high_stress_prob'].mean().reindex(WEEKS)
                    px3,py3 = only_data(pw)
                    if px3:
                        fig = go.Figure(go.Bar(
                            x=[f'W{w}' for w in px3],y=py3,
                            marker_color=[C['stress'] if v>=.4 else C['social'] if v>=.25
                                          else C['sleep'] for v in py3],
                            text=[f"{v:.0%}" for v in py3],textposition='outside'))
                        fig.add_hline(y=0.25,line_dash='dash',line_color=C['social'],
                                      annotation_text='25% risk',annotation_font_color=TEXT2)
                        pf(fig,height=280,
                           yaxis=dict(title='High-stress prob.',tickformat=',.0%',range=[0,.85],gridcolor=GRID))
                        st.plotly_chart(fig,use_container_width=True)

        # Feature importance
        if fi_df is not None:
            sec("Feature Importance")
            lc = 'label' if 'label' in fi_df.columns else 'feature'
            if lc in fi_df.columns and 'importance' in fi_df.columns:
                fi_s = fi_df.sort_values('importance',ascending=True).tail(10)
                bcols = [C['sleep'] if 'sleep' in str(f).lower()
                         else C['exercise'] if 'walk' in str(f).lower()
                         else C['social'] if 'talk' in str(f).lower()
                         else C['mood'] if any(k in str(f).lower() for k in ['device','bt'])
                         else ACCENT for f in fi_s[lc]]
                fig = go.Figure(go.Bar(
                    x=fi_s['importance'],y=fi_s[lc],orientation='h',
                    marker_color=bcols,
                    text=[f"{v:.4f}" for v in fi_s['importance']],textposition='outside'))
                pf(fig,height=350,showlegend=False,
                   xaxis=dict(title='Importance score',gridcolor=GRID))
                st.plotly_chart(fig,use_container_width=True)
                top3 = fi_df.sort_values('importance',ascending=False).head(3)
                st.markdown("**Top 3 predictors of stress:**")
                for _,row in top3.iterrows():
                    st.markdown(f"- **{row[lc]}** — {row['importance']:.4f}")

        # Clusters
        if cluster_df is not None and 'cluster' in cluster_df.columns:
            sec("Student Behaviour Clusters")
            cts = cluster_df['cluster'].value_counts().sort_index()
            c1,c2 = st.columns(2)
            with c1:
                fig = go.Figure(go.Pie(
                    labels=[f"Cluster {i}" for i in cts.index],values=cts.values,
                    marker_colors=[C['stress'],C['sleep'],C['mood'],C['exercise']][:len(cts)],
                    hole=0.42,textinfo='label+value',textfont_color=TEXT))
                pf(fig,height=260,showlegend=False)
                st.plotly_chart(fig,use_container_width=True)
            with c2:
                if 'uid' in df.columns:
                    df_c = df.merge(cluster_df[['uid','cluster']],on='uid',how='left')
                    pc   = [c for c in ['stress_avg','sleep_hours','fraction_walking',
                                        'total_talking_minutes','unique_devices_nearby']
                            if c in df_c.columns]
                    if pc:
                        prof = df_c.groupby('cluster')[pc].mean()
                        pn   = (prof-prof.min())/(prof.max()-prof.min()+1e-9)
                        pn   = pn.rename(columns={
                            'stress_avg':'Stress','sleep_hours':'Sleep',
                            'fraction_walking':'Walking',
                            'total_talking_minutes':'Talking',
                            'unique_devices_nearby':'BT devices'})
                        fig = go.Figure()
                        clr = [C['stress'],C['sleep'],C['mood'],C['exercise']]
                        for i,(idx,row) in enumerate(pn.iterrows()):
                            fig.add_bar(name=f"Cluster {idx}",x=row.index.tolist(),
                                        y=row.values,marker_color=clr[i%len(clr)])
                        pf(fig,height=260,barmode='group',
                           yaxis=dict(title='Score (0–1)',range=[0,1.2],gridcolor=GRID),
                           legend=dict(orientation='h',y=-0.25,font=dict(color=TEXT2,size=11)))
                        st.plotly_chart(fig,use_container_width=True)

            cl_cols = st.columns(min(cluster_df['cluster'].nunique(),3))
            for col_o,(cl,grp) in zip(cl_cols,cluster_df.groupby('cluster')):
                with col_o:
                    st.markdown(f"**Cluster {cl}** ({len(grp)} students)")
                    st.write(", ".join(sorted(grp['uid'].tolist())))
