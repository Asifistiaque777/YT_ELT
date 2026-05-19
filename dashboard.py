import streamlit as st
import pandas as pd
import psycopg2
import os
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="YouTube Analytics Dashboard",
    layout="wide",
    page_icon="🎬",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0f0f1a; color: #ffffff; }
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #e74c3c33;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(231,76,60,0.15);
    }
    [data-testid="metric-container"] label {
        color: #aaaacc !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #ffffff !important;
        font-size: 28px !important;
        font-weight: 800 !important;
    }
    .section-header {
        font-size: 20px;
        font-weight: 800;
        color: #e74c3c;
        margin-bottom: 10px;
    }
    hr { border-color: #e74c3c33 !important; }
    .main-title {
        font-size: 42px;
        font-weight: 900;
        background: linear-gradient(90deg, #ff416c, #ff4b2b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 10px 0 0 0;
    }
    .sub-title {
        text-align: center;
        color: #aaaacc;
        font-size: 15px;
        margin-bottom: 30px;
        letter-spacing: 2px;
    }
</style>
""", unsafe_allow_html=True)

PLOT_BG  = "#16213e"
PAPER_BG = "#1a1a2e"
FONT_CLR = "#ffffff"
RED      = "#e74c3c"
BLUE     = "#4facfe"


def base_layout(height=420):
    return dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(color=FONT_CLR, family="Inter, sans-serif"),
        margin=dict(l=20, r=20, t=40, b=20),
        height=height,
    )


@st.cache_data(ttl=300)
def get_data():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_CONN_HOST"),
            database=os.getenv("ELT_DATABASE_NAME"),
            user=os.getenv("ELT_DATABASE_USERNAME"),
            password=os.getenv("ELT_DATABASE_PASSWORD"),
            port=os.getenv("POSTGRES_CONN_PORT", "5432")
        )
        df = pd.read_sql("""
            SELECT video_id, title, published_at, duration,
                   video_type, view_count, like_count, comment_count
            FROM core.yt_api ORDER BY view_count DESC;
        """, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ DB error: {e}")
        return pd.DataFrame()


# ── Header ──
st.markdown('<div class="main-title">🎬 YouTube Channel Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">POWERED BY REAL-TIME DATA PIPELINE · AIRFLOW · POSTGRESQL</div>', unsafe_allow_html=True)

df = get_data()
if df.empty:
    st.warning("⚠️ Database is currently empty. Run the `update_db` DAG first.")
    st.stop()

# ── Clean NaN ──
df['view_count']    = df['view_count'].fillna(0).astype(float)
df['like_count']    = df['like_count'].fillna(0).astype(float)
df['comment_count'] = df['comment_count'].fillna(0).astype(float)

# ── Feature Engineering ──
df['engagement_rate'] = ((df['like_count'] + df['comment_count']) / df['view_count'].replace(0,1) * 100).round(2)
df['like_rate']       = (df['like_count']    / df['view_count'].replace(0,1) * 100).round(2)
df['comment_rate']    = (df['comment_count'] / df['view_count'].replace(0,1) * 100).round(2)
df['published_at']    = pd.to_datetime(df['published_at'])
df['month']           = df['published_at'].dt.to_period('M').astype(str)
df['short_title']     = df['title'].str[:35] + '...'

# ── KPI Cards ──
st.markdown("---")
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("📹 Videos",         f"{len(df):,}")
c2.metric("👁️ Total Views",   f"{df['view_count'].sum()/1e6:.1f}M")
c3.metric("👍 Total Likes",    f"{df['like_count'].sum()/1e3:.0f}K")
c4.metric("💬 Comments",       f"{df['comment_count'].sum()/1e3:.0f}K")
c5.metric("📈 Avg Engagement", f"{df['engagement_rate'].mean():.2f}%")
c6.metric("🎞️ Shorts",        f"{(df['video_type']=='Shorts').sum()}")
st.markdown("---")

# ══════════════════════════════
#  ROW 1: Top 15 | Donut
# ══════════════════════════════
col1, col2 = st.columns([2,1])

with col1:
    st.markdown('<p class="section-header">🚀 Top 15 Videos by Views</p>', unsafe_allow_html=True)
    top15 = df.nlargest(15,'view_count')
    fig = px.bar(top15, x='view_count', y='short_title', orientation='h',
                 color='view_count',
                 color_continuous_scale=[[0,'#c0392b'],[0.5,'#e74c3c'],[1,'#ff6b8a']],
                 text='view_count')
    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside',
                      textfont=dict(color='white', size=10))
    fig.update_layout(**base_layout(500), showlegend=False, coloraxis_showscale=False)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(autorange='reversed', showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown('<p class="section-header">🎬 Content Type Split</p>', unsafe_allow_html=True)
    type_df = df['video_type'].value_counts().reset_index()
    type_df.columns = ['Type','Count']
    fig2 = px.pie(type_df, names='Type', values='Count',
                  color_discrete_sequence=[RED, BLUE], hole=0.55)
    fig2.update_traces(textposition='outside', textinfo='label+percent',
                       textfont=dict(color='white', size=13),
                       marker=dict(line=dict(color=PAPER_BG, width=3)))
    fig2.update_layout(**base_layout(500), legend=dict(orientation='h', y=-0.1))
    st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════
#  ROW 2: Bubble | Monthly
# ══════════════════════════════
col3, col4 = st.columns(2)

with col3:
    st.markdown('<p class="section-header">💡 Views vs Likes vs Comments</p>', unsafe_allow_html=True)
    bubble_df = df.copy()
    bubble_df['comment_count'] = bubble_df['comment_count'].clip(lower=1)
    fig3 = px.scatter(bubble_df, x='view_count', y='like_count',
                      size='comment_count', color='video_type', hover_name='title',
                      color_discrete_map={'Normal':RED,'Shorts':BLUE},
                      size_max=40, opacity=0.8)
    fig3.update_layout(**base_layout(420), legend=dict(orientation='h', y=1.05))
    fig3.update_xaxes(showgrid=False)
    fig3.update_yaxes(showgrid=False)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown('<p class="section-header">📅 Monthly Upload Frequency</p>', unsafe_allow_html=True)
    monthly = df.groupby('month').agg(
        Videos=('video_id','count'),
        Total_Views=('view_count','sum')
    ).reset_index().tail(18)
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(x=monthly['month'], y=monthly['Videos'],
                          name='Videos', marker_color=RED, opacity=0.85))
    fig4.add_trace(go.Scatter(x=monthly['month'], y=monthly['Total_Views'],
                              name='Total Views', yaxis='y2',
                              line=dict(color=BLUE, width=3),
                              mode='lines+markers', marker=dict(size=6)))
    fig4.update_layout(**base_layout(420),
                       yaxis2=dict(overlaying='y', side='right',
                                   tickfont=dict(color=BLUE)),
                       legend=dict(orientation='h', y=1.05))
    fig4.update_xaxes(showgrid=False)
    fig4.update_yaxes(showgrid=False)
    st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════
#  ROW 3: Engagement | Like vs Comment
# ══════════════════════════════
col5, col6 = st.columns(2)

with col5:
    st.markdown('<p class="section-header">🏆 Top 10 by Engagement Rate</p>', unsafe_allow_html=True)
    top_eng = df.nlargest(10,'engagement_rate')
    fig5 = px.bar(top_eng, x='short_title', y='engagement_rate',
                  color='engagement_rate',
                  color_continuous_scale=[[0,'#c0392b'],[1,'#ff6b8a']],
                  text='engagement_rate')
    fig5.update_traces(texttemplate='%{text:.1f}%', textposition='outside',
                       textfont=dict(color='white'))
    fig5.update_layout(**base_layout(400), coloraxis_showscale=False)
    fig5.update_xaxes(tickangle=-30, showgrid=False)
    fig5.update_yaxes(showgrid=False)
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.markdown('<p class="section-header">📊 Like Rate vs Comment Rate</p>', unsafe_allow_html=True)
    try:
        fig6 = px.scatter(df, x='like_rate', y='comment_rate',
                          color='video_type', hover_name='title',
                          color_discrete_map={'Normal':RED,'Shorts':BLUE},
                          trendline='ols', opacity=0.75)
    except Exception:
        fig6 = px.scatter(df, x='like_rate', y='comment_rate',
                          color='video_type', hover_name='title',
                          color_discrete_map={'Normal':RED,'Shorts':BLUE},
                          opacity=0.75)
    fig6.update_layout(**base_layout(400), legend=dict(orientation='h', y=1.05))
    fig6.update_xaxes(showgrid=False)
    fig6.update_yaxes(showgrid=False)
    st.plotly_chart(fig6, use_container_width=True)

# ══════════════════════════════
#  ROW 4: Histogram | Recent Table
# ══════════════════════════════
col7, col8 = st.columns(2)

with col7:
    st.markdown('<p class="section-header">📉 Views Distribution</p>', unsafe_allow_html=True)
    fig7 = px.histogram(df, x='view_count', nbins=30, color='video_type',
                        color_discrete_map={'Normal':RED,'Shorts':BLUE},
                        barmode='overlay', opacity=0.75)
    fig7.update_layout(**base_layout(380), legend=dict(orientation='h', y=1.05))
    fig7.update_xaxes(showgrid=False)
    fig7.update_yaxes(showgrid=False)
    st.plotly_chart(fig7, use_container_width=True)

with col8:
    st.markdown('<p class="section-header">🆕 10 Most Recent Uploads</p>', unsafe_allow_html=True)
    recent = df.nlargest(10,'published_at')[
        ['title','published_at','view_count','video_type','engagement_rate']
    ].copy()
    recent['published_at'] = recent['published_at'].dt.strftime('%Y-%m-%d')
    recent.columns = ['Title','Date','Views','Type','Engagement%']
    st.dataframe(recent, use_container_width=True, height=380, hide_index=True)

# ══════════════════════════════
#  ROW 5: Cumulative Views
# ══════════════════════════════
st.markdown('<p class="section-header">📈 Cumulative Views Over Time</p>', unsafe_allow_html=True)
time_df = df.sort_values('published_at').copy()
time_df['cumulative_views'] = time_df['view_count'].cumsum()
fig8 = go.Figure()
fig8.add_trace(go.Scatter(
    x=time_df['published_at'],
    y=time_df['cumulative_views'],
    fill='tozeroy', mode='lines',
    line=dict(color=RED, width=3),
    fillcolor='rgba(231,76,60,0.15)',
    name='Cumulative Views'
))
fig8.update_layout(**base_layout(320))
fig8.update_xaxes(showgrid=False)
fig8.update_yaxes(showgrid=False)
st.plotly_chart(fig8, use_container_width=True)

# ══════════════════════════════
#  ROW 6: Most Liked | Most Commented
# ══════════════════════════════
col9, col10 = st.columns(2)

with col9:
    st.markdown('<p class="section-header">🥇 Top 5 Most Liked Videos</p>', unsafe_allow_html=True)
    top_liked = df.nlargest(5,'like_count')[['short_title','like_count']].copy()
    fig9 = px.bar(top_liked, x='like_count', y='short_title', orientation='h',
                  color_discrete_sequence=[RED], text='like_count')
    fig9.update_traces(texttemplate='%{text:,.0f}', textposition='outside',
                       textfont=dict(color='white'))
    fig9.update_layout(**base_layout(350), showlegend=False)
    fig9.update_xaxes(showgrid=False)
    fig9.update_yaxes(autorange='reversed', showgrid=False)
    st.plotly_chart(fig9, use_container_width=True)

with col10:
    st.markdown('<p class="section-header">💬 Top 5 Most Commented Videos</p>', unsafe_allow_html=True)
    top_commented = df.nlargest(5,'comment_count')[['short_title','comment_count']].copy()
    fig10 = px.bar(top_commented, x='comment_count', y='short_title', orientation='h',
                   color_discrete_sequence=[BLUE], text='comment_count')
    fig10.update_traces(texttemplate='%{text:,.0f}', textposition='outside',
                        textfont=dict(color='white'))
    fig10.update_layout(**base_layout(350), showlegend=False)
    fig10.update_xaxes(showgrid=False)
    fig10.update_yaxes(autorange='reversed', showgrid=False)
    st.plotly_chart(fig10, use_container_width=True)

# ══════════════════════════════
#  Full Table
# ══════════════════════════════
st.markdown("---")
st.markdown('<p class="section-header">📋 Full Dataset</p>', unsafe_allow_html=True)
display_df = df[['title','video_type','published_at','duration',
                  'view_count','like_count','comment_count','engagement_rate']].copy()
display_df['published_at'] = display_df['published_at'].dt.strftime('%Y-%m-%d')
display_df.columns = ['Title','Type','Published','Duration','Views','Likes','Comments','Engagement%']
st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#555;font-size:12px;">'
    'Built with ❤️ · Airflow + PostgreSQL + Streamlit · YouTube Data Pipeline'
    '</p>', unsafe_allow_html=True
)