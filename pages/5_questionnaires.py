"""
SpectrumIA — Página de Questionários Psicométricos
===================================================
Implementa CAT-Q e RAADS-R como instrumentos de triagem interativos,
seguindo a arquitetura Neurotrace AI:
  - CAT-Q  → calibrador do peso de camuflagem para o motor multimodal
  - RAADS-R → triagem ampla de traços autistas em adultos

Os resultados são salvos na sessão e consumidos pelo motor de fusão
multimodal na página de Resultados.
"""

import sys
import logging
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.auth import get_access_token, get_auth, initialize_session_state, require_auth
from core.questionnaires import (
    CATQ_ITEMS, RAADSR_ITEMS,
    score_catq, score_raadsr, combined_camouflage_weight,
)

logger = logging.getLogger(__name__)


def _save_questionnaire(auth, questionnaire_name: str, result) -> bool:
    """
    Persist questionnaire result to Supabase.
    Returns True on success, False on failure (graceful degradation).
    """
    try:
        from models.database import get_db
        user_id = auth.get_user_id()
        if not user_id:
            logger.warning("No user_id from auth — skipping DB save")
            return False
        db = get_db(get_access_token())
        db.save_questionnaire_result(
            user_id=user_id,
            questionnaire_name=questionnaire_name,
            total_score=float(result.total_score),
            subscale_scores={k: float(v) for k, v in result.subscale_scores.items()},
            raw_responses={str(k): v for k, v in result.raw_responses.items()},
            risk_level=result.risk_level if isinstance(result.risk_level, str)
                       else result.risk_level.value,
            camouflage_weight=float(result.camouflage_weight),
            interpretation=result.interpretation or "",
        )
        return True
    except Exception as e:
        logger.warning(f"Questionnaire DB save failed (non-critical): {e}")
        return False

st.set_page_config(
    page_title="SpectrumIA — Questionários",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_session_state()
auth = get_auth()

if not auth.is_authenticated():
    st.warning("🔐 Faça login para acessar os questionários.")
    if st.button("Ir para Login"):
        st.switch_page("pages/1_login.py")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("📋 Questionários")
st.sidebar.markdown(
    """
**Por que questionários?**

Instrumentos psicométricos como o **CAT-Q** e o **RAADS-R** atuam como
*calibradores de camuflagem* para o motor de IA multimodal.

Mulheres e adultos com alto mascaramento podem ter respostas de
eye-tracking aparentemente normais — os escores ajustam o limiar de
detecção automaticamente.
"""
)

# ── Estado da sessão ──────────────────────────────────────────────────────────
if "catq_responses" not in st.session_state:
    st.session_state.catq_responses = {}
if "raadsr_responses" not in st.session_state:
    st.session_state.raadsr_responses = {}
if "catq_result" not in st.session_state:
    st.session_state.catq_result = None
if "raadsr_result" not in st.session_state:
    st.session_state.raadsr_result = None

# ── Estilo ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.q-header { color: #1f77b4; margin-bottom: 0.5rem; }
.risk-high    { background: #ffebee; border-left: 4px solid #e53935; padding: 1rem; border-radius: 4px; }
.risk-moderate{ background: #fff8e1; border-left: 4px solid #ffa000; padding: 1rem; border-radius: 4px; }
.risk-low     { background: #e8f5e9; border-left: 4px solid #43a047; padding: 1rem; border-radius: 4px; }
.info-box     { background: #e3f2fd; border-left: 4px solid #1565c0; padding: 1rem; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='q-header'>📋 Questionários de Triagem</h1>", unsafe_allow_html=True)
st.markdown(
    """
<div class='info-box'>
<b>Instrução:</b> Responda com base em como você se sente a <em>maior parte do tempo</em>.
Não há respostas certas ou erradas. Os questionários são confidenciais e os dados
são utilizados exclusivamente para calibrar a análise multimodal de IA.<br><br>
<em>⚠️ Estes instrumentos são ferramentas de triagem — não substituem avaliação clínica.</em>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_catq, tab_raadsr, tab_results = st.tabs([
    "🎭 CAT-Q (Camuflagem)",
    "🔍 RAADS-R (Triagem Geral)",
    "📊 Resultados Integrados",
])

# ─────────────────────────────────────────────────────────────────────────────
# CAT-Q TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_catq:
    st.markdown("## CAT-Q — Camouflaging Autistic Traits Questionnaire")
    st.markdown(
        """
*Hull et al. (2019)* — 64 itens, escala Likert 1–7
**1** = Nunca é verdade para mim &nbsp;·&nbsp; **7** = Sempre é verdade para mim

Fatores: **Assimilação** · **Mascaramento** · **Compensação**
"""
    )

    catq_responses: dict = {}
    subscale_labels = {
        "assimilation": "🔄 Assimilação",
        "masking":       "🎭 Mascaramento",
        "compensation":  "⚙️ Compensação",
    }

    current_subscale = None
    for item in CATQ_ITEMS:
        if item.subscale != current_subscale:
            current_subscale = item.subscale
            st.markdown(f"### {subscale_labels[item.subscale]}")

        key = f"catq_{item.id}"
        saved = st.session_state.catq_responses.get(item.id, 4)
        catq_responses[item.id] = st.slider(
            f"**{item.id}.** {item.text}",
            min_value=1, max_value=7, value=saved,
            key=key,
            help="1 = Nunca · 7 = Sempre",
        )

    if st.button("✅ Calcular CAT-Q", type="primary", use_container_width=True):
        st.session_state.catq_responses = catq_responses
        result = score_catq(catq_responses)
        st.session_state.catq_result = result

        risk_class = f"risk-{result.risk_level}"
        st.markdown(
            f"""
<div class='{risk_class}'>
<h3>Resultado CAT-Q</h3>
<b>Score total:</b> {result.total_score:.0f} / 448<br>
<b>Nível:</b> {result.risk_level.upper()}<br>
<b>Peso de camuflagem:</b> {result.camouflage_weight:.1%}<br><br>
{result.interpretation}
</div>
""",
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Assimilação", f"{result.subscale_scores.get('assimilation', 0):.0f}")
        col2.metric("Mascaramento", f"{result.subscale_scores.get('masking', 0):.0f}")
        col3.metric("Compensação", f"{result.subscale_scores.get('compensation', 0):.0f}")

        # ── Persistência Supabase ────────────────────────────────────────────
        saved = _save_questionnaire(auth, "CAT-Q", result)
        if saved:
            st.success("✅ CAT-Q salvo na sessão e no banco de dados. Vá para **Resultados Integrados** ou faça o RAADS-R.")
        else:
            st.success("CAT-Q salvo na sessão! (Modo demo — banco não configurado.) Vá para **Resultados Integrados**.")

# ─────────────────────────────────────────────────────────────────────────────
# RAADS-R TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_raadsr:
    st.markdown("## RAADS-R — Ritvo Autism Asperger Diagnostic Scale – Revised")
    st.markdown(
        """
*Ritvo et al. (2011)* — 80 itens, escala 0–3
**0** = Nunca foi verdade &nbsp;·&nbsp; **1** = Verdade só quando tinha menos de 16 anos
**2** = Verdade só agora &nbsp;·&nbsp; **3** = Verdade agora e quando era jovem

Sub-escalas: **Linguagem** · **Social** · **Sensório-motor** · **Interesses Circunscritos**
"""
    )

    raadsr_responses: dict = {}
    subscale_labels_r = {
        "language":               "💬 Linguagem",
        "social":                  "👥 Social",
        "sensory_motor":           "🖐️ Sensório-motor",
        "circumscribed_interests": "🔬 Interesses Circunscritos",
    }

    current_subscale_r = None
    for item in RAADSR_ITEMS:
        subscale_key = item.subscale
        if subscale_key != current_subscale_r:
            current_subscale_r = subscale_key
            st.markdown(f"### {subscale_labels_r.get(subscale_key, subscale_key)}")

        key = f"raadsr_{item.id}"
        saved = st.session_state.raadsr_responses.get(item.id, 0)
        raadsr_responses[item.id] = st.radio(
            f"**{item.id}.** {item.text}",
            options=[0, 1, 2, 3],
            index=saved,
            horizontal=True,
            format_func=lambda x: {
                0: "0 – Nunca",
                1: "1 – Só antes dos 16",
                2: "2 – Só agora",
                3: "3 – Sempre",
            }.get(x, str(x)),
            key=key,
        )

    if st.button("✅ Calcular RAADS-R", type="primary", use_container_width=True):
        st.session_state.raadsr_responses = raadsr_responses
        result = score_raadsr(raadsr_responses)
        st.session_state.raadsr_result = result

        risk_class = f"risk-{result.risk_level}"
        st.markdown(
            f"""
<div class='{risk_class}'>
<h3>Resultado RAADS-R</h3>
<b>Score total:</b> {result.total_score:.0f} / 240 (limiar clínico ≥ 65)<br>
<b>Nível:</b> {result.risk_level.upper()}<br><br>
{result.interpretation}
</div>
""",
            unsafe_allow_html=True,
        )

        sub = result.subscale_scores
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Linguagem", f"{sub.get('language', 0):.0f}")
        c2.metric("Social", f"{sub.get('social', 0):.0f}")
        c3.metric("Sensório-motor", f"{sub.get('sensory_motor', 0):.0f}")
        c4.metric("Interesses", f"{sub.get('circumscribed_interests', 0):.0f}")

        # ── Persistência Supabase ────────────────────────────────────────────
        saved = _save_questionnaire(auth, "RAADS-R", result)
        if saved:
            st.success("✅ RAADS-R salvo na sessão e no banco de dados. Vá para **Resultados Integrados**.")
        else:
            st.success("RAADS-R salvo na sessão! (Modo demo — banco não configurado.) Vá para **Resultados Integrados**.")

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_results:
    st.markdown("## 📊 Resultados Integrados")

    catq_r = st.session_state.catq_result
    raadsr_r = st.session_state.raadsr_result

    if not catq_r and not raadsr_r:
        st.info("Preencha pelo menos um questionário (CAT-Q ou RAADS-R) para ver os resultados integrados.")
        st.stop()

    cw = combined_camouflage_weight(catq_r, raadsr_r)

    st.markdown("### Peso de Camuflagem Combinado")
    st.progress(cw, text=f"Índice de camuflagem psicossocial: {cw:.1%}")

    if cw >= 0.60:
        st.markdown("""
<div class='risk-high'>
<b>⚠️ Alto índice de camuflagem detectado.</b><br>
O motor de fusão multimodal ajustará os limiares de detecção de eye-tracking e
biomarcadores fisiológicos para maximizar a sensibilidade ao Fenótipo Autista
Feminino (FAF) com mascaramento ativo.
</div>
""", unsafe_allow_html=True)
    elif cw >= 0.40:
        st.markdown("""
<div class='risk-moderate'>
<b>Índice de camuflagem moderado.</b><br>
Análise multimodal prosseguirá com sensibilidade aumentada para padrões de compensação.
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div class='risk-low'>
<b>Índice de camuflagem baixo.</b><br>
Parâmetros padrão do motor de fusão multimodal serão utilizados.
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)

    if catq_r:
        with col_a:
            st.markdown("#### CAT-Q")
            st.metric("Score Total", f"{catq_r.total_score:.0f} / 448")
            st.metric("Assimilação", f"{catq_r.subscale_scores.get('assimilation', 0):.0f}")
            st.metric("Mascaramento", f"{catq_r.subscale_scores.get('masking', 0):.0f}")
            st.metric("Compensação",  f"{catq_r.subscale_scores.get('compensation', 0):.0f}")
            risk_badge = {"high": "🔴", "moderate": "🟡", "low": "🟢"}.get(catq_r.risk_level, "⚪")
            st.markdown(f"**Nível:** {risk_badge} {catq_r.risk_level.upper()}")

    if raadsr_r:
        with col_b:
            st.markdown("#### RAADS-R")
            st.metric("Score Total", f"{raadsr_r.total_score:.0f} / 240")
            sub = raadsr_r.subscale_scores
            st.metric("Linguagem",    f"{sub.get('language', 0):.0f}")
            st.metric("Social",       f"{sub.get('social', 0):.0f}")
            st.metric("Sensório-motor", f"{sub.get('sensory_motor', 0):.0f}")
            st.metric("Interesses",   f"{sub.get('circumscribed_interests', 0):.0f}")
            risk_badge = {"high": "🔴", "moderate": "🟡", "low": "🟢"}.get(raadsr_r.risk_level, "⚪")
            st.markdown(f"**Nível:** {risk_badge} {raadsr_r.risk_level.upper()}")

    st.markdown("---")
    st.markdown("### Próximo Passo")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📍 Ir para Calibração", use_container_width=True):
            st.switch_page("pages/2_calibration.py")
    with col2:
        if st.button("📹 Ir para Assessment", use_container_width=True):
            st.switch_page("pages/3_assessment.py")

    st.markdown("""
---
<div style='font-size:0.8rem; color:#888;'>
⚠️ <b>Aviso clínico:</b> O CAT-Q e o RAADS-R são instrumentos de triagem psicométrica, não diagnósticos.
Resultados devem ser interpretados por profissional de saúde qualificado.
Os dados coletados são processados de acordo com a LGPD.
</div>
""", unsafe_allow_html=True)
