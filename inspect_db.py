
import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect("data/inver.db")
    df = pd.read_sql("SELECT username, name, email, password_hash FROM users", conn)
    print("Users found in database:")
    print(df)
    conn.close()
except Exception as e:
    print(f"Error reading database: {e}")
