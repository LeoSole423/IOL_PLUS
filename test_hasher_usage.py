
import streamlit_authenticator as stauth

try:
    print("Trying stauth.Hasher.hash('admin123')...")
    hashed = stauth.Hasher.hash('admin123')
    print(f"Success! Hash: {hashed}")
except Exception as e:
    print(f"Failed: {e}")

try:
    print("\nTrying instance method: h = stauth.Hasher(); h.hash('admin123')...")
    h = stauth.Hasher()
    # It seems from help() that hash is a class method, but let's check if it's available on instance too or if I misinterpreted.
    # The help said "Class methods defined here", so it should be called on the class.
except Exception as e:
    print(f"Instance init failed: {e}")
