import sqlite3
from datetime import datetime, timedelta
import random

import os

def seed_data():
    db_path = "data/inver.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            date TEXT PRIMARY KEY,
            total_value REAL,
            invested_amount REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asset_snapshots (
            date TEXT,
            symbol TEXT,
            quantity REAL,
            price REAL,
            total_value REAL,
            PRIMARY KEY (date, symbol)
        )
    ''')
    
    # Target: ~1,468,500 ARS today
    current_val = 1468500.0
    
    # Base assets to track (matches default simulation)
    # Symbols: SPY.BA, GGAL.BA, MELI.BA
    # Weights approx: SPY=35%, GGAL=55%, MELI=10% (Just rough for mock)
    assets = {
        "SPY.BA": 522500.0,
        "GGAL.BA": 812500.0,
        "MELI.BA": 133500.0
    }
    
    # Generate 45 days of history
    days = 45
    history_total = []
    history_assets = []
    
    # Random walk backwards
    curr_assets = assets.copy()
    
    for i in range(days):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        
        total_daily = sum(curr_assets.values())
        history_total.append((date_str, total_daily, 1000000.0))
        
        for sym, val in curr_assets.items():
            # Approx Quantity (assuming price=val for simplicity in mock history if qty undefined)
            # Actually schema uses Quantity, Price, Total Value.
            # We'll just mock Total Value mainly for the gains calculation which relies on it.
            # Price/Qty can be derived roughly.
            price_mock = val / 10 # dummy
            qty_mock = 10 
            
            history_assets.append((date_str, sym, qty_mock, price_mock, val))
            
            # Walk backing
            change_pct = random.uniform(-0.02, 0.025)
            curr_assets[sym] = val / (1 + change_pct)
        
    # Insert Totals
    for date, value, invested in history_total:
        cursor.execute('''
            INSERT OR REPLACE INTO portfolio_snapshots (date, total_value, invested_amount)
            VALUES (?, ?, ?)
        ''', (date, value, invested))
        
    # Insert Assets
    for date, sym, qty, price, val in history_assets:
        cursor.execute('''
            INSERT OR REPLACE INTO asset_snapshots (date, symbol, quantity, price, total_value)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, sym, qty, price, val))
        
    conn.commit()
    conn.close()
    print(f"Seeded {days} days of data with asset details.")

if __name__ == "__main__":
    seed_data()
