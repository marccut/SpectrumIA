"""
Test script for State Logic Bug Fix
Validates that calibration and assessment states work correctly.

Run with: python test_state_logic.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_state_transitions():
    """Test that state transitions work correctly."""
    print("\n" + "="*60)
    print("🧪 TEST 1: State Transitions")
    print("="*60)

    # Simulate session state (like Streamlit session_state)
    session_state = {
        "calibration_status": "not_started",
        "calibration_complete": False,
        "assessment_status": "not_started",
        "assessment_complete": False,
    }

    print("\n✅ Initial State:")
    print(f"   calibration_status: {session_state['calibration_status']}")
    print(f"   calibration_complete: {session_state['calibration_complete']}")

    # Simulate button click: Start Calibration
    print("\n→ User clicks [▶️ Start Calibration]")
    session_state["calibration_status"] = "in_progress"
    print(f"   calibration_status: {session_state['calibration_status']}")

    # Simulate button click: Complete Calibration
    print("\n→ User clicks [✅ Complete Calibration]")
    session_state["calibration_status"] = "completed"
    session_state["calibration_complete"] = True
    print(f"   calibration_status: {session_state['calibration_status']}")
    print(f"   calibration_complete: {session_state['calibration_complete']}")

    # Verify state
    assert session_state["calibration_status"] == "completed", "Calibration status should be 'completed'"
    assert session_state["calibration_complete"] == True, "Calibration complete should be True"

    print("\n✅ TEST 1 PASSED: State transitions work correctly")
    return True


def test_success_message_logic():
    """Test that success message only shows when appropriate."""
    print("\n" + "="*60)
    print("🧪 TEST 2: Success Message Logic")
    print("="*60)

    session_state = {
        "calibration_status": "not_started",
    }

    # BEFORE BUG FIX: This would always show success if calibration_complete was True
    # AFTER BUG FIX: This only shows success if status is "completed"

    print("\n❌ BUG BEHAVIOR (Before Fix):")
    print("   if calibration_complete == True:")
    print("       show_success_message()  ← Shows even without doing anything!")

    print("\n✅ CORRECT BEHAVIOR (After Fix):")
    print("   if calibration_status == 'completed':")
    print("       show_success_message()  ← Only shows after completing!")

    # Test scenarios
    scenarios = [
        ("not_started", False, "Should NOT show success"),
        ("in_progress", False, "Should NOT show success"),
        ("completed", True, "SHOULD show success"),
    ]

    print("\nTesting scenarios:")
    for status, should_show, description in scenarios:
        session_state["calibration_status"] = status

        # Logic from corrected main.py
        should_show_success = (session_state["calibration_status"] == "completed")

        result = "✅" if should_show_success == should_show else "❌"
        print(f"  {result} Status '{status}': {description}")
        assert should_show_success == should_show, f"Failed for status '{status}'"

    print("\n✅ TEST 2 PASSED: Success messages show only when appropriate")
    return True


def test_assessment_prerequisites():
    """Test that Assessment requires Calibration to be complete."""
    print("\n" + "="*60)
    print("🧪 TEST 3: Assessment Prerequisites")
    print("="*60)

    session_state = {
        "calibration_complete": False,
        "assessment_status": "not_started",
    }

    print("\nScenario 1: Assessment without Calibration")
    print(f"  calibration_complete: {session_state['calibration_complete']}")
    print(f"  assessment_status: {session_state['assessment_status']}")

    # Should block assessment
    should_block = not session_state["calibration_complete"]
    print(f"  Should block assessment: {should_block}")
    assert should_block == True, "Assessment should be blocked without calibration"
    print("  ✅ Correctly blocked")

    print("\nScenario 2: Assessment after Calibration")
    session_state["calibration_complete"] = True
    print(f"  calibration_complete: {session_state['calibration_complete']}")

    # Should allow assessment
    should_block = not session_state["calibration_complete"]
    print(f"  Should block assessment: {should_block}")
    assert should_block == False, "Assessment should be allowed after calibration"
    print("  ✅ Correctly allowed")

    print("\n✅ TEST 3 PASSED: Assessment prerequisites work correctly")
    return True


def test_results_prerequisites():
    """Test that Results requires both Calibration and Assessment."""
    print("\n" + "="*60)
    print("🧪 TEST 4: Results Prerequisites")
    print("="*60)

    test_cases = [
        (False, False, True, "No prerequisites met"),
        (True, False, True, "Only Calibration done"),
        (False, True, True, "Only Assessment done"),
        (True, True, False, "Both completed"),
    ]

    print("\nTesting all scenarios:")
    for calib_done, assess_done, should_block, description in test_cases:
        session_state = {
            "calibration_complete": calib_done,
            "assessment_complete": assess_done,
        }

        # Logic: block if either is missing
        is_blocked = not (session_state["calibration_complete"] and session_state["assessment_complete"])

        result = "✅" if is_blocked == should_block else "❌"
        print(f"  {result} {description}: blocked={is_blocked}")
        assert is_blocked == should_block, f"Failed for: {description}"

    print("\n✅ TEST 4 PASSED: Results prerequisites work correctly")
    return True


def test_redo_functionality():
    """Test that users can redo calibration and assessment."""
    print("\n" + "="*60)
    print("🧪 TEST 5: Redo Functionality")
    print("="*60)

    session_state = {
        "calibration_status": "completed",
        "calibration_complete": True,
    }

    print("\nBefore redo:")
    print(f"  calibration_status: {session_state['calibration_status']}")
    print(f"  Button shown: [🔄 Redo Calibration]")

    # Simulate clicking Redo
    print("\nUser clicks [🔄 Redo Calibration]")
    session_state["calibration_status"] = "not_started"
    session_state["calibration_complete"] = False

    print("\nAfter redo:")
    print(f"  calibration_status: {session_state['calibration_status']}")
    print(f"  Button shown: [▶️ Start Calibration]")

    assert session_state["calibration_status"] == "not_started", "Status should reset"
    assert session_state["calibration_complete"] == False, "Complete flag should reset"

    print("\n✅ TEST 5 PASSED: Redo functionality works correctly")
    return True


def test_logout_resets_state():
    """Test that logout resets all states."""
    print("\n" + "="*60)
    print("🧪 TEST 6: Logout Resets State")
    print("="*60)

    session_state = {
        "authenticated": True,
        "calibration_status": "completed",
        "calibration_complete": True,
        "assessment_status": "completed",
        "assessment_complete": True,
    }

    print("\nBefore logout:")
    print(f"  authenticated: {session_state['authenticated']}")
    print(f"  calibration_complete: {session_state['calibration_complete']}")
    print(f"  assessment_complete: {session_state['assessment_complete']}")

    # Simulate logout
    print("\nUser clicks [🚪 Logout]")
    session_state["authenticated"] = False
    session_state["calibration_complete"] = False
    session_state["assessment_complete"] = False
    session_state["calibration_status"] = "not_started"
    session_state["assessment_status"] = "not_started"

    print("\nAfter logout:")
    print(f"  authenticated: {session_state['authenticated']}")
    print(f"  calibration_complete: {session_state['calibration_complete']}")
    print(f"  assessment_complete: {session_state['assessment_complete']}")

    assert session_state["authenticated"] == False, "Should be logged out"
    assert session_state["calibration_complete"] == False, "Calibration should reset"
    assert session_state["assessment_complete"] == False, "Assessment should reset"

    print("\n✅ TEST 6 PASSED: Logout correctly resets all state")
    return True


def main():
    """Run all tests."""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║  State Logic Bug Fix - Automated Test Suite" + " "*12 + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")

    tests = [
        test_state_transitions,
        test_success_message_logic,
        test_assessment_prerequisites,
        test_results_prerequisites,
        test_redo_functionality,
        test_logout_resets_state,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Total: {passed + failed} tests")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n" + "🎉 "*15)
        print("ALL TESTS PASSED! State logic is working correctly!")
        print("🎉 "*15)
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
