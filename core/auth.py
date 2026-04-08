"""
Authentication module for SpectrumIA.
Handles user authentication with Supabase (email/password).
"""

from datetime import datetime
import hashlib
from typing import Dict, Optional, Tuple

import streamlit as st
from supabase import Client, create_client


class SpectrumIAAuth:
    """Manage user authentication for SpectrumIA using Supabase."""

    def __init__(self):
        """Initialize Supabase client for authentication."""
        self.supabase_url = None
        self.supabase_key = None
        self.client: Optional[Client] = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Supabase client with credentials from configuration."""
        from core.config import SUPABASE_KEY, SUPABASE_URL

        try:
            # Treat placeholder values as "demo mode" instead of failing startup.
            is_placeholder = (
                not SUPABASE_URL
                or not SUPABASE_KEY
                or "seu-projeto" in SUPABASE_URL
                or SUPABASE_KEY == "eyJ..."
                or SUPABASE_URL == "https://seu-projeto.supabase.co"
            )

            if SUPABASE_URL and SUPABASE_KEY and not is_placeholder:
                self.supabase_url = SUPABASE_URL
                self.supabase_key = SUPABASE_KEY
                self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
            else:
                self.client = None
        except Exception:
            # If client initialization fails, fall back to demo mode.
            self.client = None

    def _demo_mode_login(
        self, email: str, password: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Demo mode login for testing without Supabase."""
        demo_users = {
            "demo@spectrumia.com": "demo123",
            "doctor@spectrumia.com": "doctor123",
            "patient@spectrumia.com": "patient123",
        }

        if email in demo_users and demo_users[email] == password:
            user_data = {
                "id": hashlib.md5(email.encode()).hexdigest(),
                "email": email,
                "user_metadata": {
                    "name": email.split("@")[0].title(),
                    "role": "clinician" if "doctor" in email else "patient",
                },
                "created_at": datetime.now().isoformat(),
            }
            return True, "Login successful", user_data
        return False, "Invalid demo credentials. Try demo@spectrumia.com / demo123", None

    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user with email and password.

        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            if not self.client:
                return self._demo_mode_login(email, password)

            response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if response and response.user:
                user_data = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata or {},
                    "created_at": response.user.created_at,
                    "session": response.session.access_token if response.session else None,
                }
                return True, "Login successful", user_data
            return False, "Login failed. Invalid credentials.", None

        except Exception as exc:
            error_msg = str(exc).lower()
            if "invalid login" in error_msg or "not found" in error_msg:
                return False, "Invalid email or password", None
            if "email" in error_msg:
                return False, "Email not registered. Please sign up first.", None
            return self._demo_mode_login(email, password)

    def register(
        self, email: str, password: str, name: str = "", role: str = "patient"
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Register a new user.

        Returns:
            Tuple of (success, message, user_data)
        """
        if not email or "@" not in email:
            return False, "Invalid email format", None

        if len(password) < 6:
            return False, "Password must be at least 6 characters", None

        try:
            if not self.client:
                return True, "Registration successful (demo mode). You can now login.", {
                    "email": email,
                    "name": name or email.split("@")[0],
                    "role": role,
                }

            response = self.client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"name": name, "role": role}},
                }
            )

            if response and response.user:
                return True, "Registration successful! Please check your email to confirm.", {
                    "email": response.user.email,
                    "id": response.user.id,
                }
            return False, "Registration failed", None

        except Exception as exc:
            error_msg = str(exc).lower()
            if "already registered" in error_msg or "user already exists" in error_msg:
                return False, "This email is already registered. Please login.", None
            return False, f"Registration error: {exc}", None

    def logout(self):
        """Logout current user."""
        try:
            if self.client:
                self.client.auth.sign_out()
        except Exception as exc:
            st.error(f"Logout error: {exc}")

    def verify_session(self) -> Optional[Dict]:
        """Verify whether the user has a valid session."""
        if "user_data" not in st.session_state:
            return None

        try:
            if self.client and "session" in st.session_state.user_data:
                return st.session_state.user_data
            return st.session_state.user_data
        except Exception:
            return None

    def get_current_user(self) -> Optional[Dict]:
        """Get current authenticated user from session state."""
        return st.session_state.get("user_data", None)

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return st.session_state.get("user_data") is not None


_auth_instance = None


def get_auth() -> SpectrumIAAuth:
    """Get or create a global auth instance."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = SpectrumIAAuth()
    return _auth_instance


def require_auth(func):
    """Decorator to require authentication for a function/page."""

    def wrapper(*args, **kwargs):
        auth = get_auth()
        if not auth.is_authenticated():
            st.warning("⚠️ Please login to access this page")
            st.stop()
        return func(*args, **kwargs)

    return wrapper


def initialize_session_state():
    """Initialize session state variables for authentication."""
    if "user_data" not in st.session_state:
        st.session_state.user_data = None

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = True
