#!/usr/bin/env python3
"""
Kalshi vs Polymarket Comparison Charts
Creates interactive Plotly charts comparing predictions between platforms
"""

import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime

# Load data
DATA_DIR = Path(__file__).parent / ".cache"


def load_data():
    """Load Kalshi and Polymarket data"""
    with open(DATA_DIR / "kalshi_data.json") as f:
        kalshi = json.load(f)
    
    with open(DATA_DIR / "daily_price_volume.json") as f:
        polymarket = json.load(f)
    
    return kalshi, polymarket


def get_matching_dates(kalshi_data: list, polymarket_data: list):
    """Find matching dates between Kalshi and Polymarket data"""
    kalshi_dates = {d["date"]: d for d in kalshi_data}
    polymarket_dates = {d["date"]: d for d in polymarket_data}
    
    # Find overlapping dates
    common_dates = sorted(set(kalshi_dates.keys()) & set(polymarket_dates.keys()))
    
    return common_dates, kalshi_dates, polymarket_dates


def create_presidential_comparison(kalshi, polymarket):
    """Create comparison chart for 2024 Presidential election"""
    kalshi_data = kalshi.get("presidential", {}).get("daily_data", [])
    polymarket_data = polymarket.get("presidential_2024_trump", {}).get("daily_data", [])
    
    if not kalshi_data:
        print("No Kalshi presidential data available")
        return None
    
    common_dates, kalshi_dict, polymarket_dict = get_matching_dates(kalshi_data, polymarket_data)
    
    # Create figure with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            "Price Comparison: Kalshi vs Polymarket",
            "Price Difference (Kalshi - Polymarket)"
        )
    )
    
    # Extract data for common dates
    dates = common_dates
    kalshi_prices = [kalshi_dict[d]["price"] * 100 for d in dates]
    polymarket_prices = [polymarket_dict[d]["price"] * 100 for d in dates]
    price_diff = [k - p for k, p in zip(kalshi_prices, polymarket_prices)]
    
    # Green/red styling for price difference
    diff_colors = ["#00C853" if d > 0 else "#FF1744" for d in price_diff]
    
    # Price comparison lines
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=kalshi_prices,
            mode="lines+markers",
            name="Kalshi",
            line=dict(color="#7C4DFF", width=3),
            marker=dict(size=6),
            hovertemplate="Kalshi: %{y:.1f}%<extra></extra>"
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=polymarket_prices,
            mode="lines+markers",
            name="Polymarket",
            line=dict(color="#00BCD4", width=3),
            marker=dict(size=6),
            hovertemplate="Polymarket: %{y:.1f}%<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Price difference bar
    fig.add_trace(
        go.Bar(
            x=dates,
            y=price_diff,
            name="Difference",
            marker_color=diff_colors,
            hovertemplate="Diff: %{y:+.1f}%<extra></extra>",
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Add key events
    events = [
        ("2024-10-27", "MSG Rally"),
        ("2024-11-01", "Final Week"),
        ("2024-11-05", "Election Day"),
    ]
    
    for date, label in events:
        if date in dates:
            fig.add_vline(
                x=date,
                line_dash="dash",
                line_color="rgba(255,255,255,0.3)",
                row=1, col=1
            )
            fig.add_annotation(
                x=date,
                y=max(kalshi_prices + polymarket_prices) + 2,
                text=label,
                showarrow=False,
                font=dict(size=10, color="white"),
                row=1, col=1
            )
    
    # Calculate statistics
    avg_diff = sum(price_diff) / len(price_diff)
    max_diff = max(price_diff)
    min_diff = min(price_diff)
    
    # Add stats box
    stats_text = f"<b>Statistics ({len(dates)} days)</b><br>"
    stats_text += f"Avg Difference: {avg_diff:+.1f}%<br>"
    stats_text += f"Max Kalshi Lead: {max_diff:+.1f}%<br>"
    stats_text += f"Max Poly Lead: {min_diff:+.1f}%"
    
    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text=stats_text,
        showarrow=False,
        font=dict(size=11, color="white"),
        align="left",
        bgcolor="rgba(0,0,0,0.5)",
        bordercolor="rgba(255,255,255,0.3)",
        borderwidth=1,
        borderpad=8
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="<b>🇺🇸 2024 Presidential Election: Trump Win Probability</b><br><sup>Kalshi vs Polymarket Platform Comparison</sup>",
            font=dict(size=20)
        ),
        template="plotly_dark",
        height=700,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(0,0,0,0.5)"
        ),
        hovermode="x unified"
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Win Probability (%)", row=1, col=1)
    fig.update_yaxes(title_text="Diff (%)", row=2, col=1)
    
    # Add zero line for difference chart
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.5)", row=2, col=1)
    
    return fig


def create_scatter_comparison(kalshi, polymarket):
    """Create scatter plot comparing Kalshi vs Polymarket prices"""
    kalshi_data = kalshi.get("presidential", {}).get("daily_data", [])
    polymarket_data = polymarket.get("presidential_2024_trump", {}).get("daily_data", [])
    
    if not kalshi_data:
        print("No Kalshi presidential data available")
        return None
    
    common_dates, kalshi_dict, polymarket_dict = get_matching_dates(kalshi_data, polymarket_data)
    
    # Extract prices
    kalshi_prices = [kalshi_dict[d]["price"] * 100 for d in common_dates]
    polymarket_prices = [polymarket_dict[d]["price"] * 100 for d in common_dates]
    
    # Color by date (earlier = lighter)
    colors = list(range(len(common_dates)))
    
    fig = go.Figure()
    
    # Add scatter points
    fig.add_trace(
        go.Scatter(
            x=polymarket_prices,
            y=kalshi_prices,
            mode="markers+text",
            marker=dict(
                size=12,
                color=colors,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(
                    title="Day",
                    tickvals=[0, len(common_dates)//2, len(common_dates)-1],
                    ticktext=[common_dates[0], common_dates[len(common_dates)//2], common_dates[-1]]
                )
            ),
            text=[d.split("-")[1] + "/" + d.split("-")[2] for d in common_dates],
            textposition="top center",
            textfont=dict(size=8, color="rgba(255,255,255,0.6)"),
            hovertemplate="<b>%{customdata}</b><br>Polymarket: %{x:.1f}%<br>Kalshi: %{y:.1f}%<extra></extra>",
            customdata=common_dates
        )
    )
    
    # Add diagonal parity line
    min_val = min(min(kalshi_prices), min(polymarket_prices)) - 2
    max_val = max(max(kalshi_prices), max(polymarket_prices)) + 2
    
    fig.add_trace(
        go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode="lines",
            line=dict(dash="dash", color="rgba(255,255,255,0.5)", width=2),
            name="Parity Line",
            showlegend=True
        )
    )
    
    # Calculate correlation
    n = len(kalshi_prices)
    mean_k = sum(kalshi_prices) / n
    mean_p = sum(polymarket_prices) / n
    
    cov = sum((k - mean_k) * (p - mean_p) for k, p in zip(kalshi_prices, polymarket_prices)) / n
    std_k = (sum((k - mean_k)**2 for k in kalshi_prices) / n) ** 0.5
    std_p = (sum((p - mean_p)**2 for p in polymarket_prices) / n) ** 0.5
    correlation = cov / (std_k * std_p)
    
    # Add annotation
    fig.add_annotation(
        x=0.05,
        y=0.95,
        xref="paper",
        yref="paper",
        text=f"<b>Correlation: r = {correlation:.3f}</b><br>Points above line: Kalshi higher<br>Points below line: Polymarket higher",
        showarrow=False,
        font=dict(size=12, color="white"),
        align="left",
        bgcolor="rgba(0,0,0,0.6)",
        bordercolor="rgba(255,255,255,0.3)",
        borderwidth=1,
        borderpad=10
    )
    
    fig.update_layout(
        title=dict(
            text="<b>📊 Platform Price Correlation: Kalshi vs Polymarket</b><br><sup>2024 Presidential Election - Trump Win Probability</sup>",
            font=dict(size=20)
        ),
        xaxis_title="Polymarket Price (%)",
        yaxis_title="Kalshi Price (%)",
        template="plotly_dark",
        height=700,
        showlegend=True,
        legend=dict(
            yanchor="bottom",
            y=0.02,
            xanchor="right",
            x=0.98
        )
    )
    
    # Make axes equal
    fig.update_xaxes(range=[min_val, max_val])
    fig.update_yaxes(range=[min_val, max_val], scaleanchor="x", scaleratio=1)
    
    return fig


def create_volume_comparison(kalshi, polymarket):
    """Create volume comparison chart"""
    kalshi_data = kalshi.get("presidential", {}).get("daily_data", [])
    polymarket_data = polymarket.get("presidential_2024_trump", {}).get("daily_data", [])
    
    if not kalshi_data:
        return None
    
    common_dates, kalshi_dict, polymarket_dict = get_matching_dates(kalshi_data, polymarket_data)
    
    # Extract volumes
    kalshi_volumes = [kalshi_dict[d]["daily_volume"] / 1e6 for d in common_dates]
    polymarket_volumes = [polymarket_dict[d]["daily_volume"] / 1e6 for d in common_dates]
    
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": True}]]
    )
    
    # Kalshi volume bars
    fig.add_trace(
        go.Bar(
            x=common_dates,
            y=kalshi_volumes,
            name="Kalshi Volume",
            marker_color="rgba(124, 77, 255, 0.7)",
            hovertemplate="Kalshi: $%{y:.1f}M<extra></extra>"
        )
    )
    
    # Polymarket volume bars
    fig.add_trace(
        go.Bar(
            x=common_dates,
            y=polymarket_volumes,
            name="Polymarket Volume",
            marker_color="rgba(0, 188, 212, 0.7)",
            hovertemplate="Polymarket: $%{y:.1f}M<extra></extra>"
        )
    )
    
    # Add total stats
    kalshi_total = sum(kalshi_volumes)
    poly_total = sum(polymarket_volumes)
    
    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text=f"<b>Total Volume ({len(common_dates)} days)</b><br>Kalshi: ${kalshi_total:.1f}M<br>Polymarket: ${poly_total:.1f}M<br>Ratio: {poly_total/kalshi_total:.1f}x",
        showarrow=False,
        font=dict(size=11, color="white"),
        align="left",
        bgcolor="rgba(0,0,0,0.5)",
        bordercolor="rgba(255,255,255,0.3)",
        borderwidth=1,
        borderpad=8
    )
    
    fig.update_layout(
        title=dict(
            text="<b>💰 Daily Trading Volume: Kalshi vs Polymarket</b><br><sup>2024 Presidential Election (Overlapping Period Only)</sup>",
            font=dict(size=20)
        ),
        xaxis_title="Date",
        yaxis_title="Daily Volume (Millions USD)",
        template="plotly_dark",
        height=500,
        barmode="group",
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(0,0,0,0.5)"
        ),
        hovermode="x unified"
    )
    
    return fig


def main():
    """Generate all comparison charts"""
    print("Loading data...")
    kalshi, polymarket = load_data()
    
    # Create output directory
    output_dir = Path(__file__).parent
    
    # Presidential comparison
    print("Creating presidential comparison chart...")
    fig = create_presidential_comparison(kalshi, polymarket)
    if fig:
        output_path = output_dir / "comparison_5_presidential_platforms.html"
        fig.write_html(output_path, include_plotlyjs="cdn")
        print(f"  ✓ Saved to {output_path}")
    
    # Scatter comparison
    print("Creating scatter comparison chart...")
    fig = create_scatter_comparison(kalshi, polymarket)
    if fig:
        output_path = output_dir / "comparison_6_scatter_platforms.html"
        fig.write_html(output_path, include_plotlyjs="cdn")
        print(f"  ✓ Saved to {output_path}")
    
    # Volume comparison
    print("Creating volume comparison chart...")
    fig = create_volume_comparison(kalshi, polymarket)
    if fig:
        output_path = output_dir / "comparison_7_volume_platforms.html"
        fig.write_html(output_path, include_plotlyjs="cdn")
        print(f"  ✓ Saved to {output_path}")
    
    print("\n✓ All comparison charts generated!")


if __name__ == "__main__":
    main()
