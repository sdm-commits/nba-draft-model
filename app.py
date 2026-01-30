import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="NBA Draft Oracle", layout="wide")

# 2. Load Data (Cached so it doesn't reload on every click)
@st.cache_data
def load_data():
    # Ensure 'nba_draft_predictions.csv' is in the same folder as this script
    # If the file isn't found, this will throw an error, so make sure to upload it!
    df = pd.read_csv('nba_draft_predictions.csv')
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("⚠️ Data file not found! Please upload 'nba_draft_predictions.csv' to your repository.")
    st.stop()

# 3. Sidebar Filters
st.sidebar.header("🔍 Filter Options")
# Sort years descending so the newest draft is first
years_available = sorted(df['year'].unique(), reverse=True)
selected_year = st.sidebar.selectbox("Select Draft Class", years_available)

# Filter logic for the main dataframe (used in metrics and table)
year_df = df[df['year'] == selected_year].sort_values('star_prob', ascending=False).reset_index(drop=True)

# 4. Main Dashboard
st.title(f"🏀 {selected_year} NBA Draft Model Predictions")
st.markdown("""
This model calculates the probability of a college player becoming an NBA Star.
It uses **XGBoost** trained on historical data (2010-2023) and classifies players into Archetypes like *Aliens* and *Heliocentric Engines*.
""")

# 5. Top Metrics (Key Stats)
col1, col2, col3 = st.columns(3)
if not year_df.empty:
    top_prospect = year_df.iloc[0]
    col1.metric("Highest Rated Prospect", top_prospect['player_name'], f"{top_prospect['star_prob']:.1%}")
    col2.metric("Archetype", top_prospect['archetype_note'])
    col3.metric("Projected Impact (BPM)", round(top_prospect['bpm_max'], 1))

# --------------------------------------------------------
# 6. INTERACTIVE SCATTER PLOT (CLEAN & FIXED)
# --------------------------------------------------------
st.subheader("Tier List: Usage vs. Star Probability")

if not year_df.empty:
    # A. CLEANING STEP: REMOVE THE NOISE
    # Only show players with > 1% Star Probability OR > 30% Usage
    # This deletes the dense "blob" of low-potential players at the bottom
    clean_df = year_df[
        (year_df['star_prob'] > 0.01) | 
        (year_df['usg_max'] > 30.0)
    ].copy()

    # B. FIX: Handle Negative BPMs for plotting sizes
    # We clip the values so nothing is below 0.1 (dots can't be negative size)
    # This fixes the "ValueError" you were seeing.
    clean_df['plot_size'] = clean_df['bpm_max'].clip(lower=0.1)

    # C. CREATE THE PLOT
    fig = px.scatter(
        clean_df,
        x="usg_max",
        y="star_prob",
        color="archetype_note",
        # Safely handle the symbol argument (only use if we have mixed years, usually None here)
        symbol="year" if len(clean_df['year'].unique()) > 1 else None,
        hover_name="player_name",
        size="plot_size",  # <--- USES THE SAFE COLUMN
        hover_data={
            "height_in": True, 
            "ast_per": True, 
            "bpm_max": True, # Show the REAL bpm in hover
            "plot_size": False # Hide the fake size column
        },
        title=f"<b>{selected_year} Draft Class: The Tier List</b>",
        labels={"usg_max": "Usage Rate (%)", "star_prob": "Star Probability (0-100%)"},
        color_discrete_map={
            "Alien": "#ff2b2b", 
            "Heliocentric Engine": "#ffa600", 
            "Efficiency God": "#0068c9", 
            "Jumbo Creator": "#83c9ff", 
            "Scoring Guard": "#ff4b4b",
            "Volatile Wing": "#808080",
            "": "#d3d3d3" # Fallback for unknown types
        },
        opacity=0.85
    )

    # D. PROFESSIONAL TOUCHES
    # 1. Add Tier Lines (Background Context)
    fig.add_hline(y=0.60, line_dash="dot", line_color="gold", annotation_text="MVP Candidate", annotation_position="top left")
    fig.add_hline(y=0.45, line_dash="dot", line_color="silver", annotation_text="All-Star Potential", annotation_position="top left")

    # 2. Smart Annotations (Only label the top 8 players permanently)
    top_prospects = clean_df.sort_values('star_prob', ascending=False).head(8)
    for i, row in top_prospects.iterrows():
        fig.add_annotation(
            x=row['usg_max'],
            y=row['star_prob'],
            text=row['player_name'],
            showarrow=True,
            arrowhead=1,
            yshift=10,
            font=dict(size=11, color="black")
        )

    # 3. Clean up the layout (White background, bottom legend)
    fig.update_layout(
        plot_bgcolor="white",
        height=600,
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=40, r=40, t=80, b=40),
        legend=dict(
            orientation="h", # Horizontal legend at bottom
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    # 4. Nice Gridlines
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0', tickformat=".0%")

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No data found for this year.")

# --------------------------------------------------------
# 7. SEARCHABLE DATA TABLE
# --------------------------------------------------------
st.subheader("📋 Full Scouting Report")
search_term = st.text_input("Search for a player:", "")

if search_term:
    display_df = year_df[year_df['player_name'].str.contains(search_term, case=False)]
else:
    display_df = year_df

# Format the dataframe for display (Add % signs, color gradients)
st.dataframe(
    display_df.style.background_gradient(subset=['star_prob'], cmap="Greens")
              .format({'star_prob': "{:.1%}", 'bpm_max': "{:.1f}", 'usg_max': "{:.1f}"}),
    use_container_width=True,
    height=500
)
