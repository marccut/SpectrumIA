"""
Authentication module for SpectrumIA
Handles user authentication with Supabase (email/password)

Security notes:
- Demo mode is only active when DEMO_MODE_ENABLED=true in environment.
  It is NEVER activated automatically as a fallback on errors.
- Session validation checks token expiry locally and refreshes via Supabase
  when needed — prevents stale/forged sessions from being accepted.
- Logout clears both Supabase server-side session and local session state.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Tuple

import streamlit as st
from supabase import create_client, Client

logger = logging.getLogger(__name__)

_AUTH_INSTANCE_KEY = "_spectrumia_auth_instance"


def _is_demo_mode_enabled() -> bool:
    """Return True only when DEMO_MODE_ENABLED=true is explicitly set in env."""
    from core.config import DEMO_MODE_ENABLED
    return DEMO_MODE_ENABLED


def _clear_session() -> None:
    """Remove all auth-related keys from Streamlit session state."""
    for key in ("user_data", "auth_mode", "session_initialized", _AUTH_INSTANCE_KEY):
        st.session_state.pop(key, None)


class SpectrumIAAuth:
    """Manages user authentication for SpectrumIA using Supabase.

    Lifecycle:
        1. _initialize_client() -> creates Supabase client if credentials are
           valid. Falls back to demo-only mode when explicitly configured.
        2. login() / register() -> interact with Supabase Auth (or demo stub).
        3. verify_session() -> validates token expiry; refreshes when possible.
        4. logout() -> invalidates server session AND clears local state.
    """

    def __init__(self):
        self.supabase_url: Optional[str] = None
        self.supabase_key: Optional[str] = None
        self.client: Optional[Client] = None
        self._demo_mode: bool = False
        self._initialize_client()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _initialize_client(self) -> None:
        """Create Supabase client from environment credentials.

        Sets self._demo_mode = True ONLY when Supabase is not configured AND
        DEMO_MODE_ENABLED=true. Never activates demo mode silently on errors.
        """
        from core.config import SUPABASE_URL, SUPABASE_KEY

        is_placeholder = (
            not SUPABASE_URL
            or not SUPABASE_KEY
            or "seu-projeto" in SUPABASE_URL
            or "supabase.com/dashboard" in SUPABASE_URL
            or len(SUPABASE_KEY) < 20
        )

        if not is_placeholder:
            try:
                self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
                self.supabase_url = SUPABASE_URL
                self.supabase_key = SUPABASE_KEY
                logger.info("Supabase auth client initialised (production mode)")
            except Exception as exc:
                # Log prominently — do NOT silently enable demo mode.
                logger.error(
                    "Failed to initialise Supabase auth client: %s. "
                    "Authentication will be unavailable until this is resolved.",
                    exc,
                )
                self.client = None
        else:
            if _is_demo_mode_enabled():
                self._demo_mode = True
                logger.warning(
                    "Supabase credentials not configured. "
                    "Running in DEMO MODE (DEMO_MODE_ENABLED=true). "
                    "Do NOT use this in production."
                )
            else:
                logger.error(
                    "Supabase credentials are missing or look like placeholders. "
                    "Set SUPABASE_URL and SUPABASE_KEY in your .env file. "
                    "To enable demo mode for local development, also set DEMO_MODE_ENABLED=true."
                )
            self.client = None

    # ------------------------------------------------------------------
    # Demo mode stub
    # ------------------------------------------------------------------

    _DEMO_USERS: Dict[str, str] = {
        "demo@spectrumia.com":    "demo123",
        "doctor@spectrumia.com":  "doctor123",
        "patient@spectrumia.com": "patient123",
    }

    @staticmethod
    def _stable_demo_uuid(email: str) -> str:
        """Return a deterministic UUID for a demo account (based on email hash).

        Using a stable UUID means the demo user is always the same across
        logins, so the public.users FK constraint is satisfied after the first
        upsert.
        """
        import hashlib
        hex_digest = hashlib.md5(f"demo:{email}".encode()).hexdigest()
        return str(uuid.UUID(hex_digest))

    def _demo_mode_login(
        self, email: str, password: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Stub login used ONLY when demo mode is explicitly enabled."""
        if not self._demo_mode:
            return False, "Servico de autenticacao indisponivel. Tente novamente.", None

        if email in self._DEMO_USERS and self._DEMO_USERS[email] == password:
            stable_id = self._stable_demo_uuid(email)
            user_data = {
                "id": stable_id,
                "email": email,
                "demo": True,
                "user_metadata": {
                    "name": email.split("@")[0].title(),
                    "role": "clinician" if "doctor" in email else "patient",
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "session": None,
                "expires_at": None,
                "refresh_token": None,
            }
            # Ensure demo user exists in public.users for FK constraints
            self._ensure_user_in_db(stable_id, email)
            return True, "Login realizado (modo demo)", user_data

        return (
            False,
            "Credenciais demo invalidas. Use demo@spectrumia.com / demo123",
            None,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def login(
        self, email: str, password: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate with Supabase (or demo stub if demo mode is active).

        Errors from Supabase are surfaced to the caller — they are NEVER
        silently converted into a demo-mode login.

        Demo mode priority rule: when DEMO_MODE_ENABLED=true AND the supplied
        e-mail matches a known demo account, demo auth is used regardless of
        whether a Supabase client exists.  This lets developers test the full
        UI flow even when real Supabase credentials are configured.
        """
        # Allow demo accounts when DEMO_MODE_ENABLED=true, even with a live
        # Supabase client (demo credentials never exist in the real database).
        if _is_demo_mode_enabled() and email in self._DEMO_USERS:
            # Temporarily enable demo mode for this call only.
            prev = self._demo_mode
            self._demo_mode = True
            result = self._demo_mode_login(email, password)
            self._demo_mode = prev
            return result

        if not self.client:
            return self._demo_mode_login(email, password)

        try:
            response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if not (response and response.user):
                return False, "Login falhou. Verifique suas credenciais.", None

            user_data = self._build_user_data(response)
            logger.info("User %s logged in successfully", email)
            return True, "Login realizado com sucesso", user_data

        except Exception as exc:
            error_msg = str(exc).lower()
            logger.warning("Login attempt failed for %s: %s", email, exc)

            if "invalid login" in error_msg or "invalid credentials" in error_msg:
                return False, "Email ou senha incorretos.", None
            if "email not confirmed" in error_msg:
                return (
                    False,
                    "Email nao confirmado. Verifique sua caixa de entrada.",
                    None,
                )
            if "not found" in error_msg or "does not exist" in error_msg:
                return False, "Email nao cadastrado. Faca o registro primeiro.", None

            # Unknown error — report it; do NOT fall through to demo mode.
            logger.error("Unexpected login error for %s: %s", email, exc)
            return (
                False,
                "Erro ao autenticar. Tente novamente ou contate o suporte.",
                None,
            )

    def register(
        self,
        email: str,
        password: str,
        name: str = "",
        role: str = "patient",
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Register a new user via Supabase Auth."""
        if not email or "@" not in email:
            return False, "Formato de email invalido.", None
        if len(password) < 6:
            return False, "A senha deve ter no minimo 6 caracteres.", None

        if not self.client:
            if self._demo_mode:
                return (
                    True,
                    "Registro simulado (modo demo). Faca login para continuar.",
                    {"email": email, "name": name or email.split("@")[0], "role": role},
                )
            return False, "Servico de registro indisponivel.", None

        try:
            response = self.client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"name": name, "role": role}},
                }
            )

            if response and response.user:
                logger.info("New user registered: %s (role=%s)", email, role)
                return (
                    True,
                    "Registro realizado! Verifique seu email para confirmar a conta.",
                    {"email": response.user.email, "id": response.user.id},
                )
            return False, "Registro falhou. Tente novamente.", None

        except Exception as exc:
            error_msg = str(exc).lower()
            logger.warning("Registration failed for %s: %s", email, exc)

            if "already registered" in error_msg or "user already exists" in error_msg:
                return False, "Este email ja esta cadastrado. Faca login.", None
            return False, f"Erro no registro: {exc}", None

    def logout(self) -> None:
        """Sign out from Supabase and wipe local session state."""
        try:
            if self.client:
                self.client.auth.sign_out()
                logger.info("User signed out from Supabase")
        except Exception as exc:
            logger.warning("Error signing out from Supabase: %s", exc)
        finally:
            # Always clear local state, even if Supabase call fails.
            _clear_session()
            st.session_state.user_data = None
            st.session_state.auth_mode = "login"

    def verify_session(self) -> Optional[Dict]:
        """Validate the current session.

        Strategy:
        1. No user_data in session_state -> not authenticated.
        2. Demo user -> always valid (no token to check).
        3. Token has expiry stored -> check it locally first.
        4. If expired, attempt a server-side refresh via refresh_session().
           On failure, clear the session and return None.
        """
        user_data: Optional[Dict] = st.session_state.get("user_data")
        if not user_data:
            return None

        # Demo users have no real token — accept as-is.
        if user_data.get("demo"):
            return user_data

        # No Supabase client -> cannot validate a real session. Fail closed:
        # never accept an unverifiable session for non-demo users.
        if not self.client:
            logger.warning("No Supabase client — cannot validate session; clearing.")
            st.session_state.user_data = None
            return None

        access_token: Optional[str] = user_data.get("session")
        if not access_token:
            logger.warning("Session found without access_token — clearing.")
            st.session_state.user_data = None
            return None

        # Fast local expiry check.
        expires_at = user_data.get("expires_at")
        if expires_at:
            try:
                expiry_dt = datetime.fromtimestamp(float(expires_at), tz=timezone.utc)
                if datetime.now(timezone.utc) >= expiry_dt:
                    logger.info("Access token expired — attempting refresh.")
                    return self._refresh_session(user_data)
            except (ValueError, TypeError):
                pass

        return user_data

    def get_current_user(self) -> Optional[Dict]:
        """Return the current authenticated user's data, or None."""
        return self.verify_session()

    def is_authenticated(self) -> bool:
        """Return True only if verify_session() confirms a live session."""
        return self.verify_session() is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_admin_client(self):
        """Return a Supabase client using the service role key (bypasses RLS)."""
        from core.config import SUPABASE_URL
        import os
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not service_key or len(service_key) < 20:
            return self.client  # fall back to regular client
        try:
            return create_client(SUPABASE_URL, service_key)
        except Exception:
            return self.client

    def _ensure_user_in_db(self, user_id: str, email: str) -> None:
        """Upsert authenticated user into public.users with default profile.

        Supabase Auth creates records in auth.users, but the app requires a
        matching record in public.users for FK constraints. Uses service role
        key to bypass RLS for this admin operation.
        """
        admin = self._get_admin_client()
        if not admin:
            return
        try:
            admin.table("users").upsert(
                {
                    "user_id": user_id,
                    "email": email,
                    "age": 25,
                    "gender": "not_specified",
                    "age_group": "adult",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                on_conflict="user_id",
            ).execute()
            logger.info("User %s upserted in public.users", user_id)
        except Exception as exc:
            logger.warning(
                "Could not upsert user %s in public.users: %s — "
                "calibration/assessment may fail if the record is missing.",
                user_id,
                exc,
            )

    def _build_user_data(self, response) -> Dict:
        """Extract user and session info from a Supabase auth response."""
        session = response.session
        user_id = response.user.id
        email = response.user.email

        # Ensure the user has a row in public.users (FK requirement).
        self._ensure_user_in_db(user_id, email)

        return {
            "id": user_id,
            "email": email,
            "demo": False,
            "user_metadata": response.user.user_metadata or {},
            "created_at": str(response.user.created_at),
            "session": session.access_token if session else None,
            "refresh_token": session.refresh_token if session else None,
            "expires_at": session.expires_at if session else None,
        }

    def _refresh_session(self, user_data: Dict) -> Optional[Dict]:
        """Attempt to refresh an expired session using the refresh token."""
        refresh_token = user_data.get("refresh_token")
        if not refresh_token or not self.client:
            logger.info("Cannot refresh session — no refresh token or client.")
            st.session_state.user_data = None
            return None

        try:
            response = self.client.auth.refresh_session(refresh_token)
            if response and response.user:
                new_data = self._build_user_data(response)
                st.session_state.user_data = new_data
                logger.info("Session refreshed for user %s", new_data.get("email"))
                return new_data
        except Exception as exc:
            logger.warning("Session refresh failed: %s", exc)

        st.session_state.user_data = None
        return None


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def get_auth() -> SpectrumIAAuth:
    """Return an auth client isolated to the current Streamlit session."""
    auth = st.session_state.get(_AUTH_INSTANCE_KEY)
    if not isinstance(auth, SpectrumIAAuth):
        auth = SpectrumIAAuth()
        st.session_state[_AUTH_INSTANCE_KEY] = auth
    return auth


def get_access_token() -> Optional[str]:
    """Return the JWT stored in the current Streamlit user session."""
    user_data = st.session_state.get("user_data") or {}
    token = user_data.get("session")
    return token if isinstance(token, str) and token else None


def require_auth(func):
    """Page decorator: stops execution if no valid session exists."""
    def wrapper(*args, **kwargs):
        auth = get_auth()
        if not auth.is_authenticated():
            st.warning("Faca login para acessar esta pagina.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def initialize_session_state() -> None:
    """Initialise auth-related session state keys (idempotent)."""
    if "user_data" not in st.session_state:
        st.session_state.user_data = None
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = True
