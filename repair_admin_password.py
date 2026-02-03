
import sqlite3
import streamlit_authenticator as stauth
import sys

# Define the new password
NEW_PASSWORD = "admin123"

print(f"Attempting to reset admin password to: '{NEW_PASSWORD}'")

try:
    # 1. Generate hash using the correct API for this version
    print("Generating hash...")
    hashed_pw = stauth.Hasher.hash(NEW_PASSWORD)
    print(f"Hash generated successfully: {hashed_pw[:10]}...")

    # 2. Update DB
    db_path = "data/inver.db"
    print(f"Updating database at {db_path}...")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("UPDATE users SET password_hash=? WHERE username='admin'", (hashed_pw,))
    
    if c.rowcount == 0:
        print("Error: User 'admin' not found in database.")
    else:
        print("Success: Admin password updated.")
        
    conn.commit()
    conn.close()

except Exception as e:
    print(f"Critical Error: {e}")
