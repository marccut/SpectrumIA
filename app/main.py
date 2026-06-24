"""
SpectrumIA home page and authentication entry point.
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.auth import get_auth, initialize_session_state as init_auth_state
from core.config import APP_DEBUG, APP_VERSION, validate_config


st.set_page_config(
    page_title="SpectrumIA - ASD Screening Tool",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def sync_user_session() -> None:
    """Mirror auth state into legacy session keys used across the app."""
    user_data = st.session_state.get("user_data")
    if not user_data:
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.user_name = None
        return

    metadata = user_data.get("user_metadata") or {}
    email = user_data.get("email")
    fallback_name = email.split("@")[0].replace(".", " ").title() if email else "User"

    st.session_state.authenticated = True
    st.session_state.user_id = user_data.get("id")
    st.session_state.user_email = email
    st.session_state.user_name = metadata.get("name") or fallback_name


def clear_user_session() -> None:
    """Clear user-facing session keys while preserving unrelated app state."""
    for key in [
        "authenticated",
        "user_id",
        "user_email",
        "user_name",
        "user_data",
        "auth_mode",
        "calibration_session_id",
        "calibration_points",
        "current_calibration_index",
        "calibration_status",
        "calibration_id",
        "active_calibration_id",
        "is_calibrated",
        "assessment_session_id",
        "assessment_status",
        "gaze_samples",
        "current_stimulus_index",
        "results_data",
        "selected_result_id",
    ]:
        st.session_state.pop(key, None)


def show_login_page(auth) -> None:
    """Render the login screen."""
    st.title("🧠 SpectrumIA")
    st.caption("Eye-Tracking Based Screening Tool for Autism Spectrum Disorder")

    _, center_col, _ = st.columns([1, 1.2, 1])

    with center_col:
        st.subheader("Login")
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Email",
                placeholder="demo@spectrumia.com",
                help="Use suas credenciais do Supabase ou as credenciais demo.",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Digite sua senha",
            )
            submitted = st.form_submit_button(
                "Entrar",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not email or not password:
                st.error("Preencha email e senha.")
            else:
                success, message, user_data = auth.login(email, password)
                if success and user_data:
                    st.session_state.user_data = user_data
                    sync_user_session()
                    st.success(f"Bem-vinda(o), {st.session_state.user_name}!")
                    st.rerun()
                else:
                    st.error(message)

    st.markdown("### Credenciais demo")
    st.markdown(
        """
        - `demo@spectrumia.com` / `demo123`
        - `doctor@spectrumia.com` / `doctor123`
        - `patient@spectrumia.com` / `patient123`
        """
    )

    st.markdown("---")
    st.markdown(
        """
        SpectrumIA é uma ferramenta de triagem baseada em eye-tracking. Os resultados
        não substituem avaliação clínica formal e devem ser interpretados por
        profissionais qualificados.
        """
    )


def show_home_page(auth) -> None:
    """Render the authenticated landing page."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1>🧠 SpectrumIA</h1>
            <p style="color: #666;">
                Fluxo oficial do app com autenticação, calibração, avaliação e resultados
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            f"""
            <div style="
                background: #e8f4f8;
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 1rem;
                border-left: 4px solid #17a2b8;
            ">
                <strong>Usuário</strong><br>
                {st.session_state.user_name}<br>
                <span style="font-size: 0.9rem; color: #666;">
                    {st.session_state.user_email}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Versão: {APP_VERSION}")
        if APP_DEBUG:
            st.caption("Debug mode ativo")
        if st.button("Sair", use_container_width=True):
            auth.logout()
            clear_user_session()
            st.rerun()

    intro_col, status_col = st.columns([1.6, 1])

    with intro_col:
        st.markdown("### Fluxo recomendado")
        st.markdown(
            """
            1. Faça a `Calibration` para registrar a sessão e validar o rastreamento.
            2. Rode a `Assessment` oficial para coletar gaze samples.
            3. Abra `Results` para revisar métricas e indicadores.
            """
        )
        st.info(
            "As páginas aparecem na navegação padrão do Streamlit na sidebar. "
            "Os botões abaixo levam direto para cada etapa."
        )

    with status_col:
        st.markdown("### Estado da sessão")
        st.metric("Autenticado", "Sim")
        st.metric(
            "Calibrado",
            "Sim" if st.session_state.get("is_calibrated") or st.session_state.get("calibration_id") else "Não",
        )
        st.metric(
            "Assessment iniciada",
            "Sim" if st.session_state.get("assessment_session_id") else "Não",
        )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Ir para Calibration", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Calibration.py")
    with col2:
        if st.button("Ir para Assessment", use_container_width=True):
            st.switch_page("pages/3_Assessment.py")
    with col3:
        if st.button("Ir para Results", use_container_width=True):
            st.switch_page("pages/4_Results.py")

    st.markdown("---")
    st.markdown("### Páginas disponíveis")
    st.markdown(
        """
        - `Calibration`: versão corrigida integrada ao fluxo oficial.
        - `Assessment`: fluxo padrão corrigido para coleta e persistência.
        - `Results`: painel oficial de leitura dos resultados.
        - `Assessment Continuous`: variante experimental mantida para comparação.
        """
    )


def main() -> None:
    """Run the main app entrypoint."""
    init_auth_state()

    try:
        validate_config()
    except ValueError as exc:
        st.error(f"Configuration Error: {exc}")
        st.stop()

    auth = get_auth()
    sync_user_session()

    if not auth.is_authenticated():
        show_login_page(auth)
    else:
        show_home_page(auth)


if __name__ == "__main__":
    main()
