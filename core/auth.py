"""
Authentication module for SpectrumIA
Handles user authentication with Supabase (email/password)

Security notes:
- Demo mode is only active when DEMO_MODE_ENABLED=true in environment.
  It is NEVER activated automatically as a fallback on errors.
- Session validation checks token expiry locally and refreshes via Supabase
  when needed -- prevents stale/forged sessions from being accepted.
- Logout clears both Supabase server-side session and local session state.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Tuple

import streamlit as st
from supabase import create_client, Client

logger = logging.getLogger(__name__)


def _is_demo_mode_enabled() -> bool:
    from core.config import DEMO_MODE_ENABLED
    return DEMO_MODE_ENABLED


def _clear_session() -> None:
    for key in ("user_data", "auth_mode", "session_initialized"):
        st.session_state.pop(key, None)


class SpectrumIAAuth:
    def __init__(self):
        self.supabase_url: Optional[str] = None
        self.supabase_key: Optional[str] = None
        self.client: Optional[Client] = None
        self._demo_mode: bool = False
        self._initialize_client()

    def _initialize_client(self) -> None:
        from core.config import SUPABASE_URL, SUPABASE_KEY
        is_placeholder = (
            not SUPABASE_URL or not SUPABASE_KEY
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
                logger.error("Failed to initialise Supabase auth client: %s", exc)
                self.client = None
        else:
            if _is_demo_mode_enabled():
                self._demo_mode = True
                logger.warning("Running in DEMO MODE. Do NOT use in production.")
            else:
                logger.error("Supabase credentials missing. Set SUPABASE_URL and SUPABASE_KEY.")
            self.client = None

    _DEMO_USERS: Dict[str, str] = {
        "demo@spectrumia.com":    "demo123",
        "doctor@spectrumia.com":  "doctor123",
        "patient@spectrumia.com": "patient123",
    }

    def _demo_mode_login(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        if not self._demo_mode:
            return False, "Servico de autenticacao indisponivel.", None
        if email in self._DEMO_USERS and self._DEMO_USERS[email] == password:
            return True, "Login realizado (modo demo)", {
                "id": uuid.uuid4().hex,
                "email": email,
                "demo": True,
                "user_metadata": {"name": email.split("@")[0].title(), "role": "clinician" if "doctor" in email else "patient"},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "session": None, "expires_at": None, "refresh_token": None,
            }
        return False, "Credenciais demo invalidas. Use demo@spectrumia.com / demo123", None

    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        if not self.client:
            return self._demo_mode_login(email, password)
        try:
            response = self.client.auth.sign_in_with_password({"email": email, "password": password})
            if not (response and response.user):
                return False, "Login falhou. Verifique suas credenciais.", None
            logger.info("User %s logged in", email)
            return True, "Login realizado com sucesso", self._build_user_data(response)
        except Exception as exc:
            error_msg = str(exc).lower()
            logger.warning("Login failed for %s: %s | repr=%r", email, exc, exc)
            if "invalid login" in error_msg or "invalid credentials" in error_msg:
                return False, "Email ou senha incorretos.", None
            if "email not confirmed" in error_msg:
                return False, "Email nao confirmado. Verifique sua caixa de entrada.", None
            if "not found" in error_msg or "does not exist" in error_msg:
                return False, "Email nao cadastrado. Faca o registro primeiro.", None
            logger.error("Unexpected login error for %s: %s", email, exc)
            return False, f"Erro ao autenticar: {exc}", None

    def register(self, email: str, password: str, name: str = "", role: str = "patient") -> Tuple[bool, str, Optional[Dict]]:
        if not email or "@" not in email:
            return False, "Formato de email invalido.", None
        if len(password) < 6:
            return False, "A senha deve ter no minimo 6 caracteres.", None
        if not self.client:
            if self._demo_mode:
                return True, "Registro simulado (modo demo).", {"email": email, "name": name or email.split("@")[0], "role": role}
            return False, "Servico de registro indisponivel.", None
        try:
            response = self.client.auth.sign_up({"email": email, "password": password, "options": {"data": {"name": name, "role": role}}})
            if response and response.user:
                return True, "Registro realizado! Verifique seu email.", {"email": response.user.email, "id": response.user.id}
            return False, "Registro falhou.", None
        except Exception as exc:
            error_msg = str(exc).lower()
            if "already registered" in error_msg or "user already exists" in error_msg:
                return False, "Email ja cadastrado. Faca login.", None
            return False, f"Erro no registro: {exc}", None

    def logout(self) -> None:
        try:
            if self.client:
                self.client.auth.sign_out()
                logger.info("User signed out")
        except Exception as exc:
            logger.warning("Error signing out: %s", exc)
        finally:
            _clear_session()
            st.session_state.user_data = None
            st.session_state.auth_mode = "login"

    def verify_session(self) -> Optional[Dict]:
        user_data: Optional[Dict] = st.session_state.get("user_data")
        if not user_data:
            return None
        if user_data.get("demo"):
            return user_data
        if not self.client:
            return user_data
        access_token: Optional[str] = user_data.get("session")
        if not access_token:
            logger.warning("Session without access_token — clearing.")
            st.session_state.user_data = None
            return None
        expires_at = user_data.get("expires_at")
        if expires_at:
            try:
                expiry_dt = datetime.fromtimestamp(float(expires_at), tz=timezone.utc)
                if datetime.now(timezone.utc) >= expiry_dt:
                    return self._refresh_session(user_data)
            except (ValueError, TypeError):
                pass
        return user_data

    def get_current_user(self) -> Optional[Dict]:
        return self.verify_session()

    def is_authenticated(self) -> bool:
        return self.verify_session() is not None

    def _build_user_data(self, response) -> Dict:
        session = response.session
        return {
            "id": response.user.id, "email": response.user.email, "demo": False,
            "user_metadata": response.user.user_metadata or {},
            "created_at": str(response.user.created_at),
            "session": session.access_token if session else None,
            "refresh_token": session.refresh_token if session else None,
            "expires_at": session.expires_at if session else None,
        }

    def _refresh_session(self, user_data: Dict) -> Optional[Dict]:
        refresh_token = user_data.get("refresh_token")
        if not refresh_token or not self.client:
            st.session_state.user_data = None
            return None
        try:
            response = self.client.auth.refresh_session(refresh_token)
            if response and response.user:
                new_data = self._build_user_data(response)
                st.session_state.user_data = new_data
                return new_data
        except Exception as exc:
            logger.warning("Session refresh failed: %s", exc)
        st.session_state.user_data = None
        return None


@st.cache_resource
def get_auth() -> SpectrumIAAuth:
    """Return a single shared SpectrumIAAuth instance (thread-safe via Streamlit cache)."""
    return SpectrumIAAuth()

def require_auth(func):
    def wrapper(*args, **kwargs):
        auth = get_auth()
        if not auth.is_authenticated():
            st.warning("Faca login para acessar esta pagina.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def initialize_session_state() -> None:
    if "user_data" not in st.session_state:
        st.session_state.user_data = None
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = True
