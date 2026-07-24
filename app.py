# ─────────────────────────────────────────────────────────────────────────────
# StudentLife Visual Analytics Dashboard
# Light Theme + Mobile Responsive
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
    initial_sidebar_state="collapsed"   # collapsed by default on mobile
)

# ── Light theme CSS + Mobile responsive ───────────────────────────────────────
st.markdown("""
<style>
/* ── Import font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global light theme ── */
* { font-family: 'Inter', sans-serif !important; }

[data-testid="stAppViewContainer"] {
    background-color: #F4F6FA;
}
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E0E4EE;
}
[data-testid="stHeader"] {
    background-color: #F4F6FA;
}
.block-container {
    padding-top: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 1400px;
}

/* ── Metric cards ── */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #E0E4EE;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    margin-bottom: 0.5rem;
}
.metric-val  { font-size: 1.6rem; font-weight: 700; color: #1F4E79; line-height: 1.2; }
.metric-lbl  { font-size: 0.72rem; font-weight: 500; color: #6B7280;
               text-transform: uppercase; letter-spacing: 0.06em; margin-top: 4px; }
.metric-sub  { font-size: 0.72rem; color: #9CA3AF; margin-top: 2px; }

/* ── Finding cards ── */
.find-card {
    background: #FFFFFF;
    border-left: 4px solid #1F4E79;
    border-radius: 0 10px 10px 0;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.find-card.red    { border-left-color: #DC2626; }
.find-card.teal   { border-left-color: #0891B2; }
.find-card.orange { border-left-color: #D97706; }
.find-title { font-size: 0.85rem; font-weight: 600; color: #111827; margin-bottom: 2px; }
.find-text  { font-size: 0.8rem;  color: #6B7280; line-height: 1.5; }

/* ── Section title ── */
.sec-title {
    font-size: 1rem; font-weight: 600; color: #1F4E79;
    border-bottom: 2px solid #DBEAFE;
    padding-bottom: 4px; margin-bottom: 0.5rem;
}

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    flex-wrap: wrap;              /* wrap tabs on small screens */
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 500;
    color: #6B7280;
    padding: 0.4rem 0.7rem;
    white-space: nowrap;
}
.stTabs [aria-selected="true"] {
    background: #1F4E79 !important;
    color: #FFFFFF !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #374151 !important;
}
[data-testid="stSidebar"] .stSelectbox label {
    color: #374151 !important;
}

/* ── Mobile responsive ── */
@media (max-width: 768px) {
    .block-container { padding-left: 0.5rem; padding-right: 0.5rem; }
    .metric-val { font-size: 1.3rem; }
    .stTabs [data-baseweb="tab"] { font-size: 0.75rem; padding: 0.3rem 0.5rem; }
    .find-card { margin-bottom: 0.4rem; }
}

/* ── Plotly chart bg ── */
.js-plotly-plot { border-radius: 10px; }

/* ── Remove red Streamlit error styling ── */
.stAlert { border-radius: 10px; }

/* ── Divider ── */
hr { border: none; border-top: 1px solid #E5E7EB; margin: 0.75rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Colour palette (light theme) ─────────────────────────────────────────────
C = {
    'stress':   '#DC2626',
    'sleep':    '#0891B2',
    'mood':     '#7C3AED',
    'exercise': '#059669',
    'social':   '#D97706',
    'neutral':  '#6B7280',
    'ml':       '#DB2777',
    'blue':     '#1F4E79',
}

# Plotly light template
PLOT = dict(
    paper_bgcolor='#FFFFFF',
    plot_bgcolor='#F9FAFB',
    font=dict(color='#374151', family='Inter, sans-serif', size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor='#E5E7EB', linecolor='#E5E7EB', zerolinecolor='#E5E7EB'),
    yaxis=dict(gridcolor='#E5E7EB', linecolor='#E5E7EB', zerolinecolor='#E5E7EB'),
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

def apply_plot(fig, height=320, **extra):
    fig.update_layout(**PLOT, height=height, **extra)
    fig.update_xaxes(gridcolor='#E5E7EB')
    fig.update_yaxes(gridcolor='#E5E7EB')
    return fig

def metric_card(label, value, sub='', color='#1F4E79'):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="color:{color}">{value}</div>
        <div class="metric-lbl">{label}</div>
        <div class="metric-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def find_card(icon, title, text, style=''):
    st.markdown(f"""
    <div class="find-card {style}">
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
    path = os.path.join(DATA_DIR, 'daily_master.csv')
    df   = pd.read_csv(path)
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
        df.rename(columns={'student_id':'uid'}, inplace=True)
    return df

# Check data exists
if not os.path.exists(os.path.join(DATA_DIR, 'daily_master.csv')):
    st.title("🎓 StudentLife Dashboard")
    st.error("**Data not found.** Add CSV files to the `data/` folder in your GitHub repository.")
    st.stop()

df         = load_master()
pred_df    = load_ml('ml_predictions.csv')
cluster_df = load_ml('ml_clusters.csv')
fi_df      = load_ml('ml_feature_importance.csv')
perf_df    = load_ml('ml_performance.csv')

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — filters only
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🎓 StudentLife")
    st.markdown("**Visual Analytics for Digital Health**")
    st.caption("Rohith Elanchezhian · Newcastle University")
    st.divider()

    st.markdown("**Filters**")
    week_filter = st.selectbox("Study week",
        ["All weeks"] + [f"Week {w}" for w in WEEKS])
    day_filter  = st.selectbox("Day type",
        ["All days", "Weekdays only", "Weekends only"])

    st.divider()
    st.markdown("**Data loaded**")
    st.success("✅ daily_master.csv")
    for f, label in [
        ('ml_predictions.csv',       'ml_predictions'),
        ('ml_clusters.csv',          'ml_clusters'),
        ('ml_feature_importance.csv','ml_feature_importance'),
        ('ml_performance.csv',       'ml_performance'),
    ]:
        if load_ml(f) is not None:
            st.success(f"✅ {label}")
        else:
            st.caption(f"⬜ {label}")

    st.divider()
    st.caption("📊 49 students · 10 weeks · Spring 2013")

# ─────────────────────────────────────────────────────────────────────────────
# FILTER
# ─────────────────────────────────────────────────────────────────────────────

filtered = df.copy()
if week_filter != "All weeks":
    filtered = filtered[filtered['study_week'] == int(week_filter.split(" ")[1])]
if day_filter == "Weekdays only":
    filtered = filtered[filtered['is_weekend'] == False]
elif day_filter == "Weekends only":
    filtered = filtered[filtered['is_weekend'] == True]

quality = quality_check(df)
sparse  = [u for u,(n,sp) in quality.items() if sp]

# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div style='background:#1F4E79;border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:1rem'>
    <h1 style='color:#FFFFFF;font-size:1.5rem;font-weight:700;margin:0'>
        🎓 StudentLife Visual Analytics
    </h1>
    <p style='color:#93C5FD;font-size:0.85rem;margin:4px 0 0'>
        Digital Health · 49 students · 10 weeks · Newcastle University
    </p>
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

# ═══════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════
with tab1:

    s_mean  = safe_mean(filtered, 'stress_avg')
    sl_mean = safe_mean(filtered, 'sleep_hours')
    m_mean  = safe_mean(filtered, 'mood_score_avg')
    t_mean  = safe_mean(filtered, 'total_talking_minutes')
    h_pct   = (filtered['high_stress'].mean()*100
               if 'high_stress' in filtered.columns else None)
    dep     = filtered['sleep_hours'].dropna() if 'sleep_hours' in filtered.columns else pd.Series([])
    d_pct   = ((dep<7).mean()*100) if len(dep) else None

    # Finding cards — 1 column on mobile, 3 on desktop
    sec("📌 Key Findings")
    c1,c2,c3 = st.columns(3)
    with c1:
        if s_mean and h_pct:
            find_card("😟","Stress",
                f"Average <b>{s_mean:.2f}/5</b> · <b>{h_pct:.0f}%</b> of days high stress",
                "red")
    with c2:
        if d_pct and sl_mean:
            find_card("😴","Sleep",
                f"Average <b>{sl_mean:.1f}h</b> · <b>{d_pct:.0f}%</b> nights under 7h",
                "teal")
    with c3:
        wd = df[df['is_weekend']==False]['stress_avg'].mean() if 'is_weekend' in df.columns else np.nan
        we = df[df['is_weekend']==True]['stress_avg'].mean()  if 'is_weekend' in df.columns else np.nan
        if pd.notna(wd) and pd.notna(we):
            d = "higher" if we>wd else "lower"
            find_card("😮","Weekend Surprise",
                f"Weekend stress <b>{we:.2f}</b> is <b>{d}</b> than weekday <b>{wd:.2f}</b> (p=0.007)",
                "orange")

    st.divider()

    # Metric cards — 3 per row on mobile, 6 on desktop
    sec("📊 Key Metrics")
    r1 = st.columns(3)
    r2 = st.columns(3)
    with r1[0]: metric_card("Avg Stress",      f"{s_mean:.2f}/5"  if s_mean  else "—","out of 5",       C['stress'])
    with r1[1]: metric_card("High Stress Days", f"{h_pct:.0f}%"   if h_pct   else "—","level 4–5",      C['social'])
    with r1[2]: metric_card("Avg Sleep",        f"{sl_mean:.1f}h" if sl_mean else "—","per night",       C['sleep'])
    with r2[0]: metric_card("Under 7h Nights",  f"{d_pct:.0f}%"  if d_pct   else "—","deprived",        C['mood'])
    with r2[1]: metric_card("Avg Mood",         f"{m_mean:.2f}"  if m_mean   else "—","−4 to +4",        C['exercise'])
    with r2[2]: metric_card("Avg Talking",      f"{t_mean:.0f}m" if t_mean   else "—","per day",         C['neutral'])

    st.divider()

    # Charts — stacked on mobile (1 col), side by side on desktop (2 col)
    col1, col2 = st.columns([1,1])

    with col1:
        sec("Stress Distribution")
        if 'stress_avg' in filtered.columns:
            v = filtered['stress_avg'].dropna()
            labels = ['1 Not stressed','2','3 Moderate','4','5 Very stressed']
            counts = pd.cut(v, bins=[0.5,1.5,2.5,3.5,4.5,5.5],
                            labels=labels).value_counts().sort_index()
            fig = go.Figure(go.Bar(
                x=counts.index.tolist(), y=counts.values,
                marker_color=['#0891B2','#0891B2','#6B7280','#DC2626','#DC2626'],
                text=[f"{val/len(v)*100:.0f}%" for val in counts.values],
                textposition='outside'
            ))
            apply_plot(fig, height=280, showlegend=False,
                       yaxis=dict(title='Responses',gridcolor='#E5E7EB'))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        sec("Sleep Categories")
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
            apply_plot(fig, height=280, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns([1,1])

    with col3:
        sec("Physical Activity")
        act = {'Stationary':'fraction_stationary',
               'Walking':'fraction_walking',
               'Running':'fraction_running'}
        vals = {k: filtered[v].mean()*100 for k,v in act.items()
                if v in filtered.columns and filtered[v].notna().any()}
        if vals:
            fig = go.Figure(go.Bar(
                x=list(vals.keys()), y=list(vals.values()),
                marker_color=[C['neutral'],C['sleep'],C['exercise']],
                text=[f"{v:.1f}%" for v in vals.values()],
                textposition='outside'
            ))
            apply_plot(fig, height=260, showlegend=False,
                       yaxis=dict(title='% of readings',range=[0,105],gridcolor='#E5E7EB'))
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        sec("Talking Time by Day")
        if all(c in filtered.columns for c in ['total_talking_minutes','day_of_week']):
            dow = (filtered.groupby('day_of_week')['total_talking_minutes']
                   .mean().reindex(range(7)))
            fig = go.Figure(go.Bar(
                x=DAY_NAMES, y=dow.values,
                marker_color=[C['social'] if i>=5 else C['blue'] for i in range(7)],
                text=[f"{v:.0f}m" if not np.isnan(v) else "" for v in dow.values],
                textposition='outside'
            ))
            apply_plot(fig, height=260, showlegend=False,
                       yaxis=dict(title='Minutes',gridcolor='#E5E7EB'))
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 2 — WEEKLY TRENDS
# ═══════════════════════════════════════════════════════════════
with tab2:
    sec("📈 Key Variables Across the 10-Week Term")
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
                        'Mood Score','Talking Time (min)'],
        vertical_spacing=0.2, horizontal_spacing=0.1)

    for row,col,key,color,yr in [
        (1,1,'stress', C['stress'], [1,5]),
        (1,2,'sleep',  C['sleep'],  [3,12]),
        (2,1,'mood',   C['mood'],   [-2,2.5]),
        (2,2,'talking',C['social'], [0,70]),
    ]:
        y = weekly[key] if key in weekly.columns else [None]*10
        fig.add_scatter(x=WEEKS, y=y, mode='lines+markers',
                        line=dict(color=color,width=2.5),
                        marker=dict(size=7,color=color), row=row, col=col)
        fig.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,
                      line_width=0, row=row, col=col)
        fig.update_yaxes(range=yr,gridcolor='#E5E7EB',row=row,col=col)
        fig.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS],
                         gridcolor='#E5E7EB',row=row,col=col)

    fig.update_layout(
        height=480, paper_bgcolor='#FFFFFF', plot_bgcolor='#F9FAFB',
        font=dict(color='#374151',size=11), showlegend=False,
        margin=dict(l=40,r=20,t=60,b=40))
    st.plotly_chart(fig, use_container_width=True)

    col1,col2 = st.columns(2)
    with col1:
        sec("BT Social Proximity by Week")
        if 'devices' in weekly.columns:
            fig2 = go.Figure(go.Bar(x=[f'W{w}' for w in WEEKS],
                                    y=weekly['devices'].values,
                                    marker_color=C['mood']))
            apply_plot(fig2,height=240,
                       yaxis=dict(title='Unique BT devices',gridcolor='#E5E7EB'))
            st.plotly_chart(fig2,use_container_width=True)

    with col2:
        sec("Walking Activity by Week")
        if 'walking' in weekly.columns:
            fig3 = go.Figure(go.Bar(x=[f'W{w}' for w in WEEKS],
                                    y=(weekly['walking']*100).values,
                                    marker_color=C['exercise']))
            apply_plot(fig3,height=240,
                       yaxis=dict(title='% time walking',gridcolor='#E5E7EB'))
            st.plotly_chart(fig3,use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 3 — CORRELATIONS
# ═══════════════════════════════════════════════════════════════
with tab3:
    sec("🔗 How Variables Relate to Each Other")
    st.caption("Each dot = one student on one day · Dashed line = trend")

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
        # On mobile: show dropdowns stacked
        s1 = st.selectbox("First chart",  keys, index=0)
        s2 = st.selectbox("Second chart", keys, index=min(1,len(keys)-1))

        def make_scatter(key):
            xc,yc,xl,yl,color = scatter_opts[key]
            d = filtered[[xc,yc]].dropna()
            if len(d)<5: return None
            r    = d[xc].corr(d[yc])
            m,b  = np.polyfit(d[xc],d[yc],1)
            xs   = np.linspace(d[xc].min(),d[xc].max(),100)
            fig  = go.Figure()
            fig.add_scatter(x=d[xc],y=d[yc],mode='markers',
                            marker=dict(color=color,size=5,opacity=0.4))
            fig.add_scatter(x=xs,y=m*xs+b,mode='lines',
                            line=dict(color='#374151',width=2,dash='dash'))
            fig.add_annotation(text=f"r = {r:.3f}",
                               xref="paper",yref="paper",x=0.05,y=0.95,
                               showarrow=False,font=dict(size=13,color='#111827'),
                               bgcolor='#F3F4F6',bordercolor='#D1D5DB',
                               borderwidth=1,borderpad=6)
            apply_plot(fig,height=300,showlegend=False,
                       xaxis=dict(title=xl,gridcolor='#E5E7EB'),
                       yaxis=dict(title=yl,gridcolor='#E5E7EB'))
            return fig

        c1,c2 = st.columns(2)
        f1,f2 = make_scatter(s1),make_scatter(s2)
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
        mask = np.triu(np.ones(corr_df.shape,dtype=bool),k=1)
        corr_df[mask] = None
        fig_c = px.imshow(corr_df,color_continuous_scale='RdBu_r',
                          zmin=-1,zmax=1,text_auto='.2f',aspect='auto')
        fig_c.update_traces(textfont_size=11)
        apply_plot(fig_c,height=360)
        st.plotly_chart(fig_c,use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 4 — STRESS HEATMAP
# ═══════════════════════════════════════════════════════════════
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
            paper_bgcolor='#FFFFFF',font=dict(color='#374151',size=11),
            margin=dict(l=80,r=20,t=40,b=40))
        st.plotly_chart(fig_hm,use_container_width=True)

        sm = df.groupby('uid')['stress_avg'].mean().dropna()
        c1,c2,c3 = st.columns(3)
        c1.metric("Most stressed",  sm.idxmax(), f"{sm.max():.2f}/5")
        c2.metric("Least stressed", sm.idxmin(), f"{sm.min():.2f}/5")
        c3.metric("Range across students", f"{sm.max()-sm.min():.2f} units")

    with st.expander("📋 Response count per student"):
        q_df = (pd.DataFrame([(uid,n,"⚠️ sparse" if sp else "✓ ok")
                               for uid,(n,sp) in quality.items()],
                              columns=["Student","Responses","Quality"])
                .sort_values("Responses",ascending=False))
        st.dataframe(q_df,use_container_width=True,hide_index=True)


# ═══════════════════════════════════════════════════════════════
# TAB 5 — STUDENT EXPLORER
# ═══════════════════════════════════════════════════════════════
with tab5:
    sec("👤 Individual Student Explorer")
    st.caption("🟢 low · 🟡 medium · 🔴 high stress  |  ⚠️ = sparse data")

    all_students  = sorted(df['uid'].unique()) if 'uid' in df.columns else []
    student_means = df.groupby('uid')['stress_avg'].mean().dropna() if 'uid' in df.columns else pd.Series([])

    def label(uid):
        m  = student_means.get(uid)
        sp = quality.get(uid,(0,False))[1]
        if m is None: return uid
        icon = "🔴" if m>=3.5 else "🟡" if m>=2.5 else "🟢"
        return f"{icon} {uid}  ({m:.1f}){' ⚠️' if sp else ''}"

    if not all_students:
        st.warning("No student data found.")
    else:
        # On mobile: selector full width, then charts below
        selected = st.selectbox("Select student", all_students, format_func=label)
        s   = df[df['uid']==selected]
        s_n = int(s['stress_avg'].notna().sum())

        # Quick stats in a row
        s_stress = s['stress_avg'].mean()
        s_sleep  = s['sleep_hours'].mean()   if 'sleep_hours'    in s.columns else np.nan
        s_mood   = s['mood_score_avg'].mean() if 'mood_score_avg' in s.columns else np.nan

        m1,m2,m3,m4 = st.columns(4)
        with m1: metric_card("Avg Stress",    f"{s_stress:.2f}/5" if pd.notna(s_stress) else "—","",C['stress'])
        with m2: metric_card("Avg Sleep",     f"{s_sleep:.1f}h"   if pd.notna(s_sleep)  else "—","",C['sleep'])
        with m3: metric_card("Avg Mood",      f"{s_mood:.2f}"     if pd.notna(s_mood)   else "—","",C['mood'])
        with m4: metric_card("Responses",     str(s_n),"stress surveys",C['neutral'])

        if s_n < 5:
            st.warning(f"⚠️ Only {s_n} responses — treat with caution.")
        if cluster_df is not None and 'uid' in cluster_df.columns:
            row = cluster_df[cluster_df['uid']==selected]
            if len(row):
                st.info(f"🔵 This student belongs to **Cluster {int(row.iloc[0]['cluster'])}**")

        # Charts — full width then side by side
        s_weekly = (s.groupby('study_week')
                    .agg(stress=('stress_avg','mean'),sleep=('sleep_hours','mean'))
                    .reindex(WEEKS))
        group_w  = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)

        # Stress chart — full width
        fig1 = go.Figure()
        fig1.add_scatter(x=WEEKS,y=s_weekly['stress'],mode='lines+markers',
                         name=selected,line=dict(color=C['stress'],width=2.5),
                         marker=dict(size=8,color=C['stress']))
        fig1.add_scatter(x=WEEKS,y=group_w,mode='lines',name='Group avg',
                         line=dict(color='#9CA3AF',width=1.5,dash='dash'))
        fig1.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,line_width=0)
        fig1.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
        apply_plot(fig1,height=260,title=f"{selected} — Stress vs Group Average",
                   yaxis=dict(range=[0,5.5],title='Stress',gridcolor='#E5E7EB'),
                   legend=dict(orientation='h',y=-0.3))
        st.plotly_chart(fig1,use_container_width=True)

        # Sleep chart — full width
        if 'sleep' in s_weekly.columns:
            sv = s_weekly['sleep'].values
            sc = [C['sleep'] if pd.notna(v) and v>=7
                  else C['social'] if pd.notna(v) and v>=5
                  else C['stress'] if pd.notna(v)
                  else '#E5E7EB' for v in sv]
            fig2 = go.Figure(go.Bar(x=[f'W{w}' for w in WEEKS],y=sv,
                                    marker_color=sc))
            fig2.add_hline(y=7,line_dash='dash',line_color=C['sleep'],
                           annotation_text='7h recommended',
                           annotation_position='top right')
            apply_plot(fig2,height=220,title=f"{selected} — Sleep by Week  (teal≥7h · orange=5–7h · red<5h)",
                       yaxis=dict(range=[0,14],title='Hours',gridcolor='#E5E7EB'))
            st.plotly_chart(fig2,use_container_width=True)

        # ML predictions if available
        if pred_df is not None and 'uid' in pred_df.columns:
            sp = pred_df[pred_df['uid']==selected]
            if len(sp) and 'stress_predicted' in sp.columns:
                sp_w = sp.groupby('study_week').agg(
                    actual=('stress_avg','mean'),
                    predicted=('stress_predicted','mean')).reindex(WEEKS)
                fig3 = go.Figure()
                fig3.add_scatter(x=WEEKS,y=sp_w['actual'],mode='lines+markers',
                                 name='Actual',line=dict(color=C['stress'],width=2))
                fig3.add_scatter(x=WEEKS,y=sp_w['predicted'],mode='lines+markers',
                                 name='Predicted',line=dict(color=C['ml'],width=2,dash='dot'))
                fig3.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
                apply_plot(fig3,height=220,title=f"{selected} — Actual vs Predicted Stress",
                           yaxis=dict(range=[0,5.5],title='Stress',gridcolor='#E5E7EB'),
                           legend=dict(orientation='h',y=-0.3))
                st.plotly_chart(fig3,use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 6 — COMPARE STUDENTS
# ═══════════════════════════════════════════════════════════════
with tab6:
    sec("⚖️ Compare Two Students")
    st.caption("Pick two students to compare their patterns side by side")

    all_students = sorted(df['uid'].unique()) if 'uid' in df.columns else []
    if len(all_students) < 2:
        st.info("Not enough student data to compare.")
    else:
        # Stacked on mobile
        sa = st.selectbox("Student A", all_students, index=0, key="csa")
        sb = st.selectbox("Student B", all_students,
                          index=min(1,len(all_students)-1), key="csb")

        da = df[df['uid']==sa]
        db = df[df['uid']==sb]

        # Comparison table
        compare_cols = [
            ("Avg Stress",    'stress_avg',            "",  C['stress'], False),
            ("Avg Sleep",     'sleep_hours',            "h", C['sleep'],  False),
            ("Avg Mood",      'mood_score_avg',         "",  C['mood'],   False),
            ("Walking %",     'fraction_walking',       "%", C['exercise'],True),
            ("Talking (min)", 'total_talking_minutes',  "m", C['social'], False),
        ]

        rows = []
        for label_c,col,unit,color,is_pct in compare_cols:
            if col not in df.columns: continue
            va = da[col].mean()
            vb = db[col].mean()
            fmta = f"{va*100:.1f}{unit}" if is_pct and pd.notna(va) else f"{va:.2f}{unit}" if pd.notna(va) else "—"
            fmtb = f"{vb*100:.1f}{unit}" if is_pct and pd.notna(vb) else f"{vb:.2f}{unit}" if pd.notna(vb) else "—"
            rows.append({"Metric":label_c, sa:fmta, sb:fmtb})

        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.divider()

        # Side by side stress charts — stack on mobile
        col1,col2 = st.columns(2)
        for col,student,data,color in [
            (col1,sa,da,C['stress']),
            (col2,sb,db,C['mood']),
        ]:
            with col:
                sec(f"{student} — Stress by Week")
                sw  = data.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)
                ga  = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)
                fig = go.Figure()
                fig.add_scatter(x=WEEKS,y=sw,mode='lines+markers',
                                name=student,line=dict(color=color,width=2.5),
                                marker=dict(size=7,color=color))
                fig.add_scatter(x=WEEKS,y=ga,mode='lines',name='Group',
                                line=dict(color='#9CA3AF',width=1.5,dash='dash'))
                fig.add_vrect(x0=9.5,x1=10.5,fillcolor='red',opacity=0.07,line_width=0)
                fig.update_xaxes(tickvals=WEEKS,ticktext=[f'W{w}' for w in WEEKS])
                apply_plot(fig,height=240,
                           yaxis=dict(range=[0,5.5],gridcolor='#E5E7EB'),
                           legend=dict(orientation='h',y=-0.3))
                st.plotly_chart(fig,use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 7 — ML PREDICTIONS
# ═══════════════════════════════════════════════════════════════
with tab7:
    sec("🤖 Machine Learning Results")

    if all(f is None for f in [pred_df,cluster_df,fi_df,perf_df]):
        st.info("Upload ML CSV files to the `data/` folder to see this tab.")
        st.markdown("""
        Files needed:
        - `ml_predictions.csv`
        - `ml_clusters.csv`
        - `ml_feature_importance.csv`
        - `ml_performance.csv`
        """)
        st.stop()

    # Model performance
    if perf_df is not None and 'task' in perf_df.columns:
        sec("Model Performance")
        col1,col2 = st.columns(2)

        with col1:
            st.caption("Regression — lower MAE = better")
            reg = perf_df[(perf_df['task']=='regression') & (perf_df['metric']=='MAE')]
            if not reg.empty:
                reg = reg.sort_values('value')
                fig = go.Figure(go.Bar(
                    x=reg['model'],y=reg['value'],
                    marker_color=[C['blue'] if i==0 else '#D1D5DB' for i in range(len(reg))],
                    text=[f"{v:.3f}" for v in reg['value']],textposition='outside'))
                apply_plot(fig,height=260,showlegend=False,
                           yaxis=dict(title='MAE',gridcolor='#E5E7EB'))
                st.plotly_chart(fig,use_container_width=True)
                st.success(f"✅ Best: **{reg.iloc[0]['model']}**  (MAE = {reg.iloc[0]['value']:.3f})")

        with col2:
            st.caption("Classification — higher AUC = better")
            cls = perf_df[(perf_df['task']=='classification') & (perf_df['metric']=='AUC')]
            if not cls.empty:
                cls = cls.sort_values('value',ascending=False)
                fig = go.Figure(go.Bar(
                    x=cls['model'],y=cls['value'],
                    marker_color=[C['blue'] if i==0 else '#D1D5DB' for i in range(len(cls))],
                    text=[f"{v:.3f}" for v in cls['value']],textposition='outside'))
                fig.add_hline(y=0.5,line_dash='dash',line_color='#9CA3AF',
                              annotation_text='Random (0.5)')
                apply_plot(fig,height=260,showlegend=False,
                           yaxis=dict(title='AUC',range=[0,1.1],gridcolor='#E5E7EB'))
                st.plotly_chart(fig,use_container_width=True)
                st.success(f"✅ Best: **{cls.iloc[0]['model']}**  (AUC = {cls.iloc[0]['value']:.3f})")

        st.divider()

    # Predicted vs actual
    if pred_df is not None and all(c in pred_df.columns for c in ['stress_avg','stress_predicted']):
        sec("Predicted vs Actual Stress")
        col1,col2 = st.columns(2)

        with col1:
            st.caption("Scatter — how close were the predictions?")
            d   = pred_df[['stress_avg','stress_predicted']].dropna()
            mae = (d['stress_avg']-d['stress_predicted']).abs().mean()
            fig = go.Figure()
            fig.add_scatter(x=d['stress_avg'],y=d['stress_predicted'],mode='markers',
                            marker=dict(color=C['blue'],size=5,opacity=0.35))
            fig.add_scatter(x=[1,5],y=[1,5],mode='lines',
                            line=dict(color='#374151',width=1.5,dash='dash'))
            fig.add_annotation(text=f"MAE = {mae:.3f}",
                               xref="paper",yref="paper",x=0.05,y=0.95,
                               showarrow=False,font=dict(size=13,color='#111827'),
                               bgcolor='#F3F4F6',borderwidth=1,borderpad=6)
            apply_plot(fig,height=300,showlegend=False,
                       xaxis=dict(title='Actual stress',range=[0.5,5.5],gridcolor='#E5E7EB'),
                       yaxis=dict(title='Predicted stress',range=[0.5,5.5],gridcolor='#E5E7EB'))
            st.plotly_chart(fig,use_container_width=True)

        with col2:
            st.caption("High stress probability by week")
            if all(c in pred_df.columns for c in ['high_stress_prob','study_week']):
                pw = pred_df.groupby('study_week')['high_stress_prob'].mean().reindex(WEEKS)
                fig = go.Figure(go.Bar(
                    x=[f'W{w}' for w in WEEKS],y=pw.values,
                    marker_color=[C['stress'] if (pd.notna(v) and v>=0.4)
                                  else C['social'] if (pd.notna(v) and v>=0.25)
                                  else C['sleep'] for v in pw.values],
                    text=[f"{v:.0%}" if pd.notna(v) else "" for v in pw.values],
                    textposition='outside'))
                fig.add_hline(y=0.25,line_dash='dash',line_color=C['social'],
                              annotation_text='25% risk')
                apply_plot(fig,height=300,
                           yaxis=dict(title='High-stress probability',
                                      tickformat=',.0%',range=[0,0.85],gridcolor='#E5E7EB'))
                st.plotly_chart(fig,use_container_width=True)

        st.divider()

    # Feature importance
    if fi_df is not None:
        sec("Feature Importance")
        st.caption("Which daily signals matter most for predicting stress?")
        lc = 'label' if 'label' in fi_df.columns else 'feature'
        if lc in fi_df.columns and 'importance' in fi_df.columns:
            fi_s = fi_df.sort_values('importance',ascending=True).tail(10)
            colors = []
            for feat in fi_s[lc]:
                fl = str(feat).lower()
                c  = (C['sleep'] if 'sleep' in fl else
                      C['exercise'] if 'walk' in fl else
                      C['social'] if 'talk' in fl else
                      C['mood'] if 'device' in fl or 'bt' in fl else C['blue'])
                colors.append(c)
            fig = go.Figure(go.Bar(
                x=fi_s['importance'],y=fi_s[lc],orientation='h',
                marker_color=colors,
                text=[f"{v:.4f}" for v in fi_s['importance']],
                textposition='outside'))
            apply_plot(fig,height=360,showlegend=False,
                       xaxis=dict(title='Importance score',gridcolor='#E5E7EB'))
            st.plotly_chart(fig,use_container_width=True)

            top3 = fi_df.sort_values('importance',ascending=False).head(3)
            st.markdown("**Top 3 predictors:**")
            for _,row in top3.iterrows():
                st.markdown(f"- **{row[lc]}** — {row['importance']:.4f}")

        st.divider()

    # Clusters
    if cluster_df is not None and 'cluster' in cluster_df.columns:
        sec("Student Behaviour Clusters")
        counts = cluster_df['cluster'].value_counts().sort_index()
        col1,col2 = st.columns(2)

        with col1:
            st.caption("Students per cluster")
            fig = go.Figure(go.Pie(
                labels=[f"Cluster {c}" for c in counts.index],
                values=counts.values,
                marker_colors=[C['stress'],C['sleep'],C['mood'],C['exercise']][:len(counts)],
                hole=0.4,textinfo='label+value'))
            apply_plot(fig,height=260,showlegend=False)
            st.plotly_chart(fig,use_container_width=True)

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
                    apply_plot(fig,height=260,barmode='group',
                               yaxis=dict(title='Score (0–1)',range=[0,1.2],gridcolor='#E5E7EB'),
                               legend=dict(orientation='h',y=-0.25))
                    st.plotly_chart(fig,use_container_width=True)

        st.markdown("**Students per cluster:**")
        cl_cols = st.columns(min(cluster_df['cluster'].nunique(),3))
        for col,(cl,grp) in zip(cl_cols,cluster_df.groupby('cluster')):
            with col:
                st.markdown(f"**Cluster {cl}** ({len(grp)})")
                st.write(", ".join(sorted(grp['uid'].tolist())))
