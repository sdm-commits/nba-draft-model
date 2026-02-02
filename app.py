import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import requests

# ==============================================================================
# 1. SETUP & CONFIG
# ==============================================================================
st.set_page_config(page_title="2025 NBA Draft Oracle", layout="wide", page_icon="🏀")

# Custom CSS
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
    .player-image {
        width: 120px;
        height: 90px;
        object-fit: cover;
        border-radius: 10px;
        margin-bottom: 10px;
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
    .highlight-link {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        color: white !important;
        padding: 5px 15px;
        border-radius: 20px;
        text-decoration: none;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-top: 10px;
    }
    .highlight-link:hover {
        opacity: 0.8;
    }
    .player-grid-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #e0e0e0;
        transition: transform 0.2s;
    }
    .player-grid-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .player-grid-image {
        width: 100px;
        height: 75px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Archetype Mapping
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

ARCH_COLORS = {
    "Generational Talent": "#FFD700",
    "Elite Producer": "#FF6B6B",
    "Star Potential": "#9B59B6",
    "Heliocentric Engine": "#F39C12",
    "Two-Way Monster": "#8E44AD",
    "Elite Shooter": "#3498DB",
    "Elite FR Shooter": "#2980B9",
    "Two-Way Wing": "#F1C40F",
    "Floor General": "#1ABC9C",
    "High Upside": "#E74C3C",
    "Consistent Producer": "#27AE60",
    "Late Bloomer": "#16A085",
    "Rim Runner": "#E67E22",
    "Rim Protector": "#95A5A6",
    "Raw Big (Risk)": "#7F8C8D",
    "Limited Big (Risk)": "#566573",
    "Freshman Phenom": "#E91E63",
    "Role Player": "#BDC3C7"
}

# ==============================================================================
# 2. NBA API FUNCTIONS
# ==============================================================================
@st.cache_data(ttl=86400)  # Cache for 24 hours
def get_nba_players():
    """Fetch all NBA players from the NBA API"""
    try:
        url = "https://stats.nba.com/stats/playerindex?Historical=0&LeagueID=00&Season=2024-25"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.nba.com/',
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        # Parse the response
        headers_list = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']

        df = pd.DataFrame(rows, columns=headers_list)

        # Create normalized name for matching
        df['norm_name'] = df['PLAYER_LAST_NAME'].str.lower() + ' ' + df['PLAYER_FIRST_NAME'].str.lower()
        df['norm_name_alt'] = df['PLAYER_FIRST_NAME'].str.lower() + ' ' + df['PLAYER_LAST_NAME'].str.lower()

        return df
    except Exception as e:
        st.warning(f"Could not fetch NBA player data: {e}")
        return pd.DataFrame()

def get_player_image_url(player_id):
    """Get NBA player headshot URL"""
    if pd.isna(player_id) or player_id == 0:
        return "https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png"
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{int(player_id)}.png"

def get_highlight_url(player_name):
    """Generate YouTube highlight search URL"""
    search_query = f"{player_name} NBA highlights 2024"
    return f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"

def get_nba_profile_url(player_id, player_name):
    """Get NBA.com player profile URL"""
    if pd.isna(player_id) or player_id == 0:
        # Fallback to search
        return f"https://www.nba.com/search?filters=&q={player_name.replace(' ', '%20')}"

    # Format name for URL (first-last)
    name_parts = player_name.lower().split()
    if len(name_parts) >= 2:
        url_name = f"{name_parts[0]}-{name_parts[-1]}"
    else:
        url_name = player_name.lower().replace(' ', '-')

    return f"https://www.nba.com/player/{int(player_id)}/{url_name}"

def match_to_nba_player(college_name, nba_players_df):
    """Match a college player name to NBA player ID"""
    if nba_players_df.empty:
        return None, None

    # Normalize the college name
    norm_name = college_name.lower().strip()

    # Try exact match
    match = nba_players_df[nba_players_df['norm_name_alt'] == norm_name]
    if len(match) > 0:
        return match.iloc[0]['PERSON_ID'], match.iloc[0]['PLAYER_FIRST_NAME'] + ' ' + match.iloc[0]['PLAYER_LAST_NAME']

    # Try partial match (last name)
    last_name = norm_name.split()[-1] if ' ' in norm_name else norm_name
    match = nba_players_df[nba_players_df['PLAYER_LAST_NAME'].str.lower() == last_name]
    if len(match) == 1:
        return match.iloc[0]['PERSON_ID'], match.iloc[0]['PLAYER_FIRST_NAME'] + ' ' + match.iloc[0]['PLAYER_LAST_NAME']

    return None, None

# ==============================================================================
# 3. LOAD & PREP DATA
# ==============================================================================
@st.cache_data
def load_data():
    possible_paths = [
        "nba_draft_predictions.csv",
        "2025_draft_predictions.csv",
        "all_draft_predictions_2024_2026.csv"
    ]

    df = None
    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            break

    if df is None:
        return None

    # Filtering
    if 'usg_max' in df.columns and 'star_prob' in df.columns:
        mask_exclude = (df['usg_max'] <= 0.0) & (df['star_prob'] < 0.001)
        df = df[~mask_exclude].copy()

    # Map Archetypes
    if 'archetype_note' in df.columns:
        df['scout_role'] = df['archetype_note'].map(ARCH_MAP).fillna(df['archetype_note'])
        df['scout_role'] = df['scout_role'].replace('', 'Role Player')
    else:
        df['scout_role'] = 'Role Player'

    # Format Height
    def fmt_height(h):
        if pd.isna(h) or h == 0: return "N/A"
        ft = int(h // 12)
        inch = int(h % 12)
        return f"{ft}'{inch}\""

    if 'height_in' in df.columns:
        df['height_fmt'] = df['height_in'].apply(fmt_height)
    else:
        df['height_fmt'] = "N/A"

    # Safety Fill
    default_cols = {
        'ts_per': 55.0, 'stock_rate': 0.0, 'years_exp': 1.0,
        'bpm_max': 0.0, 'usg_max': 20.0, 'star_prob': 0.1,
        'three_pct': 0.0, 'ast_per': 0.0, 'proj_vorp': 0.0,
        'adj_proj_vorp': 0.0, 'ev_vorp': 0.0
    }
    for col, default in default_cols.items():
        if col not in df.columns:
            df[col] = default

    # Tier Classification
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
    df['confidence'] = np.where(df['years_exp'] >= 3, "High",
                        np.where(df['years_exp'] >= 2, "Medium", "Projection"))

    return df

# Load data
df = load_data()
if df is None:
    st.error("⚠️ Data file not found.")
    st.stop()

# Load NBA players for matching
nba_players = get_nba_players()

# ==============================================================================
# 4. SIDEBAR & FILTERS
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

# Archetype Filter - handle NaN values
archetypes_list = df_year['scout_role'].dropna().unique().tolist()
archetypes_list = [a for a in archetypes_list if isinstance(a, str)]  # Remove any non-strings
all_archetypes = ['All'] + sorted(archetypes_list)
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
view_mode = st.sidebar.radio("📊 View Mode", ["Card View", "Chart View", "Grid View", "Data Table"])

st.sidebar.markdown("---")
st.sidebar.caption("Model trained on 2010-2024 NCAA data")

# Sort and rank
df_year = df_year.sort_values("star_prob", ascending=False).reset_index(drop=True)
df_year['Rank'] = df_year.index + 1

# ==============================================================================
# 5. MAIN HEADER
# ==============================================================================
st.markdown(f"<h1 class='main-header'>🏀 {selected_year} NBA Draft Oracle</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Predicting future NBA stars using <b>XGBoost</b>. Click a player's name to see their <b>Highlights</b>.</p>", unsafe_allow_html=True)
st.markdown("---")

# ==============================================================================
# 6. CARD VIEW
# ==============================================================================
if view_mode == "Card View":
    if len(df_year) > 0:
        # Filter by search
        if search_term:
            df_display = df_year[df_year['player_name'].str.contains(search_term, case=False, na=False)]
        else:
            df_display = df_year

        # Top prospect featured card
        if len(df_display) > 0:
            top_player = df_display.iloc[0]

            # Try to match to NBA player
            nba_id, nba_name = match_to_nba_player(top_player['player_name'], nba_players)
            player_img = get_player_image_url(nba_id)
            highlight_url = get_highlight_url(top_player['player_name'])

            col1, col2 = st.columns([1, 2])

            with col1:
                avg_prob = df['star_prob'].mean()
                delta = ((top_player['star_prob'] - avg_prob) / avg_prob) * 100

                st.markdown(f"""
                <div class="metric-card">
                    <span class="rank-badge">🥇 Top Prospect</span>
                    <img src="{player_img}" class="player-image" onerror="this.src='https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png'">
                    <h3>{top_player['player_name']}</h3>
                    <div class="archetype-badge">{top_player['scout_role']}</div>
                    <div class="big-stat">{top_player['star_prob']*100:.1f}%</div>
                    <div class="stat-label">⭐ Star Probability</div>
                    <span class="delta-positive">↑ {abs(delta):.1f}% vs avg</span>

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
                    </div>
                    <a href="{highlight_url}" target="_blank" class="highlight-link">▶️ Watch Highlights</a>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("##### 🏆 Top 10 Prospects")

                # Create rows of 5
                for row_start in range(0, min(10, len(df_display)), 5):
                    cols = st.columns(5)
                    for i, col in enumerate(cols):
                        idx = row_start + i
                        if idx < len(df_display):
                            player = df_display.iloc[idx]
                            nba_id_small, _ = match_to_nba_player(player['player_name'], nba_players)
                            img_url = get_player_image_url(nba_id_small)

                            with col:
                                tier_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][idx]
                                st.image(img_url, width=80)
                                st.caption(f"{tier_emoji} **{player['player_name'][:15]}**")
                                st.caption(f"{player['star_prob']*100:.0f}% | {player['bpm_max']:.1f} BPM")

# ==============================================================================
# 7. CHART VIEW
# ==============================================================================
elif view_mode == "Chart View":
    st.subheader(f"{selected_year} Usage vs. Potential")

    if len(df_year) > 0:
        df_plot = df_year.copy()
        df_plot["star_pct"] = (df_plot["star_prob"] * 100).round(1)

        min_bpm = df_plot['bpm_max'].min()
        if pd.isna(min_bpm): min_bpm = 0
        df_plot['plot_size'] = (df_plot['bpm_max'] - min_bpm + 5).clip(lower=5)

        if search_term:
            df_plot['color_group'] = np.where(
                df_plot['player_name'].str.contains(search_term, case=False, na=False),
                "🔍 Highlighted", df_plot['scout_role']
            )
        else:
            df_plot['color_group'] = df_plot['scout_role']

        fig = px.scatter(
            df_plot, x="usg_max", y="star_prob", color="color_group",
            color_discrete_map=ARCH_COLORS, size="plot_size",
            hover_name="player_name",
            labels={"usg_max": "Usage Rate (%)", "star_prob": "Star Probability"},
            height=600,
            custom_data=['scout_role', 'star_pct', 'bpm_max', 'height_fmt', 'adj_proj_vorp', 'tier']
        )

        fig.update_traces(
            hovertemplate=
            "<b>%{hovertext}</b><br><br>" +
            "🎭 Archetype: %{customdata[0]}<br>" +
            "⭐ Star Prob: %{customdata[1]}%<br>" +
            "🏆 Tier: %{customdata[5]}<br>" +
            "📊 Usage: %{x:.1f}%<br>" +
            "🔥 BPM: %{customdata[2]:.1f}<br>" +
            "<extra></extra>"
        )

        # Tier lines
        fig.add_hline(y=0.60, line_dash="dot", line_color="#FFD700",
                      annotation_text="MVP Tier", annotation_position="right")
        fig.add_hline(y=0.45, line_dash="dot", line_color="#C0C0C0",
                      annotation_text="All-Star Tier", annotation_position="right")
        fig.add_hline(y=0.25, line_dash="dot", line_color="#CD7F32",
                      annotation_text="Starter Tier", annotation_position="right")

        # Top player labels
        for _, player in df_plot.nlargest(5, 'star_prob').iterrows():
            fig.add_annotation(
                x=player['usg_max'], y=player['star_prob'] + 0.02,
                text=player['player_name'].split()[-1],
                showarrow=False, font=dict(size=10, color="white"),
                bgcolor="rgba(0,0,0,0.5)", borderpad=3
            )

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            xaxis=dict(gridcolor='rgba(0,0,0,0.1)', range=[5, 40]),
            yaxis=dict(gridcolor='rgba(0,0,0,0.1)', range=[0, 1], tickformat='.0%')
        )

        st.plotly_chart(fig, use_container_width=True)

        # Tier counts
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🥇 MVP Caliber", len(df_year[df_year['tier'] == 'MVP Caliber']))
        col2.metric("⭐ All-Star", len(df_year[df_year['tier'] == 'All-Star Potential']))
        col3.metric("✅ Starter", len(df_year[df_year['tier'] == 'Quality Starter']))
        col4.metric("📋 Role Player", len(df_year[df_year['tier'] == 'Role Player']))

# ==============================================================================
# 8. GRID VIEW WITH IMAGES & HIGHLIGHTS
# ==============================================================================
elif view_mode == "Grid View":
    st.subheader(f"📸 {selected_year} Prospect Gallery")

    if search_term:
        df_display = df_year[df_year['player_name'].str.contains(search_term, case=False, na=False)]
    else:
        df_display = df_year

    # Number of columns
    num_cols = 4

    for row_start in range(0, len(df_display), num_cols):
        cols = st.columns(num_cols)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx < len(df_display):
                player = df_display.iloc[idx]
                nba_id, _ = match_to_nba_player(player['player_name'], nba_players)
                img_url = get_player_image_url(nba_id)
                highlight_url = get_highlight_url(player['player_name'])

                with col:
                    st.markdown(f"""
                    <div class="player-grid-card">
                        <img src="{img_url}" class="player-grid-image" onerror="this.src='https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png'">
                        <h4 style="margin: 5px 0;">#{idx+1} {player['player_name']}</h4>
                        <span style="background: {ARCH_COLORS.get(player['scout_role'], '#999')}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem;">{player['scout_role']}</span>
                        <p style="margin: 10px 0 5px 0;">
                            <b style="font-size: 1.5rem; color: #4ecdc4;">{player['star_prob']*100:.0f}%</b><br>
                            <span style="color: #666; font-size: 0.8rem;">Star Probability</span>
                        </p>
                        <p style="font-size: 0.8rem; color: #666;">
                            📊 {player['bpm_max']:.1f} BPM | 📏 {player['height_fmt']}
                        </p>
                        <a href="{highlight_url}" target="_blank" style="background: #e74c3c; color: white; padding: 5px 10px; border-radius: 15px; text-decoration: none; font-size: 0.75rem;">▶️ Highlights</a>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("")  # Spacing

# ==============================================================================
# 9. DATA TABLE VIEW
# ==============================================================================
elif view_mode == "Data Table":
    st.subheader("📋 Full Draft Board")

    if search_term:
        df_display = df_year[df_year['player_name'].str.contains(search_term, case=False, na=False)]
    else:
        df_display = df_year

    # Add highlight links
    df_display = df_display.copy()
    df_display['Highlights'] = df_display['player_name'].apply(
        lambda x: f"[▶️ Watch](https://www.youtube.com/results?search_query={x.replace(' ', '+')}+highlights)"
    )

    display_cols = ['Rank', 'player_name', 'scout_role', 'tier', 'star_prob',
                    'bpm_max', 'usg_max', 'height_fmt', 'years_exp', 'Highlights']
    display_cols = [c for c in display_cols if c in df_display.columns]

    rename_map = {
        'player_name': 'Player', 'scout_role': 'Archetype', 'tier': 'Tier',
        'star_prob': 'Star Prob', 'bpm_max': 'BPM', 'usg_max': 'Usage',
        'height_fmt': 'Height', 'years_exp': 'Exp'
    }

    styled_df = df_display[display_cols].rename(columns=rename_map)

    st.dataframe(
        styled_df.style.format({
            "Star Prob": "{:.1%}", "BPM": "{:.1f}", "Usage": "{:.1f}", "Exp": "{:.0f}"
        }).background_gradient(subset=['Star Prob'], cmap="RdYlGn"),
        use_container_width=True, hide_index=True, height=600,
        column_config={
            "Highlights": st.column_config.LinkColumn("Highlights", display_text="▶️ Watch")
        }
    )

# ==============================================================================
# 10. PLAYER COMPARISON
# ==============================================================================
st.markdown("---")
st.subheader("🔄 Player Comparison")

if len(df_year) >= 2:
    compare_cols = st.columns(2)

    with compare_cols[0]:
        player1 = st.selectbox("Select Player 1", df_year['player_name'].tolist(), index=0)

    with compare_cols[1]:
        player2_options = [p for p in df_year['player_name'].tolist() if p != player1]
        player2 = st.selectbox("Select Player 2", player2_options, index=0 if player2_options else 0)

    if player1 and player2:
        p1_data = df_year[df_year['player_name'] == player1].iloc[0]
        p2_data = df_year[df_year['player_name'] == player2].iloc[0]

        # Get images
        p1_id, _ = match_to_nba_player(player1, nba_players)
        p2_id, _ = match_to_nba_player(player2, nba_players)

        img_col1, radar_col, img_col2 = st.columns([1, 2, 1])

        with img_col1:
            st.image(get_player_image_url(p1_id), width=150)
            st.markdown(f"**{player1}**")
            st.caption(f"{p1_data['scout_role']}")
            st.metric("Star Prob", f"{p1_data['star_prob']*100:.1f}%")

        with img_col2:
            st.image(get_player_image_url(p2_id), width=150)
            st.markdown(f"**{player2}**")
            st.caption(f"{p2_data['scout_role']}")
            st.metric("Star Prob", f"{p2_data['star_prob']*100:.1f}%")

        with radar_col:
            compare_metrics = ['star_prob', 'bpm_max', 'usg_max', 'stock_rate', 'adj_proj_vorp']
            metric_names = ['Star Prob', 'BPM', 'Usage', 'Stocks', 'Proj VORP']

            fig_radar = go.Figure()

            p1_values, p2_values = [], []
            for metric in compare_metrics:
                max_val = df_year[metric].max()
                min_val = df_year[metric].min()
                range_val = max_val - min_val if max_val != min_val else 1
                p1_values.append((p1_data[metric] - min_val) / range_val)
                p2_values.append((p2_data[metric] - min_val) / range_val)

            fig_radar.add_trace(go.Scatterpolar(
                r=p1_values + [p1_values[0]], theta=metric_names + [metric_names[0]],
                fill='toself', name=player1, line_color='#FF6B6B'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=p2_values + [p2_values[0]], theta=metric_names + [metric_names[0]],
                fill='toself', name=player2, line_color='#4ECDC4'
            ))

            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                showlegend=True, height=350
            )
            st.plotly_chart(fig_radar, use_container_width=True)

# ==============================================================================
# 11. FOOTER
# ==============================================================================
st.markdown("---")
st.caption("🏀 NBA Draft Oracle | Model trained on 2010-2024 NCAA data | Images from NBA.com")
