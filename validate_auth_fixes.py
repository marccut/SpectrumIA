#!/usr/bin/env python3
"""
Validation script to verify authentication fixes without running the app.
Checks code logic and session state handling.
"""

import re
import sys
from pathlib import Path

def check_file_contains(filepath, pattern, description):
    """Check if file contains a pattern"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                print(f"  ✅ {description}")
                return True
            else:
                print(f"  ❌ {description}")
                return False
    except FileNotFoundError:
        print(f"  ❌ File not found: {filepath}")
        return False

def check_login_page():
    """Verify login page stores both user_data and user_id"""
    print("\n🔍 Check 1: Login Page Session Storage")
    print("-" * 50)

    filepath = Path("app/pages/1_login.py")

    results = [
        check_file_contains(
            filepath,
            r"st\.session_state\.user_data\s*=\s*user_data",
            "Stores user_data on successful login"
        ),
        check_file_contains(
            filepath,
            r'st\.session_state\.user_id\s*=\s*user_data\.get\("id"\)',
            "Stores user_id extracted from user_data"
        ),
        check_file_contains(
            filepath,
            r'st\.session_state\.user_id\s*=\s*None',
            "Clears user_id on logout"
        ),
    ]

    return all(results)

def check_main_page():
    """Verify main page clears user_id on logout"""
    print("\n🔍 Check 2: Main Page Logout Handler")
    print("-" * 50)

    filepath = Path("app/main.py")

    results = [
        check_file_contains(
            filepath,
            r'st\.session_state\.user_id\s*=\s*None',
            "Clears user_id on logout in sidebar"
        ),
    ]

    return all(results)

def check_protected_pages():
    """Verify protected pages look for user_id in session"""
    print("\n🔍 Check 3: Protected Pages Authentication")
    print("-" * 50)

    pages = [
        ("app/pages/2_calibration.py", "Calibration"),
        ("app/pages/3_assessment.py", "Assessment"),
        ("app/pages/4_results.py", "Results"),
    ]

    results = []
    for filepath, page_name in pages:
        result = check_file_contains(
            filepath,
            r'if\s+"user_id"\s+not\s+in\s+st\.session_state',
            f"{page_name} page checks for user_id"
        )
        results.append(result)

    return all(results)

def check_auth_module():
    """Verify auth module has improved demo mode detection"""
    print("\n🔍 Check 4: Auth Module Demo Mode Fallback")
    print("-" * 50)

    filepath = Path("core/auth.py")

    results = [
        check_file_contains(
            filepath,
            r'is_placeholder\s*=\s*\(',
            "Detects placeholder credentials"
        ),
        check_file_contains(
            filepath,
            r'"seu-projeto"\s+in\s+SUPABASE_URL',
            "Checks for Portuguese placeholder"
        ),
        check_file_contains(
            filepath,
            r'if\s+SUPABASE_URL\s+and\s+SUPABASE_KEY\s+and\s+not\s+is_placeholder',
            "Only creates client for valid credentials"
        ),
        check_file_contains(
            filepath,
            r'except\s+Exception\s+as\s+e.*?self\.client\s*=\s*None',
            "Falls back to demo mode on exception"
        ),
    ]

    return all(results)

def check_registration():
    """Verify registration works in demo mode"""
    print("\n🔍 Check 5: Registration Flow")
    print("-" * 50)

    filepath = Path("core/auth.py")

    results = [
        check_file_contains(
            filepath,
            r'def\s+register\(.*?\)',
            "Register method exists"
        ),
        check_file_contains(
            filepath,
            r'if\s+not\s+self\.client:.*?return\s+True',
            "Demo mode registration returns success"
        ),
    ]

    return all(results)

def check_session_consistency():
    """Verify all pages use consistent session state keys"""
    print("\n🔍 Check 6: Session State Consistency")
    print("-" * 50)

    files = [
        "app/pages/1_login.py",
        "app/main.py",
        "app/pages/2_calibration.py",
        "app/pages/3_assessment.py",
        "app/pages/4_results.py",
    ]

    user_data_count = 0
    user_id_count = 0

    for filepath in files:
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                user_data_count += len(re.findall(r'st\.session_state\.user_data', content))
                user_id_count += len(re.findall(r'st\.session_state\.user_id', content))
        except FileNotFoundError:
            pass

    print(f"  user_data references: {user_data_count}")
    print(f"  user_id references: {user_id_count}")

    if user_id_count >= 5:  # At least login, logout, and 3 protected pages
        print(f"  ✅ All pages consistently use user_id")
        return True
    else:
        print(f"  ❌ Missing user_id references")
        return False

def main():
    """Run all validation checks"""
    print("\n" + "="*50)
    print("SpectrumIA Authentication Fixes Validation")
    print("="*50)

    results = [
        ("Login Page Storage", check_login_page()),
        ("Main Page Logout", check_main_page()),
        ("Protected Pages", check_protected_pages()),
        ("Auth Module Demo Mode", check_auth_module()),
        ("Registration Flow", check_registration()),
        ("Session Consistency", check_session_consistency()),
    ]

    # Summary
    print("\n" + "="*50)
    print("Validation Summary")
    print("="*50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All validation checks passed!")
        print("\n📝 Next Steps:")
        print("  1. Run: streamlit run app/main.py")
        print("  2. Login with: demo@spectrumia.com / demo123")
        print("  3. Try registering a new account")
        print("  4. Navigate between pages (Calibration, Assessment, Results)")
        print("  5. Session should persist across navigation")
        return 0
    else:
        print(f"\n⚠️ {total - passed} validation check(s) failed.")
        return 1

if __name__ == "__main__":
    exit(main())
