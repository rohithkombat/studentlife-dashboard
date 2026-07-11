# ─────────────────────────────────────────────────────────────────────────────
# StudentLife Visual Analytics Dashboard
# Dissertation: Visual Analytics for Digital Health
# Author: Rohith Elanchezhian | Newcastle University
#
# Data files are loaded automatically from the data/ folder.
# No manual uploading required.
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

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0f0f11; }
[data-testid="stSidebar"]          { background-color: #17171a; }
[data-testid="stHeader"]           { background-color: #0f0f11; }
.block-container { padding-top: 1.5rem; }
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
    paper_bgcolor='#17171a',
    plot_bgcolor='#1e1e22',
    font=dict(color='#e8e8ea', family='sans-serif', size=12),
    margin=dict(l=40, r=20, t=40, b=40),
)

DAY_NAMES = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
WEEKS     = list(range(1, 11))

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def safe_mean(df, col):
    if col in df.columns and df[col].notna().any():
        return df[col].mean()
    return None

def apply_layout(fig, height=300, **extra):
    fig.update_layout(**LAYOUT, height=height, **extra)
    fig.update_xaxes(gridcolor='#2a2a2f')
    fig.update_yaxes(gridcolor='#2a2a2f')
    return fig

def quality_check(df, uid_col='uid', stress_col='stress_avg', threshold=5):
    counts = df.groupby(uid_col)[stress_col].count()
    return {uid: (int(n), n < threshold) for uid, n in counts.items()}

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING — reads directly from the data/ folder, no upload needed
# ─────────────────────────────────────────────────────────────────────────────

DATA_DIR = 'data'   # folder inside the GitHub repository

@st.cache_data
def load_master():
    path = os.path.join(DATA_DIR, 'daily_master.csv')
    df = pd.read_csv(path)
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
def load_ml_file(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    if 'student_id' in df.columns:
        df.rename(columns={'student_id': 'uid'}, inplace=True)
    return df

# Check if data folder and master file exist
master_path = os.path.join(DATA_DIR, 'daily_master.csv')

if not os.path.exists(master_path):
    st.title("🎓 StudentLife Dashboard")
    st.error(
        "**Data files not found.**  \n"
        "Make sure the `data/` folder exists in your GitHub repository "
        "and contains `daily_master.csv`."
    )
    st.markdown("""
    **How to fix this:**
    1. Go to your GitHub repository
    2. Create a folder called `data`
    3. Upload these files into it:
       - `daily_master.csv` ← required
       - `ml_predictions.csv`
       - `ml_clusters.csv`
       - `ml_feature_importance.csv`
       - `ml_performance.csv`
    4. Streamlit will reload automatically
    """)
    st.stop()

# Load all files automatically
df         = load_master()
pred_df    = load_ml_file('ml_predictions.csv')
cluster_df = load_ml_file('ml_clusters.csv')
fi_df      = load_ml_file('ml_feature_importance.csv')
perf_df    = load_ml_file('ml_performance.csv')

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — filters only, no uploading
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎓 StudentLife")
    st.markdown("*Visual Analytics for Digital Health*")
    st.markdown("**Rohith Elanchezhian**")
    st.markdown("**Newcastle University**")
    st.divider()

    st.markdown("### Filters")
    week_filter = st.selectbox(
        "Study week",
        ["All weeks"] + [f"Week {w}" for w in WEEKS]
    )
    day_filter = st.selectbox(
        "Day type",
        ["All days", "Weekdays only", "Weekends only"]
    )
    st.divider()

    # Show what files are loaded
    st.markdown("### Data Status")
    st.success("✅ daily_master.csv")
    if pred_df    is not None: st.success("✅ ml_predictions.csv")
    else:                      st.warning("⚠️ ml_predictions.csv missing")
    if cluster_df is not None: st.success("✅ ml_clusters.csv")
    else:                      st.warning("⚠️ ml_clusters.csv missing")
    if fi_df      is not None: st.success("✅ ml_feature_importance.csv")
    else:                      st.warning("⚠️ ml_feature_importance.csv missing")
    if perf_df    is not None: st.success("✅ ml_performance.csv")
    else:                      st.warning("⚠️ ml_performance.csv missing")

    st.divider()
    st.caption("📊 49 students · 10 weeks · Spring 2013  \nDartmouth College, USA")

# ─────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
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
sparse_students = [uid for uid, (n, sp) in quality.items() if sp]

# ─────────────────────────────────────────────────────────────────────────────
# MAIN TITLE
# ─────────────────────────────────────────────────────────────────────────────

st.title("🎓 StudentLife Visual Analytics Dashboard")
st.caption(
    f"Showing **{len(filtered):,} rows** · "
    f"**{filtered['uid'].nunique()} students** · "
    f"Filter: {week_filter} | {day_filter}"
)
if sparse_students:
    st.warning(
        f"⚠️ {len(sparse_students)} students have fewer than 5 stress responses "
        f"— their averages are less reliable."
    )

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────

tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
    "📊 Overview",
    "📈 Weekly Trends",
    "🔗 Correlations",
    "🌡️ Stress Heatmap",
    "👤 Student Explorer",
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
    dep_valid   = (filtered['sleep_hours'].dropna()
                   if 'sleep_hours' in filtered.columns else pd.Series([]))
    dep_pct     = ((dep_valid < 7).mean()*100) if len(dep_valid) else None

    # Key findings panel
    st.markdown("### 📌 Key Findings")
    findings = []
    if stress_mean is not None and high_pct is not None:
        findings.append(("😟 Stress",
            f"Average stress is **{stress_mean:.2f}/5** and "
            f"**{high_pct:.0f}%** of days were high stress (level 4–5)."))
    if dep_pct is not None and sleep_mean is not None:
        findings.append(("😴 Sleep",
            f"Average sleep is **{sleep_mean:.1f}h** but "
            f"**{dep_pct:.0f}%** of nights fell below the recommended 7 hours."))
    if 'stress_avg' in df.columns and 'is_weekend' in df.columns:
        wd = df[df['is_weekend']==False]['stress_avg'].mean()
        we = df[df['is_weekend']==True]['stress_avg'].mean()
        if not np.isnan(wd) and not np.isnan(we):
            direction = "higher" if we > wd else "lower"
            findings.append(("😮 Surprise",
                f"Weekend stress (**{we:.2f}**) is **{direction}** than weekday "
                f"stress (**{wd:.2f}**) — unstructured time increases anxiety."))

    cols_f = st.columns(len(findings)) if findings else []
    for col, (title, text) in zip(cols_f, findings):
        col.info(f"**{title}**  \n{text}")

    st.divider()

    # Metric cards
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Avg Stress",       f"{stress_mean:.2f}/5" if stress_mean is not None else "—")
    c2.metric("High Stress Days", f"{high_pct:.0f}%"     if high_pct    is not None else "—")
    c3.metric("Avg Sleep",        f"{sleep_mean:.1f}h"   if sleep_mean  is not None else "—")
    c4.metric("Nights Under 7h",  f"{dep_pct:.0f}%"      if dep_pct     is not None else "—")
    c5.metric("Avg Mood",         f"{mood_mean:.2f}"     if mood_mean   is not None else "—")
    c6.metric("Avg Talking",      f"{talk_mean:.0f}min"  if talk_mean   is not None else "—")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Stress Level Distribution")
        if 'stress_avg' in filtered.columns:
            v = filtered['stress_avg'].dropna()
            labels = ['1 Not stressed','2','3 Moderate','4','5 Very stressed']
            counts = pd.cut(v, bins=[0.5,1.5,2.5,3.5,4.5,5.5],
                            labels=labels).value_counts().sort_index()
            fig = go.Figure(go.Bar(
                x=counts.index.tolist(), y=counts.values,
                marker_color=[C['sleep'],C['sleep'],C['neutral'],C['stress'],C['stress']],
                text=[f"{val/len(v)*100:.0f}%" for val in counts.values],
                textposition='outside'
            ))
            apply_layout(fig, height=280, showlegend=False,
                         yaxis=dict(title='Responses', gridcolor='#2a2a2f'))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Sleep Duration Categories")
        if 'sleep_hours' in filtered.columns:
            v = filtered['sleep_hours'].dropna()
            cats = pd.cut(v, bins=[-np.inf,5,7,9,np.inf],
                          labels=['Under 5h','5–7h','7–9h','Over 9h'])
            cc = cats.value_counts().sort_index()
            fig = go.Figure(go.Pie(
                labels=cc.index.tolist(), values=cc.values,
                marker_colors=[C['stress'],C['social'],C['sleep'],C['mood']],
                hole=0.45, textinfo='label+percent', textfont_size=11
            ))
            apply_layout(fig, height=280, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("##### Physical Activity Breakdown")
        act_map = {'Stationary':'fraction_stationary',
                   'Walking':'fraction_walking','Running':'fraction_running'}
        vals = {k: filtered[v].mean()*100 for k,v in act_map.items()
                if v in filtered.columns and filtered[v].notna().any()}
        if vals:
            fig = go.Figure(go.Bar(
                x=list(vals.keys()), y=list(vals.values()),
                marker_color=[C['neutral'],C['sleep'],C['exercise']],
                text=[f"{v:.1f}%" for v in vals.values()],
                textposition='outside'
            ))
            apply_layout(fig, height=260, showlegend=False,
                         yaxis=dict(title='% of readings', range=[0,105],
                                    gridcolor='#2a2a2f'))
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown("##### Talking Time by Day of Week")
        if all(c in filtered.columns for c in ['total_talking_minutes','day_of_week']):
            dow = (filtered.groupby('day_of_week')['total_talking_minutes']
                   .mean().reindex(range(7)))
            fig = go.Figure(go.Bar(
                x=DAY_NAMES, y=dow.values,
                marker_color=[C['social'] if i>=5 else C['mood'] for i in range(7)],
                text=[f"{v:.0f}m" if not np.isnan(v) else "" for v in dow.values],
                textposition='outside'
            ))
            apply_layout(fig, height=260, showlegend=False,
                         yaxis=dict(title='Minutes', gridcolor='#2a2a2f'))
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 2 — WEEKLY TRENDS
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### Key Variables Across the 10-Week Term")
    st.caption("🔴 shaded = finals week (Week 10)")

    weekly = df.groupby('study_week').agg(
        stress  =('stress_avg','mean'),
        sleep   =('sleep_hours','mean'),
        mood    =('mood_score_avg','mean'),
        talking =('total_talking_minutes','mean'),
        walking =('fraction_walking','mean'),
        devices =('unique_devices_nearby','mean'),
    ).reindex(WEEKS)

    fig = make_subplots(rows=2, cols=2,
        subplot_titles=['Stress Level (1–5)','Sleep Hours',
                        'Mood Score (−4 to +4)','Talking Time (min)'],
        vertical_spacing=0.2, horizontal_spacing=0.1)

    for row,col,key,color,yrange in [
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
        fig.update_yaxes(range=yrange,gridcolor='#2a2a2f',row=row,col=col)
        fig.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS],
                         gridcolor='#2a2a2f',row=row,col=col)

    fig.update_layout(height=500,paper_bgcolor='#17171a',plot_bgcolor='#1e1e22',
                      font=dict(color='#e8e8ea',size=11),showlegend=False,
                      margin=dict(l=40,r=20,t=60,b=40))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### BT Social Proximity by Week")
        if 'devices' in weekly.columns:
            fig2 = go.Figure(go.Bar(
                x=[f'W{w}' for w in WEEKS],
                y=weekly['devices'].values,
                marker_color=C['mood']))
            apply_layout(fig2, height=240,
                         yaxis=dict(title='Unique BT devices',gridcolor='#2a2a2f'))
            st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown("##### Walking Activity by Week")
        if 'walking' in weekly.columns:
            fig3 = go.Figure(go.Bar(
                x=[f'W{w}' for w in WEEKS],
                y=(weekly['walking']*100).values,
                marker_color=C['exercise']))
            apply_layout(fig3, height=240,
                         yaxis=dict(title='% time walking',gridcolor='#2a2a2f'))
            st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 3 — CORRELATIONS
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### How Variables Relate to Each Other")
    st.caption("Each dot = one student on one day  |  Dashed line = overall trend")

    candidates = [
        ('sleep_hours','stress_avg','Sleep hours','Stress level',C['stress']),
        ('sleep_hours','mood_score_avg','Sleep hours','Mood score',C['mood']),
        ('fraction_walking','stress_avg','Fraction walking','Stress level',C['exercise']),
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
            if len(d) < 5: return None
            r   = d[xc].corr(d[yc])
            m,b = np.polyfit(d[xc], d[yc], 1)
            xs  = np.linspace(d[xc].min(), d[xc].max(), 100)
            fig = go.Figure()
            fig.add_scatter(x=d[xc], y=d[yc], mode='markers',
                            marker=dict(color=color,size=5,opacity=0.4))
            fig.add_scatter(x=xs, y=m*xs+b, mode='lines',
                            line=dict(color='white',width=2,dash='dash'))
            fig.add_annotation(text=f"r = {r:.3f}",
                               xref="paper",yref="paper",x=0.05,y=0.95,
                               showarrow=False,font=dict(size=13,color='#e8e8ea'),
                               bgcolor='#2a2a2f',borderwidth=1,borderpad=6)
            apply_layout(fig, height=320, showlegend=False,
                         xaxis=dict(title=xl,gridcolor='#2a2a2f'),
                         yaxis=dict(title=yl,gridcolor='#2a2a2f'))
            return fig

        c1,c2 = st.columns(2)
        f1,f2 = make_scatter(s1), make_scatter(s2)
        if f1: c1.plotly_chart(f1, use_container_width=True)
        if f2: c2.plotly_chart(f2, use_container_width=True)

    st.markdown("#### Full Correlation Matrix")
    corr_map = {'stress_avg':'Stress','sleep_hours':'Sleep hrs',
                'sleep_rate':'Sleep quality','mood_score_avg':'Mood',
                'fraction_walking':'Walking','total_talking_minutes':'Talking',
                'unique_devices_nearby':'BT devices'}
    avail = {k:v for k,v in corr_map.items() if k in filtered.columns}
    if len(avail) >= 3:
        corr_df = filtered[list(avail.keys())].rename(columns=avail).corr()
        mask = np.triu(np.ones(corr_df.shape,dtype=bool),k=1)
        corr_df[mask] = None
        fig_c = px.imshow(corr_df,color_continuous_scale='RdBu_r',
                          zmin=-1,zmax=1,text_auto='.2f',aspect='auto')
        fig_c.update_traces(textfont_size=11)
        apply_layout(fig_c, height=380)
        st.plotly_chart(fig_c, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 4 — STRESS HEATMAP
# ═══════════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### Student × Week Stress Heatmap")
    st.caption("Green = calm  |  Red = high stress  |  White = no data")

    if 'stress_avg' in df.columns and 'uid' in df.columns:
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
            height=max(420, len(pivot)*18),
            paper_bgcolor='#17171a',font=dict(color='#e8e8ea',size=11),
            margin=dict(l=80,r=20,t=40,b=40),
            coloraxis_colorbar=dict(title="Stress",
                tickvals=[1,2,3,4,5],ticktext=['1 Calm','2','3 Mod','4','5 High']))
        st.plotly_chart(fig_hm, use_container_width=True)

        sm = df.groupby('uid')['stress_avg'].mean().dropna()
        if len(sm):
            c1,c2,c3 = st.columns(3)
            c1.metric("Most stressed",  sm.idxmax(), f"{sm.max():.2f}/5")
            c2.metric("Least stressed", sm.idxmin(), f"{sm.min():.2f}/5")
            c3.metric("Range", f"{sm.max()-sm.min():.2f} units","huge individual variation")

    with st.expander("📋 Data quality — responses per student"):
        q_data = [(uid,n,"⚠️ sparse" if sp else "✓ ok")
                  for uid,(n,sp) in quality.items()]
        q_df = (pd.DataFrame(q_data, columns=["Student","Stress responses","Quality"])
                .sort_values("Stress responses",ascending=False))
        st.dataframe(q_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# TAB 5 — STUDENT EXPLORER
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.markdown("#### Individual Student Explorer")
    st.caption("🟢 low stress  🟡 medium  🔴 high  |  ⚠️ = fewer than 5 responses")

    all_students  = sorted(df['uid'].unique())
    student_means = df.groupby('uid')['stress_avg'].mean().dropna()

    def label(uid):
        m  = student_means.get(uid)
        sp = quality.get(uid,(0,False))[1]
        if m is None: return uid
        icon = "🔴" if m>=3.5 else "🟡" if m>=2.5 else "🟢"
        return f"{icon} {uid}  ({m:.1f}){' ⚠️' if sp else ''}"

    col_sel, col_charts = st.columns([1,3])

    with col_sel:
        selected = st.selectbox("Select student", all_students, format_func=label)
        s   = df[df['uid']==selected]
        s_n = int(s['stress_avg'].notna().sum())
        st.markdown("---")
        s_stress = s['stress_avg'].mean()
        s_sleep  = s['sleep_hours'].mean()   if 'sleep_hours'    in s.columns else np.nan
        s_mood   = s['mood_score_avg'].mean() if 'mood_score_avg' in s.columns else np.nan
        st.metric("Avg stress",    f"{s_stress:.2f}/5" if not np.isnan(s_stress) else "—")
        st.metric("Avg sleep",     f"{s_sleep:.1f}h"   if not np.isnan(s_sleep)  else "—")
        st.metric("Avg mood",      f"{s_mood:.2f}"     if not np.isnan(s_mood)   else "—")
        st.metric("Stress surveys", s_n)
        if s_n < 5:
            st.warning(f"⚠️ Only {s_n} responses — treat with caution.")
        if cluster_df is not None and 'uid' in cluster_df.columns:
            row = cluster_df[cluster_df['uid']==selected]
            if len(row):
                st.info(f"🔵 Cluster {int(row.iloc[0]['cluster'])}")

    with col_charts:
        s_weekly = (s.groupby('study_week')
                    .agg(stress=('stress_avg','mean'),sleep=('sleep_hours','mean'))
                    .reindex(WEEKS))
        group_weekly = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)

        fig1 = go.Figure()
        fig1.add_scatter(x=WEEKS, y=s_weekly['stress'], mode='lines+markers',
                         name=selected, line=dict(color=C['stress'],width=2.5),
                         marker=dict(size=8,color=C['stress']))
        fig1.add_scatter(x=WEEKS, y=group_weekly, mode='lines',
                         name='Group average',
                         line=dict(color='#6b6b72',width=1.5,dash='dash'))
        fig1.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,line_width=0)
        fig1.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
        apply_layout(fig1, height=240,
                     title=f"{selected} — Stress vs Group Average",
                     yaxis=dict(range=[0,5.5],title='Stress',gridcolor='#2a2a2f'),
                     legend=dict(orientation='h',y=-0.3))
        st.plotly_chart(fig1, use_container_width=True)

        if 'sleep' in s_weekly.columns:
            sv = s_weekly['sleep'].values
            sc = [C['sleep'] if not np.isnan(v) and v>=7
                  else C['social'] if not np.isnan(v) and v>=5
                  else C['stress'] if not np.isnan(v)
                  else '#2a2a2f' for v in sv]
            fig2 = go.Figure(go.Bar(x=[f'W{w}' for w in WEEKS],y=sv,
                                    marker_color=sc))
            fig2.add_hline(y=7,line_dash='dash',line_color=C['sleep'],
                           annotation_text='7h recommended',
                           annotation_position='top right')
            apply_layout(fig2, height=220,
                         title=f"{selected} — Sleep by Week",
                         yaxis=dict(range=[0,14],title='Hours',gridcolor='#2a2a2f'))
            st.plotly_chart(fig2, use_container_width=True)

        if pred_df is not None and 'uid' in pred_df.columns:
            sp = pred_df[pred_df['uid']==selected]
            if len(sp) and 'stress_predicted' in sp.columns:
                sp_w = sp.groupby('study_week').agg(
                    actual=('stress_avg','mean'),
                    predicted=('stress_predicted','mean')).reindex(WEEKS)
                fig3 = go.Figure()
                fig3.add_scatter(x=WEEKS,y=sp_w['actual'],
                                 mode='lines+markers',name='Actual',
                                 line=dict(color=C['stress'],width=2))
                fig3.add_scatter(x=WEEKS,y=sp_w['predicted'],
                                 mode='lines+markers',name='Predicted',
                                 line=dict(color=C['ml'],width=2,dash='dot'))
                fig3.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
                apply_layout(fig3, height=220,
                             title=f"{selected} — Actual vs Predicted Stress",
                             yaxis=dict(range=[0,5.5],title='Stress',
                                        gridcolor='#2a2a2f'),
                             legend=dict(orientation='h',y=-0.3))
                st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 6 — ML PREDICTIONS
# ═══════════════════════════════════════════════════════════════
with tab6:
    st.markdown("#### 🤖 Machine Learning Results")

    if all(f is None for f in [pred_df, cluster_df, fi_df, perf_df]):
        st.info(
            "ML files not found in the `data/` folder.  \n"
            "Upload `ml_predictions.csv`, `ml_clusters.csv`, "
            "`ml_feature_importance.csv`, and `ml_performance.csv` "
            "to your GitHub `data/` folder."
        )
        st.stop()

    # Model performance
    if perf_df is not None:
        st.markdown("### 📊 Model Performance")
        col1,col2 = st.columns(2)

        with col1:
            st.markdown("##### Regression — lower MAE = better")
            if 'task' in perf_df.columns:
                reg = perf_df[(perf_df['task']=='regression') &
                              (perf_df['metric']=='MAE')]
                if not reg.empty:
                    reg = reg.sort_values('value')
                    colors = [C['ml'] if i==0 else C['neutral']
                              for i in range(len(reg))]
                    fig = go.Figure(go.Bar(
                        x=reg['model'], y=reg['value'],
                        marker_color=colors,
                        text=[f"{v:.3f}" for v in reg['value']],
                        textposition='outside'))
                    apply_layout(fig, height=280, showlegend=False,
                                 yaxis=dict(title='MAE',gridcolor='#2a2a2f'))
                    st.plotly_chart(fig, use_container_width=True)
                    st.success(f"✅ Best: **{reg.iloc[0]['model']}**  "
                               f"(MAE = {reg.iloc[0]['value']:.3f})")

        with col2:
            st.markdown("##### Classification — higher AUC = better")
            if 'task' in perf_df.columns:
                cls = perf_df[(perf_df['task']=='classification') &
                              (perf_df['metric']=='AUC')]
                if not cls.empty:
                    cls = cls.sort_values('value', ascending=False)
                    colors = [C['ml'] if i==0 else C['neutral']
                              for i in range(len(cls))]
                    fig = go.Figure(go.Bar(
                        x=cls['model'], y=cls['value'],
                        marker_color=colors,
                        text=[f"{v:.3f}" for v in cls['value']],
                        textposition='outside'))
                    fig.add_hline(y=0.5, line_dash='dash', line_color='#888',
                                  annotation_text='Random (0.5)')
                    apply_layout(fig, height=280, showlegend=False,
                                 yaxis=dict(title='AUC',range=[0,1.1],
                                            gridcolor='#2a2a2f'))
                    st.plotly_chart(fig, use_container_width=True)
                    st.success(f"✅ Best: **{cls.iloc[0]['model']}**  "
                               f"(AUC = {cls.iloc[0]['value']:.3f})")
        st.divider()

    # Predicted vs actual
    if pred_df is not None:
        st.markdown("### 🎯 Predicted vs Actual Stress")
        col1,col2 = st.columns(2)

        with col1:
            st.markdown("##### How close were the predictions?")
            if all(c in pred_df.columns for c in ['stress_avg','stress_predicted']):
                d = pred_df[['stress_avg','stress_predicted']].dropna()
                mae = (d['stress_avg']-d['stress_predicted']).abs().mean()
                fig = go.Figure()
                fig.add_scatter(x=d['stress_avg'], y=d['stress_predicted'],
                                mode='markers',
                                marker=dict(color=C['ml'],size=5,opacity=0.35))
                fig.add_scatter(x=[1,5],y=[1,5],mode='lines',
                                line=dict(color='white',width=1.5,dash='dash'),
                                name='Perfect')
                fig.add_annotation(text=f"MAE = {mae:.3f}",
                                   xref="paper",yref="paper",x=0.05,y=0.95,
                                   showarrow=False,font=dict(size=13,color='#e8e8ea'),
                                   bgcolor='#2a2a2f',borderwidth=1,borderpad=6)
                apply_layout(fig, height=300, showlegend=False,
                             xaxis=dict(title='Actual stress',range=[0.5,5.5],
                                        gridcolor='#2a2a2f'),
                             yaxis=dict(title='Predicted stress',range=[0.5,5.5],
                                        gridcolor='#2a2a2f'))
                st.plotly_chart(fig, use_container_width=True)
                st.caption("Points on the dashed line = perfect prediction")

        with col2:
            st.markdown("##### High stress probability by week")
            if all(c in pred_df.columns for c in ['high_stress_prob','study_week']):
                pw = (pred_df.groupby('study_week')['high_stress_prob']
                      .mean().reindex(WEEKS))
                fig = go.Figure(go.Bar(
                    x=[f'W{w}' for w in WEEKS], y=pw.values,
                    marker_color=[
                        C['stress'] if (not np.isnan(v) and v>=0.4)
                        else C['social'] if (not np.isnan(v) and v>=0.25)
                        else C['sleep'] for v in pw.values],
                    text=[f"{v:.0%}" if not np.isnan(v) else "" for v in pw.values],
                    textposition='outside'))
                fig.add_hline(y=0.25, line_dash='dash', line_color='#F0A050',
                              annotation_text='25% risk')
                apply_layout(fig, height=300,
                             yaxis=dict(title='Avg high-stress probability',
                                        tickformat=',.0%',range=[0,0.8],
                                        gridcolor='#2a2a2f'))
                st.plotly_chart(fig, use_container_width=True)

        # Residuals
        if all(c in pred_df.columns for c in ['stress_avg','stress_predicted']):
            d = pred_df[['stress_avg','stress_predicted']].dropna()
            residuals = d['stress_avg'] - d['stress_predicted']
            fig = go.Figure(go.Histogram(x=residuals, nbinsx=30,
                                         marker_color=C['ml'], opacity=0.75))
            fig.add_vline(x=0, line_dash='dash', line_color='white')
            apply_layout(fig, height=220, showlegend=False,
                         xaxis=dict(title='Error (actual − predicted)',
                                    gridcolor='#2a2a2f'),
                         yaxis=dict(title='Count',gridcolor='#2a2a2f'))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Ideal = centred on zero with a narrow spread")

        st.divider()

    # Feature importance
    if fi_df is not None:
        st.markdown("### 🏆 Feature Importance")
        st.caption("Which daily signals matter most for predicting stress?")
        label_col = 'label' if 'label' in fi_df.columns else 'feature'
        if 'importance' in fi_df.columns and label_col in fi_df.columns:
            fi_s = fi_df.sort_values('importance', ascending=True).tail(10)
            colors = []
            for feat in fi_s[label_col]:
                fl = str(feat).lower()
                if 'sleep'    in fl: colors.append(C['sleep'])
                elif 'walk'   in fl: colors.append(C['exercise'])
                elif 'talk'   in fl: colors.append(C['social'])
                elif 'bt'     in fl or 'device' in fl: colors.append(C['mood'])
                else:                colors.append(C['ml'])
            fig = go.Figure(go.Bar(
                x=fi_s['importance'], y=fi_s[label_col],
                orientation='h', marker_color=colors,
                text=[f"{v:.4f}" for v in fi_s['importance']],
                textposition='outside'))
            apply_layout(fig, height=380, showlegend=False,
                         xaxis=dict(title='Importance score',gridcolor='#2a2a2f'))
            st.plotly_chart(fig, use_container_width=True)

            top3 = fi_df.sort_values('importance',ascending=False).head(3)
            st.markdown("**Top 3 most important features for predicting stress:**")
            for _, row in top3.iterrows():
                st.markdown(f"- **{row[label_col]}** — score {row['importance']:.4f}")
        st.divider()

    # Clusters
    if cluster_df is not None:
        st.markdown("### 👥 Student Behaviour Clusters")
        st.caption("Students grouped by similar daily behaviour — no stress labels used")

        if 'cluster' in cluster_df.columns and 'uid' in cluster_df.columns:
            counts = cluster_df['cluster'].value_counts().sort_index()
            col1,col2 = st.columns([1,2])

            with col1:
                st.markdown("##### Students per cluster")
                fig = go.Figure(go.Pie(
                    labels=[f"Cluster {c}" for c in counts.index],
                    values=counts.values,
                    marker_colors=[C['stress'],C['sleep'],C['mood'],
                                   C['exercise'],C['social']][:len(counts)],
                    hole=0.4, textinfo='label+value'))
                apply_layout(fig, height=280, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                if 'uid' in df.columns:
                    df_c = df.merge(cluster_df[['uid','cluster']], on='uid', how='left')
                    pcols = [c for c in ['stress_avg','sleep_hours',
                                         'fraction_walking','total_talking_minutes',
                                         'unique_devices_nearby']
                             if c in df_c.columns]
                    if pcols:
                        profile = df_c.groupby('cluster')[pcols].mean()
                        pn = (profile - profile.min()) / \
                             (profile.max() - profile.min() + 1e-9)
                        pn = pn.rename(columns={
                            'stress_avg':'Stress','sleep_hours':'Sleep',
                            'fraction_walking':'Walking',
                            'total_talking_minutes':'Talking',
                            'unique_devices_nearby':'BT devices'})
                        st.markdown("##### Cluster profiles *(normalised 0–1)*")
                        fig = go.Figure()
                        clr = [C['stress'],C['sleep'],C['mood'],C['exercise']]
                        for i,(idx,row) in enumerate(pn.iterrows()):
                            fig.add_bar(name=f"Cluster {idx}",
                                        x=row.index.tolist(), y=row.values,
                                        marker_color=clr[i%len(clr)])
                        apply_layout(fig, height=280, barmode='group',
                                     yaxis=dict(title='Score (0–1)',range=[0,1.2],
                                                gridcolor='#2a2a2f'),
                                     legend=dict(orientation='h',y=-0.25))
                        st.plotly_chart(fig, use_container_width=True)

            st.markdown("##### Students per cluster")
            n_cl = cluster_df['cluster'].nunique()
            cols = st.columns(min(n_cl,4))
            for col,(cl,grp) in zip(cols, cluster_df.groupby('cluster')):
                col.markdown(f"**Cluster {cl}** ({len(grp)})")
                col.write(", ".join(sorted(grp['uid'].tolist())))
