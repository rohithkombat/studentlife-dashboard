# ─────────────────────────────────────────────────────────────────────────────
# StudentLife Visual Analytics Dashboard — Enhanced Version
# Author: Rohith Elanchezhian | Newcastle University
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(page_title="StudentLife Dashboard",
                   page_icon="🎓", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
* { font-family: 'Inter', sans-serif; }
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg,#0a0a0f 0%,#0f0f1a 50%,#0a0f0a 100%);
}
[data-testid="stSidebar"]  { background: rgba(15,15,25,0.97); border-right:1px solid #1e1e2e; }
[data-testid="stHeader"]   { background: transparent; }
.block-container           { padding-top: 1rem; }

.metric-card {
    background: linear-gradient(135deg,rgba(30,30,50,0.8),rgba(20,20,35,0.9));
    border: 1px solid rgba(124,106,247,0.2);
    border-radius: 14px; padding: 1.1rem 1.2rem;
    text-align: center; margin-bottom: 0.5rem;
    transition: all 0.2s ease;
}
.metric-card:hover { border-color:rgba(124,106,247,0.5); transform:translateY(-2px); }
.m-label { font-size:11px; font-weight:500; color:#6b6b9a;
           text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.35rem; }
.m-value { font-size:26px; font-weight:600; color:#e8e8ff; line-height:1; }
.m-sub   { font-size:11px; color:#4a4a7a; margin-top:0.25rem; }

.find-card { background:rgba(20,20,35,0.8); border-left:3px solid #7C6AF7;
             border-radius:0 12px 12px 0; padding:0.9rem 1.1rem; margin-bottom:0.6rem; }
.find-card.red   { border-left-color:#E05C5C; }
.find-card.teal  { border-left-color:#4ECDC4; }
.find-card.amber { border-left-color:#F0A050; }
.f-title { font-size:13px; font-weight:600; color:#c8c8ff; margin-bottom:3px; }
.f-text  { font-size:12px; color:#8888aa; line-height:1.5; }

.story-box { background:rgba(124,106,247,0.07); border:1px solid rgba(124,106,247,0.18);
             border-radius:12px; padding:0.9rem 1.1rem; margin-bottom:0.6rem; }
.s-week { font-size:11px; color:#7C6AF7; font-weight:600;
          text-transform:uppercase; letter-spacing:0.06em; }
.s-text { font-size:12px; color:#c8c8e8; line-height:1.7; margin-top:0.25rem; }
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

# rgba versions for fills
FILL = {
    'stress':   'rgba(224,92,92,0.15)',
    'sleep':    'rgba(78,205,196,0.15)',
    'mood':     'rgba(124,106,247,0.15)',
    'exercise': 'rgba(80,200,120,0.15)',
    'social':   'rgba(240,160,80,0.15)',
    'neutral':  'rgba(136,136,170,0.15)',
    'ml':       'rgba(255,107,157,0.15)',
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

def mc(label, value, sub='', color='#7C6AF7'):
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="m-label">{label}</div>'
        f'<div class="m-value" style="color:{color}">{value}</div>'
        f'<div class="m-sub">{sub}</div></div>',
        unsafe_allow_html=True
    )

def fc(icon, title, text, style=''):
    st.markdown(
        f'<div class="find-card {style}">'
        f'<div class="f-title">{icon} {title}</div>'
        f'<div class="f-text">{text}</div></div>',
        unsafe_allow_html=True
    )

def quality_check(df):
    counts = df.groupby('uid')['stress_avg'].count()
    return {uid: (int(n), n < 5) for uid, n in counts.items()}

def norm(val, col, df, invert=False):
    try:
        mn, mx = df[col].min(), df[col].max()
        if pd.isna(mn) or pd.isna(mx) or mx == mn:
            return 0.5
        n = float((val - mn) / (mx - mn))
        n = max(0.0, min(1.0, n))
        return 1.0 - n if invert else n
    except Exception:
        return 0.5


# ─────────────────────────────────────────────────────────────────────────────
# BURNOUT GAUGE
# ─────────────────────────────────────────────────────────────────────────────

def burnout_gauge(stress, sleep, mood, title):
    parts, n = 0.0, 0
    if stress is not None and not np.isnan(float(stress)):
        parts += (float(stress) - 1) / 4 * 100; n += 1
    if sleep is not None and not np.isnan(float(sleep)):
        parts += max(0, (8 - float(sleep)) / 8 * 100); n += 1
    if mood is not None and not np.isnan(float(mood)):
        parts += (-float(mood) + 4) / 8 * 100; n += 1
    risk = parts / n if n > 0 else 50.0

    if   risk < 30:  col, lbl = '#4ECDC4', 'LOW RISK'
    elif risk < 55:  col, lbl = '#F0A050', 'MODERATE'
    elif risk < 75:  col, lbl = '#E05C5C', 'HIGH RISK'
    else:            col, lbl = '#CC2222', 'CRITICAL'

    risk = max(0.0, min(100.0, float(risk)))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(risk, 1),
        title=dict(text=f"<b>{title}</b><br>"
                   f"<span style='font-size:13px;color:{col}'>{lbl}</span>",
                   font=dict(size=13, color='#c8c8e8')),
        number=dict(suffix="%", font=dict(size=26, color=col)),
        gauge=dict(
            axis=dict(range=[0,100], tickwidth=1, tickcolor='#2a2a3e',
                      tickvals=[0,25,50,75,100],
                      tickfont=dict(color='#6b6b9a', size=9)),
            bar=dict(color=col, thickness=0.25),
            bgcolor='rgba(0,0,0,0)', borderwidth=0,
            steps=[
                dict(range=[0,30],  color='rgba(78,205,196,0.10)'),
                dict(range=[30,55], color='rgba(240,160,80,0.10)'),
                dict(range=[55,75], color='rgba(224,92,92,0.10)'),
                dict(range=[75,100],color='rgba(200,30,30,0.12)'),
            ],
        )
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=210,
                      margin=dict(l=20,r=20,t=65,b=5),
                      font=dict(color='#c8c8e8'))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# RADAR CHART
# ─────────────────────────────────────────────────────────────────────────────

def radar_chart(vals_dict, title, color_key='mood'):
    cats  = list(vals_dict.keys())
    vals  = list(vals_dict.values())
    cats += [cats[0]]; vals += [vals[0]]
    fig = go.Figure(go.Scatterpolar(
        r=vals, theta=cats, fill='toself',
        fillcolor=FILL[color_key],
        line=dict(color=C[color_key], width=2),
        marker=dict(size=6, color=C[color_key]),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(15,15,25,0.5)',
            radialaxis=dict(visible=True, range=[0,1],
                            tickvals=[0.25,0.5,0.75,1.0],
                            ticktext=['25%','50%','75%','100%'],
                            tickfont=dict(size=9, color='#6b6b9a'),
                            gridcolor='#1e1e2e', linecolor='#1e1e2e'),
            angularaxis=dict(tickfont=dict(size=11, color='#c8c8e8'),
                             gridcolor='#1e1e2e', linecolor='#1e1e2e')
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        height=300, showlegend=False,
        margin=dict(l=60,r=60,t=40,b=40),
        title=dict(text=title, font=dict(color='#c8c8e8',size=12), x=0.5)
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# WEEK STORY
# ─────────────────────────────────────────────────────────────────────────────

def week_story(weekly, week):
    if week not in weekly.index:
        return "No data available for this week."
    row  = weekly.loc[week]
    avg_stress = weekly['stress'].mean() if 'stress' in weekly else np.nan
    parts = []

    try:
        stress = float(row['stress']) if 'stress' in row.index and pd.notna(row['stress']) else np.nan
        sleep  = float(row['sleep'])  if 'sleep'  in row.index and pd.notna(row['sleep'])  else np.nan
        mood   = float(row['mood'])   if 'mood'   in row.index and pd.notna(row['mood'])   else np.nan
        talk   = float(row['talking']) if 'talking' in row.index and pd.notna(row['talking']) else np.nan
    except Exception:
        return 'Data could not be read for this week.' 

    if not np.isnan(stress):
        if week == 10:
            parts.append(f"Finals week — stress spiked to {stress:.2f}/5, the highest of the term.")
        elif not np.isnan(avg_stress) and stress > avg_stress + 0.3:
            parts.append(f"A tough week: stress ({stress:.2f}/5) was above the term average.")
        elif not np.isnan(avg_stress) and stress < avg_stress - 0.3:
            parts.append(f"A calmer week: stress ({stress:.2f}/5) was below average.")
        else:
            parts.append(f"Stress ({stress:.2f}/5) was close to the term average.")

    if not np.isnan(sleep):
        if sleep >= 8:
            parts.append(f"Students slept well ({sleep:.1f}h) — possibly a study break.")
        elif sleep < 6:
            parts.append(f"Sleep was poor ({sleep:.1f}h) — students were under heavy pressure.")
        else:
            parts.append(f"Sleep averaged {sleep:.1f}h, below the recommended 7 hours.")

    if not np.isnan(mood):
        if mood > 0.5:   parts.append(f"Mood was positive ({mood:.2f}).")
        elif mood < -0.5: parts.append(f"Mood was low ({mood:.2f}).")

    if not np.isnan(talk):
        avg_talk = weekly['talking'].mean() if 'talking' in weekly else talk
        if not np.isnan(avg_talk):
            if talk < avg_talk * 0.7:
                parts.append(f"Conversations dropped ({talk:.0f} min/day) — more solo studying.")
            elif talk > avg_talk * 1.3:
                parts.append(f"Students were more social than usual ({talk:.0f} min/day).")

    return " ".join(parts) if parts else "Not enough data for this week."


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def load_master():
    df = pd.read_csv(os.path.join(DATA_DIR, 'daily_master.csv'))
    if 'student_id' in df.columns:
        df.rename(columns={'student_id':'uid'}, inplace=True)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    if 'is_weekend' in df.columns:
        df['is_weekend'] = df['is_weekend'].astype(str).str.lower().isin(
            ['true','1','yes'])
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


# ─────────────────────────────────────────────────────────────────────────────
# CHECK DATA EXISTS
# ─────────────────────────────────────────────────────────────────────────────

if not os.path.exists(os.path.join(DATA_DIR, 'daily_master.csv')):
    st.title("🎓 StudentLife Dashboard")
    st.error(
        "**daily_master.csv not found** in the `data/` folder.  \n"
        "Upload it to your GitHub repo under `data/daily_master.csv`."
    )
    st.markdown("""
    **Files to upload to GitHub → data/ folder:**
    - `daily_master.csv` ← required
    - `ml_predictions.csv`
    - `ml_clusters.csv`
    - `ml_feature_importance.csv`
    - `ml_performance.csv`
    """)
else:

    df         = load_master()
    pred_df    = load_ml('ml_predictions.csv')
    cluster_df = load_ml('ml_clusters.csv')
    fi_df      = load_ml('ml_feature_importance.csv')
    perf_df    = load_ml('ml_performance.csv')

    # ─────────────────────────────────────────────────────────────────────────
    # SIDEBAR
    # ─────────────────────────────────────────────────────────────────────────

    with st.sidebar:
        st.markdown("""
        <div style='text-align:center;padding:0.75rem 0'>
            <div style='font-size:28px'>🎓</div>
            <div style='font-size:16px;font-weight:600;color:#c8c8ff'>StudentLife</div>
            <div style='font-size:11px;color:#6b6b9a'>Visual Analytics for Digital Health</div>
            <div style='font-size:10px;color:#4a4a7a;margin-top:2px'>
                Rohith Elanchezhian · Newcastle University</div>
        </div>""", unsafe_allow_html=True)
        st.divider()

        st.markdown("**Filters**")
        week_filter = st.selectbox("Study week",
            ["All weeks"] + [f"Week {w}" for w in WEEKS])
        day_filter  = st.selectbox("Day type",
            ["All days","Weekdays only","Weekends only"])
        st.divider()

        st.markdown("**Data Status**")
        st.success("✅ daily_master.csv")
        for fname, lbl in [
            ('ml_predictions.csv','ml_predictions'),
            ('ml_clusters.csv','ml_clusters'),
            ('ml_feature_importance.csv','ml_feature_importance'),
            ('ml_performance.csv','ml_performance'),
        ]:
            if load_ml(fname) is not None: st.success(f"✅ {lbl}")
            else:                          st.caption(f"⬜ {lbl}")
        st.divider()
        st.caption("📊 49 students · 10 weeks\nSpring 2013 · Dartmouth College")

    # ─────────────────────────────────────────────────────────────────────────
    # FILTERS
    # ─────────────────────────────────────────────────────────────────────────

    filtered = df.copy()
    if week_filter != "All weeks":
        filtered = filtered[filtered['study_week'] == int(week_filter.split()[1])]
    if day_filter == "Weekdays only":
        filtered = filtered[filtered['is_weekend'] == False]
    elif day_filter == "Weekends only":
        filtered = filtered[filtered['is_weekend'] == True]

    quality = quality_check(df)
    sparse  = [u for u,(n,sp) in quality.items() if sp]

    # ─────────────────────────────────────────────────────────────────────────
    # HEADER
    # ─────────────────────────────────────────────────────────────────────────

    st.markdown("""
    <div style='padding:0.5rem 0 0.75rem'>
        <h1 style='font-size:26px;font-weight:700;color:#e8e8ff;margin:0'>
            🎓 StudentLife Visual Analytics Dashboard
        </h1>
        <p style='color:#6b6b9a;font-size:12px;margin:3px 0 0'>
            Exploring digital health patterns across 49 students · 10-week spring term
        </p>
    </div>""", unsafe_allow_html=True)

    st.caption(
        f"Showing **{len(filtered):,} rows** · "
        f"**{filtered['uid'].nunique()} students** · "
        f"{week_filter} | {day_filter}"
    )
    if sparse:
        st.warning(f"⚠️ {len(sparse)} students have <5 stress responses — treat their averages with caution.")

    # ─────────────────────────────────────────────────────────────────────────
    # TABS
    # ─────────────────────────────────────────────────────────────────────────

    tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
        "📊 Overview",
        "📈 Weekly Trends",
        "🔗 Correlations",
        "🌡️ Stress Heatmap",
        "👤 Student Explorer",
        "⚖️ Compare Students",
        "🤖 ML Predictions",
    ])

    # ═══════════════════════════════════════════════════
    # TAB 1 — OVERVIEW
    # ═══════════════════════════════════════════════════
    with tab1:

        stress_mean = safe_mean(filtered, 'stress_avg')
        sleep_mean  = safe_mean(filtered, 'sleep_hours')
        mood_mean   = safe_mean(filtered, 'mood_score_avg')
        talk_mean   = safe_mean(filtered, 'total_talking_minutes')
        high_pct    = (filtered['high_stress'].mean()*100
                       if 'high_stress' in filtered.columns else None)
        dep_v       = (filtered['sleep_hours'].dropna()
                       if 'sleep_hours' in filtered.columns else pd.Series([]))
        dep_pct     = ((dep_v < 7).mean()*100) if len(dep_v) else None

        # Finding cards
        st.markdown("### 📌 Key Findings")
        f1,f2,f3 = st.columns(3)
        with f1:
            if stress_mean and high_pct:
                fc("😟","Stress Level",
                   f"Average <b>{stress_mean:.2f}/5</b> and <b>{high_pct:.0f}%</b>"
                   f" of days were high stress (level 4–5).","red")
        with f2:
            if sleep_mean and dep_pct:
                fc("😴","Sleep Quality",
                   f"Average <b>{sleep_mean:.1f}h/night</b> but <b>{dep_pct:.0f}%</b>"
                   f" of nights fell below the recommended 7 hours.","teal")
        with f3:
            if 'stress_avg' in df.columns and 'is_weekend' in df.columns:
                wd = df[df['is_weekend']==False]['stress_avg'].mean()
                we = df[df['is_weekend']==True]['stress_avg'].mean()
                if not (np.isnan(wd) or np.isnan(we)):
                    d = "higher" if we > wd else "lower"
                    fc("😮","Surprising Finding",
                       f"Weekend stress (<b>{we:.2f}</b>) is <b>{d}</b> than"
                       f" weekday (<b>{wd:.2f}</b>).","amber")

        st.divider()

        # Metric cards
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1: mc("Avg Stress",      f"{stress_mean:.2f}/5" if stress_mean else "—","out of 5",  C['stress'])
        with c2: mc("High Stress Days",f"{high_pct:.0f}%"     if high_pct    else "—","level 4–5", C['social'])
        with c3: mc("Avg Sleep",       f"{sleep_mean:.1f}h"   if sleep_mean  else "—","per night",  C['sleep'])
        with c4: mc("Under 7h Nights", f"{dep_pct:.0f}%"      if dep_pct     else "—","deprived",   C['mood'])
        with c5: mc("Avg Mood Score",  f"{mood_mean:.2f}"     if mood_mean   else "—","−4 to +4",   C['exercise'])
        with c6: mc("Avg Talking",     f"{talk_mean:.0f}m"    if talk_mean   else "—","per day",    C['neutral'])

        st.divider()

        # Burnout gauges
        st.markdown("#### 🎯 Burnout Risk")
        g1,g2,g3 = st.columns([1,1,2])
        with g1:
            fig = burnout_gauge(stress_mean, sleep_mean, mood_mean, "Cohort Risk")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("All students · All weeks")
        with g2:
            w10 = df[df['study_week']==10]
            fig2 = burnout_gauge(
                safe_mean(w10,'stress_avg'),
                safe_mean(w10,'sleep_hours'),
                safe_mean(w10,'mood_score_avg'),
                "Finals Week (W10)"
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.caption("Week 10 only")
        with g3:
            st.markdown("**How the gauge works**")
            st.markdown("""
The burnout score combines three signals — each scored 0–100%:
- 🔴 **Stress** — higher stress = higher risk
- 😴 **Sleep** — fewer hours = higher risk
- 😟 **Mood** — more negative mood = higher risk

| Score | Risk Level |
|-------|-----------|
| 0–30  | 🟢 Low |
| 30–55 | 🟡 Moderate |
| 55–75 | 🔴 High |
| 75–100| 🚨 Critical |
""")

        st.divider()
        col1,col2 = st.columns(2)

        with col1:
            st.markdown("##### Stress Level Distribution")
            if 'stress_avg' in filtered.columns:
                v = filtered['stress_avg'].dropna()
                lbs = ['1 Not stressed','2','3 Moderate','4','5 Very stressed']
                counts = pd.cut(v, bins=[0.5,1.5,2.5,3.5,4.5,5.5],
                                labels=lbs).value_counts().sort_index()
                fig = go.Figure(go.Bar(
                    x=counts.index.tolist(), y=counts.values,
                    marker_color=[C['sleep'],C['sleep'],C['neutral'],C['stress'],C['stress']],
                    text=[f"{val/len(v)*100:.0f}%" for val in counts.values],
                    textposition='outside'))
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
                    hole=0.45, textinfo='label+percent', textfont_size=11))
                apply_layout(fig, height=260, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    # ═══════════════════════════════════════════════════
    # TAB 2 — WEEKLY TRENDS + WEEK STORIES
    # ═══════════════════════════════════════════════════
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

        fig = make_subplots(rows=2, cols=2,
            subplot_titles=['Stress (1–5)','Sleep Hours',
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

        fig.update_layout(height=470, paper_bgcolor='rgba(0,0,0,0)',
                          plot_bgcolor='rgba(15,15,25,0.6)',
                          font=dict(color='#c8c8e8',size=11), showlegend=False,
                          margin=dict(l=40,r=20,t=55,b=40))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("🔴 shaded = finals week (Week 10)")

        # Week stories
        st.markdown("#### 📖 Week-by-Week Story")
        sc1, sc2 = st.columns(2)
        for i, w in enumerate(WEEKS):
            col = sc1 if i % 2 == 0 else sc2
            with col:
                story = week_story(weekly, w)
                lbl   = f"Week {w}" + (" — Finals 🎓" if w==10 else
                                        " — Mid-term break? 😌" if w==6 else "")
                st.markdown(
                    f'<div class="story-box">'
                    f'<div class="s-week">{lbl}</div>'
                    f'<div class="s-text">{story}</div></div>',
                    unsafe_allow_html=True
                )

    # ═══════════════════════════════════════════════════
    # TAB 3 — CORRELATIONS
    # ═══════════════════════════════════════════════════
    with tab3:
        st.markdown("#### How Variables Relate to Each Other")
        st.caption("Each dot = one student-day  |  Dashed line = overall trend")

        candidates = [
            ('sleep_hours','stress_avg','Sleep hours','Stress level',C['stress']),
            ('sleep_hours','mood_score_avg','Sleep hours','Mood score',C['mood']),
            ('fraction_walking','stress_avg','Walking','Stress level',C['exercise']),
            ('total_talking_minutes','mood_score_avg','Talking (min)','Mood',C['social']),
            ('unique_devices_nearby','stress_avg','BT devices','Stress level',C['neutral']),
            ('sleep_rate','stress_avg','Sleep quality','Stress level',C['sleep']),
        ]
        scatter_opts = {
            f"{xl}  vs  {yl}": (xc,yc,xl,yl,color)
            for xc,yc,xl,yl,color in candidates
            if xc in filtered.columns and yc in filtered.columns
        }

        if scatter_opts:
            keys = list(scatter_opts.keys())
            s1 = st.selectbox("First chart",  keys, index=0)
            s2 = st.selectbox("Second chart", keys, index=min(1,len(keys)-1))

            def make_scatter(key):
                xc,yc,xl,yl,color = scatter_opts[key]
                d = filtered[[xc,yc]].dropna()
                if len(d) < 5: return None
                r   = d[xc].corr(d[yc])
                m,b = np.polyfit(d[xc], d[yc], 1)
                xs  = np.linspace(d[xc].min(), d[xc].max(), 100)
                fig = go.Figure()
                fig.add_scatter(x=d[xc], y=d[yc], mode='markers',
                                marker=dict(color=color,size=5,opacity=0.35))
                fig.add_scatter(x=xs, y=m*xs+b, mode='lines',
                                line=dict(color='white',width=2,dash='dash'))
                fig.add_annotation(text=f"r = {r:.3f}",
                                   xref="paper",yref="paper",x=0.05,y=0.95,
                                   showarrow=False,
                                   font=dict(size=13,color='#c8c8e8'),
                                   bgcolor='rgba(30,30,46,0.85)',
                                   bordercolor='#2a2a3e',borderwidth=1,borderpad=8)
                apply_layout(fig, height=320, showlegend=False,
                             xaxis=dict(title=xl,gridcolor='#1e1e2e'),
                             yaxis=dict(title=yl,gridcolor='#1e1e2e'))
                return fig

            c1,c2 = st.columns(2)
            f1,f2 = make_scatter(s1), make_scatter(s2)
            if f1: c1.plotly_chart(f1, use_container_width=True)
            if f2: c2.plotly_chart(f2, use_container_width=True)

        # Correlation matrix
        st.markdown("#### Full Correlation Matrix")
        corr_map = {
            'stress_avg':'Stress','sleep_hours':'Sleep hrs',
            'sleep_rate':'Sleep quality','mood_score_avg':'Mood',
            'fraction_walking':'Walking','total_talking_minutes':'Talking',
            'unique_devices_nearby':'BT devices'
        }
        avail = {k:v for k,v in corr_map.items() if k in filtered.columns}
        if len(avail) >= 3:
            corr_df = filtered[list(avail.keys())].rename(columns=avail).corr()
            mask = np.triu(np.ones(corr_df.shape,dtype=bool), k=1)
            corr_df[mask] = None
            fig_c = px.imshow(corr_df, color_continuous_scale='RdBu_r',
                              zmin=-1, zmax=1, text_auto='.2f', aspect='auto')
            fig_c.update_traces(textfont_size=11)
            apply_layout(fig_c, height=360)
            st.plotly_chart(fig_c, use_container_width=True)

    # ═══════════════════════════════════════════════════
    # TAB 4 — STRESS HEATMAP
    # ═══════════════════════════════════════════════════
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
                zmin=1, zmax=5, text_auto='.1f', aspect='auto',
                labels=dict(x='Study Week',y='Student ID',color='Avg Stress'))
            fig_hm.update_xaxes(tickvals=WEEKS,
                                 ticktext=[f'W{w}' for w in WEEKS])
            fig_hm.update_traces(textfont_size=9)
            fig_hm.update_layout(
                height=max(420, len(pivot)*18),
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#c8c8e8',size=11),
                margin=dict(l=80,r=20,t=40,b=40))
            st.plotly_chart(fig_hm, use_container_width=True)

            sm = df.groupby('uid')['stress_avg'].mean().dropna()
            c1,c2,c3 = st.columns(3)
            c1.metric("Most stressed",  sm.idxmax(), f"{sm.max():.2f}/5")
            c2.metric("Least stressed", sm.idxmin(), f"{sm.min():.2f}/5")
            c3.metric("Range across students",
                      f"{sm.max()-sm.min():.2f} units",
                      "huge individual variation")

        with st.expander("📋 Response count per student"):
            q_df = pd.DataFrame(
                [(uid,n,"⚠️ sparse" if sp else "✓ ok")
                 for uid,(n,sp) in quality.items()],
                columns=["Student","Responses","Quality"]
            ).sort_values("Responses",ascending=False)
            st.dataframe(q_df, use_container_width=True, hide_index=True)

    # ═══════════════════════════════════════════════════
    # TAB 5 — STUDENT EXPLORER (with radar + gauge)
    # ═══════════════════════════════════════════════════
    with tab5:
        st.markdown("#### Individual Student Explorer")

        all_students  = sorted(df['uid'].unique())
        student_means = df.groupby('uid')['stress_avg'].mean().dropna()

        def slabel(uid):
            m  = student_means.get(uid)
            sp = quality.get(uid,(0,False))[1]
            if m is None: return uid
            icon = "🔴" if m>=3.5 else "🟡" if m>=2.5 else "🟢"
            return f"{icon} {uid}  ({m:.1f}){' ⚠️' if sp else ''}"

        col_sel, col_main = st.columns([1,3])

        with col_sel:
            selected = st.selectbox("Select student", all_students, format_func=slabel)
            s   = df[df['uid']==selected]
            s_n = int(s['stress_avg'].notna().sum())
            st.markdown("---")

            s_stress = s['stress_avg'].mean()
            s_sleep  = s['sleep_hours'].mean()    if 'sleep_hours'    in s.columns else np.nan
            s_mood   = s['mood_score_avg'].mean() if 'mood_score_avg' in s.columns else np.nan

            mc("Avg Stress",    f"{s_stress:.2f}/5" if not np.isnan(s_stress) else "—","",C['stress'])
            mc("Avg Sleep",     f"{s_sleep:.1f}h"   if not np.isnan(s_sleep)  else "—","",C['sleep'])
            mc("Avg Mood",      f"{s_mood:.2f}"     if not np.isnan(s_mood)   else "—","",C['mood'])
            mc("Stress surveys", str(s_n),"",C['neutral'])

            if s_n < 5:
                st.warning(f"⚠️ Only {s_n} responses")

            if cluster_df is not None and 'uid' in cluster_df.columns:
                row = cluster_df[cluster_df['uid']==selected]
                if len(row):
                    st.info(f"🔵 Cluster {int(row.iloc[0]['cluster'])}")

            st.markdown("---")
            fig_g = burnout_gauge(
                None if np.isnan(s_stress) else s_stress,
                None if np.isnan(s_sleep)  else s_sleep,
                None if np.isnan(s_mood)   else s_mood,
                f"{selected} Risk"
            )
            st.plotly_chart(fig_g, use_container_width=True)

        with col_main:
            # Radar chart
            radar_vals = {}
            for key, col_name, inv in [
                ('Low Stress','stress_avg',True),
                ('Good Sleep','sleep_hours',False),
                ('Active','fraction_walking',False),
                ('Social','total_talking_minutes',False),
                ('Mood','mood_score_avg',False),
            ]:
                if col_name in s.columns:
                    v = s[col_name].mean()
                    if not np.isnan(v):
                        radar_vals[key] = norm(v, col_name, df, inv)

            if len(radar_vals) >= 3:
                try:
                    ck = 'stress' if (pd.notna(s_stress) and s_stress > 3) else 'sleep' if (pd.notna(s_stress) and s_stress < 2) else 'mood'
                    fig_r = radar_chart(radar_vals, f"{selected} — Wellbeing Profile", ck)
                    st.plotly_chart(fig_r, use_container_width=True)
                except Exception as e:
                    st.caption(f"Radar chart unavailable: {e}")

            # Stress over time
            s_weekly = s.groupby('study_week').agg(
                stress=('stress_avg','mean'),
                sleep=('sleep_hours','mean')
            ).reindex(WEEKS)
            group_w = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)

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
            apply_layout(fig1, height=230,
                         title=f"{selected} — Stress vs Group Average",
                         yaxis=dict(range=[0,5.5],title='Stress',gridcolor='#1e1e2e'),
                         legend=dict(orientation='h',y=-0.3))
            st.plotly_chart(fig1, use_container_width=True)

            # Sleep over time
            sv = s_weekly['sleep'].values
            sc_col = [C['sleep'] if not np.isnan(v) and v>=7
                      else C['social'] if not np.isnan(v) and v>=5
                      else C['stress'] if not np.isnan(v)
                      else '#1e1e2e' for v in sv]
            fig2 = go.Figure(go.Bar(
                x=[f'W{w}' for w in WEEKS], y=sv, marker_color=sc_col))
            fig2.add_hline(y=7, line_dash='dash', line_color=C['sleep'],
                           annotation_text='7h recommended',
                           annotation_position='top right')
            apply_layout(fig2, height=210,
                         title=f"{selected} — Sleep by Week",
                         yaxis=dict(range=[0,14],title='Hours',gridcolor='#1e1e2e'))
            st.plotly_chart(fig2, use_container_width=True)

    # ═══════════════════════════════════════════════════
    # TAB 6 — COMPARE TWO STUDENTS
    # ═══════════════════════════════════════════════════
    with tab6:
        st.markdown("#### ⚖️ Side-by-Side Student Comparison")
        st.caption("Pick two students to compare their stress, sleep, and behaviour.")

        all_students = sorted(df['uid'].unique())
        ca,cb = st.columns(2)
        sa = ca.selectbox("Student A", all_students,
                          index=0, key="sa")
        sb = cb.selectbox("Student B", all_students,
                          index=min(1,len(all_students)-1), key="sb")

        da = df[df['uid']==sa]
        db = df[df['uid']==sb]

        st.markdown("---")
        # Comparison table
        compare_metrics = [
            ("Avg Stress",    'stress_avg',            "",   False),
            ("Avg Sleep",     'sleep_hours',            "h",  False),
            ("Avg Mood",      'mood_score_avg',         "",   False),
            ("Walking %",     'fraction_walking',       "%",  True ),
            ("Talking (min)", 'total_talking_minutes',  "m",  False),
            ("BT devices",    'unique_devices_nearby',  "",   False),
        ]

        hdr = st.columns([2,1,1])
        hdr[0].markdown("**Metric**")
        hdr[1].markdown(f"**{sa}**")
        hdr[2].markdown(f"**{sb}**")
        st.markdown("---")

        for lbl, col_name, unit, is_pct in compare_metrics:
            if col_name not in da.columns: continue
            va = da[col_name].mean()
            vb = db[col_name].mean()
            row_cols = st.columns([2,1,1])
            row_cols[0].write(f"*{lbl}*")
            if not np.isnan(va):
                row_cols[1].markdown(
                    f"**{va*100:.1f}{unit}**" if is_pct else f"**{va:.2f}{unit}**")
            if not np.isnan(vb):
                row_cols[2].markdown(
                    f"**{vb*100:.1f}{unit}**" if is_pct else f"**{vb:.2f}{unit}**")

        st.markdown("---")

        # Side-by-side stress charts
        col1, col2 = st.columns(2)
        for col, student, data, color in [
            (col1, sa, da, C['stress']),
            (col2, sb, db, C['mood']),
        ]:
            with col:
                sw = data.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)
                ga = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)
                fig = go.Figure()
                fig.add_scatter(x=WEEKS, y=sw, mode='lines+markers',
                                name=student,
                                line=dict(color=color,width=2.5),
                                marker=dict(size=7,color=color))
                fig.add_scatter(x=WEEKS, y=ga, mode='lines',
                                name='Group avg',
                                line=dict(color='#4a4a7a',width=1.5,dash='dash'))
                fig.add_vrect(x0=9.5,x1=10.5,fillcolor='red',
                              opacity=0.07,line_width=0)
                fig.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
                apply_layout(fig, height=250,
                             title=f"{student} — Stress by Week",
                             yaxis=dict(range=[0,5.5],gridcolor='#1e1e2e'),
                             legend=dict(orientation='h',y=-0.3))
                st.plotly_chart(fig, use_container_width=True)

        # Overlapping radar comparison
        st.markdown("#### Wellbeing Profile Comparison")

        def get_radar_vals(data):
            vals = {}
            for key, col_name, inv in [
                ('Low Stress','stress_avg',True),
                ('Good Sleep','sleep_hours',False),
                ('Active','fraction_walking',False),
                ('Social','total_talking_minutes',False),
                ('Mood','mood_score_avg',False),
            ]:
                if col_name in data.columns:
                    v = data[col_name].mean()
                    if not np.isnan(v):
                        vals[key] = norm(v, col_name, df, inv)
            return vals

        ra = get_radar_vals(da)
        rb = get_radar_vals(db)

        if len(ra) >= 3 and len(rb) >= 3:
            cats = sorted(set(ra.keys()) & set(rb.keys()))
            va_c = [ra[c] for c in cats] + [ra[cats[0]]]
            vb_c = [rb[c] for c in cats] + [rb[cats[0]]]
            cats_c = cats + [cats[0]]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=va_c, theta=cats_c, fill='toself',
                name=sa, line=dict(color=C['stress'],width=2),
                fillcolor=FILL['stress']))
            fig.add_trace(go.Scatterpolar(
                r=vb_c, theta=cats_c, fill='toself',
                name=sb, line=dict(color=C['mood'],width=2),
                fillcolor=FILL['mood']))
            fig.update_layout(
                polar=dict(
                    bgcolor='rgba(15,15,25,0.5)',
                    radialaxis=dict(range=[0,1],gridcolor='#1e1e2e',
                                   tickfont=dict(size=9,color='#6b6b9a')),
                    angularaxis=dict(tickfont=dict(size=11,color='#c8c8e8'),
                                    gridcolor='#1e1e2e')),
                paper_bgcolor='rgba(0,0,0,0)',
                height=340, showlegend=True,
                legend=dict(orientation='h',y=-0.1,
                            font=dict(color='#c8c8e8')))
            st.plotly_chart(fig, use_container_width=True)

    # ═══════════════════════════════════════════════════
    # TAB 7 — ML PREDICTIONS
    # ═══════════════════════════════════════════════════
    with tab7:
        st.markdown("#### 🤖 Machine Learning Results")

        ml_files_loaded = any(
            f is not None for f in [pred_df, cluster_df, fi_df, perf_df]
        )

        if not ml_files_loaded:
            st.info(
                "Upload the 4 ML CSV files to the `data/` folder in your "
                "GitHub repository to see this tab.  \n"
                "Files: `ml_predictions.csv`, `ml_clusters.csv`, "
                "`ml_feature_importance.csv`, `ml_performance.csv`"
            )
        else:
            # Model performance
            if perf_df is not None and 'task' in perf_df.columns:
                st.markdown("### 📊 Model Performance")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("##### Regression — lower MAE = better")
                    reg = perf_df[(perf_df['task']=='regression') &
                                  (perf_df['metric']=='MAE')]
                    if not reg.empty:
                        reg = reg.sort_values('value')
                        clrs = [C['ml'] if i==0 else C['neutral']
                                for i in range(len(reg))]
                        fig = go.Figure(go.Bar(
                            x=reg['model'], y=reg['value'],
                            marker_color=clrs,
                            text=[f"{v:.3f}" for v in reg['value']],
                            textposition='outside'))
                        apply_layout(fig, height=250, showlegend=False,
                                     yaxis=dict(title='MAE',gridcolor='#1e1e2e'))
                        st.plotly_chart(fig, use_container_width=True)
                        st.success(
                            f"✅ Best: **{reg.iloc[0]['model']}**  "
                            f"(MAE = {reg.iloc[0]['value']:.3f})")

                with col2:
                    st.markdown("##### Classification — higher AUC = better")
                    cls = perf_df[(perf_df['task']=='classification') &
                                  (perf_df['metric']=='AUC')]
                    if not cls.empty:
                        cls = cls.sort_values('value', ascending=False)
                        clrs = [C['ml'] if i==0 else C['neutral']
                                for i in range(len(cls))]
                        fig = go.Figure(go.Bar(
                            x=cls['model'], y=cls['value'],
                            marker_color=clrs,
                            text=[f"{v:.3f}" for v in cls['value']],
                            textposition='outside'))
                        fig.add_hline(y=0.5, line_dash='dash',
                                      line_color='#4a4a7a',
                                      annotation_text='Random (0.5)')
                        apply_layout(fig, height=250, showlegend=False,
                                     yaxis=dict(title='AUC',range=[0,1.1],
                                                gridcolor='#1e1e2e'))
                        st.plotly_chart(fig, use_container_width=True)
                        st.success(
                            f"✅ Best: **{cls.iloc[0]['model']}**  "
                            f"(AUC = {cls.iloc[0]['value']:.3f})")

                st.divider()

            # Predicted vs actual
            if pred_df is not None:
                if all(c in pred_df.columns
                       for c in ['stress_avg','stress_predicted']):
                    st.markdown("### 🎯 Predicted vs Actual Stress")
                    col1, col2 = st.columns(2)

                    with col1:
                        d   = pred_df[['stress_avg','stress_predicted']].dropna()
                        mae = (d['stress_avg']-d['stress_predicted']).abs().mean()
                        fig = go.Figure()
                        fig.add_scatter(x=d['stress_avg'],
                                        y=d['stress_predicted'],
                                        mode='markers',
                                        marker=dict(color=C['ml'],
                                                    size=5,opacity=0.3))
                        fig.add_scatter(x=[1,5],y=[1,5],mode='lines',
                                        line=dict(color='white',
                                                  width=1.5,dash='dash'))
                        fig.add_annotation(
                            text=f"MAE = {mae:.3f}",
                            xref="paper",yref="paper",x=0.05,y=0.95,
                            showarrow=False,
                            font=dict(size=13,color='#c8c8e8'),
                            bgcolor='rgba(30,30,46,0.85)',
                            borderwidth=1,borderpad=8)
                        apply_layout(fig, height=300, showlegend=False,
                                     xaxis=dict(title='Actual',
                                                range=[0.5,5.5],
                                                gridcolor='#1e1e2e'),
                                     yaxis=dict(title='Predicted',
                                                range=[0.5,5.5],
                                                gridcolor='#1e1e2e'))
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption("Points on the line = perfect prediction")

                    with col2:
                        if all(c in pred_df.columns
                               for c in ['high_stress_prob','study_week']):
                            pw = (pred_df.groupby('study_week')
                                  ['high_stress_prob'].mean().reindex(WEEKS))
                            fig = go.Figure(go.Bar(
                                x=[f'W{w}' for w in WEEKS],
                                y=pw.values,
                                marker_color=[
                                    C['stress'] if (not np.isnan(v) and v>=0.4)
                                    else C['social'] if (not np.isnan(v) and v>=0.25)
                                    else C['sleep']
                                    for v in pw.values],
                                text=[f"{v:.0%}" if not np.isnan(v) else ""
                                      for v in pw.values],
                                textposition='outside'))
                            fig.add_hline(y=0.25, line_dash='dash',
                                          line_color='#F0A050',
                                          annotation_text='25% risk threshold')
                            apply_layout(fig, height=300,
                                         yaxis=dict(
                                             title='High-stress probability',
                                             tickformat=',.0%',
                                             range=[0,0.85],
                                             gridcolor='#1e1e2e'))
                            st.plotly_chart(fig, use_container_width=True)

                    st.divider()

            # Feature importance
            if fi_df is not None:
                st.markdown("### 🏆 Feature Importance")
                lc = 'label' if 'label' in fi_df.columns else 'feature'
                if lc in fi_df.columns and 'importance' in fi_df.columns:
                    fi_s = fi_df.sort_values('importance',ascending=True).tail(10)
                    clrs = []
                    for feat in fi_s[lc]:
                        fl = str(feat).lower()
                        clrs.append(
                            C['sleep']    if 'sleep' in fl else
                            C['exercise'] if 'walk'  in fl else
                            C['social']   if 'talk'  in fl else
                            C['mood']     if 'device' in fl or 'bt' in fl
                            else C['ml']
                        )
                    fig = go.Figure(go.Bar(
                        x=fi_s['importance'], y=fi_s[lc],
                        orientation='h', marker_color=clrs,
                        text=[f"{v:.4f}" for v in fi_s['importance']],
                        textposition='outside'))
                    apply_layout(fig, height=360, showlegend=False,
                                 xaxis=dict(title='Importance score',
                                            gridcolor='#1e1e2e'))
                    st.plotly_chart(fig, use_container_width=True)
                    top3 = fi_df.sort_values('importance',ascending=False).head(3)
                    st.markdown("**Top 3 predictors of stress:**")
                    for _,row in top3.iterrows():
                        st.markdown(f"- **{row[lc]}** — {row['importance']:.4f}")

                st.divider()

            # Student clusters
            if cluster_df is not None and 'cluster' in cluster_df.columns:
                st.markdown("### 👥 Student Behaviour Clusters")
                counts = cluster_df['cluster'].value_counts().sort_index()
                col1, col2 = st.columns([1,2])

                with col1:
                    fig = go.Figure(go.Pie(
                        labels=[f"Cluster {c}" for c in counts.index],
                        values=counts.values,
                        marker_colors=[C['stress'],C['sleep'],C['mood'],
                                       C['exercise'],C['social']][:len(counts)],
                        hole=0.4, textinfo='label+value'))
                    apply_layout(fig, height=260, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    if 'uid' in df.columns:
                        df_c = df.merge(cluster_df[['uid','cluster']],
                                        on='uid', how='left')
                        pcols = [c for c in [
                            'stress_avg','sleep_hours','fraction_walking',
                            'total_talking_minutes','unique_devices_nearby']
                            if c in df_c.columns]
                        if pcols:
                            profile = df_c.groupby('cluster')[pcols].mean()
                            pn = ((profile - profile.min()) /
                                  (profile.max() - profile.min() + 1e-9))
                            pn = pn.rename(columns={
                                'stress_avg':'Stress',
                                'sleep_hours':'Sleep',
                                'fraction_walking':'Walking',
                                'total_talking_minutes':'Talking',
                                'unique_devices_nearby':'BT devices'})
                            fig = go.Figure()
                            clr = [C['stress'],C['sleep'],C['mood'],C['exercise']]
                            for i,(idx,row) in enumerate(pn.iterrows()):
                                fig.add_bar(name=f"Cluster {idx}",
                                            x=row.index.tolist(),
                                            y=row.values,
                                            marker_color=clr[i%len(clr)])
                            apply_layout(fig, height=260, barmode='group',
                                         yaxis=dict(title='Score (0–1)',
                                                    range=[0,1.2],
                                                    gridcolor='#1e1e2e'),
                                         legend=dict(orientation='h',y=-0.25))
                            st.plotly_chart(fig, use_container_width=True)

                st.markdown("**Students per cluster:**")
                n_cl  = cluster_df['cluster'].nunique()
                cl_c  = st.columns(min(n_cl,4))
                for col,(cl,grp) in zip(cl_c, cluster_df.groupby('cluster')):
                    col.markdown(f"**Cluster {cl}** ({len(grp)})")
                    col.write(", ".join(sorted(grp['uid'].tolist())))
