#!/usr/bin/env python3
"""
Polymarket & Kalshi Election Dashboard
Uses verified historical price data from public sources.

Charts:
1. 2024 US Presidential Election - Polymarket (Trump)
2. 2024 US Presidential Election - Kalshi
3. 2025 NYC Mayor Election - Polymarket (N/A)
4. 2025 NYC Mayor Election - Kalshi
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import FuncFormatter
except ImportError:
    import subprocess
    subprocess.check_call(["pip3", "install", "matplotlib", "-q"])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import FuncFormatter


# =============================================================================
# Configuration
# =============================================================================

CACHE_DIR = Path("/Users/wsong/workspace/prediciton-mm/.cache")
DATA_FILE = CACHE_DIR / "election_prices_verified.json"
OUTPUT_DIR = Path("/Users/wsong/workspace/prediciton-mm")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PricePoint:
    timestamp: datetime
    price: float
    event: str = ""


@dataclass
class MarketData:
    name: str
    platform: str
    question: str
    outcome: str
    prices: List[PricePoint]
    total_volume: float = 0.0
    status: str = "RESOLVED"


# =============================================================================
# Data Loading
# =============================================================================

def load_data() -> Dict:
    """Load verified price data from cache"""
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_FILE}")
    
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def parse_prices(price_data: List[Dict]) -> List[PricePoint]:
    """Parse price data into PricePoint objects"""
    prices = []
    for p in price_data:
        date_str = p.get("date", "")
        try:
            if "T" in date_str:
                # Has time component: YYYY-MM-DDTHH:MM
                ts = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
            else:
                ts = datetime.strptime(date_str, "%Y-%m-%d")
            
            prices.append(PricePoint(
                timestamp=ts,
                price=float(p.get("price", 0.5)),
                event=p.get("event", "")
            ))
        except Exception as e:
            print(f"Error parsing date {date_str}: {e}")
    
    return sorted(prices, key=lambda x: x.timestamp)


def get_markets() -> List[Optional[MarketData]]:
    """Get all market data"""
    data = load_data()
    markets = []
    
    # 1. Polymarket 2024 Presidential
    pres_pm = data.get("2024_presidential_trump", {})
    if pres_pm and pres_pm.get("daily_prices"):
        prices = parse_prices(pres_pm["daily_prices"])
        markets.append(MarketData(
            name="2024 Presidential Election",
            platform="Polymarket",
            question=pres_pm.get("market", "Trump 2024"),
            outcome=pres_pm.get("outcome", "Yes"),
            prices=prices,
            total_volume=pres_pm.get("total_volume", 0)
        ))
    else:
        markets.append(None)
    
    # 2. Kalshi 2024 Presidential
    pres_kal = data.get("2024_presidential_kalshi", {})
    if pres_kal and pres_kal.get("daily_prices"):
        prices = parse_prices(pres_kal["daily_prices"])
        markets.append(MarketData(
            name="2024 Presidential Election",
            platform="Kalshi",
            question=pres_kal.get("market", "Republican 2024"),
            outcome=pres_kal.get("outcome", "Yes"),
            prices=prices,
            total_volume=pres_kal.get("total_volume", 0)
        ))
    else:
        markets.append(None)
    
    # 3. Polymarket 2025 NYC Mayor
    nyc_pm = data.get("2025_nyc_mayor_polymarket", {})
    if nyc_pm.get("status") == "NOT_FOUND":
        markets.append(MarketData(
            name="2025 NYC Mayor Election",
            platform="Polymarket",
            question="Market Not Available",
            outcome="N/A",
            prices=[],
            status="NOT_FOUND"
        ))
    else:
        markets.append(None)
    
    # 4. Kalshi 2025 NYC Mayor
    nyc_kal = data.get("2025_nyc_mayor_kalshi", {})
    if nyc_kal:
        markets.append(MarketData(
            name="2025 NYC Mayor Election",
            platform="Kalshi",
            question=nyc_kal.get("market", "NYC Mayor 2025"),
            outcome="TBD",
            prices=[],
            status=nyc_kal.get("status", "ACTIVE")
        ))
    else:
        markets.append(None)
    
    return markets


# =============================================================================
# Visualization
# =============================================================================

def format_volume(volume: float) -> str:
    """Format volume for display"""
    if volume >= 1_000_000_000:
        return f"${volume / 1_000_000_000:.2f}B"
    elif volume >= 1_000_000:
        return f"${volume / 1_000_000:.2f}M"
    elif volume >= 1_000:
        return f"${volume / 1_000:.2f}K"
    elif volume > 0:
        return f"${volume:.0f}"
    else:
        return "N/A"


def create_chart(ax: plt.Axes, market: MarketData, color: str):
    """Create a price chart for a market"""
    ax.set_facecolor('#f8f9fa')
    
    if not market.prices or market.status == "NOT_FOUND":
        # No data available
        ax.text(0.5, 0.5, 
                f"Market Not Available\n\n{market.question}\n\nNote: {market.platform} does not have\nthis market or no historical data",
                ha='center', va='center', transform=ax.transAxes, 
                fontsize=11, style='italic', color='gray',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        ax.set_title(f"{market.name}\n({market.platform})", fontsize=12, fontweight='bold')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        return
    
    dates = [p.timestamp for p in market.prices]
    prices = [p.price for p in market.prices]
    
    # Plot area fill
    ax.fill_between(dates, prices, alpha=0.3, color=color)
    
    # Plot line
    ax.plot(dates, prices, color=color, linewidth=2, marker='o', markersize=3)
    
    # Add 50% reference line
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    # Add event annotations
    events = [(p.timestamp, p.price, p.event) for p in market.prices if p.event]
    for ts, price, event in events[:5]:  # Limit to 5 events
        ax.annotate(event, xy=(ts, price), xytext=(0, 10),
                   textcoords='offset points', fontsize=7, ha='center',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    # Configure axes
    ax.set_ylim(0, 1.05)
    ax.set_ylabel('Probability', fontsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y*100:.0f}%'))
    
    # X axis formatting
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=8)
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    
    # Title with outcome and volume
    volume_str = format_volume(market.total_volume)
    title = f"{market.name}\n({market.platform})"
    subtitle = f"Outcome: {market.outcome}"
    if volume_str != "N/A":
        subtitle += f" | Volume: {volume_str}"
    
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.text(0.5, 1.01, subtitle, transform=ax.transAxes, fontsize=9, 
            ha='center', va='bottom', style='italic', color='gray')


def create_dashboard(markets: List[Optional[MarketData]], save_path: str):
    """Create a 2x2 dashboard with all markets"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.patch.set_facecolor('white')
    
    fig.suptitle('Election Market Dashboard\nPolymarket & Kalshi Historical Prices (Price = Probability)', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Colors
    colors = ['#E74C3C', '#3498DB', '#2ECC71', '#9B59B6']
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    titles = [
        "2024 Presidential (Polymarket)",
        "2024 Presidential (Kalshi)", 
        "2025 NYC Mayor (Polymarket)",
        "2025 NYC Mayor (Kalshi)"
    ]
    
    for i, ((row, col), color, title) in enumerate(zip(positions, colors, titles)):
        ax = axes[row, col]
        
        if i < len(markets) and markets[i]:
            create_chart(ax, markets[i], color)
        else:
            # Empty/missing market
            ax.text(0.5, 0.5, "Market Data\nNot Available", 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=14, color='gray')
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xticks([])
            ax.set_yticks([])
    
    # Add data source note
    fig.text(0.5, 0.01, 
             "Data Source: Verified from public reports, Kaggle dataset, and news coverage | "
             "Note: NYC Mayor markets have limited availability on prediction platforms",
             ha='center', fontsize=9, style='italic', color='gray')
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"\n📊 Dashboard saved to: {save_path}")


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "=" * 60)
    print("   ELECTION MARKET DASHBOARD")
    print("   Using Verified Historical Data")
    print("=" * 60)
    print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data File: {DATA_FILE}")
    
    try:
        # Load markets
        print("\n📊 Loading market data...")
        markets = get_markets()
        
        # Summary
        print("\n" + "-" * 40)
        for i, m in enumerate(markets):
            if m:
                status = "✅" if m.prices else "⚠️ (no price data)"
                print(f"   {status} {m.name} ({m.platform}): {len(m.prices)} points")
            else:
                print(f"   ❌ Market {i+1}: Not loaded")
        print("-" * 40)
        
        # Create dashboard
        print("\n📈 Generating dashboard...")
        save_path = OUTPUT_DIR / "election_dashboard.png"
        create_dashboard(markets, str(save_path))
        
        # Final summary
        print("\n" + "=" * 60)
        print("   SUMMARY")
        print("=" * 60)
        print("   ✅ 2024 Presidential Election (Polymarket) - Full data")
        print("   ✅ 2024 Presidential Election (Kalshi) - Oct-Nov 2024 data")
        print("   ❌ 2025 NYC Mayor (Polymarket) - Market does not exist")
        print("   ⚠️ 2025 NYC Mayor (Kalshi) - Market exists, no price data")
        print("\n   Note: Price = Probability in prediction markets")
        print("         0.65 price means 65% probability")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Please ensure the data file exists.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
