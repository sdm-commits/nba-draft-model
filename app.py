import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# ==============================================================================
# 1. SETUP & CONFIG
# ==============================================================================
st.set_page_config(page_title="NBA Draft Oracle", layout="wide", page_icon="🏀")

# ==============================================================================
# EXCLUDED PLAYERS CONFIG
# ==============================================================================
EXCLUDED_PLAYERS = {
    2025: [
        "Nate Bittle",
        "Yaxel Lendeborg",
        "Nolan Winter",
        "Joshua Jefferson",
        "Thomas Haugh",
        "Alvaro Folgueiras",
        "Tomislav Ivisic",
        "JT Toppin",
        "Bennett Stirtz",
        "Zuby Ejiofor",
        "Mouhamed Dioubate",
        "Joseph Tugler",
        "Jayden Quaintance",
        "Keanu Dawes",
        "Malik Reneau",
        "Henri Veesaar",
        "Alex Condon",
        "Anthony Robinson II",
        "Miles Byrd",
        "Amael L'Etang",
        "Mister Dean",
        "Eric Dailey Jr.",
        "Darrion Williams",
        "Trey Kaufman-Renn",
        "Xaivian Lee",
        "Dailyn Swain"
    ],
    2026: [],
}

def get_excluded_players(year):
    return EXCLUDED_PLAYERS.get(year, [])

# Clean, Apple-inspired CSS
st.markdown("""
<style>
    .block-container {
        padding-top: 3rem;
        padding-bottom: 2rem;
    }
    header[data-testid="stHeader"] {
        background: transparent;
    }
    /* Typography */
    .main-title {
        font-size: 2.2rem;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 0.25rem;
        letter-spacing: -0.5px;
    }
    .subtitle {
        font-size: 1rem;
        color: #86868b;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }
    /* Player Card - Updated Design */
    .player-card {
        background: #ffffff;
        border: 1px solid #e5e5e7;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        position: relative;
    }
    .player-card:hover {
        border-color: #0071e3;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    /* Rank Badge */
    .rank-badge {
        position: absolute;
        top: 16px;
        left: 16px;
        width: 36px;
        height: 36px;
        background: #1d1d1f;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .rank-badge.top3 { background: #bf8700; }
    .rank-badge.top10 { background: #5856d6; }
    /* Card Header */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
        padding-left: 44px;
    }
    .player-name {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 4px;
    }
    .player-meta {
        display: flex;
        gap: 8px;
        align-items: center;
    }
    .tier-badge {
        background: #f5f5f7;
        color: #1d1d1f;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .tier-badge.tier1 { background: #fef3c7; color: #92400e; }
    .tier-badge.tier2 { background: #ede9fe; color: #5b21b6; }
    .tier-badge.tier3 { background: #d1fae5; color: #065f46; }
    .archetype-label {
        color: #86868b;
        font-size: 0.75rem;
    }
    /* Rating */
    .rating-box {
        text-align: right;
    }
    .rating-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1d1d1f;
    }
    .rating-label {
        font-size: 0.65rem;
        color: #86868b;
        text-transform: uppercase;
    }
    /* Comparison Bar */
    .comparison-bar {
        margin: 16px 0;
        padding: 12px 0;
        border-top: 1px solid #f0f0f0;
        border-bottom: 1px solid #f0f0f0;
    }
    .bar-container {
        position: relative;
        height: 6px;
        background: #e5e5e7;
        border-radius: 3px;
        margin: 8px 0;
    }
    .bar-fill {
        position: absolute;
        height: 100%;
        border-radius: 3px;
        background: linear-gradient(90deg, #34c759, #ff9500);
    }
    .bar-labels {
        display: flex;
        justify-content: space-between;
        font-size: 0.7rem;
        color: #86868b;
    }
    .bar-value {
        font-weight: 600;
        color: #1d1d1f;
    }
    /* Stats Row */
    .stats-row {
        display: flex;
        justify-content: space-around;
        margin-top: 12px;
    }
    .stat-box {
        text-align: center;
    }
    .stat-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1d1d1f;
    }
    .stat-value.positive { color: #34c759; }
    .stat-value.negative { color: #ff3b30; }
    .stat-label {
        font-size: 0.65rem;
        color: #86868b;
        text-transform: uppercase;
    }
    /* Results Card */
    .results-card {
        background: #ffffff;
        border: 1px solid #e5e5e7;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .results-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .results-name {
        font-weight: 600;
        color: #1d1d1f;
    }
    .draft-pick {
        background: #f5f5f7;
        padding: 4px 10px;
        border-radius: 100px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .draft-pick.lottery { background: #fef3c7; color: #92400e; }
    .draft-pick.first-round { background: #d1fae5; color: #065f46; }
    .draft-pick.second-round { background: #f3f4f6; color: #6b7280; }
    .results-stats {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
        text-align: center;
    }
    .results-stat-value {
        font-size: 1rem;
        font-weight: 600;
        color: #1d1d1f;
    }
    .results-stat-label {
        font-size: 0.6rem;
        color: #86868b;
        text-transform: uppercase;
    }
    /* Highlight Button */
    .highlight-btn {
        display: inline-block;
        background: #1d1d1f;
        color: #ffffff !important;
        padding: 8px 16px;
        border-radius: 100px;
        text-decoration: none;
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 12px;
        transition: background 0.2s;
    }
    .highlight-btn:hover {
        background: #424245;
    }
    /* Section Headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1d1d1f;
        margin: 2rem 0 1rem 0;
    }
    /* Grid */
    .prospect-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Archetype Mapping
ARCH_MAP = {
    "Generational": "Generational",
    "Elite Producer": "Elite Producer",
    "Star Potential": "Star Potential",
    "Heliocentric Engine": "Primary Creator",
    "Monstar": "Two-Way Star",
    "Elite Shooter": "Elite Shooter",
    "Elite FR Shooter": "Elite Shooter",
    "Two-Way Wing": "Two-Way Wing",
    "Playmaker": "Playmaker",
    "High Upside": "High Upside",
    "Consistent Producer": "Consistent Producer",
    "Improver": "Improver",
    "Rim Runner": "Rim Runner",
    "Rim Protector": "Rim Protector",
    "Raw Big": "Raw Big",
    "Limited Big": "Limited Big",
    "Freshman Phenom": "Freshman Phenom",
    "": "Prospect"
}

ARCH_COLORS = {
    "Generational": "#bf8700",
    "Elite Producer": "#ff3b30",
    "Star Potential": "#5856d6",
    "Primary Creator": "#ff9500",
    "Two-Way Star": "#af52de",
    "Elite Shooter": "#007aff",
    "Two-Way Wing": "#ffcc00",
    "Playmaker": "#30d158",
    "High Upside": "#ff2d55",
    "Consistent Producer": "#34c759",
    "Improver": "#00c7be",
    "Rim Runner": "#ff9f0a",
    "Rim Protector": "#8e8e93",
    "Raw Big": "#636366",
    "Limited Big": "#48484a",
    "Freshman Phenom": "#ff375f",
    "Prospect": "#aeaeb2"
}

# ==============================================================================
# 2. NBA API FUNCTIONS
# ==============================================================================
@st.cache_data(ttl=86400)
def get_nba_players():
    """Fetch NBA players using nba_api package"""
    try:
        from nba_api.stats.static import players
        all_players = players.get_players()
        df = pd.DataFrame(all_players)
        df['norm_name'] = df['full_name'].str.lower().str.strip()
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=86400)
def get_draft_history(year):
    """Fetch draft picks for a given year"""
    try:
        from nba_api.stats.endpoints import drafthistory
        import time
        time.sleep(0.6)  # Rate limiting
        draft = drafthistory.DraftHistory(season_year_nullable=year)
        df = draft.get_data_frames()[0]
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_player_season_stats(player_id, season="2024-25"):
    """Fetch player stats for a season"""
    try:
        from nba_api.stats.endpoints import playercareerstats
        import time
        time.sleep(0.6)
        stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        df = stats.get_data_frames()[0]
        season_stats = df[df['SEASON_ID'] == season]
        if len(season_stats) > 0:
            return season_stats.iloc[0].to_dict()
        return None
    except:
        return None

def get_player_image_url(player_id):
    if pd.isna(player_id) or player_id == 0 or player_id is None:
        return "https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png"
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{int(player_id)}.png"

def get_highlight_url(player_name):
    query = f"{player_name} highlights 2024"
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

def match_to_nba_player(college_name, nba_df):
    if nba_df.empty:
        return None
    norm_name = college_name.lower().strip()
    match = nba_df[nba_df['norm_name'] == norm_name]
    if len(match) > 0:
        return match.iloc[0]['id']
    last_name = norm_name.split()[-1] if ' ' in norm_name else norm_name
    match = nba_df[nba_df['last_name'].str.lower() == last_name]
    if len(match) == 1:
        return match.iloc[0]['id']
    return None

# ==============================================================================
# 3. LOAD DATA
# ==============================================================================
@st.cache_data
possible_paths = [
    "all_draft_predictions.csv",  # Add this first
    "nba_draft_predictions.csv",
    "2025_draft_predictions.csv",
    ]
    df = None
    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            break

    if df is None:
        return None

    if 'usg_max' in df.columns and 'star_prob' in df.columns:
        mask = (df['usg_max'] > 0) | (df['star_prob'] >= 0.001)
        df = df[mask].copy()

    if 'archetype_note' in df.columns:
        df['scout_role'] = df['archetype_note'].map(ARCH_MAP).fillna('Prospect')
    else:
        df['scout_role'] = 'Prospect'

    def fmt_height(h):
        if pd.isna(h) or h == 0: return "—"
        ft, inch = int(h // 12), int(h % 12)
        return f"{ft}'{inch}\""

    df['height_fmt'] = df['height_in'].apply(fmt_height) if 'height_in' in df.columns else "—"

    defaults = {'bpm_max': 0, 'usg_max': 20, 'star_prob': 0.1, 'stock_rate': 0,
                'years_exp': 1, 'adj_proj_vorp': 0, 'three_pct': 0}
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val

    # Calculate age_adjusted_bpm if not present
    # Younger players with same BPM are more valuable
    # years_exp=1 (freshman) gets 1.25x multiplier, senior gets 0.8x
    if 'age_adjusted_bpm' not in df.columns:
        df['age_adjusted_bpm'] = df['bpm_max'] * (1.4 - (df['years_exp'] * 0.15))

    df['tier'] = pd.cut(df['star_prob'],
                        bins=[-1, 0.25, 0.45, 0.60, 1.01],
                        labels=['Role Player', 'Starter', 'All-Star', 'MVP'])

    # Calculate rating (0-100 scale based on star_prob)
    df['rating'] = (df['star_prob'] * 100).clip(0, 100)

    return df

df = load_data()

if df is None:
    st.error("Data file not found. Please add your predictions CSV.")
    st.stop()

nba_players = get_nba_players()

# ==============================================================================
# 4. SIDEBAR
# ==============================================================================
st.sidebar.markdown("### Filters")

if 'year' in df.columns:
    years = sorted(df['year'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Draft Class", years)
    df_year = df[df['year'] == selected_year].copy()
else:
    selected_year = 2025
    df_year = df.copy()

excluded_players = get_excluded_players(selected_year)
if excluded_players:
    df_year = df_year[~df_year['player_name'].isin(excluded_players)]
    st.sidebar.caption(f"{len(excluded_players)} players hidden")

archetypes = ['All'] + sorted([a for a in df_year['scout_role'].dropna().unique() if isinstance(a, str)])
selected_arch = st.sidebar.selectbox("Archetype", archetypes)

if selected_arch != 'All':
    df_year = df_year[df_year['scout_role'] == selected_arch]

search = st.sidebar.text_input("Search", placeholder="Player name...")
if search:
    df_year = df_year[df_year['player_name'].str.contains(search, case=False, na=False)]

# Updated view options
view = st.sidebar.radio("View", ["Board", "Chart", "Results", "Table"])

df_year = df_year.sort_values("star_prob", ascending=False).reset_index(drop=True)
df_year['rank'] = range(1, len(df_year) + 1)

# ==============================================================================
# 5. HEADER
# ==============================================================================
st.markdown(f"<p class='main-title'>{selected_year} NBA Draft Oracle</p>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Projecting future NBA stars from college performance data</p>", unsafe_allow_html=True)

# ==============================================================================
# 6. BOARD VIEW (New card design)
# ==============================================================================
if view == "Board" and len(df_year) > 0:
    # Top 3 featured
    st.markdown("<p class='section-header'>Top Prospects</p>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, col in enumerate(cols):
        if i < len(df_year):
            p = df_year.iloc[i]
            nba_id = match_to_nba_player(p['player_name'], nba_players)
            img_url = get_player_image_url(nba_id)
            hl_url = get_highlight_url(p['player_name'])

            tier_class = "tier1" if p['star_prob'] >= 0.45 else ("tier2" if p['star_prob'] >= 0.30 else "tier3")
            tier_label = "All-NBA Upside" if p['star_prob'] >= 0.45 else ("All-Star Upside" if p['star_prob'] >= 0.30 else "Starter")
            rank_class = "top3" if i < 3 else ("top10" if i < 10 else "")

            with col:
                st.markdown(f"""
                <div class="player-card">
                    <div class="rank-badge {rank_class}">{i+1}</div>
                    <div class="card-header">
                        <div>
                            <div class="player-name">{p['player_name']}</div>
                            <div class="player-meta">
                                <span class="tier-badge {tier_class}">{tier_label}</span>
                                <span class="archetype-label">{p['scout_role']}</span>
                            </div>
                        </div>
                        <div class="rating-box">
                            <div class="rating-value">{p['rating']:.1f}</div>
                            <div class="rating-label">Rating</div>
                        </div>
                    </div>
                    <img src="{img_url}" style="width:100%; max-width:180px; display:block; margin:12px auto; border-radius:8px;"
                         onerror="this.style.display='none'">
                    <div class="stats-row">
                        <div class="stat-box">
                            <div class="stat-value">{p['bpm_max']:.1f}</div>
                            <div class="stat-label">BPM</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{p['usg_max']:.0f}%</div>
                            <div class="stat-label">Usage</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{p['height_fmt']}</div>
                            <div class="stat-label">Height</div>
                        </div>
                    </div>
                    <center><a href="{hl_url}" target="_blank" class="highlight-btn">Watch Highlights</a></center>
                </div>
                """, unsafe_allow_html=True)

    # Rest of top 10
    st.markdown("<p class='section-header'>Prospects 4-10</p>", unsafe_allow_html=True)
    for i in range(3, min(10, len(df_year))):
        p = df_year.iloc[i]
        cols = st.columns([0.5, 2.5, 1.5, 1, 1, 1])
        cols[0].markdown(f"**{i+1}**")
        cols[1].markdown(f"**{p['player_name']}**")
        cols[2].markdown(f"{p['scout_role']}")
        cols[3].markdown(f"**{p['rating']:.0f}**")
        cols[4].markdown(f"{p['bpm_max']:.1f} BPM")
        cols[5].markdown(f"{p['usg_max']:.0f}% USG")

# ==============================================================================
# 7. CHART VIEW - Merged with toggle between Star Prob and Age-Adjusted BPM
# ==============================================================================
elif view == "Chart" and len(df_year) > 0:
    st.markdown("<p class='section-header'>Draft Landscape</p>", unsafe_allow_html=True)

    # Toggle between views
    chart_type = st.radio("Y-Axis", ["Star Probability", "Age-Adjusted BPM"], horizontal=True)

    # Limit to top 40 for cleaner chart
    df_plot = df_year.head(40).copy()

    # Size based on star_prob (model confidence)
    df_plot['size'] = (df_plot['star_prob'] * 30 + 8).clip(8, 25)

    fig = go.Figure()

    if chart_type == "Age-Adjusted BPM":
        y_col = 'age_adjusted_bpm'
        y_title = "Age-Adjusted BPM"
        y_range = [df_plot[y_col].min() - 1, df_plot[y_col].max() + 2]

        # Sweet spot: high usage + high age-adjusted BPM
        fig.add_shape(
            type="rect",
            x0=23, x1=35,
            y0=10, y1=18,
            fillcolor="rgba(52, 199, 89, 0.12)",
            line=dict(color="rgba(52, 199, 89, 0.4)", width=2, dash="dot"),
            layer="below"
        )
        fig.add_annotation(
            x=34, y=17,
            text="🎯 Sweet Spot",
            showarrow=False,
            font=dict(size=11, color="#34c759"),
            opacity=0.8
        )

        # Tier lines for age-adjusted BPM
        fig.add_hline(y=12, line_dash="dot", line_color="#bf8700", line_width=1,
                      annotation_text="Elite (12+)", annotation_position="right",
                      annotation_font_size=9, annotation_font_color="#bf8700")
        fig.add_hline(y=8, line_dash="dot", line_color="#5856d6", line_width=1,
                      annotation_text="Star Potential (8+)", annotation_position="right",
                      annotation_font_size=9, annotation_font_color="#5856d6")

        y_format = '.1f'
        hover_template = "<b>%{hovertext}</b><br>Usage: %{x:.1f}%<br>Age-Adj BPM: %{y:.1f}<br>Exp: %{customdata[0]:.0f} yr<extra></extra>"

    else:  # Star Probability
        y_col = 'star_prob'
        y_title = "Star Probability"
        y_range = [0.05, 0.80]

        # Sweet spot for star prob
        fig.add_shape(
            type="rect",
            x0=22, x1=35,
            y0=0.40, y1=0.75,
            fillcolor="rgba(52, 199, 89, 0.12)",
            line=dict(color="rgba(52, 199, 89, 0.4)", width=2, dash="dot"),
            layer="below"
        )
        fig.add_annotation(
            x=33, y=0.72,
            text="Sweet Spot",
            showarrow=False,
            font=dict(size=11, color="#34c759"),
            opacity=0.8
        )

        fig.add_hline(y=0.60, line_dash="dot", line_color="#bf8700", line_width=1,
                      annotation_text="MVP Tier", annotation_position="right",
                      annotation_font_size=9, annotation_font_color="#bf8700")
        fig.add_hline(y=0.45, line_dash="dot", line_color="#5856d6", line_width=1,
                      annotation_text="All-Star", annotation_position="right",
                      annotation_font_size=9, annotation_font_color="#5856d6")

        y_format = '.0%'
        hover_template = "<b>%{hovertext}</b><br>Usage: %{x:.1f}%<br>Star Prob: %{y:.1%}<extra></extra>"

    # Add scatter points by archetype
    for arch in df_plot['scout_role'].unique():
        df_arch = df_plot[df_plot['scout_role'] == arch]
        color = ARCH_COLORS.get(arch, '#86868b')

        fig.add_trace(go.Scatter(
            x=df_arch['usg_max'],
            y=df_arch[y_col],
            mode='markers+text',
            name=arch,
            marker=dict(
                size=df_arch['size'],
                color=color,
                opacity=0.8,
                line=dict(width=1.5, color='white')
            ),
            text=df_arch['player_name'].apply(lambda x: x.split()[-1]),
            textposition='top center',
            textfont=dict(size=9),
            hovertemplate=hover_template,
            hovertext=df_arch['player_name'],
            customdata=df_arch[['years_exp']].values if chart_type == "Age-Adjusted BPM" else None
        ))

    fig.update_layout(
        plot_bgcolor='#fafafa',
        paper_bgcolor='#ffffff',
        font=dict(family="SF Pro Display, -apple-system, sans-serif", color='#1d1d1f'),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5, font=dict(size=9)),
        margin=dict(t=30, b=80, l=60, r=40),
        xaxis=dict(
            title="Usage Rate %",
            gridcolor='#e5e5e7',
            range=[15, 38],
            dtick=5
        ),
        yaxis=dict(
            title=y_title,
            gridcolor='#e5e5e7',
            range=y_range,
            tickformat=y_format
        ),
        height=520,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # Quick stats - updated for both views
    c1, c2, c3, c4 = st.columns(4)
    if chart_type == "Age-Adjusted BPM":
        elite = df_year[df_year['age_adjusted_bpm'] >= 12]
        sweet_spot = df_year[(df_year['usg_max'] >= 23) & (df_year['age_adjusted_bpm'] >= 10)]
        c1.metric("Elite Age-Adj BPM (12+)", len(elite))
        c2.metric("In Sweet Spot", len(sweet_spot))
        c3.metric("Freshmen in Top 10", len(df_year.head(10)[df_year.head(10)['years_exp'] == 1]))
        c4.metric("Avg Age-Adj BPM", f"{df_year['age_adjusted_bpm'].mean():.1f}")
    else:
        sweet_spot = df_year[(df_year['usg_max'] >= 22) & (df_year['star_prob'] >= 0.40)]
        c1.metric("In Sweet Spot", len(sweet_spot))
        c2.metric("All-Star Tier+", len(df_year[df_year['star_prob'] >= 0.45]))
        c3.metric("Freshmen in Top 10", len(df_year.head(10)[df_year.head(10)['years_exp'] == 1]))
        c4.metric("Avg Star Prob", f"{df_year['star_prob'].mean():.1%}")

# ==============================================================================
# 8. RESULTS VIEW (Shows actual draft results)
# ==============================================================================
elif view == "Results":
    st.markdown("<p class='section-header'>Draft Results & Rookie Performance</p>", unsafe_allow_html=True)

    # Only show for years with actual results
    if selected_year > 2025:
        st.info("Results will be available after the draft. Select 2025 or earlier to see actual outcomes.")
    else:
        st.markdown(f"**{selected_year} Draft Class** — Comparing predictions to actual results")

        # Fetch draft history
        draft_df = get_draft_history(selected_year)

        if draft_df.empty:
            st.warning("Could not load draft data. NBA API may be unavailable.")
        else:
            # Match predictions to actual draft picks
            results = []
            for _, pred in df_year.head(20).iterrows():
                player_name = pred['player_name']

                # Find in draft
                draft_match = draft_df[draft_df['PLAYER_NAME'].str.lower().str.contains(
                    player_name.lower().split()[-1], na=False
                )]

                if len(draft_match) > 0:
                    pick = draft_match.iloc[0]

                    # Get current season stats
                    if selected_year == 2025:
                        season = "2025-26"
                    elif selected_year == 2024:
                        season = "2024-25"
                    else:
                        season = "2023-24"

                    stats = get_player_season_stats(pick['PERSON_ID'], season)

                    results.append({
                        'name': player_name,
                        'pred_rank': pred['rank'],
                        'actual_pick': pick['OVERALL_PICK'],
                        'team': pick['TEAM_ABBREVIATION'],
                        'player_id': pick['PERSON_ID'],
                        'ppg': stats['PTS'] / stats['GP'] if stats and stats.get('GP', 0) > 0 else None,
                        'rpg': stats['REB'] / stats['GP'] if stats and stats.get('GP', 0) > 0 else None,
                        'apg': stats['AST'] / stats['GP'] if stats and stats.get('GP', 0) > 0 else None,
                        'gp': stats['GP'] if stats else None,
                        'star_prob': pred['star_prob'],
                        'archetype': pred['scout_role']
                    })

            if results:
                for r in results[:15]:
                    pick_class = "lottery" if r['actual_pick'] <= 14 else ("first-round" if r['actual_pick'] <= 30 else "second-round")
                    img_url = get_player_image_url(r['player_id'])

                    if r['ppg'] is not None:
                        stats_html = f'''<div class="results-stats">
                            <div><div class="results-stat-value">{r["ppg"]:.1f}</div><div class="results-stat-label">PPG</div></div>
                            <div><div class="results-stat-value">{r["rpg"]:.1f}</div><div class="results-stat-label">RPG</div></div>
                            <div><div class="results-stat-value">{r["apg"]:.1f}</div><div class="results-stat-label">APG</div></div>
                            <div><div class="results-stat-value">{r["gp"]}</div><div class="results-stat-label">GP</div></div>
                        </div>'''
                    else:
                        stats_html = '<div style="color:#86868b; font-size:0.8rem; margin-top:8px;">No stats available yet</div>'

                    st.markdown(f"""
                    <div class="results-card" style="display:flex; gap:16px; align-items:flex-start;">
                        <img src="{img_url}" style="width:70px; height:52px; object-fit:cover; border-radius:6px; flex-shrink:0;"
                             onerror="this.style.display='none'">
                        <div style="flex:1; min-width:0;">
                            <div class="results-header">
                                <div>
                                    <span class="results-name">{r['name']}</span>
                                    <span style="color:#86868b; font-size:0.8rem; margin-left:8px;">{r['archetype']}</span>
                                </div>
                                <span class="draft-pick {pick_class}">Pick #{r['actual_pick']}</span>
                            </div>
                            <div style="display:flex; gap:24px; align-items:center; margin:8px 0;">
                                <div>
                                    <span style="color:#86868b; font-size:0.75rem;">Model Rank</span>
                                    <span style="font-weight:600; margin-left:4px;">#{r['pred_rank']}</span>
                                </div>
                                <div>
                                    <span style="color:#86868b; font-size:0.75rem;">Star Prob</span>
                                    <span style="font-weight:600; margin-left:4px;">{r['star_prob']:.0%}</span>
                                </div>
                                <div>
                                    <span style="color:#86868b; font-size:0.75rem;">Team</span>
                                    <span style="font-weight:600; margin-left:4px;">{r['team']}</span>
                                </div>
                            </div>
                            {stats_html}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No matching players found in draft data.")

# ==============================================================================
# 9. TABLE VIEW
# ==============================================================================
elif view == "Table" and len(df_year) > 0:
    st.markdown("<p class='section-header'>Full Draft Board</p>", unsafe_allow_html=True)

    display_cols = ['rank', 'player_name', 'scout_role', 'tier', 'star_prob', 'rating',
                    'bpm_max', 'usg_max', 'height_fmt', 'years_exp', 'age_adjusted_bpm']
    display_cols = [c for c in display_cols if c in df_year.columns]

    styled = df_year[display_cols].rename(columns={
        'rank': '#', 'player_name': 'Player', 'scout_role': 'Archetype',
        'tier': 'Tier', 'star_prob': 'Star Prob', 'rating': 'Rating',
        'bpm_max': 'BPM', 'usg_max': 'Usage', 'height_fmt': 'Height',
        'years_exp': 'Exp', 'age_adjusted_bpm': 'Age-Adj BPM'
    })

    st.dataframe(
        styled.style.format({
            'Star Prob': '{:.1%}',
            'Rating': '{:.0f}',
            'BPM': '{:.1f}',
            'Usage': '{:.0f}',
            'Exp': '{:.0f}',
            'Age-Adj BPM': '{:.1f}'
        }).background_gradient(subset=['Rating'], cmap='Greens'),
        use_container_width=True, hide_index=True, height=600
    )

# ==============================================================================
# FOOTER (at the very end, after all view conditionals)
# ==============================================================================
st.markdown("---")
st.caption("NBA Draft Oracle · Model trained on 2010–2024 college data · Player images from NBA.com")
