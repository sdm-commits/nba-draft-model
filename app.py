import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

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
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .big-stat {
        font-size: 24px;
        font-weight: bold;
        color: #0e1117;
    }
    .sub-stat {
        font-size: 14px;
        color: #555;
        line-height: 1.5;
    }
    .role-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 0.8em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Plain English Archetype Mapping (Matches your V8 Model)
ARCH_MAP = {
    "Heliocentric Engine": "Primary Creator (Luka/Trae)",
    "Monstar": "Physical Force (Zion/AD)",
    "Alien": "Unicorn (Wemby/Chet)",
    "Efficiency God": "Efficient Connector (Jokic/Sengun)",
    "Two-Way Wing": "Elite 3-and-D (Kawhi/Mikal)",
    "Low Ceiling Senior": "Safe Floor / Low Ceiling",
    "Inefficient Volume": "Volume Scorer Risk",
    "Undersized Paint Hustler": "Undersized Energy Big",
    "": "Rotation Player / Role"
}

# ==============================================================================
# 2. LOAD DATA
# ==============================================================================
@st.cache_data
def load_data():
    file_path = "nba_draft_predictions.csv"
    
    if not os.path.exists(file_path):
        return None

    # Load the csv
    df = pd.read_csv(file_path) 
    
    # 1. Map Archetypes to Plain English
    df['scout_role'] = df['archetype_note'].map(ARCH_MAP).fillna(df['archetype_note'])
    
    # 2. Format Height
    def fmt_height(h):
        if pd.isna(h) or h == 0: return "N/A"
        ft = int(h // 12)
        inch = int(h % 12)
        return f"{ft}'{inch}\""
    
    df['height_fmt'] = df['height_in'].apply(fmt_height)
    
    # 3. Safety Fill for Missing Cols (Just in case)
    if 'ts_used' not in df.columns: df['ts_used'] = 0.55
    if 'stock_rate' not in df.columns: df['stock_rate'] = 0.0
    
    return df

df = load_data()

if df is None:
    st.error("⚠️ Data file `nba_draft_predictions.csv` not found. Please run your model notebook and download the CSV to this folder.")
    st.stop()

# ==============================================================================
# 3. SIDEBAR CONTROLS
# ==============================================================================
st.sidebar.header("🔍 Filters")

# Filter Year
all_years = sorted(df['year'].unique(), reverse=True)
selected_year = st.sidebar.selectbox("Draft Class", all_years)

# Filter Data to Year
df_year = df[df['year'] == selected_year].copy()
df_year = df_year.sort_values("star_prob", ascending=False).reset_index(drop=True)
df_year['Rank'] = df_year.index + 1

# View Mode
view_mode = st.sidebar.radio("View Mode", ["Simple (Scouting)", "Analyst (Deep Dive)"])

# Highlight Player
search_term = st.sidebar.text_input("Highlight Player", "")

# ==============================================================================
# 4. MAIN DASHBOARD
# ==============================================================================

# Header
st.title(f"🏀 {selected_year} NBA Draft Board")
st.markdown(f"""
Showing **{len(df_year)}** prospects from the {selected_year} class.
This model identifies players with statistical profiles similar to historical All-Stars.
""")

# TOP SECTION: THE BOARD (Top 3 Cards)
if view_mode == "Simple (Scouting)":
    st.subheader(f"🏆 Top Prospects")
    
    # Iterate through Top 3 for "Card" View
    cols = st.columns(3)
    for i, player in df_year.head(3).iterrows():
        role_label = player['scout_role'] if player['scout_role'] else "Standard Prospect"
        
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <h3>#{i+1} {player['player_name']}</h3>
                <span class="role-badge">{role_label}</span>
                <p class="big-stat" style="margin-top: 10px;">{player['star_prob']*100:.1f}% <span style="font-size:14px; color:#555;">Star Prob</span></p>
                <div class="sub-stat">
                📏 <b>{player['height_fmt']}</b> | 🎓 Exp: {player['years_exp']:.0f}<br>
                📈 Usage: {player['usg_max']:.1f}%<br>
                🛡️ Stocks: {player['stock_rate']:.1f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")

# ==============================================================================
# 5. THE SCATTER PLOT (TRUST & CONTEXT)
# ==============================================================================
st.subheader("📊 The Landscape: Usage vs. Probability")

# Prepare Plot Data
df_plot = df_year.copy()
df_plot["star_pct"] = (df_plot["star_prob"] * 100).round(1)
df_plot["usg_fmt"] = df_plot["usg_max"].round(1)
df_plot["stocks_fmt"] = df_plot["stock_rate"].round(1)
df_plot["ts_fmt"] = (df_plot["ts_used"] * 100).round(1)

# Color Logic: Highlight searched player, otherwise by Role
if search_term:
    df_plot['color_group'] = np.where(df_plot['player_name'].str.contains(search_term, case=False), "Highlight", "Others")
    color_map = {"Highlight": "#ff4b4b", "Others": "#dddddd"}
else:
    df_plot['color_group'] = df_plot['scout_role']
    color_map = None # Auto assign

fig = px.scatter(
    df_plot,
    x="usg_max",
    y="star_prob",
    color="color_group",
    color_discrete_map=color_map,
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
        "stocks_fmt"     # 5
    ]
)

# The Clean "Scouting Card" Hover Template
fig.update_traces(
    hovertemplate=
    "<b>%{hovertext}</b><br>" +
    "----------------<br>" +
    "📝 <b>Role:</b> %{customdata[0]}<br>" +
    "⭐ <b>Star Prob:</b> %{customdata[1]}%<br>" +
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

# Search Filter in Table
if search_term:
    df_year = df_year[df_year['player_name'].str.contains(search_term, case=False)]

if view_mode == "Simple (Scouting)":
    # Clean Columns for public view
    show_cols = ['Rank', 'player_name', 'scout_role', 'star_prob', 'height_fmt', 'years_exp', 'usg_max', 'ts_used']
    
    # Rename for display
    display_df = df_year[show_cols].rename(columns={
        'player_name': 'Player',
        'scout_role': 'Archetype',
        'star_prob': 'Star Probability',
        'height_fmt': 'Height',
        'years_exp': 'Exp',
        'usg_max': 'Usage %',
        'ts_used': 'TS %'
    })

    st.dataframe(
        display_df.style.format({
            "Star Probability": "{:.1%}",
            "Usage %": "{:.1f}%",
            "Exp": "{:.0f}",
            "TS %": "{:.1%}"
        }).background_gradient(subset=['Star Probability'], cmap="Greens"),
        use_container_width=True,
        hide_index=True
    )

else:
    # Analyst Mode (Everything)
    st.dataframe(
        df_year.style.format({
            "star_prob": "{:.1%}",
            "bpm_max": "{:.1f}",
            "ts_used": "{:.1%}",
            "stock_rate": "{:.1f}"
        }).background_gradient(subset=['star_prob'], cmap="RdYlGn"),
        use_container_width=True
    )
