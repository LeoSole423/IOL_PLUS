import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

class PortfolioManager:
    def __init__(self, db_path="data/inver.db"):
        self.db_path = self._resolve_db_path(db_path)
        self._ensure_db_dir()
        self.init_db()

    def _resolve_db_path(self, db_path):
        if os.path.isabs(db_path):
            return db_path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(project_root, db_path)

    def _ensure_db_dir(self):
        """Ensures the data directory exists."""
        dirname = os.path.dirname(self.db_path)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)

    def init_db(self):
        """Creates the necessary tables if they don't exist and migrates schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if migration is needed (missing user_id in portfolio_snapshots)
        try:
            # We try to check if user_id exists by selecting it
            cursor.execute("SELECT user_id FROM portfolio_snapshots LIMIT 1")
        except sqlite3.OperationalError:
            # Column missing, we assume V1 schema. Migrate.
            print("Migrating DB schema to V2 (Multi-user)...")
            try:
                self._migrate_to_v2(cursor)
            except Exception as e:
                print(f"Migration failed: {e}")
        except sqlite3.DatabaseError:
             # Table might not exist yet
             pass
        
        # Standard creation (V2 schema)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                date TEXT,
                user_id TEXT,
                total_value REAL,
                invested_amount REAL,
                PRIMARY KEY (date, user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_snapshots (
                date TEXT,
                user_id TEXT,
                symbol TEXT,
                quantity REAL,
                price REAL,
                total_value REAL,
                PRIMARY KEY (date, symbol, user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_id TEXT,
                model TEXT,
                investment_amount REAL,
                portfolio_value REAL,
                response TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def _migrate_to_v2(self, cursor):
        """Migrates V1 tables to V2 (adding user_id and updating PKs)."""
        # 1. Portfolio Snapshots
        cursor.execute("ALTER TABLE portfolio_snapshots RENAME TO portfolio_snapshots_old")
        cursor.execute('''
            CREATE TABLE portfolio_snapshots (
                date TEXT,
                user_id TEXT,
                total_value REAL,
                invested_amount REAL,
                PRIMARY KEY (date, user_id)
            )
        ''')
        cursor.execute('''
            INSERT INTO portfolio_snapshots (date, user_id, total_value, invested_amount)
            SELECT date, 'admin', total_value, invested_amount FROM portfolio_snapshots_old
        ''')
        cursor.execute("DROP TABLE portfolio_snapshots_old")
        
        # 2. Asset Snapshots
        cursor.execute("ALTER TABLE asset_snapshots RENAME TO asset_snapshots_old")
        cursor.execute('''
            CREATE TABLE asset_snapshots (
                date TEXT,
                user_id TEXT,
                symbol TEXT,
                quantity REAL,
                price REAL,
                total_value REAL,
                PRIMARY KEY (date, symbol, user_id)
            )
        ''')
        cursor.execute('''
            INSERT INTO asset_snapshots (date, user_id, symbol, quantity, price, total_value)
            SELECT date, 'admin', symbol, quantity, price, total_value FROM asset_snapshots_old
        ''')
        cursor.execute("DROP TABLE asset_snapshots_old")
        
        # 3. AI Analyses (Just add column)
        try:
             cursor.execute("ALTER TABLE ai_analyses ADD COLUMN user_id TEXT DEFAULT 'admin'")
        except:
             pass 

    def save_daily_snapshot(self, total_value, assets_data=[], invested_amount=0.0, user_id='admin'):
        """Saves or updates the portfolio snapshot for the current day and user."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Save Total
        cursor.execute('''
            INSERT INTO portfolio_snapshots (date, user_id, total_value, invested_amount)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date, user_id) DO UPDATE SET
                total_value = excluded.total_value,
                invested_amount = excluded.invested_amount
        ''', (date_str, user_id, total_value, invested_amount))
        
        # 2. Save Assets
        for asset in assets_data:
            cursor.execute('''
                INSERT INTO asset_snapshots (date, user_id, symbol, quantity, price, total_value)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(date, symbol, user_id) DO UPDATE SET
                    quantity = excluded.quantity,
                    price = excluded.price,
                    total_value = excluded.total_value
            ''', (
                date_str, 
                user_id,
                asset.get("Symbol"), 
                asset.get("Quantity", 0), 
                asset.get("Last Price", 0), 
                asset.get("Total Value", 0)
            ))
        
        conn.commit()
        conn.close()

    def get_history(self, days=30, user_id='admin'):
        """Returns history for a specific user."""
        conn = sqlite3.connect(self.db_path)
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        query = "SELECT * FROM portfolio_snapshots WHERE date >= ? AND user_id = ? ORDER BY date ASC"
        df = pd.read_sql_query(query, conn, params=(start_date, user_id))
        conn.close()
        return df

    def calculate_gains(self, current_value, user_id='admin'):
        history = self.get_history(days=40, user_id=user_id)
        if history.empty:
            return {}
            
        def get_value_days_ago(n_days):
            target_date = (datetime.now() - timedelta(days=n_days)).strftime("%Y-%m-%d")
            mask = history['date'] <= target_date
            candidates = history[mask]
            if not candidates.empty:
                return candidates.iloc[-1]['total_value']
            return None

        prev_day_val = get_value_days_ago(1)
        prev_week_val = get_value_days_ago(7)
        prev_month_val = get_value_days_ago(30)
        
        result = {}
        if prev_day_val is not None:
            diff = current_value - prev_day_val
            pct = (diff / prev_day_val) * 100 if prev_day_val else 0
            result['daily'] = (diff, pct)
        if prev_week_val is not None:
            diff = current_value - prev_week_val
            pct = (diff / prev_week_val) * 100 if prev_week_val else 0
            result['weekly'] = (diff, pct)
        if prev_month_val is not None:
            diff = current_value - prev_month_val
            pct = (diff / prev_month_val) * 100 if prev_month_val else 0
            result['monthly'] = (diff, pct)
            
        return result

    def calculate_asset_gains(self, current_assets, user_id='admin'):
        enriched_assets = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for asset in current_assets:
            symbol = asset['Symbol']
            curr_val = asset['Total Value']
            new_asset = asset.copy()
            new_asset['Daily Gain'] = 0.0
            new_asset['Weekly Gain'] = 0.0
            new_asset['Monthly Gain'] = 0.0
            
            def get_hist_val(days_ago):
                target = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                cursor.execute('''
                    SELECT total_value FROM asset_snapshots 
                    WHERE symbol = ? AND user_id = ? AND date <= ? 
                    ORDER BY date DESC LIMIT 1
                ''', (symbol, user_id, target))
                res = cursor.fetchone()
                return res[0] if res else None

            val_1d = get_hist_val(1)
            val_7d = get_hist_val(7)
            val_30d = get_hist_val(30)
            
            if val_1d is not None: new_asset['Daily Gain'] = curr_val - val_1d
            if val_7d is not None: new_asset['Weekly Gain'] = curr_val - val_7d
            if val_30d is not None: new_asset['Monthly Gain'] = curr_val - val_30d
                
            enriched_assets.append(new_asset)
            
        conn.close()
        return enriched_assets

    def save_analysis(self, model, investment_amount, portfolio_value, response, user_id='admin'):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_analyses (timestamp, user_id, model, investment_amount, portfolio_value, response)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, user_id, model, investment_amount, portfolio_value, response))
        conn.commit()
        conn.close()
    
    def get_analyses(self, limit=10, user_id='admin'):
        conn = sqlite3.connect(self.db_path)
        query = "SELECT id, timestamp, model, investment_amount, portfolio_value, response FROM ai_analyses WHERE user_id = ? ORDER BY id DESC LIMIT ?"
        df = pd.read_sql_query(query, conn, params=(user_id, limit))
        conn.close()
        return df
