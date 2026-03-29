"""
SpectrumIA Results Page

Display assessment results and screening outcomes.
Shows detailed metrics, risk factors, and clinical recommendations.

Integração:
- Supabase: Load assessment results
- Core: Gaze data retrieval e metrics visualization
- Clinical: Risk interpretation e recommendations
"""

import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import logging
from typing import Optional, List

from models.schemas import (
    AssessmentResultsResponse,
    ScreeningResult,
)
from models.database import get_db

logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state for results."""
    if "results_data" not in st.session_state:
        st.session_state.results_data = None
    if "selected_result_id" not in st.session_state:
        st.session_state.selected_result_id = None


def get_risk_color(screening_result: ScreeningResult) -> str:
    """Get color code for risk level."""
    if screening_result == ScreeningResult.LOW_RISK:
        return "green"
    elif screening_result == ScreeningResult.MODERATE_RISK:
        return "orange"
    elif screening_result == ScreeningResult.HIGH_RISK:
        return "red"
    else:
        return "blue"


def get_risk_icon(screening_result: ScreeningResult) -> str:
    """Get icon for risk level."""
    if screening_result == ScreeningResult.LOW_RISK:
        return "✅"
    elif screening_result == ScreeningResult.MODERATE_RISK:
        return "⚠️"
    elif screening_result == ScreeningResult.HIGH_RISK:
        return "🔴"
    else:
        return "❓"


def load_user_results(user_id: str) -> List[AssessmentResultsResponse]:
    """Load all results for a user from database."""
    db = get_db()
    try:
        results = db.list_user_results(user_id, limit=50)
        return results
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        st.error(f"Erro ao carregar resultados: {str(e)}")
        return []


def generate_clinical_interpretation(result: AssessmentResultsResponse) -> str:
    """Generate clinical interpretation based on result."""
    risk_factors = result.risk_factors

    interpretation = "## 📋 Interpretação Clínica\n\n"

    if result.screening_result == ScreeningResult.LOW_RISK:
        interpretation += """
        ### ✅ Risco Baixo

        O padrão de rastreamento ocular não apresenta características típicas do Transtorno do Espectro Autista (TEA).

        **Características Observadas:**
        - Atenção apropriada a características sociais (olhos e boca)
        - Padrões de fixação típicos
        - Dinâmica de saccades dentro do esperado
        """

    elif result.screening_result == ScreeningResult.MODERATE_RISK:
        interpretation += """
        ### ⚠️ Risco Moderado

        O padrão de rastreamento ocular apresenta algumas características atípicas que podem estar associadas ao TEA.

        **Recomendação:**
        Uma avaliação clínica mais aprofundada é recomendada para investigar melhor.
        """

    else:  # HIGH_RISK or INCONCLUSIVE
        interpretation += """
        ### 🔴 Risco Elevado

        O padrão de rastreamento ocular apresenta múltiplas características atípicas potencialmente associadas ao TEA.

        **Recomendação Urgente:**
        Uma avaliação clínica completa (ADOS-2, ADI-R) é altamente recomendada.
        """

    # Add specific findings
    interpretation += "\n\n### 🔍 Achados Específicos\n\n"

    if risk_factors.reduced_eye_gaze:
        interpretation += "- **Atenção Reduzida aos Olhos:** Tempo diminuído focando na região ocular\n"

    if risk_factors.reduced_mouth_gaze:
        interpretation += "- **Atenção Reduzida à Boca:** Padrão atípico de não seguir movimentos labiais\n"

    if risk_factors.reduced_social_attention:
        interpretation += "- **Índice de Atenção Social Baixo:** Preferência reduzida por características faciais\n"

    if risk_factors.atypical_fixation_patterns:
        interpretation += "- **Padrões de Fixação Atípicos:** Duração ou distribuição anormal de fixações\n"

    if risk_factors.increased_scanpath_entropy:
        interpretation += "- **Entropia de Scanpath Aumentada:** Padrão de rastreamento menos previsível\n"

    if risk_factors.increased_blink_rate:
        interpretation += "- **Taxa de Piscadas Aumentada:** Possível desconforto ou fadiga ocular\n"

    if risk_factors.poor_signal_quality:
        interpretation += "- **Qualidade de Sinal Pobre:** Dados podem não ser totalmente confiáveis\n"

    return interpretation


def generate_recommendations(result: AssessmentResultsResponse) -> str:
    """Generate clinical recommendations."""
    recommendations = "## 💡 Recomendações\n\n"

    if result.screening_result == ScreeningResult.LOW_RISK:
        recommendations += """
        1. **Monitoramento Contínuo:** Continue observando o desenvolvimento social e comunicativo
        2. **Avaliações Periódicas:** Considere uma reavaliação em 12 meses
        3. **Educação Parental:** Informações sobre desenvolvimento típico em neurodiversidade
        """

    elif result.screening_result == ScreeningResult.MODERATE_RISK:
        recommendations += """
        1. **Avaliação Clínica Recomendada:** Consulte um psiquiatra ou psicólogo especializados em neurodesenvolvimento
        2. **Bateria Completa:** ADOS-2, GARS-3, e testes cognitivos se indicado
        3. **Seguimento:** Reavaliação em 3-6 meses
        4. **Suporte Educacional:** Avaliação educacional e plano de intervenção preventiva
        """

    else:  # HIGH_RISK
        recommendations += """
        1. **URGENTE - Avaliação Clínica:** Agendamento prioritário com especialista em TEA
        2. **Bateria Diagnóstica Completa:**
           - ADOS-2 (Autism Diagnostic Observation Schedule)
           - ADI-R (Autism Diagnostic Interview Revised)
           - Testes cognitivos e de linguagem
        3. **Avaliações Multidisciplinares:**
           - Fonoaudiólogo (linguagem/comunicação)
           - Terapeuta ocupacional (integração sensorial)
           - Geneticista (se indicado)
        4. **Intervenção Precoce:** Se confirmado TEA, iniciar intervenção imediata
        5. **Suporte Familiar:** Aconselhamento e educação dos pais
        """

    recommendations += f"\n\n**Nível de Confiança:** {result.confidence_score:.0%}"

    return recommendations


def render_results_interface():
    """Render main results interface."""
    st.set_page_config(
        page_title="Resultados - SpectrumIA",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 Resultados da Avaliação")
    st.markdown("Análise completa dos dados de rastreamento ocular")

    initialize_session_state()

    # Check user authentication
    if "user_id" not in st.session_state:
        st.warning("Por favor, faça login primeiro na página principal")
        st.stop()

    user_id = st.session_state.user_id

    # ========================================================================
    # SIDEBAR - Results List
    # ========================================================================

    with st.sidebar:
        st.header("📋 Histórico de Avaliações")

        # Load results
        results_list = load_user_results(user_id)

        if results_list:
            # Create selector
            result_options = {
                f"{r.results_generated_at.strftime('%d/%m/%Y %H:%M')} - {r.screening_result.value}": r.result_id
                for r in results_list
            }

            selected_option = st.selectbox(
                "Selecione uma avaliação:",
                result_options.keys(),
                index=0
            )

            selected_result_id = result_options[selected_option]
            st.session_state.selected_result_id = selected_result_id

            # Find selected result
            selected_result = next(
                (r for r in results_list if r.result_id == selected_result_id),
                None
            )

            if selected_result:
                st.session_state.results_data = selected_result

        else:
            st.info("Nenhuma avaliação disponível")

        st.divider()

        # Export options
        st.subheader("📥 Exportar Dados")

        if st.session_state.results_data:
            # Export as JSON
            if st.button("📄 JSON", use_container_width=True):
                import json
                json_str = json.dumps(
                    st.session_state.results_data.model_dump(mode='json'),
                    indent=2,
                    default=str
                )
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"resultado_{st.session_state.results_data.result_id}.json",
                    mime="application/json"
                )

            # Export as CSV
            if st.button("📊 CSV", use_container_width=True):
                metrics = st.session_state.results_data.metrics_snapshot
                df = pd.DataFrame({
                    "Métrica": [
                        "Social Attention Index",
                        "Eye Preference",
                        "Mean Fixation Duration",
                        "Mean Saccade Amplitude",
                        "Scanpath Entropy",
                        "Signal Quality",
                    ],
                    "Valor": [
                        metrics.mean_social_attention_index,
                        metrics.mean_eye_preference,
                        metrics.mean_fixation_duration_ms,
                        metrics.mean_saccade_amplitude_deg,
                        metrics.mean_scanpath_entropy,
                        metrics.signal_quality_mean,
                    ]
                })

                st.download_button(
                    label="Download CSV",
                    data=df.to_csv(index=False),
                    file_name=f"resultado_{st.session_state.results_data.result_id}.csv",
                    mime="text/csv"
                )

    # ========================================================================
    # MAIN CONTENT
    # ========================================================================

    if not st.session_state.results_data:
        st.info("👉 Selecione uma avaliação na barra lateral")
        return

    result = st.session_state.results_data

    # ========================================================================
    # SCREENING RESULT HEADER
    # ========================================================================

    icon = get_risk_icon(result.screening_result)
    color = get_risk_color(result.screening_result)

    # Main result display
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            f"{icon} Resultado do Rastreamento",
            result.screening_result.value.replace('_', ' ').upper(),
        )

    with col2:
        st.metric(
            "Risco (%)",
            f"{result.risk_percentage:.1f}%",
        )

    with col3:
        st.metric(
            "Confiança",
            f"{result.confidence_score:.0%}",
        )

    st.divider()

    # ========================================================================
    # METRICS DASHBOARD
    # ========================================================================

    st.subheader("📈 Métricas de Rastreamento Ocular")

    metrics = result.metrics_snapshot

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Social Attention Index", f"{metrics.mean_social_attention_index:.3f}")
        st.caption("🧠 Métrica-chave: (olhos + boca) / total")
        st.metric("Eye Preference", f"{metrics.mean_eye_preference:.3f}")
        st.caption("👁️ Preferência por olhos")
        st.metric("Mean Fixation Duration", f"{metrics.mean_fixation_duration_ms:.1f}ms")
        st.metric("Mean Saccade Amplitude", f"{metrics.mean_saccade_amplitude_deg:.2f}°")

    with col2:
        st.metric("Scanpath Entropy", f"{metrics.mean_scanpath_entropy:.3f}")
        st.caption("🌀 Previsibilidade do padrão")
        st.metric("Time to First Fixation", f"{metrics.mean_time_to_first_fixation_ms:.1f}ms")
        st.caption("⏱️ Latência de resposta")
        st.metric("Blink Rate", f"{metrics.mean_blink_rate:.2f}/min")
        st.metric("Signal Quality", f"{metrics.signal_quality_mean:.0%}")

    # ========================================================================
    # RISK FACTORS
    # ========================================================================

    st.divider()
    st.subheader("⚠️ Fatores de Risco Identificados")

    risk_factors = result.risk_factors
    risk_count = result.risk_factor_count

    # Risk factors grid
    col1, col2 = st.columns(2)

    factors = [
        ("Atenção Reduzida aos Olhos", risk_factors.reduced_eye_gaze),
        ("Atenção Reduzida à Boca", risk_factors.reduced_mouth_gaze),
        ("Padrões de Fixação Atípicos", risk_factors.atypical_fixation_patterns),
        ("Atenção Social Reduzida", risk_factors.reduced_social_attention),
        ("Entropia de Scanpath Aumentada", risk_factors.increased_scanpath_entropy),
        ("Taxa de Piscadas Aumentada", risk_factors.increased_blink_rate),
        ("Qualidade de Sinal Fraca", risk_factors.poor_signal_quality),
    ]

    with col1:
        for factor_name, factor_present in factors[:4]:
            status = "✅ Presente" if factor_present else "❌ Ausente"
            st.write(f"{status}: {factor_name}")

    with col2:
        for factor_name, factor_present in factors[4:]:
            status = "✅ Presente" if factor_present else "❌ Ausente"
            st.write(f"{status}: {factor_name}")

    st.info(f"📊 Total de fatores de risco: {risk_count}/7")

    # ========================================================================
    # CLINICAL INTERPRETATION
    # ========================================================================

    st.divider()
    interpretation_text = generate_clinical_interpretation(result)
    st.markdown(interpretation_text)

    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================

    st.divider()
    recommendations_text = generate_recommendations(result)
    st.markdown(recommendations_text)

    # ========================================================================
    # METADATA
    # ========================================================================

    st.divider()
    st.subheader("📝 Informações da Avaliação")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**ID do Resultado:** {result.result_id}")
        st.write(f"**ID da Sessão:** {result.session_id}")
        st.write(f"**Tipo de Avaliação:** {result.assessment_type}")

    with col2:
        st.write(f"**Data da Avaliação:** {result.assessment_completed_at.strftime('%d/%m/%Y %H:%M')}")
        st.write(f"**Data dos Resultados:** {result.results_generated_at.strftime('%d/%m/%Y %H:%M')}")
        if result.expires_at:
            st.write(f"**Expira em:** {result.expires_at.strftime('%d/%m/%Y')}")

    # Clinical notes
    if result.clinical_notes:
        st.subheader("🏥 Notas Clínicas")
        st.write(result.clinical_notes)

    # ========================================================================
    # ACTIONS
    # ========================================================================

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Nova Avaliação", use_container_width=True):
            st.session_state.assessment_session_id = None
            st.switch_page("pages/assessment.py")

    with col2:
        if st.button("🧭 Calibração", use_container_width=True):
            st.switch_page("pages/calibration.py")

    with col3:
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app/main.py")


if __name__ == "__main__":
    render_results_interface()
