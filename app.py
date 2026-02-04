# ==============================================================================
# 7. CHART VIEW - Updated to use Age-Adjusted BPM
# ==============================================================================
elif view == "Chart" and len(df_year) > 0:
    st.markdown("<p class='section-header'>Draft Landscape</p>", unsafe_allow_html=True)
    
    # Toggle between views
    chart_type = st.radio("Y-Axis", ["Age-Adjusted BPM", "Star Probability"], horizontal=True)
    
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
            font=dict(size=11, color="#34c759", weight="bold"),
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
        hover_template = "<b>%{hovertext}</b><br>Usage: %{x:.1f}%<br>Age-Adj BPM: %{y:.1f}<br>Age: %{customdata[0]:.0f} yrs<extra></extra>"
        
    else:
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
            font=dict(size=11, color="#34c759", weight="bold"),
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
    
    # Quick stats - updated for age-adjusted view
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
