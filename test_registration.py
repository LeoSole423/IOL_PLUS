#!/usr/bin/env python3
"""Test script to verify registration functionality"""
import sys
sys.path.insert(0, 'src')

from auth_manager import AuthManager

def test_registration():
    auth = AuthManager()
    
    # Test user creation
    print("Testing user registration...")
    success, message = auth.register_user("testuser", "Test User", "test@example.com", "password123")
    print(f"Result: {success}, Message: {message}")
    
    # Test duplicate username
    print("\nTesting duplicate username...")
    success2, message2 = auth.register_user("testuser", "Another User", "another@example.com", "password456")
    print(f"Result: {success2}, Message: {message2}")
    
    # Check if user exists
    print("\nChecking if 'testuser' exists...")
    exists = auth.user_exists("testuser")
    print(f"User exists: {exists}")
    
    print("\nChecking if 'nonexistent' exists...")
    exists2 = auth.user_exists("nonexistent")
    print(f"User exists: {exists2}")

if __name__ == "__main__":
    test_registration()
