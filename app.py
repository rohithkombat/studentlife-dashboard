# ─────────────────────────────────────────────────────────────────────────────
# StudentLife Visual Analytics Dashboard
# Dissertation: Visual Analytics for Digital Health
# Author: Rohith Elanchezhian | Newcastle University
#
# HOW TO RUN:
#   pip install streamlit plotly pandas numpy
#   streamlit run app.py
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
    .main { background-color: #0f0f11; }
    .stMetric {
        background: #17171a;
        border: 1px solid #2a2a2f;
        border-radius: 12px;
        padding: 1rem;
    }
    .stMetric label { color: #6b6b72 !important; font-size: 12px !important; }
    .stMetric [data-testid="metric-container"] { color: #e8e8ea; }
    h1, h2, h3 { color: #e8e8ea; }
    .stTabs [data-baseweb="tab"] { color: #6b6b72; }
    .stTabs [aria-selected="true"] { color: #7c6af7; }
    div[data-testid="stSidebarContent"] { background: #17171a; }
    .finding-box {
        background: #17171a;
        border: 1px solid #2a2a2f;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .upload-hint {
        background: #1e1e22;
        border: 1px dashed #2a2a2f;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        color: #6b6b72;
    }
</style>
""", unsafe_allow_html=True)

# ── Colour palette ─────────────────────────────────────────────────────────────
COLOURS = {
    'stress':   '#E05C5C',
    'sleep':    '#4ECDC4',
    'mood':     '#7C6AF7',
    'exercise': '#50C878',
    'social':   '#F0A050',
    'neutral':  '#8888AA',
    'bg':       '#17171a',
    'surface':  '#1e1e22',
    'border':   '#2a2a2f',
    'text':     '#e8e8ea',
    'muted':    '#6b6b72',
}

# Plot template for dark theme
TEMPLATE = dict(
    layout=dict(
        paper_bgcolor='#17171a',
        plot_bgcolor='#1e1e22',
        font=dict(color='#e8e8ea', family='DM Sans, sans-serif', size=12),
        xaxis=dict(gridcolor='#2a2a2f', linecolor='#2a2a2f'),
        yaxis=dict(gridcolor='#2a2a2f', linecolor='#2a2a2f'),
        margin=dict(l=40, r=20, t=40, b=40),
    )
)

DAY_NAMES  = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
WEEKS      = list(range(1, 11))

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def load_data(file):
    """Load and prepare the daily master CSV."""
    df = pd.read_csv(file)

    # Rename student_id to uid if needed
    if 'student_id' in df.columns:
        df.rename(columns={'student_id': 'uid'}, inplace=True)

    # Parse date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # Ensure booleans
    if 'is_weekend' in df.columns:
        df['is_weekend'] = df['is_weekend'].astype(bool)

    # High stress flag
    if 'stress_avg' in df.columns:
        df['high_stress'] = df['stress_avg'] >= 4

    return df

@st.cache_data
def load_csv(file):
    return pd.read_csv(file)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎓 StudentLife")
    st.markdown("**Visual Analytics for Digital Health**")
    st.markdown("---")

    st.markdown("### Upload your data")
    st.markdown("Upload the CSV files saved by the cleaning notebook.")

    master_file = st.file_uploader(
        "daily_master.csv  (required)",
        type="csv", key="master"
    )

    st.markdown("---")

    if master_file:
        st.markdown("### Filters")

        week_opt = st.selectbox(
            "Study week",
            ["All weeks"] + [f"Week {w}" for w in WEEKS]
        )

        day_opt = st.selectbox(
            "Day type",
            ["All days", "Weekdays only", "Weekends only"]
        )

        st.markdown("---")
        st.markdown("### About")
        st.markdown(
            "Dataset: [StudentLife](https://www.kaggle.com/datasets/dartweichen/student-life)  \n"
            "49 students · 10 weeks · Spring 2013  \n"
            "Dartmouth College, USA"
        )

# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────────────────────────

st.title("StudentLife Visual Analytics Dashboard")

if not master_file:
    st.markdown("""
    <div class="upload-hint">
        <h3 style="color:#7c6af7">👆 Upload daily_master.csv to get started</h3>
        <p>Find it in your Google Drive → clean_data folder.<br>
        It was saved there by the cleaning notebook.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Load data
df = load_data(master_file)

# Apply filters
filtered = df.copy()
if week_opt != "All weeks":
    wk = int(week_opt.split(" ")[1])
    filtered = filtered[filtered['study_week'] == wk]
if day_opt == "Weekdays only":
    filtered = filtered[filtered['is_weekend'] == False]
elif day_opt == "Weekends only":
    filtered = filtered[filtered['is_weekend'] == True]

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Overview",
    "📈  Weekly Trends",
    "🔗  Correlations",
    "🌡️  Stress Heatmap",
    "👤  Student Explorer"
])

# ═══════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════
with tab1:

    # ── Metric cards ──────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    def safe_mean(col):
        if col in filtered.columns:
            return filtered[col].mean()
        return None

    stress_mean = safe_mean('stress_avg')
    sleep_mean  = safe_mean('sleep_hours')
    mood_mean   = safe_mean('mood_score_avg')
    talk_mean   = safe_mean('total_talking_minutes')

    high_stress_pct = None
    if 'high_stress' in filtered.columns:
        high_stress_pct = filtered['high_stress'].mean() * 100

    deprived_pct = None
    if 'sleep_hours' in filtered.columns:
        valid = filtered['sleep_hours'].dropna()
        if len(valid):
            deprived_pct = (valid < 7).mean() * 100

    with c1:
        st.metric("Avg Stress", f"{stress_mean:.2f}/5" if stress_mean else "—",
                  help="Average self-reported stress level (1=calm, 5=very stressed)")
    with c2:
        st.metric("High Stress Days", f"{high_stress_pct:.0f}%" if high_stress_pct else "—",
                  help="% of days where stress was level 4 or 5")
    with c3:
        st.metric("Avg Sleep", f"{sleep_mean:.1f}h" if sleep_mean else "—",
                  help="Average hours of sleep per night")
    with c4:
        st.metric("Under 7h Nights", f"{deprived_pct:.0f}%" if deprived_pct else "—",
                  help="% of nights with less than recommended 7 hours")
    with c5:
        st.metric("Avg Mood Score", f"{mood_mean:.2f}" if mood_mean else "—",
                  help="Mood score: happy minus sad (-4 to +4)")
    with c6:
        st.metric("Avg Talking", f"{talk_mean:.0f}min" if talk_mean else "—",
                  help="Average daily conversation time in minutes")

    st.markdown("---")

    col1, col2 = st.columns(2)

    # Stress distribution
    with col1:
        st.markdown("#### Stress Level Distribution")
        if 'stress_avg' in filtered.columns:
            valid = filtered['stress_avg'].dropna()
            bins  = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
            labels= ['1\nNot stressed','2','3\nModerate','4','5\nVery stressed']
            counts = pd.cut(valid, bins=bins, labels=labels).value_counts().sort_index()
            fig = go.Figure()
            fig.add_bar(
                x=counts.index.tolist(),
                y=counts.values,
                marker_color=[COLOURS['sleep']]*2 + [COLOURS['neutral']] +
                              [COLOURS['stress']]*2,
                text=[f"{v/len(valid)*100:.0f}%" for v in counts.values],
                textposition='outside'
            )
            fig.update_layout(**TEMPLATE['layout'], height=280,
                              showlegend=False,
                              yaxis_title="Responses")
            st.plotly_chart(fig, use_container_width=True)

    # Sleep categories
    with col2:
        st.markdown("#### Sleep Duration Categories")
        if 'sleep_hours' in filtered.columns:
            valid = filtered['sleep_hours'].dropna()
            cats  = pd.cut(valid,
                           bins=[-np.inf, 5, 7, 9, np.inf],
                           labels=['Under 5h\n(deprived)', '5–7h\n(short)',
                                   '7–9h\n(adequate)', 'Over 9h\n(long)'])
            cc = cats.value_counts().sort_index()
            fig = go.Figure(go.Pie(
                labels=cc.index.tolist(),
                values=cc.values,
                marker_colors=[COLOURS['stress'], COLOURS['social'],
                                COLOURS['sleep'], COLOURS['mood']],
                hole=0.45,
                textinfo='label+percent'
            ))
            fig.update_layout(**TEMPLATE['layout'], height=280,
                              showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    # Activity breakdown
    with col3:
        st.markdown("#### Physical Activity Breakdown")
        act_cols = {
            'Stationary': 'fraction_stationary',
            'Walking':    'fraction_walking',
            'Running':    'fraction_running',
        }
        act_data = {}
        for label, col in act_cols.items():
            if col in filtered.columns:
                act_data[label] = filtered[col].mean() * 100
        if act_data:
            fig = go.Figure(go.Bar(
                x=list(act_data.keys()),
                y=list(act_data.values()),
                marker_color=[COLOURS['neutral'], COLOURS['sleep'], COLOURS['exercise']],
                text=[f"{v:.1f}%" for v in act_data.values()],
                textposition='outside'
            ))
            fig.update_layout(**TEMPLATE['layout'], height=260,
                              showlegend=False,
                              yaxis_title="% of sensor readings",
                              yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)

    # Talking time by day
    with col4:
        st.markdown("#### Avg Talking Time by Day of Week")
        if 'total_talking_minutes' in filtered.columns and 'day_of_week' in filtered.columns:
            dow = (filtered.groupby('day_of_week')['total_talking_minutes']
                   .mean().reindex(range(7)))
            colors = [COLOURS['social'] if i >= 5 else COLOURS['mood']
                      for i in range(7)]
            fig = go.Figure(go.Bar(
                x=DAY_NAMES,
                y=dow.values,
                marker_color=colors,
                text=[f"{v:.0f}m" if not np.isnan(v) else "" for v in dow.values],
                textposition='outside'
            ))
            fig.update_layout(**TEMPLATE['layout'], height=260,
                              showlegend=False,
                              yaxis_title="Minutes")
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 2 — WEEKLY TRENDS
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### All Key Variables Across the 10-Week Term")
    st.markdown("*Use this to see how students changed over the academic term.*")

    weekly_agg = df.groupby('study_week').agg(
        stress   = ('stress_avg', 'mean'),
        sleep    = ('sleep_hours', 'mean'),
        mood     = ('mood_score_avg', 'mean'),
        talking  = ('total_talking_minutes', 'mean'),
        walking  = ('fraction_walking', 'mean'),
        devices  = ('unique_devices_nearby', 'mean'),
    ).reset_index()

    # Big 4 trends
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Average Stress Level (1–5)',
                        'Average Sleep Hours',
                        'Average Mood Score (−4 to +4)',
                        'Average Talking Time (min)'],
        vertical_spacing=0.18,
        horizontal_spacing=0.1
    )

    def add_trend(fig, row, col, y_data, color, yrange=None):
        weeks = weekly_agg['study_week']
        fig.add_scatter(x=weeks, y=y_data,
                        mode='lines+markers',
                        line=dict(color=color, width=2.5),
                        marker=dict(size=7, color=color),
                        fill='tozeroy',
                        fillcolor=color.replace(')', ',0.08)').replace('rgb','rgba')
                                  if 'rgb' in color else color + '15',
                        row=row, col=col)
        # Finals week shading
        fig.add_vrect(x0=9.5, x1=10.5, fillcolor='red',
                      opacity=0.06, line_width=0,
                      row=row, col=col)
        if yrange:
            fig.update_yaxes(range=yrange, row=row, col=col)

    add_trend(fig, 1, 1, weekly_agg['stress'],  COLOURS['stress'],  [1, 5])
    add_trend(fig, 1, 2, weekly_agg['sleep'],   COLOURS['sleep'],   [4, 12])
    add_trend(fig, 2, 1, weekly_agg['mood'],    COLOURS['mood'],    [-2, 2])
    add_trend(fig, 2, 2, weekly_agg['talking'], COLOURS['social'],  [0, 60])

    fig.update_layout(
        height=520,
        paper_bgcolor='#17171a',
        plot_bgcolor='#1e1e22',
        font=dict(color='#e8e8ea', size=11),
        showlegend=False,
        margin=dict(l=40, r=20, t=60, b=40)
    )
    fig.update_xaxes(tickvals=WEEKS, ticktext=[f'W{w}' for w in WEEKS],
                     gridcolor='#2a2a2f')
    fig.update_yaxes(gridcolor='#2a2a2f')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "<p style='color:#6b6b72;font-size:13px;text-align:center'>"
        "🔴 shaded area = finals week (Week 10)</p>",
        unsafe_allow_html=True
    )

    # Additional weekly charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Social Proximity by Week")
        if 'devices' in weekly_agg.columns:
            fig2 = go.Figure(go.Bar(
                x=[f'W{w}' for w in weekly_agg['study_week']],
                y=weekly_agg['devices'],
                marker_color=COLOURS['mood'],
            ))
            fig2.update_layout(**TEMPLATE['layout'], height=260,
                               yaxis_title="Unique BT devices nearby")
            st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown("#### Physical Activity by Week")
        if 'walking' in weekly_agg.columns:
            fig3 = go.Figure(go.Bar(
                x=[f'W{w}' for w in weekly_agg['study_week']],
                y=weekly_agg['walking'] * 100,
                marker_color=COLOURS['exercise'],
            ))
            fig3.update_layout(**TEMPLATE['layout'], height=260,
                               yaxis_title="% time walking")
            st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 3 — CORRELATIONS
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### How Variables Relate to Each Other")
    st.markdown(
        "*Each dot = one student on one day. "
        "The dashed line shows the overall trend.*"
    )

    scatter_opts = {
        'Sleep hours vs Stress':       ('sleep_hours', 'stress_avg',
                                        'Sleep hours', 'Stress level',
                                        COLOURS['stress']),
        'Sleep hours vs Mood':         ('sleep_hours', 'mood_score_avg',
                                        'Sleep hours', 'Mood score',
                                        COLOURS['mood']),
        'Walking vs Stress':           ('fraction_walking', 'stress_avg',
                                        'Fraction walking', 'Stress level',
                                        COLOURS['exercise']),
        'Talking time vs Mood':        ('total_talking_minutes', 'mood_score_avg',
                                        'Talking time (min)', 'Mood score',
                                        COLOURS['social']),
        'BT devices vs Stress':        ('unique_devices_nearby', 'stress_avg',
                                        'Unique BT devices nearby', 'Stress level',
                                        COLOURS['neutral']),
        'Sleep quality vs Stress':     ('sleep_rate', 'stress_avg',
                                        'Sleep quality (1–5)', 'Stress level',
                                        COLOURS['sleep']),
    }

    col1, col2 = st.columns(2)

    # Let user pick which pair to show
    pair_x = col1.selectbox("X axis (horizontal)", list(scatter_opts.keys()), index=0)
    pair_y = col2.selectbox("Y axis (pick another)", list(scatter_opts.keys()), index=1)

    def scatter_fig(key, df):
        x_col, y_col, xl, yl, color = scatter_opts[key]
        if x_col not in df.columns or y_col not in df.columns:
            return None
        d = df[[x_col, y_col, 'uid']].dropna()
        if len(d) < 5:
            return None
        # Correlation
        r = d[x_col].corr(d[y_col])
        fig = px.scatter(d, x=x_col, y=y_col,
                         opacity=0.35,
                         trendline='ols',
                         color_discrete_sequence=[color],
                         labels={x_col: xl, y_col: yl},
                         trendline_color_override='#FFFFFF')
        fig.update_traces(marker=dict(size=6))
        fig.add_annotation(
            text=f"r = {r:.3f}",
            xref="paper", yref="paper",
            x=0.05, y=0.95,
            showarrow=False,
            font=dict(size=14, color='#e8e8ea'),
            bgcolor='#1e1e22',
            bordercolor='#2a2a2f',
            borderwidth=1,
            borderpad=6
        )
        fig.update_layout(**TEMPLATE['layout'], height=340)
        return fig

    c1, c2 = st.columns(2)
    fig_x = scatter_fig(pair_x, filtered)
    fig_y = scatter_fig(pair_y, filtered)
    if fig_x:
        c1.plotly_chart(fig_x, use_container_width=True)
    if fig_y:
        c2.plotly_chart(fig_y, use_container_width=True)

    # Correlation matrix
    st.markdown("#### Full Correlation Matrix")
    corr_cols = {
        'stress_avg': 'Stress',
        'sleep_hours': 'Sleep hours',
        'sleep_rate': 'Sleep quality',
        'mood_score_avg': 'Mood score',
        'fraction_walking': 'Walking',
        'total_talking_minutes': 'Talking time',
        'unique_devices_nearby': 'BT devices',
    }
    avail = {k: v for k, v in corr_cols.items() if k in filtered.columns}
    if len(avail) >= 3:
        corr_df = filtered[list(avail.keys())].rename(columns=avail).corr()
        mask = np.triu(np.ones(corr_df.shape), k=1).astype(bool)
        corr_masked = corr_df.where(~mask)
        fig_corr = px.imshow(
            corr_masked,
            color_continuous_scale='RdBu_r',
            zmin=-1, zmax=1,
            text_auto='.2f',
            aspect='auto'
        )
        fig_corr.update_layout(**TEMPLATE['layout'], height=380,
                               coloraxis_colorbar=dict(title="r"))
        fig_corr.update_traces(textfont_size=11)
        st.plotly_chart(fig_corr, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 4 — STRESS HEATMAP
# ═══════════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### Student × Week Stress Heatmap")
    st.markdown(
        "*Green = calm. Red = high stress. White = no data.*  \n"
        "*Each row = one student. Each column = one study week.*"
    )

    if 'stress_avg' in df.columns:
        pivot = (df.groupby(['uid', 'study_week'])['stress_avg']
                 .mean()
                 .unstack(fill_value=np.nan)
                 .reindex(columns=WEEKS))

        fig_hm = px.imshow(
            pivot,
            color_continuous_scale=[
                [0.0, '#4ECDC4'],
                [0.3, '#F0A050'],
                [0.6, '#E05C5C'],
                [1.0, '#8B0000']
            ],
            zmin=1, zmax=5,
            text_auto='.1f',
            aspect='auto',
            labels=dict(x='Study Week', y='Student', color='Avg Stress')
        )
        fig_hm.update_xaxes(tickvals=WEEKS, ticktext=[f'W{w}' for w in WEEKS])
        fig_hm.update_traces(textfont_size=9)
        fig_hm.update_layout(
            height=max(400, len(pivot) * 18),
            paper_bgcolor='#17171a',
            plot_bgcolor='#17171a',
            font=dict(color='#e8e8ea', size=11),
            margin=dict(l=80, r=20, t=40, b=40),
            coloraxis_colorbar=dict(
                title="Stress",
                tickvals=[1, 2, 3, 4, 5],
                ticktext=['1\nCalm', '2', '3\nMod', '4', '5\nHigh']
            )
        )
        st.plotly_chart(fig_hm, use_container_width=True)

        # Highlight the most and least stressed students
        student_means = df.groupby('uid')['stress_avg'].mean().dropna()
        if len(student_means):
            c1, c2, c3 = st.columns(3)
            c1.metric("Most stressed student",
                      student_means.idxmax(),
                      f"Mean {student_means.max():.2f}/5")
            c2.metric("Least stressed student",
                      student_means.idxmin(),
                      f"Mean {student_means.min():.2f}/5")
            c3.metric("Stress range across students",
                      f"{student_means.max()-student_means.min():.2f} units",
                      "huge individual variation")


# ═══════════════════════════════════════════════════════════════
# TAB 5 — STUDENT EXPLORER
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.markdown("#### Individual Student Explorer")
    st.markdown("*Pick a student to see their personal profile across the term.*")

    all_students = sorted(df['uid'].unique()) if 'uid' in df.columns else []

    if not all_students:
        st.warning("No student data found.")
    else:
        col_sel, col_info = st.columns([1, 3])

        # Student selector with stress colour indicator
        student_means = df.groupby('uid')['stress_avg'].mean().dropna()

        with col_sel:
            st.markdown("##### Select a student")
            # Build label with stress level
            def student_label(uid):
                m = student_means.get(uid, None)
                if m is None:
                    return uid
                indicator = "🔴" if m >= 3.5 else "🟡" if m >= 2.5 else "🟢"
                return f"{indicator} {uid}  ({m:.1f})"

            selected = st.selectbox(
                "Student ID",
                all_students,
                format_func=student_label,
                label_visibility="collapsed"
            )

            # Mini stats for selected student
            s_data = df[df['uid'] == selected]
            st.markdown("---")
            st.markdown(f"**{selected} overview**")

            s_stress = s_data['stress_avg'].mean()
            s_sleep  = s_data['sleep_hours'].mean()
            s_mood   = s_data['mood_score_avg'].mean() if 'mood_score_avg' in s_data.columns else None
            s_n      = s_data['stress_avg'].notna().sum()

            st.metric("Avg stress", f"{s_stress:.2f}/5" if not np.isnan(s_stress) else "—")
            st.metric("Avg sleep",  f"{s_sleep:.1f}h"  if not np.isnan(s_sleep)  else "—")
            if s_mood is not None and not np.isnan(s_mood):
                st.metric("Avg mood", f"{s_mood:.2f}")
            st.metric("Stress responses", int(s_n))

        with col_info:
            # Stress by week for this student
            s_weekly = (s_data.groupby('study_week')
                        .agg(stress=('stress_avg','mean'),
                             sleep=('sleep_hours','mean'))
                        .reindex(WEEKS))

            fig_s1 = go.Figure()
            fig_s1.add_scatter(
                x=WEEKS,
                y=s_weekly['stress'],
                mode='lines+markers',
                name='Stress',
                line=dict(color=COLOURS['stress'], width=2.5),
                marker=dict(size=8, color=COLOURS['stress']),
                fill='tozeroy',
                fillcolor='rgba(224,92,92,0.1)'
            )
            # Group average for comparison
            group_weekly = df.groupby('study_week')['stress_avg'].mean().reindex(WEEKS)
            fig_s1.add_scatter(
                x=WEEKS,
                y=group_weekly,
                mode='lines',
                name='Group average',
                line=dict(color='#6b6b72', width=1.5, dash='dash')
            )
            fig_s1.add_vrect(x0=9.5, x1=10.5, fillcolor='red',
                              opacity=0.06, line_width=0)
            fig_s1.update_layout(
                **TEMPLATE['layout'],
                height=240,
                title=f"{selected} — Stress by Week (vs group average)",
                xaxis=dict(tickvals=WEEKS, ticktext=[f'W{w}' for w in WEEKS],
                           gridcolor='#2a2a2f'),
                yaxis=dict(range=[0, 5.5], gridcolor='#2a2a2f',
                           title='Stress level'),
                legend=dict(orientation='h', y=-0.25)
            )
            st.plotly_chart(fig_s1, use_container_width=True)

            # Sleep by week for this student
            fig_s2 = go.Figure(go.Bar(
                x=[f'W{w}' for w in WEEKS],
                y=s_weekly['sleep'],
                marker_color=[
                    COLOURS['sleep'] if (not np.isnan(v) and v >= 7)
                    else COLOURS['social'] if (not np.isnan(v) and v >= 5)
                    else COLOURS['stress'] if not np.isnan(v)
                    else '#2a2a2f'
                    for v in s_weekly['sleep']
                ],
            ))
            fig_s2.add_hline(y=7, line_dash='dash', line_color='#4ECDC4',
                              annotation_text='7h recommended',
                              annotation_position='top right')
            fig_s2.update_layout(
                **TEMPLATE['layout'],
                height=220,
                title=f"{selected} — Sleep by Week",
                yaxis=dict(range=[0, 14], gridcolor='#2a2a2f',
                           title='Hours'),
                xaxis=dict(gridcolor='#2a2a2f')
            )
            st.plotly_chart(fig_s2, use_container_width=True)

