#!/usr/bin/env python3
"""
Dune Analytics Data Fetcher for Polymarket
Fetches real on-chain volume data for Super Bowl 2025
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Installing python-dotenv...")
    import subprocess
    subprocess.run(["pip3", "install", "python-dotenv"], capture_output=True)
    from dotenv import load_dotenv
    load_dotenv()

DUNE_API_KEY = os.getenv("DUNE_API_KEY")
if not DUNE_API_KEY:
    print("Error: DUNE_API_KEY not found in .env file")
    print("Please add: DUNE_API_KEY=your_key_here")
    exit(1)

BASE_URL = "https://api.dune.com/api/v1"
HEADERS = {"X-Dune-API-Key": DUNE_API_KEY}


def execute_sql_query(sql: str):
    """Execute a raw SQL query on Dune"""
    url = f"{BASE_URL}/query/execute"
    
    payload = {
        "query_sql": sql,
        "is_private": False
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code != 200:
        print(f"Execute failed: {response.status_code}")
        print(response.text)
        return None
    
    exec_data = response.json()
    execution_id = exec_data.get("execution_id")
    print(f"Query executing... ID: {execution_id}")
    
    # Poll for results
    import time
    
    for i in range(60):  # Max 60 attempts (2 minutes)
        time.sleep(2)
        status_url = f"{BASE_URL}/execution/{execution_id}/status"
        status_resp = requests.get(status_url, headers=HEADERS)
        status = status_resp.json()
        state = status.get("state")
        
        if i % 5 == 0:
            print(f"  Status: {state} ({i*2}s)")
        
        if state == "QUERY_STATE_COMPLETED":
            results_url = f"{BASE_URL}/execution/{execution_id}/results"
            results_resp = requests.get(results_url, headers=HEADERS)
            return results_resp.json()
        elif state in ["QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"]:
            print(f"Query failed: {status}")
            return None
    
    print("Query timed out")
    return None


def fetch_polymarket_daily_volume():
    """Fetch Polymarket daily trading volume from on-chain data"""
    print("Fetching Polymarket daily volume from Dune Analytics...")
    print(f"API Key: {DUNE_API_KEY[:8]}...")
    
    # Query for Polymarket daily volume on Polygon
    # Using the CTF Exchange and NegRisk Exchange events
    sql = """
    SELECT 
        date_trunc('day', block_time) as date,
        SUM(
            CASE 
                WHEN tx_to = 0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e THEN value / 1e6
                WHEN tx_to = 0xC5d563A36AE78145C45a50134d48A1215220f80a THEN value / 1e6
                ELSE 0
            END
        ) as volume_usd
    FROM polygon.transactions
    WHERE block_time >= date '2024-09-01'
        AND block_time < date '2025-03-01'
        AND (
            tx_to = 0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e  -- CTF Exchange
            OR tx_to = 0xC5d563A36AE78145C45a50134d48A1215220f80a  -- NegRisk Exchange
        )
        AND success = true
    GROUP BY 1
    ORDER BY 1
    """
    
    results = execute_sql_query(sql)
    
    if results and "result" in results:
        rows = results["result"].get("rows", [])
        print(f"\n✓ Successfully fetched {len(rows)} days of data!")
        
        # Save to cache
        cache_dir = Path(__file__).parent / ".cache"
        cache_dir.mkdir(exist_ok=True)
        
        output_path = cache_dir / "dune_polymarket_volume.json"
        with open(output_path, "w") as f:
            json.dump(rows, f, indent=2)
        print(f"✓ Data saved to {output_path}")
        
        # Print sample
        print("\nSample data:")
        for row in rows[:10]:
            date = row.get('date', 'N/A')[:10] if row.get('date') else 'N/A'
            vol = row.get('volume_usd', 0)
            print(f"  {date}: ${vol:,.0f}")
        
        return rows
    
    print("\n⚠ Query returned no results")
    return None


def main():
    """Main function"""
    data = fetch_polymarket_daily_volume()
    
    if data:
        print("\n✓ Successfully fetched real on-chain Polymarket data!")
        print(f"Total days: {len(data)}")
    else:
        print("\n⚠ Could not fetch data. Check API credits or query syntax.")


if __name__ == "__main__":
    main()

