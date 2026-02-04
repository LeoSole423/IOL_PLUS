import sqlite3
import os
import streamlit_authenticator as stauth
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

class AuthManager:
    def __init__(self, db_path="data/inver.db"):
        self.db_path = self._resolve_db_path(db_path)
        self._ensure_db_dir()
        self._key = os.getenv("ENCRYPTION_KEY")
        if not self._key:
            # Generate a key if missing (fallback for dev, but better to enforce env)
            # In live, we might want to warn.
            print("WARNING: ENCRYPTION_KEY not found. Helper functions will fail.")
            self.cipher = None
        else:
            self.cipher = Fernet(self._key)
            
        self.cookie_key = os.getenv("COOKIE_KEY", "random_default_123")
        self._init_users_table()

    def _resolve_db_path(self, db_path):
        if os.path.isabs(db_path):
            return db_path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(project_root, db_path)

    def _ensure_db_dir(self):
        dirname = os.path.dirname(self.db_path)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        
    def _init_users_table(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                password_hash TEXT,
                gemini_key_enc TEXT,
                iol_user_enc TEXT,
                iol_pass_enc TEXT
            )
        ''')
        # Check if we need to create default admin
        c.execute("SELECT count(*) FROM users")
        if c.fetchone()[0] == 0:
            self.create_default_admin(c)
            
        conn.commit()
        conn.close()

    def create_default_admin(self, cursor):
        """Creates a default admin user migrating current .env credentials"""
        print("Creating default admin user...")
        # Default pass: admin123
        try:
            # New API for streamlit-authenticator > 0.3.0
            hashed_pw = stauth.Hasher.hash("admin123")
        except Exception as e:
            print(f"Primary hashing method failed: {e}. Trying legacy method...")
            try:
                # Legacy API check
                hasher = stauth.Hasher(["admin123"])
                hashed_pw = hasher.generate()[0]
            except Exception as e2:
                print(f"Error hashing password: {e2}")
                hashed_pw = "$2b$12$DEFAULT_HASH_IF_FAILED_TO_GEN" # Fallback, should not happen

        # Get env vars to migrate
        gemini = os.getenv("GEMINI_API_KEY", "")
        iol_u = os.getenv("IOL_USERNAME", "")
        iol_p = os.getenv("IOL_PASSWORD", "")
        
        # Encrypt
        gemini_enc = self.encrypt(gemini) if gemini else None
        iol_u_enc = self.encrypt(iol_u) if iol_u else None
        iol_p_enc = self.encrypt(iol_p) if iol_p else None
        
        cursor.execute('''
            INSERT INTO users (username, name, email, password_hash, gemini_key_enc, iol_user_enc, iol_pass_enc)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ("admin", "Administrator", "admin@inver.app", hashed_pw, gemini_enc, iol_u_enc, iol_p_enc))

    def encrypt(self, text):
        if not text or not self.cipher: return None
        return self.cipher.encrypt(text.encode()).decode()

    def decrypt(self, text):
        if not text or not self.cipher: return None
        try:
            return self.cipher.decrypt(text.encode()).decode()
        except:
            return None

    def get_authenticator(self):
        """Returns the Authenticator object populated with DB users."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql("SELECT * FROM users", conn)
        conn.close()
        
        credentials = {"usernames": {}}
        for _, row in df.iterrows():
            credentials["usernames"][row['username']] = {
                "name": row['name'],
                "email": row['email'],
                "password": row['password_hash']
            }
            
        return stauth.Authenticate(
            credentials,
            "inver_cookie",
            self.cookie_key,
            cookie_expiry_days=30
        )
        
    def get_user_keys(self, username):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT gemini_key_enc, iol_user_enc, iol_pass_enc FROM users WHERE username=? COLLATE NOCASE", (username,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "gemini": self.decrypt(row[0]),
                "iol_user": self.decrypt(row[1]),
                "iol_pass": self.decrypt(row[2])
            }
        return {}

    def update_user_keys(self, username, gemini=None, iol_user=None, iol_pass=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if gemini is not None:
            enc = self.encrypt(gemini)
            c.execute("UPDATE users SET gemini_key_enc=? WHERE username=? COLLATE NOCASE", (enc, username))
        
        if iol_user is not None:
            enc = self.encrypt(iol_user)
            c.execute("UPDATE users SET iol_user_enc=? WHERE username=? COLLATE NOCASE", (enc, username))
            
        if iol_pass is not None:
            enc = self.encrypt(iol_pass)
            c.execute("UPDATE users SET iol_pass_enc=? WHERE username=? COLLATE NOCASE", (enc, username))
            
        conn.commit()
        conn.close()

    def user_exists(self, username):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT 1 FROM users WHERE username=? COLLATE NOCASE", (username,))
        exists = c.fetchone() is not None
        conn.close()
        return exists

    def register_user(self, username, name, email, password):
        if self.user_exists(username):
            return False, "Username already exists"

        try:
            # Hash password (using the fixed API)
            hashed_pw = stauth.Hasher.hash(password)
        except Exception as e:
            # Fallback for safety, though unlikely now
            try:
                hasher = stauth.Hasher([password])
                hashed_pw = hasher.generate()[0]
            except:
                return False, f"Error hashing password: {e}"

        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT INTO users (username, name, email, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (username, name, email, hashed_pw))
            conn.commit()
            conn.close()
            return True, "User created successfully"
        except Exception as e:
            return False, f"Database error: {e}"
