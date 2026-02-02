import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import json

# ==============================================================================
# 1. SETUP & CONFIG
# ==============================================================================
st.set_page_config(page_title="NBA Draft Oracle", layout="wide", page_icon="🏀")

# ==============================================================================
# EXCLUDED PLAYERS CONFIG
# ==============================================================================
# Players who haven't declared / still in school - edit this list directly
EXCLUDED_PLAYERS = {
    2025: [
        # Add players still in school for 2025 here
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
    ],
    2026: [
        # Add players still in school for 2026 here
    ],
}

def get_excluded_players(year):
    """Get list of excluded players for a given year"""
    return EXCLUDED_PLAYERS.get(year, [])

# Clean, Apple-inspired CSS
st.markdown("""
<style>
    /* Global - fix top cutoff */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 2rem;
    }

    /* Hide default header spacing */
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

    /* Player Card */
    .player-card {
        background: #ffffff;
        border: 1px solid #e5e5e7;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
    }
    .player-card:hover {
        border-color: #0071e3;
    }
    .player-rank {
        font-size: 0.75rem;
        color: #86868b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .player-name {
        font-size: 1.4rem;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 8px;
    }
    .player-archetype {
        display: inline-block;
        background: #f5f5f7;
        color: #1d1d1f;
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-bottom: 16px;
    }
    .stat-main {
        font-size: 3rem;
        font-weight: 600;
        color: #1d1d1f;
        line-height: 1;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #86868b;
        margin-top: 4px;
    }
    .stat-delta {
        font-size: 0.8rem;
        color: #34c759;
        font-weight: 500;
    }
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-top: 20px;
        padding-top: 20px;
        border-top: 1px solid #e5e5e7;
    }
    .stat-item {
        text-align: center;
    }
    .stat-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1d1d1f;
    }
    .stat-name {
        font-size: 0.7rem;
        color: #86868b;
        text-transform: uppercase;
        letter-spacing: 0.3px;
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
        margin-top: 16px;
        transition: background 0.2s;
    }
    .highlight-btn:hover {
        background: #424245;
    }

    /* Grid Card */
    .grid-card {
        background: #ffffff;
        border: 1px solid #e5e5e7;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        height: 100%;
    }
    .grid-card img {
        width: 80px;
        height: 60px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .grid-name {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 4px;
    }
    .grid-archetype {
        font-size: 0.7rem;
        color: #86868b;
        margin-bottom: 8px;
    }
    .grid-prob {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1d1d1f;
    }
    .grid-prob-label {
        font-size: 0.7rem;
        color: #86868b;
    }

    /* Tier Badge */
    .tier-mvp { color: #bf8700; }
    .tier-allstar { color: #5856d6; }
    .tier-starter { color: #34c759; }
    .tier-role { color: #86868b; }

    /* Section Headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1d1d1f;
        margin: 2rem 0 1rem 0;
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

# Clean color palette
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
# 2. NBA PLAYER DATA (using nba_api)
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
    except ImportError:
        st.sidebar.warning("Install nba_api: pip install nba_api")
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def get_player_image_url(player_id):
    """Get NBA player headshot URL"""
    if pd.isna(player_id) or player_id == 0 or player_id is None:
        return "https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png"
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{int(player_id)}.png"

def get_highlight_url(player_name):
    """Generate YouTube highlight search URL"""
    query = f"{player_name} highlights 2024"
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

def match_to_nba_player(college_name, nba_df):
    """Match college player to NBA player ID"""
    if nba_df.empty:
        return None

    norm_name = college_name.lower().strip()
    match = nba_df[nba_df['norm_name'] == norm_name]

    if len(match) > 0:
        return match.iloc[0]['id']

    # Try last name match
    last_name = norm_name.split()[-1] if ' ' in norm_name else norm_name
    match = nba_df[nba_df['last_name'].str.lower() == last_name]
    if len(match) == 1:
        return match.iloc[0]['id']

    return None

# ==============================================================================
# 3. LOAD DATA
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

    # Filter invalid rows
    if 'usg_max' in df.columns and 'star_prob' in df.columns:
        mask = (df['usg_max'] > 0) | (df['star_prob'] >= 0.001)
        df = df[mask].copy()

    # Map archetypes
    if 'archetype_note' in df.columns:
        df['scout_role'] = df['archetype_note'].map(ARCH_MAP).fillna('Prospect')
    else:
        df['scout_role'] = 'Prospect'

    # Format height
    def fmt_height(h):
        if pd.isna(h) or h == 0: return "—"
        ft, inch = int(h // 12), int(h % 12)
        return f"{ft}'{inch}\""

    df['height_fmt'] = df['height_in'].apply(fmt_height) if 'height_in' in df.columns else "—"

    # Fill defaults
    defaults = {'bpm_max': 0, 'usg_max': 20, 'star_prob': 0.1, 'stock_rate': 0,
                'years_exp': 1, 'adj_proj_vorp': 0, 'three_pct': 0}
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val

    # Tier classification
    df['tier'] = pd.cut(df['star_prob'],
                        bins=[-1, 0.25, 0.45, 0.60, 1.01],
                        labels=['Role Player', 'Starter', 'All-Star', 'MVP'])

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

# Year
if 'year' in df.columns:
    years = sorted(df['year'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Draft Class", years)
    df_year = df[df['year'] == selected_year].copy()
else:
    selected_year = 2025
    df_year = df.copy()

# Apply persistent exclusions from config
excluded_players = get_excluded_players(selected_year)
if excluded_players:
    df_year = df_year[~df_year['player_name'].isin(excluded_players)]
    st.sidebar.caption(f"{len(excluded_players)} players hidden")

# Archetype
archetypes = ['All'] + sorted([a for a in df_year['scout_role'].dropna().unique() if isinstance(a, str)])
selected_arch = st.sidebar.selectbox("Archetype", archetypes)
if selected_arch != 'All':
    df_year = df_year[df_year['scout_role'] == selected_arch]

# Search
search = st.sidebar.text_input("Search", placeholder="Player name...")
if search:
    df_year = df_year[df_year['player_name'].str.contains(search, case=False, na=False)]

# View
view = st.sidebar.radio("View", ["Overview", "Chart", "Grid", "Table"])

# Sort and rank
df_year = df_year.sort_values("star_prob", ascending=False).reset_index(drop=True)
df_year['rank'] = range(1, len(df_year) + 1)

# ==============================================================================
# 5. HEADER
# ==============================================================================
st.markdown(f"<p class='main-title'>{selected_year} NBA Draft Oracle</p>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Projecting future NBA stars from college performance data</p>", unsafe_allow_html=True)

# ==============================================================================
# 6. OVERVIEW
# ==============================================================================
if view == "Overview" and len(df_year) > 0:
    top = df_year.iloc[0]
    nba_id = match_to_nba_player(top['player_name'], nba_players)
    img_url = get_player_image_url(nba_id)
    highlight_url = get_highlight_url(top['player_name'])

    avg_prob = df['star_prob'].mean()
    delta = ((top['star_prob'] - avg_prob) / avg_prob) * 100

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
        <div class="player-card">
            <div class="player-rank">Top Prospect</div>
            <img src="{img_url}" style="width:100%; max-width:200px; border-radius:8px; margin-bottom:16px;"
                 onerror="this.style.display='none'">
            <div class="player-name">{top['player_name']}</div>
            <span class="player-archetype">{top['scout_role']}</span>
            <div class="stat-main">{top['star_prob']*100:.1f}%</div>
            <div class="stat-label">Star Probability</div>
            <div class="stat-delta">+{delta:.0f}% vs class average</div>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{top['bpm_max']:.1f}</div>
                    <div class="stat-name">BPM</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{top['usg_max']:.0f}%</div>
                    <div class="stat-name">Usage</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{top['height_fmt']}</div>
                    <div class="stat-name">Height</div>
                </div>
            </div>
            <a href="{highlight_url}" target="_blank" class="highlight-btn">Watch Highlights</a>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<p class='section-header'>Top 10</p>", unsafe_allow_html=True)

        for i, (_, p) in enumerate(df_year.head(10).iterrows()):
            tier_class = {
                'MVP': 'tier-mvp', 'All-Star': 'tier-allstar',
                'Starter': 'tier-starter', 'Role Player': 'tier-role'
            }.get(p['tier'], 'tier-role')

            cols = st.columns([0.5, 3, 2, 1.5, 1.5])
            cols[0].markdown(f"**{i+1}**")
            cols[1].markdown(f"**{p['player_name']}**")
            cols[2].markdown(f"<span class='player-archetype' style='font-size:0.7rem;'>{p['scout_role']}</span>", unsafe_allow_html=True)
            cols[3].markdown(f"**{p['star_prob']*100:.0f}%**")
            cols[4].markdown(f"{p['bpm_max']:.1f} BPM")

# ==============================================================================
# 7. CHART VIEW
# ==============================================================================
elif view == "Chart" and len(df_year) > 0:
    st.markdown("<p class='section-header'>Usage vs Star Probability</p>", unsafe_allow_html=True)

    df_plot = df_year.copy()
    min_bpm = df_plot['bpm_max'].min()
    df_plot['size'] = (df_plot['bpm_max'] - min_bpm + 3).clip(lower=3)

    fig = px.scatter(
        df_plot, x="usg_max", y="star_prob",
        color="scout_role", color_discrete_map=ARCH_COLORS,
        size="size", hover_name="player_name",
        labels={"usg_max": "Usage Rate", "star_prob": "Star Probability"},
        height=550
    )

    # Tier lines
    fig.add_hline(y=0.60, line_dash="dot", line_color="#bf8700", line_width=1,
                  annotation_text="MVP", annotation_position="right",
                  annotation_font_size=10, annotation_font_color="#bf8700")
    fig.add_hline(y=0.45, line_dash="dot", line_color="#5856d6", line_width=1,
                  annotation_text="All-Star", annotation_position="right",
                  annotation_font_size=10, annotation_font_color="#5856d6")

    # Top labels
    for _, p in df_plot.nlargest(3, 'star_prob').iterrows():
        fig.add_annotation(
            x=p['usg_max'], y=p['star_prob'] + 0.03,
            text=p['player_name'].split()[-1],
            showarrow=False, font=dict(size=10, color="#1d1d1f")
        )

    fig.update_layout(
        plot_bgcolor='#fafafa', paper_bgcolor='#ffffff',
        font=dict(family="SF Pro Display, -apple-system, sans-serif", color='#1d1d1f'),
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
                    font=dict(size=10)),
        margin=dict(t=20, b=80),
        xaxis=dict(gridcolor='#e5e5e7', range=[10, 40]),
        yaxis=dict(gridcolor='#e5e5e7', range=[0, 0.85], tickformat='.0%')
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>Usage: %{x:.1f}%<br>Star Prob: %{y:.1%}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tier summary
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MVP Tier", len(df_year[df_year['tier'] == 'MVP']))
    c2.metric("All-Star", len(df_year[df_year['tier'] == 'All-Star']))
    c3.metric("Starter", len(df_year[df_year['tier'] == 'Starter']))
    c4.metric("Role Player", len(df_year[df_year['tier'] == 'Role Player']))

# ==============================================================================
# 8. GRID VIEW
# ==============================================================================
elif view == "Grid" and len(df_year) > 0:
    st.markdown("<p class='section-header'>Prospect Gallery</p>", unsafe_allow_html=True)

    cols_per_row = 4
    for row_start in range(0, min(20, len(df_year)), cols_per_row):
        cols = st.columns(cols_per_row)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx < len(df_year):
                p = df_year.iloc[idx]
                nba_id = match_to_nba_player(p['player_name'], nba_players)
                img_url = get_player_image_url(nba_id)
                hl_url = get_highlight_url(p['player_name'])

                with col:
                    st.markdown(f"""
                    <div class="grid-card">
                        <img src="{img_url}" onerror="this.style.display='none'">
                        <div class="grid-name">#{idx+1} {p['player_name']}</div>
                        <div class="grid-archetype">{p['scout_role']}</div>
                        <div class="grid-prob">{p['star_prob']*100:.0f}%</div>
                        <div class="grid-prob-label">Star Probability</div>
                        <a href="{hl_url}" target="_blank" class="highlight-btn" style="font-size:0.7rem; padding:6px 12px;">Highlights</a>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("")

# ==============================================================================
# 9. TABLE VIEW
# ==============================================================================
elif view == "Table" and len(df_year) > 0:
    st.markdown("<p class='section-header'>Full Draft Board</p>", unsafe_allow_html=True)

    display_cols = ['rank', 'player_name', 'scout_role', 'tier', 'star_prob',
                    'bpm_max', 'usg_max', 'height_fmt', 'years_exp']
    display_cols = [c for c in display_cols if c in df_year.columns]

    styled = df_year[display_cols].rename(columns={
        'rank': '#', 'player_name': 'Player', 'scout_role': 'Archetype',
        'tier': 'Tier', 'star_prob': 'Star Prob', 'bpm_max': 'BPM',
        'usg_max': 'Usage', 'height_fmt': 'Height', 'years_exp': 'Exp'
    })

    st.dataframe(
        styled.style.format({'Star Prob': '{:.1%}', 'BPM': '{:.1f}', 'Usage': '{:.0f}', 'Exp': '{:.0f}'}
        ).background_gradient(subset=['Star Prob'], cmap='Greens'),
        use_container_width=True, hide_index=True, height=600
    )

# ==============================================================================
# 10. COMPARISON
# ==============================================================================
if len(df_year) >= 2:
    st.markdown("---")
    st.markdown("<p class='section-header'>Compare Players</p>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    p1_name = c1.selectbox("Player 1", df_year['player_name'].tolist(), index=0, key="p1")
    p2_opts = [n for n in df_year['player_name'].tolist() if n != p1_name]
    p2_name = c2.selectbox("Player 2", p2_opts, index=0 if p2_opts else None, key="p2")

    if p1_name and p2_name:
        p1 = df_year[df_year['player_name'] == p1_name].iloc[0]
        p2 = df_year[df_year['player_name'] == p2_name].iloc[0]

        metrics = ['star_prob', 'bpm_max', 'usg_max', 'stock_rate']
        labels = ['Star Prob', 'BPM', 'Usage', 'Stocks']

        # Normalize for radar
        vals1, vals2 = [], []
        for m in metrics:
            mx, mn = df_year[m].max(), df_year[m].min()
            rng = mx - mn if mx != mn else 1
            vals1.append((p1[m] - mn) / rng)
            vals2.append((p2[m] - mn) / rng)

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=vals1 + [vals1[0]], theta=labels + [labels[0]],
                                       fill='toself', name=p1_name, line_color='#ff3b30'))
        fig.add_trace(go.Scatterpolar(r=vals2 + [vals2[0]], theta=labels + [labels[0]],
                                       fill='toself', name=p2_name, line_color='#007aff'))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1], showticklabels=False)),
            showlegend=True, height=350, margin=dict(t=30, b=30),
            font=dict(family="SF Pro Display, -apple-system, sans-serif")
        )

        st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("---")
st.caption("NBA Draft Oracle · Model trained on 2010–2024 college data · Player images from NBA.com")
