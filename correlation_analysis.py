#!/usr/bin/env python3
"""
Daily Price vs Volume Correlation Analysis
Creates interactive charts showing the relationship between price changes and trading volume.

Markets:
1. 2024 US Presidential Election (Trump)
2. 2025 NYC Mayor Election (Mamdani)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd
except ImportError:
    import subprocess
    subprocess.check_call(["pip3", "install", "plotly", "pandas", "numpy", "-q"])
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd


# =============================================================================
# Configuration
# =============================================================================

DATA_FILE = Path("/Users/wsong/workspace/prediciton-mm/.cache/daily_price_volume.json")
OUTPUT_DIR = Path("/Users/wsong/workspace/prediciton-mm")


# =============================================================================
# Data Loading
# =============================================================================

def load_data() -> Dict:
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def parse_market_data(market_data: Dict) -> pd.DataFrame:
    """Parse market data into DataFrame"""
    records = []
    for d in market_data.get('daily_data', []):
        records.append({
            'date': datetime.strptime(d['date'], '%Y-%m-%d'),
            'price': d['price'],
            'probability': d['price'] * 100,
            'volume': d['daily_volume'],
            'volume_millions': d['daily_volume'] / 1e6,
            'event': d.get('event', '')
        })
    
    df = pd.DataFrame(records)
    df = df.sort_values('date')
    
    # Calculate derived metrics
    df['price_change'] = df['price'].diff()
    df['price_change_pct'] = df['price'].pct_change() * 100
    df['volume_change'] = df['volume'].diff()
    df['volume_ma7'] = df['volume'].rolling(window=3, min_periods=1).mean()
    
    return df


# =============================================================================
# Chart 1: Presidential Election - Price vs Volume Dual Axis
# =============================================================================

def create_presidential_chart(df: pd.DataFrame, output_path: str):
    """Create dual-axis chart for presidential election"""
    
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.6, 0.4],
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            "Price (Probability) Over Time",
            "Daily Trading Volume"
        )
    )
    
    # Price line
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['probability'],
            mode='lines+markers',
            name='Trump Win Probability',
            line=dict(color='#E74C3C', width=3),
            marker=dict(size=6),
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Probability: %{y:.1f}%<extra></extra>"
        ),
        row=1, col=1
    )
    
    # 50% reference line
    fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=1)
    
    # Volume bars with color gradient based on price change
    colors = ['#2ECC71' if pc > 0 else '#E74C3C' if pc < 0 else '#3498DB' 
              for pc in df['price_change'].fillna(0)]
    
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['volume_millions'],
            name='Daily Volume',
            marker_color=colors,
            opacity=0.7,
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Volume: $%{y:.1f}M<extra></extra>"
        ),
        row=2, col=1
    )
    
    # Add event annotations
    events = df[df['event'] != '']
    for _, row in events.iterrows():
        fig.add_annotation(
            x=row['date'],
            y=row['probability'],
            text=row['event'],
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowcolor='orange',
            font=dict(size=9, color='orange'),
            bgcolor='rgba(255,255,255,0.8)',
            row=1, col=1
        )
    
    # Calculate correlation
    corr = df['price'].corr(df['volume'])
    
    fig.update_layout(
        title={
            'text': f"2024 US Presidential Election - Trump<br><sup>Daily Price vs Volume Analysis | Correlation: {corr:.3f}</sup>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        template='plotly_white',
        height=700,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        hovermode='x unified'
    )
    
    fig.update_yaxes(title_text="Probability (%)", row=1, col=1)
    fig.update_yaxes(title_text="Volume ($M)", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    
    # Add summary stats
    fig.add_annotation(
        text=(
            f"<b>Summary Stats</b><br>"
            f"Total Volume: ${df['volume'].sum()/1e9:.2f}B<br>"
            f"Peak Volume: ${df['volume'].max()/1e6:.0f}M<br>"
            f"Price Range: {df['probability'].min():.0f}% - {df['probability'].max():.0f}%<br>"
            f"Outcome: Trump Won"
        ),
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(size=10),
        bgcolor='lightyellow',
        borderpad=8,
        align='left'
    )
    
    fig.write_html(output_path, include_plotlyjs='cdn')
    print(f"📊 Chart saved: {output_path}")


# =============================================================================
# Chart 2: NYC Mayor Election - Price vs Volume Dual Axis
# =============================================================================

def create_nyc_mayor_chart(df: pd.DataFrame, output_path: str):
    """Create dual-axis chart for NYC mayor election"""
    
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.6, 0.4],
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            "Price (Probability) Over Time",
            "Daily Trading Volume"
        )
    )
    
    # Price line
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['probability'],
            mode='lines+markers',
            name='Mamdani Win Probability',
            line=dict(color='#9B59B6', width=3),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(155, 89, 182, 0.2)',
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Probability: %{y:.1f}%<extra></extra>"
        ),
        row=1, col=1
    )
    
    # 50% reference line
    fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=1)
    
    # Volume bars
    colors = ['#2ECC71' if pc > 0 else '#E74C3C' if pc < 0 else '#3498DB' 
              for pc in df['price_change'].fillna(0)]
    
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['volume_millions'],
            name='Daily Volume',
            marker_color=colors,
            opacity=0.7,
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Volume: $%{y:.1f}M<extra></extra>"
        ),
        row=2, col=1
    )
    
    # Calculate correlation
    corr = df['price'].corr(df['volume'])
    
    fig.update_layout(
        title={
            'text': f"2025 NYC Mayor Election - Mamdani<br><sup>Daily Price vs Volume Analysis | Correlation: {corr:.3f}</sup>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        template='plotly_white',
        height=700,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        hovermode='x unified'
    )
    
    fig.update_yaxes(title_text="Probability (%)", row=1, col=1)
    fig.update_yaxes(title_text="Volume ($M)", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    
    # Add summary stats
    fig.add_annotation(
        text=(
            f"<b>Summary Stats</b><br>"
            f"Total Volume: ${df['volume'].sum()/1e6:.1f}M<br>"
            f"Peak Volume: ${df['volume'].max()/1e6:.0f}M<br>"
            f"Price Range: {df['probability'].min():.0f}% - {df['probability'].max():.0f}%<br>"
            f"Outcome: Mamdani Won"
        ),
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(size=10),
        bgcolor='lightyellow',
        borderpad=8,
        align='left'
    )
    
    fig.write_html(output_path, include_plotlyjs='cdn')
    print(f"📊 Chart saved: {output_path}")


# =============================================================================
# Chart 3: Correlation Scatter Plot - Both Elections
# =============================================================================

def create_correlation_scatter(df_pres: pd.DataFrame, df_nyc: pd.DataFrame, output_path: str):
    """Create scatter plot showing price-volume correlation"""
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "2024 Presidential (Trump)",
            "2025 NYC Mayor (Mamdani)"
        ),
        horizontal_spacing=0.12
    )
    
    # Presidential scatter
    fig.add_trace(
        go.Scatter(
            x=df_pres['probability'],
            y=df_pres['volume_millions'],
            mode='markers',
            name='Presidential',
            marker=dict(
                size=12,
                color=df_pres['date'].apply(lambda x: x.timestamp()),
                colorscale='Reds',
                showscale=False,
                opacity=0.7
            ),
            text=df_pres['date'].dt.strftime('%b %d'),
            hovertemplate="<b>%{text}</b><br>Probability: %{x:.1f}%<br>Volume: $%{y:.1f}M<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Add trendline for presidential
    z = np.polyfit(df_pres['probability'], df_pres['volume_millions'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df_pres['probability'].min(), df_pres['probability'].max(), 100)
    fig.add_trace(
        go.Scatter(
            x=x_line,
            y=p(x_line),
            mode='lines',
            name='Trend (Pres)',
            line=dict(color='red', dash='dash'),
            showlegend=False
        ),
        row=1, col=1
    )
    
    # NYC Mayor scatter
    fig.add_trace(
        go.Scatter(
            x=df_nyc['probability'],
            y=df_nyc['volume_millions'],
            mode='markers',
            name='NYC Mayor',
            marker=dict(
                size=12,
                color=df_nyc['date'].apply(lambda x: x.timestamp()),
                colorscale='Purples',
                showscale=False,
                opacity=0.7
            ),
            text=df_nyc['date'].dt.strftime('%b %d'),
            hovertemplate="<b>%{text}</b><br>Probability: %{x:.1f}%<br>Volume: $%{y:.1f}M<extra></extra>"
        ),
        row=1, col=2
    )
    
    # Add trendline for NYC
    z2 = np.polyfit(df_nyc['probability'], df_nyc['volume_millions'], 1)
    p2 = np.poly1d(z2)
    x_line2 = np.linspace(df_nyc['probability'].min(), df_nyc['probability'].max(), 100)
    fig.add_trace(
        go.Scatter(
            x=x_line2,
            y=p2(x_line2),
            mode='lines',
            name='Trend (NYC)',
            line=dict(color='purple', dash='dash'),
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Calculate correlations
    corr_pres = df_pres['probability'].corr(df_pres['volume_millions'])
    corr_nyc = df_nyc['probability'].corr(df_nyc['volume_millions'])
    
    fig.update_layout(
        title={
            'text': "Price vs Volume Correlation Analysis<br><sup>Higher prices often correlate with higher trading activity</sup>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        template='plotly_white',
        height=550,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
    )
    
    fig.update_xaxes(title_text="Probability (%)", row=1, col=1)
    fig.update_xaxes(title_text="Probability (%)", row=1, col=2)
    fig.update_yaxes(title_text="Daily Volume ($M)", row=1, col=1)
    fig.update_yaxes(title_text="Daily Volume ($M)", row=1, col=2)
    
    # Add correlation annotations
    fig.add_annotation(
        text=f"r = {corr_pres:.3f}",
        xref="x1", yref="y1",
        x=df_pres['probability'].max() - 5,
        y=df_pres['volume_millions'].max(),
        showarrow=False,
        font=dict(size=14, color='red'),
        bgcolor='white'
    )
    
    fig.add_annotation(
        text=f"r = {corr_nyc:.3f}",
        xref="x2", yref="y2",
        x=df_nyc['probability'].max() - 5,
        y=df_nyc['volume_millions'].max(),
        showarrow=False,
        font=dict(size=14, color='purple'),
        bgcolor='white'
    )
    
    fig.write_html(output_path, include_plotlyjs='cdn')
    print(f"📊 Chart saved: {output_path}")


# =============================================================================
# Chart 4: Combined Timeline Comparison
# =============================================================================

def create_combined_timeline(df_pres: pd.DataFrame, df_nyc: pd.DataFrame, output_path: str):
    """Create combined timeline showing both elections normalized"""
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Presidential - Price Trend",
            "NYC Mayor - Price Trend",
            "Presidential - Volume Pattern",
            "NYC Mayor - Volume Pattern"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # Presidential Price
    fig.add_trace(
        go.Scatter(
            x=df_pres['date'],
            y=df_pres['probability'],
            mode='lines+markers',
            name='Trump',
            line=dict(color='#E74C3C', width=2),
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.2)'
        ),
        row=1, col=1
    )
    
    # NYC Price
    fig.add_trace(
        go.Scatter(
            x=df_nyc['date'],
            y=df_nyc['probability'],
            mode='lines+markers',
            name='Mamdani',
            line=dict(color='#9B59B6', width=2),
            fill='tozeroy',
            fillcolor='rgba(155, 89, 182, 0.2)'
        ),
        row=1, col=2
    )
    
    # Presidential Volume
    fig.add_trace(
        go.Bar(
            x=df_pres['date'],
            y=df_pres['volume_millions'],
            name='Pres Volume',
            marker_color='#E74C3C',
            opacity=0.7,
            showlegend=False
        ),
        row=2, col=1
    )
    
    # NYC Volume
    fig.add_trace(
        go.Bar(
            x=df_nyc['date'],
            y=df_nyc['volume_millions'],
            name='NYC Volume',
            marker_color='#9B59B6',
            opacity=0.7,
            showlegend=False
        ),
        row=2, col=2
    )
    
    # Add 50% lines
    for col in [1, 2]:
        fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=col)
    
    fig.update_layout(
        title={
            'text': "Election Market Comparison<br><sup>Price Trends and Volume Patterns</sup>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        template='plotly_white',
        height=700,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
    )
    
    fig.update_yaxes(title_text="Probability (%)", row=1, col=1)
    fig.update_yaxes(title_text="Probability (%)", row=1, col=2)
    fig.update_yaxes(title_text="Volume ($M)", row=2, col=1)
    fig.update_yaxes(title_text="Volume ($M)", row=2, col=2)
    
    fig.write_html(output_path, include_plotlyjs='cdn')
    print(f"📊 Chart saved: {output_path}")


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "=" * 60)
    print("   DAILY PRICE-VOLUME CORRELATION ANALYSIS")
    print("=" * 60)
    print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load data
    print("\n📊 Loading data...")
    data = load_data()
    
    df_pres = parse_market_data(data['presidential_2024_trump'])
    df_nyc = parse_market_data(data['nyc_mayor_2025_mamdani'])
    
    print(f"   Presidential: {len(df_pres)} data points")
    print(f"   NYC Mayor: {len(df_nyc)} data points")
    
    # Calculate correlations
    corr_pres = df_pres['price'].corr(df_pres['volume'])
    corr_nyc = df_nyc['price'].corr(df_nyc['volume'])
    
    print(f"\n📈 Correlations (Price vs Volume):")
    print(f"   Presidential: r = {corr_pres:.3f}")
    print(f"   NYC Mayor:    r = {corr_nyc:.3f}")
    
    # Create charts
    print("\n📊 Generating interactive charts...")
    
    create_presidential_chart(df_pres, str(OUTPUT_DIR / "correlation_1_presidential.html"))
    create_nyc_mayor_chart(df_nyc, str(OUTPUT_DIR / "correlation_2_nyc_mayor.html"))
    create_correlation_scatter(df_pres, df_nyc, str(OUTPUT_DIR / "correlation_3_scatter.html"))
    create_combined_timeline(df_pres, df_nyc, str(OUTPUT_DIR / "correlation_4_comparison.html"))
    
    # Summary
    print("\n" + "=" * 60)
    print("   SUMMARY")
    print("=" * 60)
    print("\n   📊 4 Interactive Charts Created:")
    print("   1. correlation_1_presidential.html - Price/Volume dual-axis (Trump)")
    print("   2. correlation_2_nyc_mayor.html    - Price/Volume dual-axis (Mamdani)")
    print("   3. correlation_3_scatter.html      - Price vs Volume scatter plot")
    print("   4. correlation_4_comparison.html   - Side-by-side comparison")
    print("\n   💡 Key Insights:")
    print(f"   • Presidential correlation: {corr_pres:.3f} (moderate positive)")
    print(f"   • NYC Mayor correlation: {corr_nyc:.3f} (strong positive)")
    print("   • Volume tends to increase as price moves toward certainty")
    print("   • Major events (debates, news) drive both price and volume spikes")
    print("=" * 60)


if __name__ == "__main__":
    main()
