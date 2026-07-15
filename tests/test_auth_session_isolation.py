"""Tests for per-session authentication and JWT isolation."""

from unittest.mock import patch

import core.auth as auth_module


def test_get_auth_is_reused_only_within_same_streamlit_session():
    """Different Streamlit sessions must not share one Supabase auth client."""
    session_a = {}
    session_b = {}

    with patch.object(auth_module.SpectrumIAAuth, "_initialize_client"):
        with patch.object(auth_module.st, "session_state", session_a):
            auth_a = auth_module.get_auth()
            assert auth_module.get_auth() is auth_a

        with patch.object(auth_module.st, "session_state", session_b):
            auth_b = auth_module.get_auth()

    assert auth_b is not auth_a


def test_get_access_token_reads_only_current_streamlit_session():
    """The database JWT comes from the active user's session state."""
    with patch.object(
        auth_module.st,
        "session_state",
        {"user_data": {"session": "jwt-current-user"}},
    ):
        assert auth_module.get_access_token() == "jwt-current-user"

    with patch.object(auth_module.st, "session_state", {"user_data": None}):
        assert auth_module.get_access_token() is None

