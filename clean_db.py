import sqlite3
from datetime import datetime

db_path = "data/inver.db"
today = datetime.now().strftime("%Y-%m-%d")

print(f"Cleaning database {db_path}...")
print(f"Keeping only data for today: {today}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get count before
cursor.execute("SELECT count(*) FROM portfolio_snapshots")
count_snapshots = cursor.fetchone()[0]
cursor.execute("SELECT count(*) FROM asset_snapshots")
count_assets = cursor.fetchone()[0]
cursor.execute("SELECT count(*) FROM ai_analyses")
count_ai = cursor.fetchone()[0]

print(f"Before: {count_snapshots} snapshots, {count_assets} asset records, {count_ai} analyses")

# Delete old data
cursor.execute("DELETE FROM portfolio_snapshots WHERE date < ?", (today,))
cursor.execute("DELETE FROM asset_snapshots WHERE date < ?", (today,))

# Also likely want to keep recent AI analyses? The user said "elimina los datos de la base de datos que fueron inventados". 
# Usually AI analyses are history, maybe keep them? 
# "deja solo los de hoy" implies deleting everything old.
# Let's delete old AI analyses too to be safe, or maybe just portfolio data?
# User said "datos de la base de datos... deja solo los de hoy".
# I acts on everything.
current_ts = datetime.now().strftime("%Y-%m-%d 00:00:00")
# ai_analyses uses timestamp "YYYY-MM-DD HH:MM:SS"
cursor.execute("DELETE FROM ai_analyses WHERE timestamp < ?", (current_ts,))

conn.commit()

# Get count after
cursor.execute("SELECT count(*) FROM portfolio_snapshots")
after_snapshots = cursor.fetchone()[0]
cursor.execute("SELECT count(*) FROM asset_snapshots")
after_assets = cursor.fetchone()[0]
cursor.execute("SELECT count(*) FROM ai_analyses")
after_ai = cursor.fetchone()[0]

print(f"After: {after_snapshots} snapshots, {after_assets} asset records, {after_ai} analyses")

conn.close()
print("Done.")
