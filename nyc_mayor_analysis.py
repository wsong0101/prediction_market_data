#!/usr/bin/env python3
"""
NYC Mayor 2025 Election Analysis
Creates 4 separate interactive HTML charts:
1. Candidate Volume Comparison (Bar Chart)
2. Market Share Distribution (Pie Chart)
3. Price/Probability Timeline (Line Chart) - for main candidates
4. Daily Volume Analysis (Area Chart)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
except ImportError:
    import subprocess
    subprocess.check_call(["pip3", "install", "plotly", "pandas", "-q"])
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots

import pandas as pd


# =============================================================================
# Configuration
# =============================================================================

DATA_FILE = Path("/Users/wsong/workspace/prediciton-mm/.cache/nyc_mayor_markets.json")
OUTPUT_DIR = Path("/Users/wsong/workspace/prediciton-mm")


# =============================================================================
# Data Loading
# =============================================================================

def load_market_data() -> Dict:
    """Load market data from cache"""
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    return data[0] if data else {}


def parse_markets(event_data: Dict) -> pd.DataFrame:
    """Parse market data into DataFrame"""
    markets = event_data.get('markets', [])
    
    records = []
    for m in markets:
        name = m.get('groupItemTitle', m.get('question', 'Unknown')[:30])
        
        # Skip placeholder markets
        if name.startswith('Person ') or name == 'Other':
            continue
        
        volume = float(m.get('volume', 0) or 0)
        volume_1wk = float(m.get('volume1wk', 0) or 0)
        volume_1mo = float(m.get('volume1mo', 0) or 0)
        
        prices_raw = m.get('outcomePrices', '[0, 0]')
        prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
        yes_price = float(prices[0]) if prices else 0
        
        clob_ids_raw = m.get('clobTokenIds', '[]')
        clob_ids = json.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
        
        start_date = m.get('startDate', '')
        end_date = m.get('endDate', '')
        closed = m.get('closed', False)
        
        records.append({
            'candidate': name,
            'market_id': m.get('id', ''),
            'volume': volume,
            'volume_millions': volume / 1e6,
            'volume_1wk': volume_1wk,
            'volume_1mo': volume_1mo,
            'price': yes_price,
            'probability_pct': yes_price * 100,
            'token_id': clob_ids[0] if clob_ids else '',
            'start_date': start_date,
            'end_date': end_date,
            'closed': closed,
            'winner': yes_price >= 0.99
        })
    
    df = pd.DataFrame(records)
    df = df.sort_values('volume', ascending=False)
    return df


# =============================================================================
# Chart 1: Volume Comparison Bar Chart
# =============================================================================

def create_volume_chart(df: pd.DataFrame, output_path: str):
    """Create interactive bar chart comparing candidate volumes"""
    
    # Color based on winner
    colors = ['#2ECC71' if w else '#3498DB' for w in df['winner']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['candidate'],
        y=df['volume_millions'],
        marker_color=colors,
        text=[f"${v:.2f}M" for v in df['volume_millions']],
        textposition='outside',
        hovertemplate=(
            "<b>%{x}</b><br>" +
            "Total Volume: $%{y:.2f}M<br>" +
            "Probability: %{customdata[0]:.1f}%<br>" +
            "<extra></extra>"
        ),
        customdata=df[['probability_pct']].values
    ))
    
    fig.update_layout(
        title={
            'text': "NYC Mayor 2025 Election<br><sup>Total Trading Volume by Candidate</sup>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Candidate",
        yaxis_title="Trading Volume (Millions USD)",
        template='plotly_white',
        height=600,
        showlegend=False,
        hovermode='x unified'
    )
    
    # Add annotation for winner
    winner = df[df['winner'] == True]['candidate'].values
    if len(winner) > 0:
        fig.add_annotation(
            text=f"🏆 Winner: {winner[0]}",
            xref="paper", yref="paper",
            x=0.98, y=0.98,
            showarrow=False,
            font=dict(size=14, color='green'),
            bgcolor='lightgreen',
            borderpad=4
        )
    
    # Total volume annotation
    total_vol = df['volume_millions'].sum()
    fig.add_annotation(
        text=f"Total Market Volume: ${total_vol:.2f}M",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(size=12)
    )
    
    fig.write_html(output_path, include_plotlyjs='cdn')
    print(f"📊 Chart 1 saved: {output_path}")


# =============================================================================
# Chart 2: Market Share Pie Chart
# =============================================================================

def create_market_share_chart(df: pd.DataFrame, output_path: str):
    """Create interactive pie chart showing market share by volume"""
    
    # Only include candidates with significant volume
    df_filtered = df[df['volume_millions'] > 1].copy()
    
    # Add "Other" category for small volume candidates
    other_vol = df[df['volume_millions'] <= 1]['volume_millions'].sum()
    if other_vol > 0:
        other_row = pd.DataFrame([{
            'candidate': 'Other Candidates',
            'volume_millions': other_vol,
            'probability_pct': 0,
            'winner': False
        }])
        df_filtered = pd.concat([df_filtered, other_row], ignore_index=True)
    
    # Custom colors
    colors = px.colors.qualitative.Set2[:len(df_filtered)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        labels=df_filtered['candidate'],
        values=df_filtered['volume_millions'],
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent',
        textposition='outside',
        hovertemplate=(
            "<b>%{label}</b><br>" +
            "Volume: $%{value:.2f}M<br>" +
            "Share: %{percent}<br>" +
            "<extra></extra>"
        )
    ))
    
    fig.update_layout(
        title={
            'text': "NYC Mayor 2025 Election<br><sup>Market Share by Trading Volume</sup>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        template='plotly_white',
        height=700,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        annotations=[dict(
            text=f'${df["volume_millions"].sum():.1f}M<br>Total',
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False
        )]
    )
    
    fig.write_html(output_path, include_plotlyjs='cdn')
    print(f"📊 Chart 2 saved: {output_path}")


# =============================================================================
# Chart 3: Candidate Comparison Multi-metric
# =============================================================================

def create_candidate_comparison_chart(df: pd.DataFrame, output_path: str):
    """Create grouped bar chart comparing multiple metrics"""
    
    # Top candidates only
    df_top = df.head(8).copy()
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Total Trading Volume", "Weekly vs Monthly Volume"),
        vertical_spacing=0.15
    )
    
    # Chart 1: Total Volume
    fig.add_trace(
        go.Bar(
            x=df_top['candidate'],
            y=df_top['volume_millions'],
            name='Total Volume',
            marker_color=['#2ECC71' if w else '#3498DB' for w in df_top['winner']],
            text=[f"${v:.1f}M" for v in df_top['volume_millions']],
            textposition='outside',
        ),
        row=1, col=1
    )
    
    # Chart 2: Weekly vs Monthly
    fig.add_trace(
        go.Bar(
            x=df_top['candidate'],
            y=df_top['volume_1wk'] / 1e6,
            name='1 Week Volume',
            marker_color='#E74C3C',
            text=[f"${v/1e6:.1f}M" for v in df_top['volume_1wk']],
            textposition='outside',
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=df_top['candidate'],
            y=df_top['volume_1mo'] / 1e6,
            name='1 Month Volume',
            marker_color='#9B59B6',
            opacity=0.7,
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title={
            'text': "NYC Mayor 2025 Election<br><sup>Candidate Volume Analysis</sup>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        template='plotly_white',
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        barmode='group'
    )
    
    fig.update_yaxes(title_text="Volume (Millions USD)", row=1, col=1)
    fig.update_yaxes(title_text="Volume (Millions USD)", row=2, col=1)
    
    fig.write_html(output_path, include_plotlyjs='cdn')
    print(f"📊 Chart 3 saved: {output_path}")


# =============================================================================
# Chart 4: Final Probabilities & Results
# =============================================================================

def create_results_chart(df: pd.DataFrame, output_path: str):
    """Create detailed results chart with probabilities"""
    
    df_sorted = df.sort_values('volume', ascending=True)
    
    fig = go.Figure()
    
    # Horizontal bar for final probability
    colors = ['#2ECC71' if w else '#E74C3C' for w in df_sorted['winner']]
    
    fig.add_trace(go.Bar(
        y=df_sorted['candidate'],
        x=df_sorted['probability_pct'],
        orientation='h',
        marker_color=colors,
        text=[f"{p:.0f}%" for p in df_sorted['probability_pct']],
        textposition='inside',
        textfont=dict(color='white', size=12),
        hovertemplate=(
            "<b>%{y}</b><br>" +
            "Final Probability: %{x:.1f}%<br>" +
            "Volume: $%{customdata[0]:.2f}M<br>" +
            "<extra></extra>"
        ),
        customdata=df_sorted[['volume_millions']].values
    ))
    
    fig.update_layout(
        title={
            'text': "NYC Mayor 2025 Election<br><sup>Final Probabilities & Results</sup>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Final Probability (%)",
        template='plotly_white',
        height=700,
        showlegend=False,
        xaxis=dict(range=[0, 105])
    )
    
    # Add vertical line at 50%
    fig.add_vline(x=50, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Winner annotation
    winner = df[df['winner'] == True]
    if not winner.empty:
        winner_name = winner['candidate'].values[0]
        winner_vol = winner['volume_millions'].values[0]
        
        fig.add_annotation(
            text=f"🏆 WINNER: {winner_name}<br>Volume: ${winner_vol:.2f}M",
            xref="paper", yref="paper",
            x=0.98, y=0.02,
            showarrow=False,
            font=dict(size=14, color='white'),
            bgcolor='green',
            borderpad=8,
            align='right'
        )
    
    # Summary stats
    total_vol = df['volume_millions'].sum()
    num_candidates = len(df)
    
    fig.add_annotation(
        text=(
            f"<b>Market Summary</b><br>"
            f"Total Volume: ${total_vol:.2f}M<br>"
            f"Candidates: {num_candidates}<br>"
            f"Election Date: Nov 4, 2025"
        ),
        xref="paper", yref="paper",
        x=0.98, y=0.98,
        showarrow=False,
        font=dict(size=11),
        bgcolor='lightyellow',
        borderpad=8,
        align='left'
    )
    
    fig.write_html(output_path, include_plotlyjs='cdn')
    print(f"📊 Chart 4 saved: {output_path}")


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "=" * 60)
    print("   NYC MAYOR 2025 ELECTION ANALYSIS")
    print("   Creating 4 Interactive Charts")
    print("=" * 60)
    print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load data
    print("\n📊 Loading market data...")
    event_data = load_market_data()
    df = parse_markets(event_data)
    
    print(f"\n   Event: {event_data.get('title', 'NYC Mayor Election')}")
    print(f"   Candidates: {len(df)}")
    print(f"   Total Volume: ${df['volume_millions'].sum():.2f}M")
    print(f"   Winner: {df[df['winner'] == True]['candidate'].values}")
    
    # Create charts
    print("\n📈 Generating interactive charts...")
    
    # Chart 1: Volume Comparison
    create_volume_chart(df, str(OUTPUT_DIR / "nyc_mayor_1_volume.html"))
    
    # Chart 2: Market Share
    create_market_share_chart(df, str(OUTPUT_DIR / "nyc_mayor_2_market_share.html"))
    
    # Chart 3: Candidate Comparison
    create_candidate_comparison_chart(df, str(OUTPUT_DIR / "nyc_mayor_3_comparison.html"))
    
    # Chart 4: Final Results
    create_results_chart(df, str(OUTPUT_DIR / "nyc_mayor_4_results.html"))
    
    # Summary
    print("\n" + "=" * 60)
    print("   SUMMARY")
    print("=" * 60)
    print("\n   📊 4 Interactive HTML Charts Created:")
    print("   1. nyc_mayor_1_volume.html      - Volume comparison bar chart")
    print("   2. nyc_mayor_2_market_share.html - Market share pie chart")
    print("   3. nyc_mayor_3_comparison.html  - Multi-metric comparison")
    print("   4. nyc_mayor_4_results.html     - Final probabilities & results")
    print("\n   💡 Open any HTML file in browser to view interactive charts")
    print("      - Zoom: scroll or drag")
    print("      - Pan: drag while holding shift")
    print("      - Hover for details")
    print("=" * 60)
    
    # Data summary table
    print("\n📋 Data Summary:\n")
    print(f"{'Candidate':<20} {'Volume':>12} {'Probability':>12} {'Winner':>8}")
    print("-" * 55)
    for _, row in df.iterrows():
        winner_icon = "🏆" if row['winner'] else ""
        print(f"{row['candidate']:<20} ${row['volume_millions']:>9.2f}M {row['probability_pct']:>10.1f}% {winner_icon:>8}")


if __name__ == "__main__":
    main()
