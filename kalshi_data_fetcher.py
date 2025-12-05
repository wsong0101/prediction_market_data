#!/usr/bin/env python3
"""
Kalshi Data Fetcher
Fetches historical candlestick data from Kalshi API for comparison with Polymarket
"""

import json
import requests
from datetime import datetime
from pathlib import Path

# Kalshi API base URL
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

# Market tickers
MARKETS = {
    "presidential": {
        "series_ticker": "PRES",
        "market_ticker": "PRES-2024-DJT",
        "title": "2024 Presidential Election - Trump",
        "start_ts": 1704067200,  # 2024-01-01
        "end_ts": 1731024000,    # 2024-11-08
    },
    "nyc_mayor": {
        "series_ticker": "KXPCTVOTEMAM",
        "market_ticker": "KXPCTVOTEMAM-26-ZMAM-T50",
        "title": "2025 NYC Mayoral Election - Mamdani",
        "start_ts": 1714521600,  # 2024-05-01
        "end_ts": 1730851200,    # 2024-11-06
    }
}


def fetch_candlesticks(series_ticker: str, market_ticker: str, start_ts: int, end_ts: int) -> list:
    """Fetch daily candlestick data from Kalshi API"""
    url = f"{BASE_URL}/series/{series_ticker}/markets/{market_ticker}/candlesticks"
    params = {
        "start_ts": start_ts,
        "end_ts": end_ts,
        "period_interval": 1440  # Daily
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching {market_ticker}: {response.status_code}")
        print(response.text)
        return []
    
    data = response.json()
    return data.get("candlesticks", [])


def process_candlesticks(candlesticks: list) -> list:
    """Process raw candlestick data into daily price/volume records"""
    daily_data = []
    
    for candle in candlesticks:
        # Extract timestamp and convert to date
        end_ts = candle.get("end_period_ts", 0)
        date = datetime.utcfromtimestamp(end_ts).strftime("%Y-%m-%d")
        
        # Extract price data (closing price in cents, convert to 0-1 scale)
        price_data = candle.get("price", {})
        close_price = price_data.get("close", 0) / 100.0
        high_price = price_data.get("high", 0) / 100.0
        low_price = price_data.get("low", 0) / 100.0
        open_price = price_data.get("open", 0) / 100.0
        
        # Extract volume
        volume = candle.get("volume", 0)
        open_interest = candle.get("open_interest", 0)
        
        daily_data.append({
            "date": date,
            "price": close_price,
            "high": high_price,
            "low": low_price,
            "open": open_price,
            "daily_volume": volume,
            "open_interest": open_interest
        })
    
    # Sort by date
    daily_data.sort(key=lambda x: x["date"])
    
    return daily_data


def main():
    """Main function to fetch all market data"""
    output = {
        "source": "Kalshi Exchange API",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "note": "Kalshi launched 2024 presidential markets in Oct 2024, so data coverage is shorter than Polymarket"
    }
    
    for market_key, market_info in MARKETS.items():
        print(f"Fetching {market_info['title']}...")
        
        candlesticks = fetch_candlesticks(
            market_info["series_ticker"],
            market_info["market_ticker"],
            market_info["start_ts"],
            market_info["end_ts"]
        )
        
        if candlesticks:
            daily_data = process_candlesticks(candlesticks)
            
            # Calculate total volume
            total_volume = sum(d["daily_volume"] for d in daily_data)
            
            output[market_key] = {
                "title": market_info["title"],
                "market_ticker": market_info["market_ticker"],
                "total_volume": total_volume,
                "days_of_data": len(daily_data),
                "daily_data": daily_data
            }
            
            print(f"  ✓ Fetched {len(daily_data)} days of data")
            if daily_data:
                print(f"  ✓ Date range: {daily_data[0]['date']} to {daily_data[-1]['date']}")
                print(f"  ✓ Total volume: ${total_volume:,.0f}")
        else:
            print(f"  ✗ No data available")
    
    # Save to cache
    cache_dir = Path(__file__).parent / ".cache"
    cache_dir.mkdir(exist_ok=True)
    output_path = cache_dir / "kalshi_data.json"
    
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Data saved to {output_path}")
    return output


if __name__ == "__main__":
    main()
