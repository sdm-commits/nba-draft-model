import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration (Must be first)
st.set_page_config(
    page_title="NBA Draft Oracle", 
    page_icon="🏀", 
    layout="wide"
)

# Custom CSS to style the metrics better
st.markdown("""
<style>
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# 2. Load Data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('nba_draft_predictions.csv')
        # Fill missing numeric values with 0 to prevent plotting errors
        cols_to_fill = ['usg_max', 'star_prob', 'bpm_max', 'ast_per', 'stock_rate', 'treerate', 'ts_used']
        for col in cols_to_fill:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        return df
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("⚠️ Data file not found! Please upload 'nba_draft_predictions.csv'.")
    st.stop()

# 3. Sidebar: Filters & Controls
with st.sidebar:
    st.header("🔍 Analysis Controls")
    
    # Year Selector
    years_available = sorted(df['year'].unique(), reverse=True)
    selected_year = st.selectbox("Select Draft Class", years_available)
    
    st.divider()
    
    # Chart Controls
    st.subheader("🎨 Chart Settings")
    num_labels = st.slider("Number of labels:", min_value=0, max_value=20, value=5)
    
    st.divider()

    # --- ARCHETYPE GLOSSARY ---
    with st.expander("🧬 Archetype Glossary"):
        st.markdown("""
        **🦄 Monstar (Purple)**
        *Generational outliers.*
        - **Criteria:** BPM > 11.5 + Age ≤ 20
        - **Examples:** Zion, AD, Mobley
        
        **👽 Alien (Red)**
        *Unicorn bigs who do it all.*
        - **Criteria:** High Stocks (Blk+Stl) + High Usage
        - **Examples:** Chet, Wemby, Sengun
        
        **🚀 Heliocentric Engine (Orange)**
        *Offense-in-a-box creators.*
        - **Criteria:** Freshman + High Usage + High Assists
        - **Examples:** Trae Young, Luka, Cade
        
        **📊 Efficiency God (Blue)**
        *Advanced stats darlings.*
        - **Criteria:** High BPM + Efficient Shooting + Low Turnovers
        - **Examples:** Jokic, Brandon Clarke
        
        **⚠️ Red Flags (Grey)**
        - **Undersized Paint Hustler:** Short bigs with no shot.
        - **Inefficient Volume:** Short scorers with low efficiency.
        """)

# Filter Data for Selected Year
year_df = df[df['year'] == selected_year].sort_values('star_prob', ascending=False).reset_index(drop=True)

# 4. Header Section
st.title(f"🏀 {selected_year} NBA Draft Oracle")
st.markdown("Predicting future NBA stars using **XGBoost** and **Archetype Classification**.")

st.divider()

# 5. Top Metrics Row
if not year_df.empty:
    top_prospect = year_df.iloc[0]
    avg_star_prob = year_df['star_prob'].mean()
    
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("🥇 Top Prospect", top_prospect['player_name'])
    with m2: st.metric("⭐ Star Probability", f"{top_prospect['star_prob']:.1%}", delta=f"{top_prospect['star_prob'] - avg_star_prob:.1%} vs Avg")
    with m3: st.metric("🧬 Archetype", top_prospect['archetype_note'])
    with m4: st.metric("🔥 Impact (BPM)", round(top_prospect['bpm_max'], 1))

# 6. Main Content Area: TABS
tab_chart, tab_data = st.tabs(["📈 Visual Analysis", "💾 Deep Dive Data"])

with tab_chart:
    if not year_df.empty:
        # A. Clean Noise (Hide low prob players unless high usage)
        clean_df = year_df[(year_df['star_prob'] > 0.01) | (year_df['usg_max'] > 30.0)].copy()
        clean_df['plot_size'] = clean_df['bpm_max'].clip(lower=0.1)

        # B. Plot
        fig = px.scatter(
            clean_df,
            x="usg_max",
            y="star_prob",
            color="archetype_note",
            hover_name="player_name",
            size="plot_size",
            hover_data={
                "height_in": True, "ast_per": True, "bpm_max": True,
                "stock_rate": True, "treerate": True, "plot_size": False
            },
            title=f"<b>{selected_year} Tier List: Usage vs. Potential</b>",
            labels={"usg_max": "Usage Rate (%)", "star_prob": "Star Probability"},
            color_discrete_map={
                "Monstar": "#800080",            # Purple
                "Alien": "#ff2b2b",              # Red
                "Heliocentric Engine": "#ffa600",# Orange
                "Efficiency God": "#0068c9",     # Blue
                "Undersized Paint Hustler": "#808080",
                "Inefficient Volume": "#d3d3d3",
                "": "#d3d3d3"
            },
            opacity=0.85
        )

        # Tier Lines
        fig.add_hline(y=0.60, line_dash="dot", line_color="gold", annotation_text="MVP Tier")
        fig.add_hline(y=0.45, line_dash="dot", line_color="silver", annotation_text="All-Star Tier")

        # C. Dynamic Labels
        top_prospects = clean_df.sort_values('star_prob', ascending=False).head(num_labels)
        for i, row in top_prospects.iterrows():
            shift_y = 15 if i % 2 == 0 else -15
            fig.add_annotation(
                x=row['usg_max'], y=row['star_prob'],
                text=row['player_name'], showarrow=False, yshift=shift_y,
                font=dict(size=11, color="black")
            )

        fig.update_layout(plot_bgcolor="white", height=600, legend=dict(orientation="h", y=-0.2))
        fig.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0', tickformat=".0%")

        st.plotly_chart(fig, use_container_width=True)

with tab_data:
    st.subheader("📋 Scouting Database")
    search_term = st.text_input("🔍 Search Player:", "")
    display_df = year_df[year_df['player_name'].str.contains(search_term, case=False)] if search_term else year_df

    # Smart Columns
    table_cols = ['player_name', 'star_prob', 'archetype_note', 'height_in', 'bpm_max', 'usg_max', 'ts_used']
    if 'stock_rate' in display_df.columns: table_cols.append('stock_rate')
    if 'treerate' in display_df.columns: table_cols.append('treerate')

    st.dataframe(
        display_df[table_cols],
        column_config={
            "player_name": "Player",
            "star_prob": st.column_config.ProgressColumn("Star Probability", format="%.1f%%", min_value=0, max_value=1),
            "archetype_note": "Archetype",
            "bpm_max": st.column_config.NumberColumn("BPM", format="%.1f"),
            "usg_max": st.column_config.NumberColumn("Usage", format="%.1f%%"),
            "ts_used": st.column_config.NumberColumn("True Shooting", format="%.2f"),
            "stock_rate": st.column_config.NumberColumn("Stock %", format="%.1f"),
            "treerate": st.column_config.NumberColumn("3P Rate", format="%.2f"),
        },
        use_container_width=True, hide_index=True, height=600
    )
