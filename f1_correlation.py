#!/usr/bin/env python3
"""
F1 2025 Championship: Price-Volume Correlation Analysis
Using real trade data from Kaggle Polymarket Dataset
"""

import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

def load_data():
    """Load F1 daily data from cache"""
    with open('.cache/f1_norris_daily.json', 'r') as f:
        return json.load(f)

def calculate_correlation(prices, volumes):
    """Calculate Pearson correlation coefficient"""
    n = len(prices)
    if n < 2:
        return 0
    
    mean_p = sum(prices) / n
    mean_v = sum(volumes) / n
    
    cov = sum((p - mean_p) * (v - mean_v) for p, v in zip(prices, volumes)) / n
    std_p = (sum((p - mean_p)**2 for p in prices) / n) ** 0.5
    std_v = (sum((v - mean_v)**2 for v in volumes) / n) ** 0.5
    
    if std_p > 0 and std_v > 0:
        return cov / (std_p * std_v)
    return 0

def create_correlation_chart():
    """Create price-volume correlation chart for F1 2025"""
    data = load_data()
    daily = data['daily_data']
    
    dates = [d['date'] for d in daily]
    prices = [d['avg_price'] * 100 for d in daily]  # Convert to percentage
    volumes = [d['daily_volume'] / 1e3 for d in daily]  # Convert to thousands
    trades = [d['trades'] for d in daily]
    
    # Calculate correlation
    correlation = calculate_correlation(prices, volumes)
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Volume bars
    fig.add_trace(
        go.Bar(
            x=dates,
            y=volumes,
            name="Trading Volume ($K)",
            marker=dict(
                color=volumes,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Vol ($K)")
            ),
            opacity=0.7,
            hovertemplate="Date: %{x}<br>Volume: $%{y:,.0f}K<extra></extra>"
        ),
        secondary_y=False
    )
    
    # Price line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=prices,
            mode="lines+markers",
            name="Win Probability (%)",
            line=dict(color="#FF6B00", width=3),  # McLaren orange
            marker=dict(size=10),
            hovertemplate="Date: %{x}<br>Probability: %{y:.1f}%<extra></extra>"
        ),
        secondary_y=True
    )
    
    # Stats annotation
    total_vol = sum(d['daily_volume'] for d in daily)
    total_trades = sum(d['trades'] for d in daily)
    
    stats_text = f"""<b>Price-Volume Correlation</b>
r = {correlation:.3f}

<b>Market Stats:</b>
Total Volume: ${total_vol/1e6:.2f}M
Total Trades: {total_trades:,}
Days: {len(daily)}

<b>Data Source:</b>
Kaggle Polymarket Dataset
(Real on-chain trades)
"""
    
    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text=stats_text,
        showarrow=False,
        font=dict(size=11, color="white"),
        align="left",
        bgcolor="rgba(0,0,0,0.7)",
        bordercolor="rgba(255,255,255,0.3)",
        borderwidth=1,
        borderpad=10
    )
    
    fig.update_layout(
        title=dict(
            text="<b>🏎️ F1 2025: Lando Norris Championship Odds</b><br><sup>Price-Volume Correlation (Real Polymarket Trade Data)</sup>",
            font=dict(size=20)
        ),
        template="plotly_dark",
        height=600,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.85,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(0,0,0,0.5)"
        ),
        hovermode="x unified"
    )
    
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Trading Volume (Thousands $)", secondary_y=False)
    fig.update_yaxes(title_text="Win Probability (%)", secondary_y=True, range=[30, 45])
    
    return fig, correlation

def create_scatter_chart():
    """Create scatter plot for price vs volume"""
    data = load_data()
    daily = data['daily_data']
    
    prices = [d['avg_price'] * 100 for d in daily]
    volumes = [d['daily_volume'] for d in daily]
    dates = [d['date'] for d in daily]
    
    correlation = calculate_correlation(prices, volumes)
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=prices,
            y=volumes,
            mode="markers+text",
            text=[d[-5:] for d in dates],  # Show date suffix
            textposition="top center",
            marker=dict(
                size=15,
            color=list(range(len(prices))),
                colorscale="Plasma",
                showscale=True,
                colorbar=dict(title="Day")
            ),
            hovertemplate="Price: %{x:.1f}%<br>Volume: $%{y:,.0f}<br><extra></extra>"
        )
    )
    
    fig.update_layout(
        title=dict(
            text=f"<b>🏎️ F1 2025: Price vs Volume Scatter</b><br><sup>Lando Norris Championship (r = {correlation:.3f})</sup>",
            font=dict(size=20)
        ),
        xaxis_title="Win Probability (%)",
        yaxis_title="Daily Trading Volume ($)",
        template="plotly_dark",
        height=550
    )
    
    return fig

def main():
    """Generate F1 correlation charts"""
    print("Generating F1 2025 correlation charts from Kaggle data...")
    
    output_dir = Path(__file__).parent
    
    # Timeline chart
    print("Creating price-volume timeline...")
    fig, corr = create_correlation_chart()
    output_path = output_dir / "correlation_6_f1_norris.html"
    fig.write_html(output_path, include_plotlyjs="cdn")
    print(f"  ✓ Saved to {output_path}")
    print(f"  Correlation: r = {corr:.3f}")
    
    # Scatter chart
    print("Creating scatter plot...")
    fig = create_scatter_chart()
    output_path = output_dir / "correlation_7_f1_scatter.html"
    fig.write_html(output_path, include_plotlyjs="cdn")
    print(f"  ✓ Saved to {output_path}")
    
    print("\n✓ F1 correlation charts generated with REAL trade data!")

if __name__ == "__main__":
    main()
