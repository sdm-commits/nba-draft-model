import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(
    page_title="NBA Draft Oracle", 
    page_icon="🏀", 
    layout="wide"
)

st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 24px; color: #333; }
    a { text-decoration: none; color: #0068c9 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 2. Load Data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('nba_draft_predictions.csv')
        cols_to_fill = ['usg_max', 'star_prob', 'bpm_max', 'ast_per', 'stock_rate', 'treerate', 'ts_used']
        for col in cols_to_fill:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        # --- NEW: GENERATE SCOUTING LINKS ---
        # This creates a Google Search URL for every player
        if 'player_name' in df.columns:
            df['search_url'] = df['player_name'].apply(
                lambda x: f"https://www.google.com/search?q={x.replace(' ', '+')}+basketball+highlights&tbm=vid"
            )
        
        return df
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("⚠️ Data file not found! Please upload 'nba_draft_predictions.csv'.")
    st.stop()

# 3. Sidebar
with st.sidebar:
    st.header("🔍 Analysis Controls")
    years_available = sorted(df['year'].unique(), reverse=True)
    selected_year = st.selectbox("Select Draft Class", years_available)
    
    st.divider()
    
    st.subheader("🎨 Chart Settings")
    num_labels = st.slider("Number of labels:", 0, 20, 5)
    
    st.divider()

    with st.expander("🧬 Archetype Glossary"):
        st.markdown("""
        **🦄 Monstar (Purple)**: Generational outliers (BPM > 11.5).
        **👽 Alien (Red)**: Unicorn bigs (High Stocks + Usage).
        **🚀 Heliocentric (Orange)**: High Usage + Assists creators.
        **📊 Efficiency God (Blue)**: High BPM + Efficient + Low TOV.
        """)

# Filter Data
year_df = df[df['year'] == selected_year].sort_values('star_prob', ascending=False).reset_index(drop=True)

# 4. Header
st.title(f"🏀 {selected_year} NBA Draft Oracle")
st.markdown("Predicting future NBA stars using **XGBoost**. Click a player's name to see their **Highlights**.")

st.divider()

# 5. Top Metrics
if not year_df.empty:
    top_prospect = year_df.iloc[0]
    avg_star_prob = year_df['star_prob'].mean()
    
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("🥇 Top Prospect", top_prospect['player_name'])
    with m2: st.metric("⭐ Star Prob", f"{top_prospect['star_prob']:.1%}", delta=f"{top_prospect['star_prob'] - avg_star_prob:.1%}")
    with m3: st.metric("🧬 Archetype", top_prospect['archetype_note'])
    with m4: st.metric("🔥 Impact (BPM)", round(top_prospect['bpm_max'], 1))

# 6. Main Content
tab_chart, tab_data = st.tabs(["📈 Visual Analysis", "💾 Deep Dive Data"])

with tab_chart:
    if not year_df.empty:
        clean_df = year_df[(year_df['star_prob'] > 0.01) | (year_df['usg_max'] > 30.0)].copy()
        clean_df['plot_size'] = clean_df['bpm_max'].clip(lower=0.1)

        fig = px.scatter(
            clean_df, x="usg_max", y="star_prob", color="archetype_note",
            hover_name="player_name", size="plot_size",
            hover_data={"height_in": True, "ast_per": True, "bpm_max": True, "stock_rate": True, "treerate": True, "plot_size": False},
            title=f"<b>{selected_year} Usage vs. Potential</b>",
            labels={"usg_max": "Usage Rate (%)", "star_prob": "Star Probability"},
            color_discrete_map={
                "Monstar": "#800080", "Alien": "#ff2b2b", "Heliocentric Engine": "#ffa600",
                "Efficiency God": "#0068c9", "Undersized Paint Hustler": "#808080", "Inefficient Volume": "#d3d3d3", "": "#d3d3d3"
            },
            opacity=0.85
        )
        
        fig.add_hline(y=0.60, line_dash="dot", line_color="gold", annotation_text="MVP Tier")
        fig.add_hline(y=0.45, line_dash="dot", line_color="silver", annotation_text="All-Star Tier")

        top_prospects = clean_df.sort_values('star_prob', ascending=False).head(num_labels)
        for i, row in top_prospects.iterrows():
            shift_y = 15 if i % 2 == 0 else -15
            fig.add_annotation(x=row['usg_max'], y=row['star_prob'], text=row['player_name'], showarrow=False, yshift=shift_y, font=dict(size=11, color="black"))

        fig.update_layout(plot_bgcolor="white", height=600, legend=dict(orientation="h", y=-0.2))
        fig.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0', tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

with tab_data:
    st.subheader("📋 Scouting Database")
    search_term = st.text_input("🔍 Search Player:", "")
    display_df = year_df[year_df['player_name'].str.contains(search_term, case=False)] if search_term else year_df

    # --- TABLE CONFIGURATION ---
    # We define standard columns
    table_cols = ['player_name', '
