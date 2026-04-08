#!/usr/bin/env python3
"""
Test script to verify authentication fixes work correctly.
Tests session state management and registration flow.
"""

import sys
from pathlib import Path
import hashlib

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.auth import SpectrumIAAuth

def test_demo_mode_login():
    """Test demo mode login with correct credentials"""
    print("\n🧪 Test 1: Demo Mode Login")
    print("-" * 50)

    auth = SpectrumIAAuth()

    # Test valid demo login
    success, message, user_data = auth.login("demo@spectrumia.com", "demo123")

    print(f"  Email: demo@spectrumia.com")
    print(f"  Password: demo123")
    print(f"  Result: {success}")
    print(f"  Message: {message}")

    if success:
        print(f"  User ID: {user_data.get('id')}")
        print(f"  Email: {user_data.get('email')}")
        print(f"  ✅ PASSED")
        return user_data
    else:
        print(f"  ❌ FAILED")
        return None

def test_invalid_login():
    """Test invalid login"""
    print("\n🧪 Test 2: Invalid Login")
    print("-" * 50)

    auth = SpectrumIAAuth()

    success, message, user_data = auth.login("wrong@example.com", "wrongpass")

    print(f"  Email: wrong@example.com")
    print(f"  Password: wrongpass")
    print(f"  Result: {success}")
    print(f"  Message: {message}")

    if not success:
        print(f"  ✅ PASSED (correctly rejected)")
        return True
    else:
        print(f"  ❌ FAILED (should have been rejected)")
        return False

def test_registration():
    """Test registration in demo mode"""
    print("\n🧪 Test 3: New Account Registration")
    print("-" * 50)

    auth = SpectrumIAAuth()

    test_email = "newuser@spectrumia.test"
    test_password = "TestPassword123"
    test_name = "Test User"
    test_role = "patient"

    success, message, user_data = auth.register(
        email=test_email,
        password=test_password,
        name=test_name,
        role=test_role
    )

    print(f"  Email: {test_email}")
    print(f"  Password: {test_password}")
    print(f"  Name: {test_name}")
    print(f"  Role: {test_role}")
    print(f"  Result: {success}")
    print(f"  Message: {message}")

    if success:
        print(f"  Returned User Data:")
        print(f"    - Email: {user_data.get('email')}")
        print(f"    - Name: {user_data.get('name')}")
        print(f"    - Role: {user_data.get('role')}")
        print(f"  ✅ PASSED")
        return True
    else:
        print(f"  ❌ FAILED")
        return False

def test_invalid_registration():
    """Test registration with invalid email"""
    print("\n🧪 Test 4: Invalid Email Registration")
    print("-" * 50)

    auth = SpectrumIAAuth()

    success, message, user_data = auth.register(
        email="invalid-email",  # No @
        password="TestPassword123",
        name="Test User"
    )

    print(f"  Email: invalid-email (no @)")
    print(f"  Result: {success}")
    print(f"  Message: {message}")

    if not success and "Invalid email" in message:
        print(f"  ✅ PASSED (correctly rejected)")
        return True
    else:
        print(f"  ❌ FAILED")
        return False

def test_short_password_registration():
    """Test registration with password too short"""
    print("\n🧪 Test 5: Short Password Registration")
    print("-" * 50)

    auth = SpectrumIAAuth()

    success, message, user_data = auth.register(
        email="test@example.com",
        password="123",  # Only 3 chars, needs 6
        name="Test User"
    )

    print(f"  Email: test@example.com")
    print(f"  Password: 123 (too short)")
    print(f"  Result: {success}")
    print(f"  Message: {message}")

    if not success and "6 characters" in message:
        print(f"  ✅ PASSED (correctly rejected)")
        return True
    else:
        print(f"  ❌ FAILED")
        return False

def test_session_state_extraction():
    """Test that user_id can be extracted from user_data"""
    print("\n🧪 Test 6: Session State Extraction")
    print("-" * 50)

    auth = SpectrumIAAuth()

    # Login
    success, message, user_data = auth.login("demo@spectrumia.com", "demo123")

    if success:
        # Extract user_id like the login page does
        user_id = user_data.get("id")
        user_email = user_data.get("email")

        print(f"  Original user_data: {user_data}")
        print(f"  Extracted user_id: {user_id}")
        print(f"  Extracted email: {user_email}")

        if user_id and user_email:
            print(f"  ✅ PASSED")
            return True
        else:
            print(f"  ❌ FAILED (couldn't extract user_id)")
            return False
    else:
        print(f"  ❌ FAILED (login failed)")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("SpectrumIA Authentication Tests")
    print("="*50)

    results = []

    # Run tests
    user_data = test_demo_mode_login()
    results.append(("Demo Mode Login", user_data is not None))

    results.append(("Invalid Login", test_invalid_login()))
    results.append(("Registration", test_registration()))
    results.append(("Invalid Email", test_invalid_registration()))
    results.append(("Short Password", test_short_password_registration()))
    results.append(("Session Extraction", test_session_state_extraction()))

    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Authentication system is working correctly.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    exit(main())
