import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ==============================================================================
# 1. SETUP & CONFIG
# ==============================================================================
st.set_page_config(page_title="NBA Draft Model", layout="wide", page_icon="🏀")

# Custom CSS for "Scouting Card" feel
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    .big-stat {
        font-size: 24px;
        font-weight: bold;
    }
    .sub-stat {
        font-size: 14px;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# Plain English Archetype Mapping
ARCH_MAP = {
    "Heliocentric Engine": "Primary Creator",
    "Monstar": "Two-Way Dominant",
    "Alien": "Unicorn / High Upside",
    "Efficiency God": "Efficient Finisher",
    "Two-Way Wing": "3-and-D Plus",
    "Sniper": "Elite Shooter",
    "Low Ceiling Senior": "Safe Floor / Low Ceiling",
    "Inefficient Volume": "Volume Scorer (Risk)",
    "Pass First Guard": "Floor General",
    "": "Role Player"
}

# ==============================================================================
# 2. LOAD DATA
# ==============================================================================
@st.cache_data
def load_data():
    # Load the FIXED csv
    df = pd.read_csv("nba_draft_predictions_v2.csv") 
    
    # 1. Create "Confidence" Score based on Minutes (Proxy for Sample Size)
    # Assuming 'mp' or 'total_minutes' isn't explicitly in export, we improvise or use years_exp
    # For now, let's just use years_exp + star_prob as a proxy for 'stability'
    # Ideally, export 'total_minutes' from the model pipeline.
    
    # 2. Map Archetypes to Plain English
    df['scout_role'] = df['archetype_note'].map(ARCH_MAP).fillna(df['archetype_note'])
    
    # 3. Format Height
    def fmt_height(h):
        if pd.isna(h): return "N/A"
        ft = int(h // 12)
        inch = int(h % 12)
        return f"{ft}'{inch}\""
    
    df['height_fmt'] = df['height_in'].apply(fmt_height)
    
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("⚠️ Data file not found. Please run the model pipeline and save 'nba_draft_predictions_v2.csv'.")
    st.stop()

# ==============================================================================
# 3. SIDEBAR CONTROLS
# ==============================================================================
st.sidebar.header("🔍 Filters")
selected_year = st.sidebar.selectbox("Draft Class", sorted(df['year'].unique(), reverse=True))

# Filter to selected year
df_year = df[df['year'] == selected_year].copy()
df_year = df_year.sort_values("star_prob", ascending=False).reset_index(drop=True)
df_year['Rank'] = df_year.index + 1

# View Mode
view_mode = st.sidebar.radio("View Mode", ["Simple (Scouting)", "Analyst (Deep Dive)"])

# ==============================================================================
# 4. MAIN DASHBOARD
# ==============================================================================

# Header with "Trust Statement"
st.title(f"🏀 {selected_year} NBA Draft Board")
st.markdown("""
> **What is this?** This model estimates the probability of a player becoming a **Top-Tier Starter** based on historical college-to-NBA progression (2010-2024). 
> It values **Efficiency, Age, and Physical Tools** over raw points per game.
""")

# TOP SECTION: THE BOARD
if view_mode == "Simple (Scouting)":
    st.subheader(f"🏆 Top Prospects: {selected_year}")
    
    # Iterate through Top 5 for "Card" View
    cols = st.columns(3)
    for i, player in df_year.head(3).iterrows():
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <h3>#{i+1} {player['player_name']}</h3>
                <p><b>Role:</b> {player['scout_role']}</p>
                <p class="big-stat">{player['star_prob']*100:.1f}% Star Prob</p>
                <p class="sub-stat">
                📏 {player['height_fmt']} | 🎓 Exp: {player['years_exp']:.1f}<br>
                📈 Usage: {player['usg_max']:.1f}% | 🛡️ Stocks: {player['stock_rate']:.1f}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")

# ==============================================================================
# 5. THE SCATTER PLOT (TRUST & CONTEXT)
# ==============================================================================
st.subheader("📊 The Landscape: Usage vs. Efficiency")

# Prepare Plot Data (Scouting Card Hover)
df_plot = df_year.copy()
df_plot["star_pct"] = (df_plot["star_prob"] * 100).round(1)
df_plot["usg_fmt"] = df_plot["usg_max"].round(1)
df_plot["stocks_fmt"] = df_plot["stock_rate"].round(1)
df_plot["ts_fmt"] = (df_plot["ts_used"] * 100).round(1)
# Create a dummy 'Confidence' metric if minutes aren't available
df_plot["confidence"] = np.where(df_plot['years_exp'] >= 2.0, "High", "Med") 

fig = px.scatter(
    df_plot,
    x="usg_max",
    y="star_prob",
    color="scout_role", 
    size="bpm_max", # Bubble size = Impact
    hover_name="player_name",
    title=f"{selected_year} Draft Landscape (Size = BPM Impact)",
    labels={"usg_max": "Usage Rate (%)", "star_prob": "Star Probability"},
    height=600,
    custom_data=[
        "scout_role",    # 0
        "star_pct",      # 1
        "usg_fmt",       # 2
        "height_fmt",    # 3
        "ts_fmt",        # 4
        "stocks_fmt",    # 5
        "confidence"     # 6
    ]
)

# The Clean "Scouting Card" Hover Template
fig.update_traces(
    hovertemplate=
    "<b>%{hovertext}</b><br>" +
    "----------------<br>" +
    "📝 <b>Role:</b> %{customdata[0]}<br>" +
    "⭐ <b>Star Prob:</b> %{customdata[1]}%<br>" +
    "🔒 <b>Confidence:</b> %{customdata[6]}<br>" +
    "<br>" +
    "📊 <b>Stats Profile:</b><br>" +
    "• Usage: %{customdata[2]}%<br>" +
    "• Efficiency (TS): %{customdata[4]}%<br>" +
    "• Height: %{customdata[3]}<br>" +
    "• Defensive Stocks: %{customdata[5]}<br>" +
    "<extra></extra>"
)

# Add "Star Zone" Rectangle
fig.add_shape(type="rect",
    x0=25, y0=0.40, x1=40, y1=1.0,
    line=dict(color="Green", width=1, dash="dot"),
    fillcolor="Green", opacity=0.1,
    layer="below"
)
fig.add_annotation(x=32, y=0.9, text="Superstar Zone", showarrow=False, font=dict(color="green"))

st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# 6. THE DATA TABLE
# ==============================================================================
st.subheader("📋 Detailed Board")

if view_mode == "Simple (Scouting)":
    # Clean Columns for public view
    show_cols = ['Rank', 'player_name', 'scout_role', 'star_prob', 'height_fmt', 'years_exp', 'usg_max']
    
    st.dataframe(
        df_year[show_cols].style.format({
            "star_prob": "{:.1%}",
            "usg_max": "{:.1f}%",
            "years_exp": "{:.1f}"
        }).background_gradient(subset=['star_prob'], cmap="Greens"),
        use_container_width=True,
        hide_index=True
    )

else:
    # Analyst Mode (Everything)
    st.dataframe(
        df_year.style.format({
            "star_prob": "{:.1%}",
            "bpm_max": "{:.1f}",
            "ts_used": "{:.1%}"
        }).background_gradient(subset=['star_prob'], cmap="RdYlGn"),
        use_container_width=True
    )
