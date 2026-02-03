
import inspect
import streamlit_authenticator as stauth

print("Streamlit Authenticator version:", getattr(stauth, "__version__", "unknown"))
print("\nHasher init signature:")
try:
    print(inspect.signature(stauth.Hasher.__init__))
except Exception as e:
    print(f"Could not get signature: {e}")

print("\nHasher help:")
help(stauth.Hasher)
