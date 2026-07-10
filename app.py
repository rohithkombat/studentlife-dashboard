# ─────────────────────────────────────────────────────────────────────────────
# StudentLife Visual Analytics Dashboard
# Dissertation: Visual Analytics for Digital Health
# Author: Rohith Elanchezhian | Newcastle University
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudentLife Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0f0f11; }
[data-testid="stSidebar"] { background-color: #17171a; }
[data-testid="stHeader"] { background-color: #0f0f11; }
.stMetric { background:#17171a; border:1px solid #2a2a2f;
            border-radius:12px; padding:1rem; }
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
}

# Plotly dark layout defaults
LAYOUT = dict(
    paper_bgcolor='#17171a',
    plot_bgcolor='#1e1e22',
    font=dict(color='#e8e8ea', family='sans-serif', size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor='#2a2a2f', linecolor='#2a2a2f'),
    yaxis=dict(gridcolor='#2a2a2f', linecolor='#2a2a2f'),
)

DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
WEEKS     = list(range(1, 11))


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def safe_mean(df, col):
    if col in df.columns and df[col].notna().any():
        return df[col].mean()
    return None

def apply_layout(fig, height=300, **extra):
    """Apply dark theme layout to any figure."""
    settings = {**LAYOUT, 'height': height, **extra}
    fig.update_layout(**settings)
    fig.update_xaxes(gridcolor='#2a2a2f')
    fig.update_yaxes(gridcolor='#2a2a2f')
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def load_master(file):
    df = pd.read_csv(file)
    # Normalise column names
    if 'student_id' in df.columns:
        df.rename(columns={'student_id': 'uid'}, inplace=True)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    if 'is_weekend' in df.columns:
        df['is_weekend'] = df['is_weekend'].astype(str).str.lower().isin(['true','1','yes'])
    if 'stress_avg' in df.columns:
        df['high_stress'] = df['stress_avg'] >= 4
    return df


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎓 StudentLife")
    st.markdown("*Visual Analytics for Digital Health*")
    st.markdown("**Rohith Elanchezhian | Newcastle University**")
    st.divider()

    master_file = st.file_uploader(
        "Upload daily_master.csv",
        type="csv",
        help="Find this file in Google Drive → clean_data → daily_master.csv"
    )

    if master_file:
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
        st.markdown("📊 Dataset: **49 students · 10 weeks**  \n📅 Spring 2013, Dartmouth College")


# ─────────────────────────────────────────────────────────────────────────────
# UPLOAD SCREEN
# ─────────────────────────────────────────────────────────────────────────────

st.title("🎓 StudentLife Visual Analytics Dashboard")

if not master_file:
    st.info(
        "👈 **Upload your daily_master.csv file** using the sidebar to get started.  \n"
        "Find it in: Google Drive → clean_data → daily_master.csv"
    )
    st.markdown("""
    ### What this dashboard shows
    | Tab | Contents |
    |-----|----------|
    | 📊 Overview | Summary statistics and distributions |
    | 📈 Weekly Trends | How stress, sleep, mood change across 10 weeks |
    | 🔗 Correlations | Which variables are related to each other |
    | 🌡️ Stress Heatmap | Every student × every week, colour coded |
    | 👤 Student Explorer | Individual student profiles |
    """)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# LOAD & FILTER
# ─────────────────────────────────────────────────────────────────────────────

df = load_master(master_file)

# Apply sidebar filters
filtered = df.copy()
if week_filter != "All weeks":
    wk = int(week_filter.split(" ")[1])
    filtered = filtered[filtered['study_week'] == wk]
if day_filter == "Weekdays only":
    filtered = filtered[filtered['is_weekend'] == False]
elif day_filter == "Weekends only":
    filtered = filtered[filtered['is_weekend'] == True]

# Show data size info
st.caption(
    f"Showing **{len(filtered):,} rows** from **{filtered['uid'].nunique()} students** "
    f"— Filter: {week_filter} | {day_filter}"
)


# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "📈 Weekly Trends",
    "🔗 Correlations",
    "🌡️ Stress Heatmap",
    "👤 Student Explorer"
])


# ═══════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════
with tab1:

    # Metric cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    stress_mean = safe_mean(filtered, 'stress_avg')
    sleep_mean  = safe_mean(filtered, 'sleep_hours')
    mood_mean   = safe_mean(filtered, 'mood_score_avg')
    talk_mean   = safe_mean(filtered, 'total_talking_minutes')

    high_pct  = (filtered['high_stress'].mean() * 100
                 if 'high_stress' in filtered.columns else None)
    dep_valid = filtered['sleep_hours'].dropna() if 'sleep_hours' in filtered.columns else pd.Series([])
    dep_pct   = ((dep_valid < 7).mean() * 100) if len(dep_valid) else None

    c1.metric("Avg Stress",      f"{stress_mean:.2f}/5"  if stress_mean is not None else "—")
    c2.metric("High Stress Days", f"{high_pct:.0f}%"     if high_pct    is not None else "—")
    c3.metric("Avg Sleep",        f"{sleep_mean:.1f}h"   if sleep_mean  is not None else "—")
    c4.metric("Nights Under 7h",  f"{dep_pct:.0f}%"      if dep_pct     is not None else "—")
    c5.metric("Avg Mood Score",   f"{mood_mean:.2f}"     if mood_mean   is not None else "—")
    c6.metric("Avg Talking",      f"{talk_mean:.0f} min" if talk_mean   is not None else "—")

    st.divider()
    col1, col2 = st.columns(2)

    # Stress distribution histogram
    with col1:
        st.markdown("##### Stress Level Distribution")
        if 'stress_avg' in filtered.columns:
            v = filtered['stress_avg'].dropna()
            bins   = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
            labels = ['1 — Not stressed', '2', '3 — Moderate', '4', '5 — Very stressed']
            counts = pd.cut(v, bins=bins, labels=labels).value_counts().sort_index()
            fig = go.Figure(go.Bar(
                x=counts.index.tolist(),
                y=counts.values,
                marker_color=[C['sleep'], C['sleep'], C['neutral'], C['stress'], C['stress']],
                text=[f"{val/len(v)*100:.0f}%" for val in counts.values],
                textposition='outside'
            ))
            apply_layout(fig, height=280, showlegend=False,
                         yaxis=dict(title='Responses', gridcolor='#2a2a2f'))
            st.plotly_chart(fig, use_container_width=True)

    # Sleep categories donut
    with col2:
        st.markdown("##### Sleep Duration Categories")
        if 'sleep_hours' in filtered.columns:
            v = filtered['sleep_hours'].dropna()
            cats = pd.cut(v,
                          bins=[-np.inf, 5, 7, 9, np.inf],
                          labels=['Under 5h (deprived)', '5–7h (short)',
                                  '7–9h (adequate)', 'Over 9h (long)'])
            cc = cats.value_counts().sort_index()
            fig = go.Figure(go.Pie(
                labels=cc.index.tolist(),
                values=cc.values,
                marker_colors=[C['stress'], C['social'], C['sleep'], C['mood']],
                hole=0.45,
                textinfo='label+percent',
                textfont_size=11
            ))
            apply_layout(fig, height=280, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    # Activity breakdown
    with col3:
        st.markdown("##### Physical Activity Breakdown")
        act_map = {
            'Stationary': 'fraction_stationary',
            'Walking':    'fraction_walking',
            'Running':    'fraction_running',
        }
        vals = {k: filtered[v].mean() * 100
                for k, v in act_map.items()
                if v in filtered.columns and filtered[v].notna().any()}
        if vals:
            fig = go.Figure(go.Bar(
                x=list(vals.keys()),
                y=list(vals.values()),
                marker_color=[C['neutral'], C['sleep'], C['exercise']],
                text=[f"{v:.1f}%" for v in vals.values()],
                textposition='outside'
            ))
            apply_layout(fig, height=260, showlegend=False,
                         yaxis=dict(title='% of readings', range=[0, 105],
                                    gridcolor='#2a2a2f'))
            st.plotly_chart(fig, use_container_width=True)

    # Talking by day of week
    with col4:
        st.markdown("##### Talking Time by Day of Week")
        if all(c in filtered.columns for c in ['total_talking_minutes', 'day_of_week']):
            dow = (filtered.groupby('day_of_week')['total_talking_minutes']
                   .mean().reindex(range(7)))
            colors = [C['social'] if i >= 5 else C['mood'] for i in range(7)]
            fig = go.Figure(go.Bar(
                x=DAY_NAMES,
                y=dow.values,
                marker_color=colors,
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
    st.caption("🔴 shaded area = finals week (Week 10)")

    # Always use the full dataset for weekly trends (not filtered by week)
    weekly = df.groupby('study_week').agg(
        stress  = ('stress_avg',            'mean'),
        sleep   = ('sleep_hours',           'mean'),
        mood    = ('mood_score_avg',         'mean'),
        talking = ('total_talking_minutes',  'mean'),
        walking = ('fraction_walking',       'mean'),
        devices = ('unique_devices_nearby',  'mean'),
    ).reindex(WEEKS)

    # 4-panel chart
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            'Stress Level (1–5)',
            'Sleep Hours',
            'Mood Score (−4 to +4)',
            'Talking Time (min)'
        ],
        vertical_spacing=0.2,
        horizontal_spacing=0.1
    )

    panels = [
        (1, 1, 'stress',  C['stress'],   [1, 5]),
        (1, 2, 'sleep',   C['sleep'],    [3, 12]),
        (2, 1, 'mood',    C['mood'],     [-2, 2.5]),
        (2, 2, 'talking', C['social'],   [0, 70]),
    ]

    for row, col, key, color, yrange in panels:
        y = weekly[key] if key in weekly.columns else [None] * 10
        fig.add_scatter(
            x=WEEKS, y=y,
            mode='lines+markers',
            line=dict(color=color, width=2.5),
            marker=dict(size=7, color=color),
            row=row, col=col
        )
        fig.add_vrect(
            x0=9.5, x1=10.5,
            fillcolor='red', opacity=0.07, line_width=0,
            row=row, col=col
        )
        fig.update_yaxes(range=yrange, row=row, col=col, gridcolor='#2a2a2f')
        fig.update_xaxes(tickvals=WEEKS,
                         ticktext=[f'W{w}' for w in WEEKS],
                         row=row, col=col, gridcolor='#2a2a2f')

    fig.update_layout(
        height=500,
        paper_bgcolor='#17171a',
        plot_bgcolor='#1e1e22',
        font=dict(color='#e8e8ea', size=11),
        showlegend=False,
        margin=dict(l=40, r=20, t=60, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Second row — extra charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Social Proximity by Week (BT devices nearby)")
        if 'devices' in weekly.columns:
            fig2 = go.Figure(go.Bar(
                x=[f'W{w}' for w in WEEKS],
                y=weekly['devices'].values,
                marker_color=C['mood']
            ))
            apply_layout(fig2, height=240,
                         yaxis=dict(title='Unique BT devices', gridcolor='#2a2a2f'))
            st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown("##### Walking Activity by Week")
        if 'walking' in weekly.columns:
            fig3 = go.Figure(go.Bar(
                x=[f'W{w}' for w in WEEKS],
                y=(weekly['walking'] * 100).values,
                marker_color=C['exercise']
            ))
            apply_layout(fig3, height=240,
                         yaxis=dict(title='% time walking', gridcolor='#2a2a2f'))
            st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 3 — CORRELATIONS
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### How Variables Relate to Each Other")
    st.caption("Each dot = one student on one day. The line shows the overall trend.")

    # Available pairs
    scatter_opts = {}
    candidates = [
        ('sleep_hours',           'stress_avg',         'Sleep hours',       'Stress level',    C['stress']),
        ('sleep_hours',           'mood_score_avg',      'Sleep hours',       'Mood score',      C['mood']),
        ('fraction_walking',      'stress_avg',          'Fraction walking',  'Stress level',    C['exercise']),
        ('total_talking_minutes', 'mood_score_avg',      'Talking (min)',     'Mood score',      C['social']),
        ('unique_devices_nearby', 'stress_avg',          'BT devices nearby', 'Stress level',    C['neutral']),
        ('sleep_rate',            'stress_avg',          'Sleep quality',     'Stress level',    C['sleep']),
        ('sleep_hours',           'unique_devices_nearby','Sleep hours',      'BT devices',      C['mood']),
    ]
    for xc, yc, xl, yl, color in candidates:
        if xc in filtered.columns and yc in filtered.columns:
            label = f"{xl}  vs  {yl}"
            scatter_opts[label] = (xc, yc, xl, yl, color)

    if scatter_opts:
        keys = list(scatter_opts.keys())
        col1, col2 = st.columns(2)
        sel1 = col1.selectbox("First scatter plot", keys, index=0)
        sel2 = col2.selectbox("Second scatter plot", keys,
                              index=min(1, len(keys)-1))

        def make_scatter(key):
            xc, yc, xl, yl, color = scatter_opts[key]
            d = filtered[[xc, yc]].dropna()
            if len(d) < 5:
                return None
            r = d[xc].corr(d[yc])

            # Scatter
            fig = go.Figure()
            fig.add_scatter(
                x=d[xc], y=d[yc],
                mode='markers',
                marker=dict(color=color, size=5, opacity=0.4),
                name='Data'
            )

            # Trend line (manual linear regression — no statsmodels needed)
            m, b = np.polyfit(d[xc], d[yc], 1)
            x_line = np.linspace(d[xc].min(), d[xc].max(), 100)
            fig.add_scatter(
                x=x_line, y=m * x_line + b,
                mode='lines',
                line=dict(color='white', width=2, dash='dash'),
                name='Trend'
            )

            fig.add_annotation(
                text=f"r = {r:.3f}",
                xref="paper", yref="paper", x=0.05, y=0.95,
                showarrow=False,
                font=dict(size=13, color='#e8e8ea'),
                bgcolor='#2a2a2f', bordercolor='#444', borderwidth=1, borderpad=6
            )
            apply_layout(fig, height=320,
                         xaxis=dict(title=xl, gridcolor='#2a2a2f'),
                         yaxis=dict(title=yl, gridcolor='#2a2a2f'),
                         showlegend=False)
            return fig

        c1, c2 = st.columns(2)
        f1 = make_scatter(sel1)
        f2 = make_scatter(sel2)
        if f1: c1.plotly_chart(f1, use_container_width=True)
        if f2: c2.plotly_chart(f2, use_container_width=True)

    # Correlation heatmap
    st.markdown("#### Full Correlation Matrix")
    corr_map = {
        'stress_avg':            'Stress',
        'sleep_hours':           'Sleep hrs',
        'sleep_rate':            'Sleep quality',
        'mood_score_avg':        'Mood',
        'fraction_walking':      'Walking',
        'total_talking_minutes': 'Talking',
        'unique_devices_nearby': 'BT devices',
    }
    avail = {k: v for k, v in corr_map.items() if k in filtered.columns}
    if len(avail) >= 3:
        corr_df = (filtered[list(avail.keys())]
                   .rename(columns=avail)
                   .corr())
        # Mask upper triangle
        mask = np.triu(np.ones(corr_df.shape, dtype=bool), k=1)
        corr_df[mask] = None

        fig_c = px.imshow(
            corr_df,
            color_continuous_scale='RdBu_r',
            zmin=-1, zmax=1,
            text_auto='.2f',
            aspect='auto'
        )
        fig_c.update_traces(textfont_size=11)
        apply_layout(fig_c, height=380)
        st.plotly_chart(fig_c, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 4 — STRESS HEATMAP
# ═══════════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### Student × Week Stress Heatmap")
    st.caption("Green = calm  |  Red = high stress  |  White = no data that week")

    if 'stress_avg' in df.columns and 'uid' in df.columns:
        pivot = (df.groupby(['uid', 'study_week'])['stress_avg']
                 .mean()
                 .unstack(fill_value=np.nan)
                 .reindex(columns=WEEKS))

        fig_hm = px.imshow(
            pivot,
            color_continuous_scale=[
                [0.0,  '#4ECDC4'],
                [0.25, '#A8E6CE'],
                [0.5,  '#F0A050'],
                [0.75, '#E05C5C'],
                [1.0,  '#8B0000'],
            ],
            zmin=1, zmax=5,
            text_auto='.1f',
            aspect='auto',
            labels=dict(x='Study Week', y='Student ID', color='Avg Stress')
        )
        fig_hm.update_xaxes(
            tickvals=WEEKS,
            ticktext=[f'W{w}' for w in WEEKS]
        )
        fig_hm.update_traces(textfont_size=9)
        fig_hm.update_layout(
            height=max(420, len(pivot) * 18),
            paper_bgcolor='#17171a',
            font=dict(color='#e8e8ea', size=11),
            margin=dict(l=80, r=20, t=40, b=40),
            coloraxis_colorbar=dict(
                title="Stress",
                tickvals=[1, 2, 3, 4, 5],
                ticktext=['1 Calm', '2', '3 Mod', '4', '5 High']
            )
        )
        st.plotly_chart(fig_hm, use_container_width=True)

        # Stats below heatmap
        student_means = df.groupby('uid')['stress_avg'].mean().dropna()
        if len(student_means):
            c1, c2, c3 = st.columns(3)
            c1.metric("Most stressed student",
                      student_means.idxmax(),
                      f"Mean {student_means.max():.2f}/5")
            c2.metric("Least stressed student",
                      student_means.idxmin(),
                      f"Mean {student_means.min():.2f}/5")
            c3.metric("Range across all students",
                      f"{student_means.max() - student_means.min():.2f} units",
                      "huge individual variation")


# ═══════════════════════════════════════════════════════════════
# TAB 5 — STUDENT EXPLORER
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.markdown("#### Individual Student Explorer")
    st.caption("Pick a student to see their personal stress and sleep profile across the term.")

    if 'uid' not in df.columns:
        st.warning("Student ID column not found in your data.")
        st.stop()

    all_students = sorted(df['uid'].unique())
    student_means = df.groupby('uid')['stress_avg'].mean().dropna()

    # Student selector
    def label(uid):
        m = student_means.get(uid)
        if m is None:
            return uid
        icon = "🔴" if m >= 3.5 else "🟡" if m >= 2.5 else "🟢"
        return f"{icon}  {uid}  (stress avg {m:.1f})"

    col_sel, col_charts = st.columns([1, 3])

    with col_sel:
        selected = st.selectbox(
            "Select a student",
            all_students,
            format_func=label
        )
        st.markdown("---")
        s = df[df['uid'] == selected]

        # Mini profile
        s_stress = s['stress_avg'].mean()
        s_sleep  = s['sleep_hours'].mean() if 'sleep_hours' in s.columns else None
        s_mood   = s['mood_score_avg'].mean() if 'mood_score_avg' in s.columns else None
        s_n      = int(s['stress_avg'].notna().sum())

        st.metric("Avg stress",    f"{s_stress:.2f}/5" if not np.isnan(s_stress) else "—")
        if s_sleep is not None and not np.isnan(s_sleep):
            st.metric("Avg sleep", f"{s_sleep:.1f}h")
        if s_mood is not None and not np.isnan(s_mood):
            st.metric("Avg mood",  f"{s_mood:.2f}")
        st.metric("Stress surveys", s_n)

        if s_n < 5:
            st.warning("⚠️ Fewer than 5 responses — treat with caution.")

    with col_charts:
        s_weekly = (s.groupby('study_week')
                    .agg(stress=('stress_avg', 'mean'),
                         sleep=('sleep_hours', 'mean'))
                    .reindex(WEEKS))
        group_weekly = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)

        # Stress chart
        fig1 = go.Figure()
        fig1.add_scatter(
            x=WEEKS, y=s_weekly['stress'],
            mode='lines+markers',
            name=f'{selected} stress',
            line=dict(color=C['stress'], width=2.5),
            marker=dict(size=8, color=C['stress'])
        )
        fig1.add_scatter(
            x=WEEKS, y=group_weekly,
            mode='lines',
            name='Group average',
            line=dict(color='#6b6b72', width=1.5, dash='dash')
        )
        fig1.add_vrect(x0=9.5, x1=10.5, fillcolor='red',
                       opacity=0.07, line_width=0)
        fig1.update_xaxes(tickvals=WEEKS, ticktext=[f'W{w}' for w in WEEKS])
        apply_layout(fig1, height=240,
                     title=f"{selected} — Stress vs Group Average",
                     yaxis=dict(range=[0, 5.5], title='Stress level',
                                gridcolor='#2a2a2f'),
                     legend=dict(orientation='h', y=-0.3))
        st.plotly_chart(fig1, use_container_width=True)

        # Sleep chart
        if 'sleep' in s_weekly.columns:
            sleep_vals = s_weekly['sleep'].values
            sleep_colors = []
            for v in sleep_vals:
                if np.isnan(v):
                    sleep_colors.append('#2a2a2f')
                elif v >= 7:
                    sleep_colors.append(C['sleep'])
                elif v >= 5:
                    sleep_colors.append(C['social'])
                else:
                    sleep_colors.append(C['stress'])

            fig2 = go.Figure(go.Bar(
                x=[f'W{w}' for w in WEEKS],
                y=sleep_vals,
                marker_color=sleep_colors
            ))
            fig2.add_hline(y=7, line_dash='dash', line_color=C['sleep'],
                           annotation_text='7h recommended',
                           annotation_position='top right')
            apply_layout(fig2, height=220,
                         title=f"{selected} — Sleep by Week  (teal≥7h · orange=5–7h · red<5h)",
                         yaxis=dict(range=[0, 14], title='Hours',
                                    gridcolor='#2a2a2f'))
            st.plotly_chart(fig2, use_container_width=True)

