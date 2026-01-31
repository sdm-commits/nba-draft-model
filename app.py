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

# Plain English Archetype Mapping (Request #5)
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
    "Undersized Paint Hustler": "Energy Big",
    "": "Role Player"
}

# ==============================================================================
# 2. LOAD & PREP DATA
# ==============================================================================
@st.cache_data
def load_data():
    file_path = "nba_draft_predictions.csv"
    if not os.path.exists(file_path):
        return None

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
    
    # 3. Safety Fill & Confidence Logic (Request #2)
    # If we don't have raw minutes, we use Experience as a proxy for Confidence
    if 'ts_used' not in df.columns: df['ts_used'] = 0.55
    if 'stock_rate' not in df.columns: df['stock_rate'] = 0.0
    
    # Simple Confidence Bucket
    df['confidence'] = np.where(df['years_exp'] >= 2.0, "High (Vet)", "Med (Young)")
    
    return df

df = load_data()

if df is None:
    st.error("⚠️ Data file `nba_draft_predictions.csv` not found. Please run the notebook first.")
    st.stop()

# ==============================================================================
# 3. SIDEBAR & FILTERS
# ==============================================================================
st.sidebar.header("🔍 Filters")

# Year Filter
all_years = sorted(df['year'].unique(), reverse=True)
selected_year = st.sidebar.selectbox("Draft Class", all_years)

# View Mode (Request #8)
view_mode = st.sidebar.radio("View Mode", ["Simple (Scouting)", "Analyst (Deep Dive)"])

# Highlight Player
search_term = st.sidebar.text_input("Highlight Player", "")

# Filter Data to Year
df_year = df[df['year'] == selected_year].copy()
df_year = df_year.sort_values("star_prob", ascending=False).reset_index(drop=True)
df_year['Rank'] = df_year.index + 1

# ==============================================================================
# 4. HEADER (TRUST & CONTEXT)
# ==============================================================================
st.title(f"🏀 {selected_year} NBA Draft Board")

# Request #1: The "What this means" sentence
st.markdown("""
> **What is this?** This model estimates the probability of a player becoming a **Top-Tier Starter** based on historical college-to-NBA progression (2010-2024).  
> It values **Efficiency, Age, and Physical Tools** over raw points per game. **It is a ranking tool, not a guarantee.**
""")

# ==============================================================================
# 5. TOP PROSPECTS (CARDS)
# ==============================================================================
if view_mode == "Simple (Scouting)":
    st.subheader(f"🏆 Top Prospects")
    
    # Top 3 Cards
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
                📏 <b>{player['height_fmt']}</b> | 🔒 Conf: {player['confidence']}<br>
                } stats]<br>
                📈 Usage: {player['usg_max']:.1f}%<br>
                🛡️ Stocks: {player['stock_rate']:.1f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")

# ==============================================================================
# 6. SCATTER PLOT (CLEAN & TRUSTWORTHY)
# ==============================================================================
st.subheader("📊 The Landscape: Usage vs. Efficiency")

# Prepare Plot Data (Request #4 & #7)
df_plot = df_year.copy()
df_plot["star_pct"] = (df_plot["star_prob"] * 100).round(1)
df_plot["usg_fmt"] = df_plot["usg_max"].round(1)
df_plot["stocks_fmt"] = df_plot["stock_rate"].round(1)
df_plot["ts_fmt"] = (df_plot["ts_used"] * 100).round(1)

# Fix Negative Size Bug
min_bpm = df_plot['bpm_max'].min()
if min_bpm < 0:
    df_plot['plot_size'] = df_plot['bpm_max'] + abs(min_bpm) + 10
else:
    df_plot['plot_size'] = df_plot['bpm_max'] + 10

# Color Logic
if search_term:
    df_plot['color_group'] = np.where(df_plot['player_name'].str.contains(search_term, case=False), "Highlight", "Others")
    color_map = {"Highlight": "#ff4b4b", "Others": "#dddddd"}
else:
    df_plot['color_group'] = df_plot['scout_role']
    color_map = None 

# Plotly Chart
fig = px.scatter(
    df_plot,
    x="usg_max",
    y="star_prob",
    color="color_group",
    color_discrete_map=color_map,
    size="plot_size",  # Safe size column
    hover_name="player_name",
    title=f"{selected_year} Draft Landscape (Size = BPM Impact)",
    labels={"usg_max": "Usage Rate (Offensive Load)", "star_prob": "Star Probability"},
    height=600,
    # Pass clean data for hover
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

# Request #4: The Clean "Scouting Card" Hover
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
    "• Def Activity: %{customdata[5]}<br>" +
    "<extra></extra>"
)

# Request #4: "Typical NBA Star Zone" Box
fig.add_shape(type="rect",
    x0=25, y0=0.40, x1=40, y1=1.0,
    line=dict(color="Green", width=1, dash="dot"),
    fillcolor="Green", opacity=0.1,
    layer="below"
)
fig.add_annotation(x=32, y=0.9, text="Superstar Zone", showarrow=False, font=dict(color="green"))

st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# 7. DATA TABLE
# ==============================================================================
st.subheader("📋 Detailed Board")

if search_term:
    df_year = df_year[df_year['player_name'].str.contains(search_term, case=False)]

if view_mode == "Simple (Scouting)":
    # Simple Columns
    show_cols = ['Rank', 'player_name', 'scout_role', 'star_prob', 'height_fmt', 'years_exp', 'confidence']
    
    # Rename
    display_df = df_year[show_cols].rename(columns={
        'player_name': 'Player',
        'scout_role': 'Archetype',
        'star_prob': 'Star Probability',
        'height_fmt': 'Height',
        'years_exp': 'Exp',
        'confidence': 'Trust'
    })

    st.dataframe(
        display_df.style.format({
            "Star Probability": "{:.1%}",
            "Exp": "{:.0f}"
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
