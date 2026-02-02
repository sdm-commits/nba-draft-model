import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# ==============================================================================
# 1. SETUP & CONFIG
# ==============================================================================
st.set_page_config(page_title="2025 NBA Draft Oracle", layout="wide", page_icon="🏀")

# Custom CSS for modern scouting card feel
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-top: 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #ff6b6b;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        color: white;
        margin-bottom: 10px;
    }
    .metric-card h3 {
        margin: 0;
        color: #fff;
        font-size: 1.3rem;
    }
    .metric-card .rank-badge {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 8px;
    }
    .big-stat {
        font-size: 2.8rem;
        font-weight: bold;
        color: #4ecdc4;
        line-height: 1.1;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #aaa;
        margin-top: -5px;
    }
    .delta-positive {
        color: #4ecdc4;
        font-size: 0.85rem;
        background: rgba(78, 205, 196, 0.2);
        padding: 2px 8px;
        border-radius: 10px;
    }
    .delta-negative {
        color: #ff6b6b;
        font-size: 0.85rem;
        background: rgba(255, 107, 107, 0.2);
        padding: 2px 8px;
        border-radius: 10px;
    }
    .archetype-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin: 8px 0;
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    .stat-item {
        text-align: center;
    }
    .stat-value {
        font-size: 1.1rem;
        font-weight: bold;
        color: #fff;
    }
    .stat-name {
        font-size: 0.7rem;
        color: #888;
        text-transform: uppercase;
    }
    .tier-mvp {
        color: #ffd700;
        font-weight: bold;
    }
    .tier-allstar {
        color: #c0c0c0;
        font-weight: bold;
    }
    .tier-starter {
        color: #cd7f32;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Updated Archetype Mapping (matches your model output)
ARCH_MAP = {
    "Generational": "Generational Talent",
    "Elite Producer": "Elite Producer",
    "Star Potential": "Star Potential",
    "Heliocentric Engine": "Heliocentric Engine",
    "Monstar": "Two-Way Monster",
    "Elite Shooter": "Elite Shooter",
    "Elite FR Shooter": "Elite FR Shooter",
    "Two-Way Wing": "Two-Way Wing",
    "Playmaker": "Floor General",
    "High Upside": "High Upside",
    "Consistent Producer": "Consistent Producer",
    "Improver": "Late Bloomer",
    "Rim Runner": "Rim Runner",
    "Rim Protector": "Rim Protector",
    "Raw Big": "Raw Big (Risk)",
    "Limited Big": "Limited Big (Risk)",
    "Freshman Phenom": "Freshman Phenom",
    "": "Role Player"
}

# Archetype Colors (matching your screenshot aesthetic)
ARCH_COLORS = {
    "Generational Talent": "#FFD700",      # Gold
    "Elite Producer": "#FF6B6B",            # Coral Red
    "Star Potential": "#9B59B6",            # Purple
    "Heliocentric Engine": "#F39C12",       # Orange
    "Two-Way Monster": "#8E44AD",           # Deep Purple
    "Elite Shooter": "#3498DB",             # Blue
    "Elite FR Shooter": "#2980B9",          # Darker Blue
    "Two-Way Wing": "#F1C40F",              # Yellow
    "Floor General": "#1ABC9C",             # Teal
    "High Upside": "#E74C3C",               # Red
    "Consistent Producer": "#27AE60",       # Green
    "Late Bloomer": "#16A085",              # Dark Teal
    "Rim Runner": "#E67E22",                # Dark Orange
    "Rim Protector": "#95A5A6",             # Gray
    "Raw Big (Risk)": "#7F8C8D",            # Dark Gray
    "Limited Big (Risk)": "#566573",        # Darker Gray
    "Freshman Phenom": "#E91E63",           # Pink
    "Role Player": "#BDC3C7"                # Light Gray
}

# ==============================================================================
# 2. LOAD & PREP DATA
# ==============================================================================
@st.cache_data
def load_data():
    # Try multiple possible file paths
    possible_paths = [
        "nba_draft_predictions.csv",
        "2025_draft_predictions.csv",
        "/content/drive/MyDrive/nba_model_data/2025_draft_predictions.csv"
    ]

    df = None
    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            break

    if df is None:
        return None

    # --- FILTERING LOGIC ---
    # Exclude invalid rows
    if 'usg_max' in df.columns and 'star_prob' in df.columns:
        mask_exclude = (df['usg_max'] <= 0.0) & (df['star_prob'] < 0.001)
        df = df[~mask_exclude].copy()

    # 1. Map Archetypes to Plain English
    if 'archetype_note' in df.columns:
        df['scout_role'] = df['archetype_note'].map(ARCH_MAP).fillna(df['archetype_note'])
        df['scout_role'] = df['scout_role'].replace('', 'Role Player')
    else:
        df['scout_role'] = 'Role Player'

    # 2. Format Height
    def fmt_height(h):
        if pd.isna(h) or h == 0: return "N/A"
        ft = int(h // 12)
        inch = int(h % 12)
        return f"{ft}'{inch}\""

    if 'height_in' in df.columns:
        df['height_fmt'] = df['height_in'].apply(fmt_height)
    else:
        df['height_fmt'] = "N/A"

    # 3. Safety Fill
    default_cols = {
        'ts_per': 55.0, 'stock_rate': 0.0, 'years_exp': 1.0,
        'bpm_max': 0.0, 'usg_max': 20.0, 'star_prob': 0.1,
        'three_pct': 0.0, 'ast_per': 0.0, 'proj_vorp': 0.0,
        'adj_proj_vorp': 0.0, 'ev_vorp': 0.0
    }
    for col, default in default_cols.items():
        if col not in df.columns:
            df[col] = default

    # 4. Tier Classification
    def get_tier(prob):
        if prob >= 0.60:
            return "MVP Caliber"
        elif prob >= 0.45:
            return "All-Star Potential"
        elif prob >= 0.25:
            return "Quality Starter"
        else:
            return "Role Player"

    df['tier'] = df['star_prob'].apply(get_tier)

    # 5. Confidence based on experience
    df['confidence'] = np.where(df['years_exp'] >= 3, "High",
                        np.where(df['years_exp'] >= 2, "Medium", "Projection"))

    # 6. Calculate percentile within class
    df['prob_percentile'] = df['star_prob'].rank(pct=True) * 100

    return df

df = load_data()

if df is None:
    st.error("⚠️ Data file not found. Please ensure `nba_draft_predictions.csv` or `2025_draft_predictions.csv` exists.")
    st.stop()

# ==============================================================================
# 3. SIDEBAR & FILTERS
# ==============================================================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/889/889442.png", width=80)
st.sidebar.title("🏀 Draft Oracle")
st.sidebar.markdown("---")

# Year Filter
if 'year' in df.columns:
    all_years = sorted(df['year'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("📅 Draft Class", all_years)
    df_year = df[df['year'] == selected_year].copy()
else:
    selected_year = 2025
    df_year = df.copy()

# Archetype Filter
all_archetypes = ['All'] + sorted(df_year['scout_role'].unique().tolist())
selected_archetype = st.sidebar.selectbox("🎭 Archetype Filter", all_archetypes)

if selected_archetype != 'All':
    df_year = df_year[df_year['scout_role'] == selected_archetype]

# Tier Filter
tier_filter = st.sidebar.multiselect(
    "🏆 Tier Filter",
    ["MVP Caliber", "All-Star Potential", "Quality Starter", "Role Player"],
    default=["MVP Caliber", "All-Star Potential", "Quality Starter"]
)
df_year = df_year[df_year['tier'].isin(tier_filter)]

# Search
search_term = st.sidebar.text_input("🔍 Search Player", "")

# View Mode
view_mode = st.sidebar.radio("📊 View Mode", ["Visual Analysis", "Deep Dive Data"])

st.sidebar.markdown("---")
st.sidebar.markdown("**Model Info**")
st.sidebar.caption("XGBoost classifier trained on 2010-2024 college stats. Predicts probability of becoming a top-tier NBA contributor.")

# Sort and rank
df_year = df_year.sort_values("star_prob", ascending=False).reset_index(drop=True)
df_year['Rank'] = df_year.index + 1

# ==============================================================================
# 4. MAIN HEADER
# ==============================================================================
st.markdown(f"<h1 class='main-header'>🏀 {selected_year} NBA Draft Oracle</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Predicting future NBA stars using <b>XGBoost</b>. Click a player's name to see their <b>Highlights</b>.</p>", unsafe_allow_html=True)
st.markdown("---")

# ==============================================================================
# 5. TOP PROSPECT CARDS
# ==============================================================================
if view_mode == "Visual Analysis":
    if len(df_year) > 0:
        # Get top prospect
        top_player = df_year.iloc[0]

        col1, col2 = st.columns([1, 2])

        with col1:
            # Calculate delta (difference from average)
            avg_prob = df['star_prob'].mean()
            delta = ((top_player['star_prob'] - avg_prob) / avg_prob) * 100
            delta_class = "delta-positive" if delta > 0 else "delta-negative"
            delta_sign = "↑" if delta > 0 else "↓"

            st.markdown(f"""
            <div class="metric-card">
                <span class="rank-badge">🥇 Top Prospect</span>
                <h3>{top_player['player_name']}</h3>
                <div class="archetype-badge">{top_player['scout_role']}</div>
                <div class="big-stat">{top_player['star_prob']*100:.1f}%</div>
                <div class="stat-label">⭐ Star Probability</div>
                <span class="{delta_class}">{delta_sign} {abs(delta):.1f}% vs avg</span>

                <div class="stat-row">
                    <div class="stat-item">
                        <div class="stat-value">{top_player['bpm_max']:.1f}</div>
                        <div class="stat-name">BPM</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{top_player['usg_max']:.1f}%</div>
                        <div class="stat-name">Usage</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{top_player['height_fmt']}</div>
                        <div class="stat-name">Height</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{top_player['adj_proj_vorp']:.1f}</div>
                        <div class="stat-name">Proj VORP</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Top 5 mini cards
            st.markdown("##### 🏆 Top 5 Prospects")
            top5_cols = st.columns(5)
            for i, (idx, player) in enumerate(df_year.head(5).iterrows()):
                with top5_cols[i]:
                    tier_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
                    st.metric(
                        label=f"{tier_emoji} {player['player_name'][:12]}",
                        value=f"{player['star_prob']*100:.0f}%",
                        delta=f"{player['bpm_max']:.1f} BPM"
                    )

    st.markdown("---")

# ==============================================================================
# 6. MAIN SCATTER PLOT
# ==============================================================================
tab1, tab2 = st.tabs(["📊 Visual Analysis", "📋 Deep Dive Data"])

with tab1:
    st.subheader(f"{selected_year} Usage vs. Potential")

    if len(df_year) > 0:
        df_plot = df_year.copy()
        df_plot["star_pct"] = (df_plot["star_prob"] * 100).round(1)

        # Handle BPM for bubble size
        min_bpm = df_plot['bpm_max'].min()
        if pd.isna(min_bpm): min_bpm = 0
        df_plot['plot_size'] = (df_plot['bpm_max'] - min_bpm + 5).clip(lower=5)

        # Color by archetype or highlight
        if search_term:
            df_plot['color_group'] = np.where(
                df_plot['player_name'].str.contains(search_term, case=False, na=False),
                "🔍 Highlighted",
                df_plot['scout_role']
            )
        else:
            df_plot['color_group'] = df_plot['scout_role']

        # Create figure
        fig = px.scatter(
            df_plot,
            x="usg_max",
            y="star_prob",
            color="color_group",
            color_discrete_map=ARCH_COLORS,
            size="plot_size",
            hover_name="player_name",
            labels={"usg_max": "Usage Rate (%)", "star_prob": "Star Probability"},
            height=600,
            custom_data=['scout_role', 'star_pct', 'bpm_max', 'height_fmt', 'adj_proj_vorp', 'tier']
        )

        # Custom hover template
        fig.update_traces(
            hovertemplate=
            "<b>%{hovertext}</b><br>" +
            "<br>" +
            "🎭 <b>Archetype:</b> %{customdata[0]}<br>" +
            "⭐ <b>Star Prob:</b> %{customdata[1]}%<br>" +
            "🏆 <b>Tier:</b> %{customdata[5]}<br>" +
            "<br>" +
            "📊 <b>Usage:</b> %{x:.1f}%<br>" +
            "🔥 <b>BPM:</b> %{customdata[2]:.1f}<br>" +
            "📏 <b>Height:</b> %{customdata[3]}<br>" +
            "📈 <b>Proj VORP:</b> %{customdata[4]:.1f}<br>" +
            "<extra></extra>"
        )

        # Add tier threshold lines
        fig.add_hline(y=0.60, line_dash="dot", line_color="#FFD700",
                      annotation_text="MVP Tier", annotation_position="right")
        fig.add_hline(y=0.45, line_dash="dot", line_color="#C0C0C0",
                      annotation_text="All-Star Tier", annotation_position="right")
        fig.add_hline(y=0.25, line_dash="dot", line_color="#CD7F32",
                      annotation_text="Starter Tier", annotation_position="right")

        # Add top player labels
        top_players = df_plot.nlargest(5, 'star_prob')
        for _, player in top_players.iterrows():
            fig.add_annotation(
                x=player['usg_max'],
                y=player['star_prob'] + 0.02,
                text=player['player_name'].split()[-1],  # Last name only
                showarrow=False,
                font=dict(size=10, color="white"),
                bgcolor="rgba(0,0,0,0.5)",
                borderpad=3
            )

        # Layout
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#333'),
            legend=dict(
                title="Archetype",
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(gridcolor='rgba(0,0,0,0.1)', range=[5, 40]),
            yaxis=dict(gridcolor='rgba(0,0,0,0.1)', range=[0, 1], tickformat='.0%')
        )

        st.plotly_chart(fig, use_container_width=True)

        # Tier breakdown
        col1, col2, col3, col4 = st.columns(4)
        mvp_count = len(df_year[df_year['tier'] == 'MVP Caliber'])
        allstar_count = len(df_year[df_year['tier'] == 'All-Star Potential'])
        starter_count = len(df_year[df_year['tier'] == 'Quality Starter'])
        role_count = len(df_year[df_year['tier'] == 'Role Player'])

        col1.metric("🥇 MVP Caliber", mvp_count, help="Star Prob ≥ 60%")
        col2.metric("⭐ All-Star", allstar_count, help="Star Prob 45-60%")
        col3.metric("✅ Starter", starter_count, help="Star Prob 25-45%")
        col4.metric("📋 Role Player", role_count, help="Star Prob < 25%")
    else:
        st.info("No players match the current filters.")

with tab2:
    st.subheader("📋 Full Draft Board")

    if search_term:
        df_display = df_year[df_year['player_name'].str.contains(search_term, case=False, na=False)]
    else:
        df_display = df_year

    # Select columns to display
    display_cols = ['Rank', 'player_name', 'scout_role', 'tier', 'star_prob',
                    'bpm_max', 'usg_max', 'height_fmt', 'years_exp', 'adj_proj_vorp']

    # Filter to available columns
    display_cols = [c for c in display_cols if c in df_display.columns]

    # Rename for display
    rename_map = {
        'player_name': 'Player',
        'scout_role': 'Archetype',
        'tier': 'Tier',
        'star_prob': 'Star Prob',
        'bpm_max': 'BPM',
        'usg_max': 'Usage',
        'height_fmt': 'Height',
        'years_exp': 'Exp',
        'adj_proj_vorp': 'Proj VORP'
    }

    styled_df = df_display[display_cols].rename(columns=rename_map)

    st.dataframe(
        styled_df.style.format({
            "Star Prob": "{:.1%}",
            "BPM": "{:.1f}",
            "Usage": "{:.1f}",
            "Exp": "{:.0f}",
            "Proj VORP": "{:.1f}"
        }).background_gradient(subset=['Star Prob'], cmap="RdYlGn"),
        use_container_width=True,
        hide_index=True,
        height=600
    )

# ==============================================================================
# 7. PLAYER COMPARISON
# ==============================================================================
st.markdown("---")
st.subheader("🔄 Player Comparison")

compare_cols = st.columns(2)

with compare_cols[0]:
    player1 = st.selectbox("Select Player 1", df_year['player_name'].tolist(), index=0)

with compare_cols[1]:
    player2_options = [p for p in df_year['player_name'].tolist() if p != player1]
    player2 = st.selectbox("Select Player 2", player2_options, index=min(1, len(player2_options)-1) if player2_options else 0)

if player1 and player2:
    p1_data = df_year[df_year['player_name'] == player1].iloc[0]
    p2_data = df_year[df_year['player_name'] == player2].iloc[0]

    compare_metrics = ['star_prob', 'bpm_max', 'usg_max', 'stock_rate', 'adj_proj_vorp']
    metric_names = ['Star Prob', 'BPM', 'Usage', 'Stocks', 'Proj VORP']

    # Radar chart
    fig_radar = go.Figure()

    # Normalize values for radar chart
    p1_values = []
    p2_values = []
    for metric in compare_metrics:
        max_val = df_year[metric].max()
        min_val = df_year[metric].min()
        range_val = max_val - min_val if max_val != min_val else 1
        p1_values.append((p1_data[metric] - min_val) / range_val)
        p2_values.append((p2_data[metric] - min_val) / range_val)

    fig_radar.add_trace(go.Scatterpolar(
        r=p1_values + [p1_values[0]],
        theta=metric_names + [metric_names[0]],
        fill='toself',
        name=player1,
        line_color='#FF6B6B'
    ))

    fig_radar.add_trace(go.Scatterpolar(
        r=p2_values + [p2_values[0]],
        theta=metric_names + [metric_names[0]],
        fill='toself',
        name=player2,
        line_color='#4ECDC4'
    ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        height=400
    )

    st.plotly_chart(fig_radar, use_container_width=True)

    # Side by side stats
    stat_cols = st.columns(2)
    with stat_cols[0]:
        st.markdown(f"**{player1}** - {p1_data['scout_role']}")
        st.write(f"⭐ Star Prob: **{p1_data['star_prob']*100:.1f}%**")
        st.write(f"🔥 BPM: **{p1_data['bpm_max']:.1f}**")
        st.write(f"📊 Usage: **{p1_data['usg_max']:.1f}%**")

    with stat_cols[1]:
        st.markdown(f"**{player2}** - {p2_data['scout_role']}")
        st.write(f"⭐ Star Prob: **{p2_data['star_prob']*100:.1f}%**")
        st.write(f"🔥 BPM: **{p2_data['bpm_max']:.1f}**")
        st.write(f"📊 Usage: **{p2_data['usg_max']:.1f}%**")

# ==============================================================================
# 8. FOOTER
# ==============================================================================
st.markdown("---")
st.caption("🏀 NBA Draft Oracle | Model trained on 2010-2024 NCAA data | Not financial advice")

