# ─────────────────────────────────────────────────────────────────────────────
# StudentLife Visual Analytics Dashboard — Enhanced Version
# Dissertation: Visual Analytics for Digital Health
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
    initial_sidebar_state="expanded"
)

# ── Custom CSS — dark glassmorphism design ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

* { font-family: 'Inter', sans-serif; }

[data-testid="stAppViewContainer"] { background: linear-gradient(135deg,#0a0a0f 0%,#0f0f1a 50%,#0a0f0a 100%); }
[data-testid="stSidebar"]          { background: rgba(15,15,25,0.95); border-right:1px solid #1e1e2e; }
[data-testid="stHeader"]           { background: transparent; }
.block-container                   { padding-top:1rem; }

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, rgba(30,30,50,0.8), rgba(20,20,35,0.9));
    border: 1px solid rgba(124,106,247,0.2);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: all 0.2s ease;
    margin-bottom: 0.5rem;
}
.metric-card:hover { border-color: rgba(124,106,247,0.5); transform: translateY(-2px); }
.metric-label { font-size: 11px; font-weight: 500; color: #6b6b9a;
                text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; }
.metric-value { font-size: 28px; font-weight: 600; color: #e8e8ff; line-height: 1; }
.metric-sub   { font-size: 11px; color: #4a4a7a; margin-top: 0.3rem; }

/* Finding cards */
.find-card {
    background: rgba(20,20,35,0.8);
    border-left: 3px solid #7C6AF7;
    border-radius: 0 12px 12px 0;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
    backdrop-filter: blur(8px);
}
.find-card.red   { border-left-color: #E05C5C; }
.find-card.teal  { border-left-color: #4ECDC4; }
.find-card.amber { border-left-color: #F0A050; }
.find-title { font-size: 13px; font-weight: 600; color: #c8c8ff; margin-bottom: 3px; }
.find-text  { font-size: 12px; color: #8888aa; line-height: 1.5; }

/* Story box */
.story-box {
    background: rgba(124,106,247,0.08);
    border: 1px solid rgba(124,106,247,0.2);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin: 0.5rem 0;
}
.story-week { font-size: 12px; color: #7C6AF7; font-weight: 600;
              text-transform: uppercase; letter-spacing: 0.06em; }
.story-text { font-size: 13px; color: #c8c8e8; line-height: 1.7; margin-top: 0.3rem; }

/* Risk gauge label */
.risk-label {
    text-align: center;
    font-size: 13px;
    color: #8888aa;
    margin-top: -0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── Colours ───────────────────────────────────────────────────────────────────
C = {
    'stress':   '#E05C5C',
    'sleep':    '#4ECDC4',
    'mood':     '#7C6AF7',
    'exercise': '#50C878',
    'social':   '#F0A050',
    'neutral':  '#8888AA',
    'ml':       '#FF6B9D',
}

LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(15,15,25,0.6)',
    font=dict(color='#c8c8e8', family='Inter, sans-serif', size=12),
    margin=dict(l=40, r=20, t=40, b=40),
)

DAY_NAMES = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
WEEKS     = list(range(1, 11))
DATA_DIR  = 'data'

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def safe_mean(df, col):
    if col in df.columns and df[col].notna().any():
        return df[col].mean()
    return None

def apply_layout(fig, height=300, **extra):
    fig.update_layout(**LAYOUT, height=height, **extra)
    fig.update_xaxes(gridcolor='#1e1e2e', linecolor='#1e1e2e')
    fig.update_yaxes(gridcolor='#1e1e2e', linecolor='#1e1e2e')
    return fig

def metric_card(label, value, sub="", color="#7C6AF7"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{color}">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def finding_card(icon, title, text, style=""):
    st.markdown(f"""
    <div class="find-card {style}">
        <div class="find-title">{icon} {title}</div>
        <div class="find-text">{text}</div>
    </div>""", unsafe_allow_html=True)

def story_box(week_label, text):
    st.markdown(f"""
    <div class="story-box">
        <div class="story-week">{week_label}</div>
        <div class="story-text">{text}</div>
    </div>""", unsafe_allow_html=True)

def quality_check(df):
    counts = df.groupby('uid')['stress_avg'].count()
    return {uid: (int(n), n < 5) for uid, n in counts.items()}

# ─────────────────────────────────────────────────────────────────────────────
# GAUGE CHART — Burnout Risk
# ─────────────────────────────────────────────────────────────────────────────

def burnout_gauge(stress, sleep, mood=None, title="Burnout Risk"):
    """Create a speedometer gauge showing overall wellbeing risk."""
    # Composite risk score 0-100
    # High stress = bad, low sleep = bad, low mood = bad
    risk = 0
    n    = 0
    if stress is not None and not np.isnan(stress):
        risk += (stress - 1) / 4 * 100   # 1→0, 5→100
        n += 1
    if sleep is not None and not np.isnan(sleep):
        sleep_risk = max(0, (8 - sleep) / 8 * 100)  # 8h→0, 0h→100
        risk += sleep_risk
        n += 1
    if mood is not None and not np.isnan(mood):
        mood_risk = (-mood + 4) / 8 * 100  # +4→0, -4→100
        risk += mood_risk
        n += 1
    risk = risk / n if n > 0 else 50

    if   risk < 30:  color, label = "#4ECDC4", "LOW RISK"
    elif risk < 55:  color, label = "#F0A050", "MODERATE"
    elif risk < 75:  color, label = "#E05C5C", "HIGH RISK"
    else:            color, label = "#8B0000", "CRITICAL"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(risk, 1),
        title=dict(text=f"<b>{title}</b><br><span style='font-size:14px;color:{color}'>{label}</span>",
                   font=dict(size=14, color='#c8c8e8')),
        number=dict(suffix="%", font=dict(size=28, color=color)),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor='#2a2a3e',
                      tickvals=[0,25,50,75,100],
                      ticktext=['0','25','50','75','100'],
                      tickfont=dict(color='#6b6b9a', size=10)),
            bar=dict(color=color, thickness=0.25),
            bgcolor='rgba(0,0,0,0)',
            borderwidth=0,
            steps=[
                dict(range=[0,30],  color='rgba(78,205,196,0.12)'),
                dict(range=[30,55], color='rgba(240,160,80,0.12)'),
                dict(range=[55,75], color='rgba(224,92,92,0.12)'),
                dict(range=[75,100],color='rgba(139,0,0,0.15)'),
            ],
            threshold=dict(
                line=dict(color=color, width=3),
                thickness=0.85, value=risk)
        )
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        height=220,
        margin=dict(l=20, r=20, t=60, b=10),
        font=dict(color='#c8c8e8')
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# RADAR CHART — Student Profile
# ─────────────────────────────────────────────────────────────────────────────

def radar_chart(values_dict, title="Student Profile", color="#7C6AF7"):
    """Spider web chart showing a student across multiple dimensions."""
    categories = list(values_dict.keys())
    values     = list(values_dict.values())
    values_closed = values + [values[0]]
    cats_closed   = categories + [categories[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=cats_closed,
        fill='toself',
        fillcolor=color.replace('#', 'rgba(') + ',0.15)' if '#' in color else color,
        line=dict(color=color, width=2),
        marker=dict(size=6, color=color),
        name=title
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(15,15,25,0.5)',
            radialaxis=dict(
                visible=True, range=[0, 1],
                tickvals=[0.25,0.5,0.75,1.0],
                ticktext=['25%','50%','75%','100%'],
                tickfont=dict(size=9, color='#6b6b9a'),
                gridcolor='#1e1e2e', linecolor='#1e1e2e'
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color='#c8c8e8'),
                gridcolor='#1e1e2e', linecolor='#1e1e2e'
            )
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=60, r=60, t=40, b=40),
        showlegend=False,
        title=dict(text=title, font=dict(color='#c8c8e8', size=13), x=0.5)
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# WEEK STORY — auto-generates narrative from data
# ─────────────────────────────────────────────────────────────────────────────

def generate_week_story(weekly_df, week):
    """Generate a plain-English description of what happened in a given week."""
    if week not in weekly_df.index:
        return "No data available for this week."

    row = weekly_df.loc[week]
    parts = []

    stress = row.get('stress', np.nan)
    sleep  = row.get('sleep',  np.nan)
    mood   = row.get('mood',   np.nan)
    talk   = row.get('talking', np.nan)

    overall_stress = weekly_df['stress'].mean() if 'stress' in weekly_df else np.nan

    # Stress narrative
    if not np.isnan(stress):
        if week == 10:
            parts.append(f"Finals week hit hard — stress spiked to {stress:.2f}/5, the highest of the term.")
        elif stress > overall_stress + 0.3:
            parts.append(f"A tough week: stress ({stress:.2f}/5) was noticeably above the term average.")
        elif stress < overall_stress - 0.3:
            parts.append(f"A calmer week than usual: stress ({stress:.2f}/5) was below the term average.")
        else:
            parts.append(f"Stress ({stress:.2f}/5) was close to the term average this week.")

    # Sleep narrative
    if not np.isnan(sleep):
        if sleep >= 8:
            parts.append(f"Students slept well ({sleep:.1f}h on average) — possibly a study break or reading period.")
        elif sleep < 6:
            parts.append(f"Sleep was poor this week ({sleep:.1f}h) — students were clearly under pressure.")
        else:
            parts.append(f"Sleep averaged {sleep:.1f}h — below the recommended 7 hours for many nights.")

    # Mood narrative
    if not np.isnan(mood):
        if mood > 0.5:
            parts.append(f"Mood was positive (score {mood:.2f}) — students were feeling relatively good.")
        elif mood < -0.5:
            parts.append(f"Mood was low (score {mood:.2f}) — many students were feeling down.")
        else:
            parts.append(f"Mood was roughly neutral (score {mood:.2f}) this week.")

    # Talking narrative
    if not np.isnan(talk):
        avg_talk = weekly_df['talking'].mean() if 'talking' in weekly_df else talk
        if talk < avg_talk * 0.7:
            parts.append(f"Social conversations dropped ({talk:.0f} min/day) — students may have been studying alone more.")
        elif talk > avg_talk * 1.3:
            parts.append(f"Students were more socially active than usual ({talk:.0f} min/day of conversation).")

    return " ".join(parts) if parts else "Not enough data to describe this week."

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def load_master():
    path = os.path.join(DATA_DIR, 'daily_master.csv')
    df   = pd.read_csv(path)
    if 'student_id' in df.columns:
        df.rename(columns={'student_id':'uid'}, inplace=True)
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
        df.rename(columns={'student_id':'uid'}, inplace=True)
    return df

# Check data exists
if not os.path.exists(os.path.join(DATA_DIR, 'daily_master.csv')):
    st.title("🎓 StudentLife Dashboard")
    st.error("Data files not found. Upload CSVs to the `data/` folder in your GitHub repository.")
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
    st.markdown("""
    <div style='text-align:center;padding:1rem 0'>
        <div style='font-size:32px'>🎓</div>
        <div style='font-size:17px;font-weight:600;color:#c8c8ff'>StudentLife</div>
        <div style='font-size:11px;color:#6b6b9a;margin-top:4px'>Visual Analytics for Digital Health</div>
        <div style='font-size:11px;color:#4a4a7a;margin-top:2px'>Rohith Elanchezhian · Newcastle University</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("**Filters**")

    week_filter = st.selectbox("Study week",
        ["All weeks"] + [f"Week {w}" for w in WEEKS])
    day_filter = st.selectbox("Day type",
        ["All days","Weekdays only","Weekends only"])

    st.divider()
    st.markdown("**Data Status**")
    st.success("✅ daily_master.csv")
    for fname, label in [
        ('ml_predictions.csv',      'ml_predictions'),
        ('ml_clusters.csv',         'ml_clusters'),
        ('ml_feature_importance.csv','ml_feature_importance'),
        ('ml_performance.csv',      'ml_performance'),
    ]:
        loaded = load_ml(fname) is not None
        if loaded: st.success(f"✅ {label}")
        else:      st.caption(f"⬜ {label} not loaded")

    st.divider()
    st.caption("📊 49 students · 10 weeks · Spring 2013\nDartmouth College, USA")

# ─────────────────────────────────────────────────────────────────────────────
# FILTER
# ─────────────────────────────────────────────────────────────────────────────

filtered = df.copy()
if week_filter != "All weeks":
    wk = int(week_filter.split(" ")[1])
    filtered = filtered[filtered['study_week'] == wk]
if day_filter == "Weekdays only":
    filtered = filtered[filtered['is_weekend'] == False]
elif day_filter == "Weekends only":
    filtered = filtered[filtered['is_weekend'] == True]

quality = quality_check(df)
sparse  = [u for u,(n,sp) in quality.items() if sp]

# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div style='padding:1rem 0 0.5rem'>
    <h1 style='font-size:28px;font-weight:700;color:#e8e8ff;margin:0'>
        StudentLife Visual Analytics Dashboard
    </h1>
    <p style='color:#6b6b9a;font-size:13px;margin:4px 0 0'>
        Exploring digital health patterns in 49 university students across a 10-week term
    </p>
</div>
""", unsafe_allow_html=True)

st.caption(
    f"Showing **{len(filtered):,} rows** · "
    f"**{filtered['uid'].nunique()} students** · "
    f"{week_filter} | {day_filter}"
)
if sparse:
    st.warning(f"⚠️ {len(sparse)} students have sparse data (<5 responses) — treat their averages with caution.")

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────

tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
    "📊 Overview",
    "📈 Weekly Trends",
    "🔗 Correlations",
    "🌡️ Stress Heatmap",
    "👤 Student Explorer",
    "⚖️ Compare Students",
    "🤖 ML Predictions",
])


# ═══════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════
with tab1:

    stress_mean = safe_mean(filtered, 'stress_avg')
    sleep_mean  = safe_mean(filtered, 'sleep_hours')
    mood_mean   = safe_mean(filtered, 'mood_score_avg')
    talk_mean   = safe_mean(filtered, 'total_talking_minutes')
    high_pct    = (filtered['high_stress'].mean()*100
                   if 'high_stress' in filtered.columns else None)
    dep_valid   = filtered['sleep_hours'].dropna() if 'sleep_hours' in filtered.columns else pd.Series([])
    dep_pct     = ((dep_valid < 7).mean()*100) if len(dep_valid) else None

    # ── Finding cards ──
    st.markdown("### 📌 Key Findings")
    fc1, fc2, fc3 = st.columns(3)

    with fc1:
        if stress_mean and high_pct:
            finding_card("😟","Stress Level",
                f"Average is <b>{stress_mean:.2f}/5</b> and <b>{high_pct:.0f}%</b> "
                f"of days were high stress (level 4–5).","red")
    with fc2:
        if dep_pct and sleep_mean:
            finding_card("😴","Sleep Quality",
                f"Average <b>{sleep_mean:.1f}h/night</b> but <b>{dep_pct:.0f}%</b> "
                f"of nights fell below the recommended 7 hours.","teal")
    with fc3:
        if 'stress_avg' in df.columns and 'is_weekend' in df.columns:
            wd = df[df['is_weekend']==False]['stress_avg'].mean()
            we = df[df['is_weekend']==True]['stress_avg'].mean()
            if not (np.isnan(wd) or np.isnan(we)):
                d = "higher" if we > wd else "lower"
                finding_card("😮","Surprising Finding",
                    f"Weekend stress (<b>{we:.2f}</b>) is <b>{d}</b> than weekday "
                    f"(<b>{wd:.2f}</b>) — unstructured time increases anxiety.","amber")

    st.divider()

    # ── Custom metric cards ──
    cols = st.columns(6)
    data = [
        ("Avg Stress",      f"{stress_mean:.2f}/5" if stress_mean else "—", "out of 5",  C['stress']),
        ("High Stress Days",f"{high_pct:.0f}%"     if high_pct    else "—", "level 4–5", C['social']),
        ("Avg Sleep",       f"{sleep_mean:.1f}h"   if sleep_mean  else "—", "per night",  C['sleep']),
        ("Under 7h Nights", f"{dep_pct:.0f}%"      if dep_pct     else "—", "deprived",   C['mood']),
        ("Avg Mood Score",  f"{mood_mean:.2f}"      if mood_mean   else "—", "−4 to +4",   C['exercise']),
        ("Avg Talking",     f"{talk_mean:.0f}m"     if talk_mean   else "—", "per day",    C['neutral']),
    ]
    for col, (label, value, sub, color) in zip(cols, data):
        with col:
            metric_card(label, value, sub, color)

    st.divider()

    # ── Overall burnout gauge ──
    st.markdown("#### 🎯 Overall Cohort Risk Level")
    gc1, gc2, gc3 = st.columns([1,1,2])
    with gc1:
        fig = burnout_gauge(stress_mean, sleep_mean, mood_mean, "Cohort Burnout Risk")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<p class="risk-label">Based on stress + sleep + mood</p>',
                    unsafe_allow_html=True)
    with gc2:
        # Finals week gauge
        w10 = df[df['study_week']==10]
        w10s = w10['stress_avg'].mean() if 'stress_avg' in w10.columns else None
        w10l = w10['sleep_hours'].mean() if 'sleep_hours' in w10.columns else None
        w10m = w10['mood_score_avg'].mean() if 'mood_score_avg' in w10.columns else None
        fig2 = burnout_gauge(w10s, w10l, w10m, "Finals Week (W10) Risk")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('<p class="risk-label">Week 10 only</p>', unsafe_allow_html=True)
    with gc3:
        st.markdown("#### How the risk score is calculated")
        st.markdown("""
        The burnout risk gauge combines three signals:

        - 🔴 **Stress** — higher reported stress → higher risk
        - 😴 **Sleep** — fewer hours slept → higher risk
        - 😟 **Mood** — more negative mood score → higher risk

        Each signal is normalised to 0–100% and averaged.

        | Score | Risk Level |
        |-------|-----------|
        | 0–30 | 🟢 Low |
        | 30–55 | 🟡 Moderate |
        | 55–75 | 🔴 High |
        | 75–100 | 🚨 Critical |
        """)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Stress Level Distribution")
        if 'stress_avg' in filtered.columns:
            v      = filtered['stress_avg'].dropna()
            labels = ['1 Not stressed','2','3 Moderate','4','5 Very stressed']
            counts = pd.cut(v, bins=[0.5,1.5,2.5,3.5,4.5,5.5],
                            labels=labels).value_counts().sort_index()
            fig = go.Figure(go.Bar(
                x=counts.index.tolist(), y=counts.values,
                marker_color=[C['sleep'],C['sleep'],C['neutral'],C['stress'],C['stress']],
                text=[f"{val/len(v)*100:.0f}%" for val in counts.values],
                textposition='outside'
            ))
            apply_layout(fig, height=260, showlegend=False,
                         yaxis=dict(title='Responses',gridcolor='#1e1e2e'))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Sleep Duration Categories")
        if 'sleep_hours' in filtered.columns:
            v    = filtered['sleep_hours'].dropna()
            cats = pd.cut(v, bins=[-np.inf,5,7,9,np.inf],
                          labels=['Under 5h','5–7h','7–9h','Over 9h'])
            cc   = cats.value_counts().sort_index()
            fig  = go.Figure(go.Pie(
                labels=cc.index.tolist(), values=cc.values,
                marker_colors=[C['stress'],C['social'],C['sleep'],C['mood']],
                hole=0.45, textinfo='label+percent', textfont_size=11
            ))
            apply_layout(fig, height=260, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 2 — WEEKLY TRENDS + WEEK STORY
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### Key Variables Across the 10-Week Term")

    weekly = df.groupby('study_week').agg(
        stress  =('stress_avg','mean'),
        sleep   =('sleep_hours','mean'),
        mood    =('mood_score_avg','mean'),
        talking =('total_talking_minutes','mean'),
        walking =('fraction_walking','mean'),
        devices =('unique_devices_nearby','mean'),
    ).reindex(WEEKS)

    # 4-panel trend chart
    fig = make_subplots(rows=2, cols=2,
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
        fig.add_scatter(x=WEEKS, y=y, mode='lines+markers',
                        line=dict(color=color,width=2.5),
                        marker=dict(size=7,color=color), row=row, col=col)
        fig.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,
                      line_width=0, row=row, col=col)
        fig.update_yaxes(range=yr,gridcolor='#1e1e2e',row=row,col=col)
        fig.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS],
                         gridcolor='#1e1e2e',row=row,col=col)

    fig.update_layout(height=480, paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(15,15,25,0.6)',
                      font=dict(color='#c8c8e8',size=11), showlegend=False,
                      margin=dict(l=40,r=20,t=60,b=40))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("🔴 shaded = finals week (Week 10)")

    # ── Week Story Panel ──────────────────────────────────────
    st.markdown("#### 📖 Week-by-Week Story")
    st.caption("Auto-generated description of what the data shows each week")

    story_cols = st.columns(2)
    for i, week in enumerate(WEEKS):
        col = story_cols[i % 2]
        with col:
            story = generate_week_story(weekly, week)
            label = f"Week {week}" + (" — Finals 🎓" if week==10 else
                                       " — Mid-term break? 😌" if week==6 else "")
            story_box(label, story)


# ═══════════════════════════════════════════════════════════════
# TAB 3 — CORRELATIONS
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### How Variables Relate to Each Other")
    st.caption("Each dot = one student on one day  |  Dashed line = overall trend")

    candidates = [
        ('sleep_hours','stress_avg','Sleep hours','Stress level',C['stress']),
        ('sleep_hours','mood_score_avg','Sleep hours','Mood score',C['mood']),
        ('fraction_walking','stress_avg','Walking fraction','Stress level',C['exercise']),
        ('total_talking_minutes','mood_score_avg','Talking (min)','Mood score',C['social']),
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
            r    = d[xc].corr(d[yc])
            m,b  = np.polyfit(d[xc], d[yc], 1)
            xs   = np.linspace(d[xc].min(), d[xc].max(), 100)
            fig  = go.Figure()
            fig.add_scatter(x=d[xc], y=d[yc], mode='markers',
                            marker=dict(color=color,size=5,opacity=0.35))
            fig.add_scatter(x=xs, y=m*xs+b, mode='lines',
                            line=dict(color='white',width=2,dash='dash'))
            sig = "** p<.05" if abs(r)>0.15 and len(d)>50 else ""
            fig.add_annotation(text=f"r = {r:.3f} {sig}",
                               xref="paper",yref="paper",x=0.05,y=0.95,
                               showarrow=False,font=dict(size=13,color='#c8c8e8'),
                               bgcolor='rgba(30,30,46,0.8)',
                               bordercolor='#2a2a3e',borderwidth=1,borderpad=8)
            apply_layout(fig, height=320, showlegend=False,
                         xaxis=dict(title=xl,gridcolor='#1e1e2e'),
                         yaxis=dict(title=yl,gridcolor='#1e1e2e'))
            return fig

        c1,c2 = st.columns(2)
        f1,f2 = make_scatter(s1), make_scatter(s2)
        if f1: c1.plotly_chart(f1, use_container_width=True)
        if f2: c2.plotly_chart(f2, use_container_width=True)

    # Correlation heatmap
    st.markdown("#### Full Correlation Matrix")
    corr_map = {'stress_avg':'Stress','sleep_hours':'Sleep hrs',
                'sleep_rate':'Sleep quality','mood_score_avg':'Mood',
                'fraction_walking':'Walking','total_talking_minutes':'Talking',
                'unique_devices_nearby':'BT devices'}
    avail = {k:v for k,v in corr_map.items() if k in filtered.columns}
    if len(avail)>=3:
        corr_df = filtered[list(avail.keys())].rename(columns=avail).corr()
        mask = np.triu(np.ones(corr_df.shape,dtype=bool),k=1)
        corr_df[mask] = None
        fig_c = px.imshow(corr_df,color_continuous_scale='RdBu_r',
                          zmin=-1,zmax=1,text_auto='.2f',aspect='auto')
        fig_c.update_traces(textfont_size=11)
        apply_layout(fig_c, height=360)
        st.plotly_chart(fig_c, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 4 — STRESS HEATMAP
# ═══════════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### Student × Week Stress Heatmap")
    st.caption("🟢 Green = calm  |  🔴 Red = high stress  |  ⬜ White = no data")

    if 'stress_avg' in df.columns:
        pivot = (df.groupby(['uid','study_week'])['stress_avg']
                 .mean().unstack(fill_value=np.nan).reindex(columns=WEEKS))

        fig_hm = px.imshow(pivot,
            color_continuous_scale=[
                [0.0,'#4ECDC4'],[0.25,'#A8E6CE'],
                [0.5,'#F0A050'],[0.75,'#E05C5C'],[1.0,'#8B0000']],
            zmin=1,zmax=5,text_auto='.1f',aspect='auto',
            labels=dict(x='Study Week',y='Student ID',color='Avg Stress'))
        fig_hm.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
        fig_hm.update_traces(textfont_size=9)
        fig_hm.update_layout(
            height=max(420,len(pivot)*18),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#c8c8e8',size=11),
            margin=dict(l=80,r=20,t=40,b=40))
        st.plotly_chart(fig_hm, use_container_width=True)

        sm = df.groupby('uid')['stress_avg'].mean().dropna()
        c1,c2,c3 = st.columns(3)
        c1.metric("Most stressed",  sm.idxmax(), f"{sm.max():.2f}/5")
        c2.metric("Least stressed", sm.idxmin(), f"{sm.min():.2f}/5")
        c3.metric("Range across students", f"{sm.max()-sm.min():.2f} units")

    with st.expander("📋 Response count per student"):
        q_df = (pd.DataFrame(
            [(uid,n,"⚠️ sparse" if sp else "✓ ok")
             for uid,(n,sp) in quality.items()],
            columns=["Student","Responses","Quality"])
                .sort_values("Responses",ascending=False))
        st.dataframe(q_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# TAB 5 — STUDENT EXPLORER (with radar chart)
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.markdown("#### Individual Student Explorer")

    all_students  = sorted(df['uid'].unique())
    student_means = df.groupby('uid')['stress_avg'].mean().dropna()

    def label(uid):
        m  = student_means.get(uid)
        sp = quality.get(uid,(0,False))[1]
        if m is None: return uid
        icon = "🔴" if m>=3.5 else "🟡" if m>=2.5 else "🟢"
        return f"{icon} {uid}  ({m:.1f}){' ⚠️' if sp else ''}"

    col_sel, col_main = st.columns([1,3])

    with col_sel:
        selected = st.selectbox("Select student", all_students, format_func=label)
        s   = df[df['uid']==selected]
        s_n = int(s['stress_avg'].notna().sum())
        st.markdown("---")
        s_stress = s['stress_avg'].mean()
        s_sleep  = s['sleep_hours'].mean()    if 'sleep_hours'    in s.columns else np.nan
        s_mood   = s['mood_score_avg'].mean() if 'mood_score_avg' in s.columns else np.nan
        s_walk   = s['fraction_walking'].mean() if 'fraction_walking' in s.columns else np.nan
        s_talk   = s['total_talking_minutes'].mean() if 'total_talking_minutes' in s.columns else np.nan

        metric_card("Avg Stress",    f"{s_stress:.2f}/5" if not np.isnan(s_stress) else "—", "", C['stress'])
        metric_card("Avg Sleep",     f"{s_sleep:.1f}h"   if not np.isnan(s_sleep)  else "—", "", C['sleep'])
        metric_card("Avg Mood",      f"{s_mood:.2f}"     if not np.isnan(s_mood)   else "—", "", C['mood'])
        metric_card("Stress surveys", str(s_n), "", C['neutral'])

        if s_n < 5:
            st.warning(f"⚠️ Only {s_n} responses")
        if cluster_df is not None and 'uid' in cluster_df.columns:
            row = cluster_df[cluster_df['uid']==selected]
            if len(row):
                st.info(f"🔵 Cluster {int(row.iloc[0]['cluster'])}")

        # Burnout gauge for this student
        st.markdown("---")
        fig_g = burnout_gauge(s_stress, s_sleep, s_mood, f"{selected} Risk")
        st.plotly_chart(fig_g, use_container_width=True)

    with col_main:
        # Radar chart
        group_means = df[['stress_avg','sleep_hours','fraction_walking',
                           'total_talking_minutes','unique_devices_nearby']].mean()

        def normalise_for_radar(val, col, invert=False):
            mn  = df[col].min()
            mx  = df[col].max()
            rng = mx - mn
            if rng == 0: return 0.5
            n = (val - mn) / rng
            return 1 - n if invert else n

        radar_vals = {}
        if not np.isnan(s_stress):
            radar_vals['Low Stress'] = normalise_for_radar(s_stress,'stress_avg',invert=True)
        if not np.isnan(s_sleep):
            radar_vals['Good Sleep'] = normalise_for_radar(s_sleep,'sleep_hours')
        if not np.isnan(s_walk):
            radar_vals['Active']     = normalise_for_radar(s_walk,'fraction_walking')
        if not np.isnan(s_talk):
            radar_vals['Social']     = normalise_for_radar(s_talk,'total_talking_minutes')
        if not np.isnan(s_mood):
            radar_vals['Mood']       = normalise_for_radar(s_mood,'mood_score_avg')

        if len(radar_vals) >= 3:
            color = C['stress'] if s_stress>3 else C['sleep'] if s_stress<2 else C['mood']
            fig_r = radar_chart(radar_vals, f"{selected} — Wellbeing Profile", color)
            st.plotly_chart(fig_r, use_container_width=True)

        # Stress over time
        s_weekly = s.groupby('study_week').agg(
            stress=('stress_avg','mean'), sleep=('sleep_hours','mean')).reindex(WEEKS)
        group_w  = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)

        fig1 = go.Figure()
        fig1.add_scatter(x=WEEKS, y=s_weekly['stress'],
                         mode='lines+markers', name=selected,
                         line=dict(color=C['stress'],width=2.5),
                         marker=dict(size=8,color=C['stress']))
        fig1.add_scatter(x=WEEKS, y=group_w, mode='lines',
                         name='Group avg',
                         line=dict(color='#4a4a7a',width=1.5,dash='dash'))
        fig1.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,line_width=0)
        fig1.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
        apply_layout(fig1, height=220,
                     title=f"{selected} — Stress vs Group Average",
                     yaxis=dict(range=[0,5.5],title='Stress',gridcolor='#1e1e2e'),
                     legend=dict(orientation='h',y=-0.3))
        st.plotly_chart(fig1, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 6 — COMPARE TWO STUDENTS (new!)
# ═══════════════════════════════════════════════════════════════
with tab6:
    st.markdown("#### ⚖️ Side-by-Side Student Comparison")
    st.caption("Pick two students to compare their stress, sleep, and behaviour patterns.")

    all_students = sorted(df['uid'].unique())

    ca, cb = st.columns(2)
    student_a = ca.selectbox("Student A", all_students, index=0,   key="sa")
    student_b = cb.selectbox("Student B", all_students, index=min(1,len(all_students)-1), key="sb")

    da = df[df['uid']==student_a]
    db = df[df['uid']==student_b]

    # Comparison metric cards
    st.markdown("---")
    compare_metrics = [
        ("Avg Stress",    'stress_avg',            "—", C['stress'], False),
        ("Avg Sleep",     'sleep_hours',            "h", C['sleep'],  False),
        ("Avg Mood",      'mood_score_avg',         "",  C['mood'],   False),
        ("Walking %",     'fraction_walking',       "%", C['exercise'],True),
        ("Talking time",  'total_talking_minutes',  "m", C['social'], False),
        ("BT devices",    'unique_devices_nearby',  "",  C['neutral'],False),
    ]

    header_cols = st.columns([2,1,1])
    header_cols[0].markdown("**Metric**")
    header_cols[1].markdown(f"**{student_a}**")
    header_cols[2].markdown(f"**{student_b}**")
    st.markdown("---")

    for label,col,unit,color,is_pct in compare_metrics:
        if col not in da.columns: continue
        va = da[col].mean()
        vb = db[col].mean()
        row_cols = st.columns([2,1,1])
        row_cols[0].markdown(f"*{label}*")
        if not np.isnan(va):
            val_a = f"{va*100:.1f}{unit}" if is_pct else f"{va:.2f}{unit}"
            row_cols[1].markdown(f"**{val_a}**")
        if not np.isnan(vb):
            val_b = f"{vb*100:.1f}{unit}" if is_pct else f"{vb:.2f}{unit}"
            row_cols[2].markdown(f"**{val_b}**")

    st.markdown("---")

    # Side by side stress charts
    col1, col2 = st.columns(2)
    for col, student, data, color in [
        (col1, student_a, da, C['stress']),
        (col2, student_b, db, C['mood']),
    ]:
        with col:
            sw = data.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)
            ga = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)
            fig = go.Figure()
            fig.add_scatter(x=WEEKS, y=sw, mode='lines+markers',
                            name=student, line=dict(color=color,width=2.5),
                            marker=dict(size=7,color=color))
            fig.add_scatter(x=WEEKS, y=ga, mode='lines', name='Group avg',
                            line=dict(color='#4a4a7a',width=1.5,dash='dash'))
            fig.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,line_width=0)
            fig.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
            apply_layout(fig, height=250,
                         title=f"{student} — Stress",
                         yaxis=dict(range=[0,5.5],gridcolor='#1e1e2e'),
                         legend=dict(orientation='h',y=-0.3))
            st.plotly_chart(fig, use_container_width=True)

    # Radar comparison
    st.markdown("#### Wellbeing Profile Comparison")

    def get_radar(data):
        vals = {}
        for key,col,inv in [
            ('Low Stress','stress_avg',True),
            ('Good Sleep','sleep_hours',False),
            ('Active','fraction_walking',False),
            ('Social','total_talking_minutes',False),
            ('Mood','mood_score_avg',False),
        ]:
            if col in data.columns:
                v = data[col].mean()
                if not np.isnan(v):
                    mn,mx = df[col].min(), df[col].max()
                    n = (v-mn)/(mx-mn+1e-9)
                    vals[key] = 1-n if inv else n
        return vals

    ra = get_radar(da)
    rb = get_radar(db)

    if len(ra)>=3 and len(rb)>=3:
        cats = list(set(ra.keys()) & set(rb.keys()))
        vals_a = [ra[c] for c in cats]
        vals_b = [rb[c] for c in cats]
        cats_c = cats + [cats[0]]
        vals_a_c = vals_a + [vals_a[0]]
        vals_b_c = vals_b + [vals_b[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=vals_a_c, theta=cats_c, fill='toself',
            name=student_a, line=dict(color=C['stress'],width=2),
            fillcolor='rgba(224,92,92,0.15)'))
        fig.add_trace(go.Scatterpolar(r=vals_b_c, theta=cats_c, fill='toself',
            name=student_b, line=dict(color=C['mood'],width=2),
            fillcolor='rgba(124,106,247,0.15)'))
        fig.update_layout(
            polar=dict(bgcolor='rgba(15,15,25,0.5)',
                       radialaxis=dict(range=[0,1],gridcolor='#1e1e2e',
                                       tickfont=dict(size=9,color='#6b6b9a')),
                       angularaxis=dict(tickfont=dict(size=11,color='#c8c8e8'),
                                        gridcolor='#1e1e2e')),
            paper_bgcolor='rgba(0,0,0,0)',
            height=350, showlegend=True,
            legend=dict(orientation='h',y=-0.1,
                        font=dict(color='#c8c8e8')))
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 7 — ML PREDICTIONS
# ═══════════════════════════════════════════════════════════════
with tab7:
    st.markdown("#### 🤖 Machine Learning Results")

    if all(f is None for f in [pred_df, cluster_df, fi_df, perf_df]):
        st.info("ML files not found in `data/` folder. Upload the 4 ML CSV files to see this tab.")
        st.stop()

    # Model performance
    if perf_df is not None and 'task' in perf_df.columns:
        st.markdown("### 📊 Model Performance")
        col1,col2 = st.columns(2)

        with col1:
            st.markdown("##### Regression — lower MAE = better")
            reg = perf_df[(perf_df['task']=='regression') & (perf_df['metric']=='MAE')]
            if not reg.empty:
                reg = reg.sort_values('value')
                cols_colors = [C['ml'] if i==0 else C['neutral'] for i in range(len(reg))]
                fig = go.Figure(go.Bar(x=reg['model'],y=reg['value'],
                    marker_color=cols_colors,
                    text=[f"{v:.3f}" for v in reg['value']],textposition='outside'))
                apply_layout(fig, height=260, showlegend=False,
                             yaxis=dict(title='MAE',gridcolor='#1e1e2e'))
                st.plotly_chart(fig, use_container_width=True)
                st.success(f"✅ Best: **{reg.iloc[0]['model']}**  (MAE = {reg.iloc[0]['value']:.3f})")

        with col2:
            st.markdown("##### Classification — higher AUC = better")
            cls = perf_df[(perf_df['task']=='classification') & (perf_df['metric']=='AUC')]
            if not cls.empty:
                cls = cls.sort_values('value',ascending=False)
                cols_colors = [C['ml'] if i==0 else C['neutral'] for i in range(len(cls))]
                fig = go.Figure(go.Bar(x=cls['model'],y=cls['value'],
                    marker_color=cols_colors,
                    text=[f"{v:.3f}" for v in cls['value']],textposition='outside'))
                fig.add_hline(y=0.5,line_dash='dash',line_color='#4a4a7a',
                              annotation_text='Random (0.5)')
                apply_layout(fig, height=260, showlegend=False,
                             yaxis=dict(title='AUC',range=[0,1.1],gridcolor='#1e1e2e'))
                st.plotly_chart(fig, use_container_width=True)
                st.success(f"✅ Best: **{cls.iloc[0]['model']}**  (AUC = {cls.iloc[0]['value']:.3f})")

        st.divider()

    # Predicted vs actual
    if pred_df is not None and all(c in pred_df.columns for c in ['stress_avg','stress_predicted']):
        st.markdown("### 🎯 Predicted vs Actual Stress")
        col1,col2 = st.columns(2)

        with col1:
            d   = pred_df[['stress_avg','stress_predicted']].dropna()
            mae = (d['stress_avg']-d['stress_predicted']).abs().mean()
            fig = go.Figure()
            fig.add_scatter(x=d['stress_avg'],y=d['stress_predicted'],
                            mode='markers',
                            marker=dict(color=C['ml'],size=5,opacity=0.3))
            fig.add_scatter(x=[1,5],y=[1,5],mode='lines',
                            line=dict(color='white',width=1.5,dash='dash'))
            fig.add_annotation(text=f"MAE = {mae:.3f}",
                               xref="paper",yref="paper",x=0.05,y=0.95,
                               showarrow=False,font=dict(size=13,color='#c8c8e8'),
                               bgcolor='rgba(30,30,46,0.8)',borderwidth=1,borderpad=8)
            apply_layout(fig,height=300,showlegend=False,
                         xaxis=dict(title='Actual stress',range=[0.5,5.5],gridcolor='#1e1e2e'),
                         yaxis=dict(title='Predicted stress',range=[0.5,5.5],gridcolor='#1e1e2e'))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            if 'high_stress_prob' in pred_df.columns and 'study_week' in pred_df.columns:
                pw = pred_df.groupby('study_week')['high_stress_prob'].mean().reindex(WEEKS)
                fig = go.Figure(go.Bar(
                    x=[f'W{w}' for w in WEEKS], y=pw.values,
                    marker_color=[C['stress'] if (not np.isnan(v) and v>=0.4)
                                  else C['social'] if (not np.isnan(v) and v>=0.25)
                                  else C['sleep'] for v in pw.values],
                    text=[f"{v:.0%}" if not np.isnan(v) else "" for v in pw.values],
                    textposition='outside'))
                fig.add_hline(y=0.25,line_dash='dash',line_color='#F0A050',
                              annotation_text='25% risk threshold')
                apply_layout(fig,height=300,
                             yaxis=dict(title='High-stress probability',
                                        tickformat=',.0%',range=[0,0.85],
                                        gridcolor='#1e1e2e'))
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

    # Feature importance
    if fi_df is not None:
        st.markdown("### 🏆 Feature Importance")
        lc = 'label' if 'label' in fi_df.columns else 'feature'
        if lc in fi_df.columns and 'importance' in fi_df.columns:
            fi_s = fi_df.sort_values('importance',ascending=True).tail(10)
            colors = []
            for feat in fi_s[lc]:
                fl = str(feat).lower()
                c  = (C['sleep'] if 'sleep' in fl else
                      C['exercise'] if 'walk' in fl else
                      C['social'] if 'talk' in fl else
                      C['mood'] if 'device' in fl or 'bt' in fl else C['ml'])
                colors.append(c)
            fig = go.Figure(go.Bar(
                x=fi_s['importance'],y=fi_s[lc],orientation='h',
                marker_color=colors,
                text=[f"{v:.4f}" for v in fi_s['importance']],
                textposition='outside'))
            apply_layout(fig,height=360,showlegend=False,
                         xaxis=dict(title='Importance score',gridcolor='#1e1e2e'))
            st.plotly_chart(fig, use_container_width=True)
            top3 = fi_df.sort_values('importance',ascending=False).head(3)
            st.markdown("**Top 3 predictors of stress:**")
            for _,row in top3.iterrows():
                st.markdown(f"- **{row[lc]}** — {row['importance']:.4f}")

        st.divider()

    # Clusters
    if cluster_df is not None and 'cluster' in cluster_df.columns:
        st.markdown("### 👥 Student Behaviour Clusters")
        counts = cluster_df['cluster'].value_counts().sort_index()
        col1,col2 = st.columns([1,2])

        with col1:
            fig = go.Figure(go.Pie(
                labels=[f"Cluster {c}" for c in counts.index],
                values=counts.values,
                marker_colors=[C['stress'],C['sleep'],C['mood'],
                               C['exercise'],C['social']][:len(counts)],
                hole=0.4,textinfo='label+value'))
            apply_layout(fig,height=260,showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            if 'uid' in df.columns:
                df_c = df.merge(cluster_df[['uid','cluster']],on='uid',how='left')
                pcols = [c for c in ['stress_avg','sleep_hours','fraction_walking',
                                      'total_talking_minutes','unique_devices_nearby']
                         if c in df_c.columns]
                if pcols:
                    profile = df_c.groupby('cluster')[pcols].mean()
                    pn = ((profile-profile.min())/(profile.max()-profile.min()+1e-9))
                    pn = pn.rename(columns={'stress_avg':'Stress','sleep_hours':'Sleep',
                                            'fraction_walking':'Walking',
                                            'total_talking_minutes':'Talking',
                                            'unique_devices_nearby':'BT devices'})
                    fig = go.Figure()
                    clr = [C['stress'],C['sleep'],C['mood'],C['exercise']]
                    for i,(idx,row) in enumerate(pn.iterrows()):
                        fig.add_bar(name=f"Cluster {idx}",
                                    x=row.index.tolist(),y=row.values,
                                    marker_color=clr[i%len(clr)])
                    apply_layout(fig,height=260,barmode='group',
                                 yaxis=dict(title='Score (0–1)',range=[0,1.2],
                                            gridcolor='#1e1e2e'),
                                 legend=dict(orientation='h',y=-0.25))
                    st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Students per cluster:**")
        cl_cols = st.columns(min(cluster_df['cluster'].nunique(),4))
        for col,(cl,grp) in zip(cl_cols,cluster_df.groupby('cluster')):
            col.markdown(f"**Cluster {cl}** ({len(grp)} students)")
            col.write(", ".join(sorted(grp['uid'].tolist())))
