"""
SpectrumIA — Análise de Fenótipo Multimodal (Neurotrace AI)
============================================================
Dashboard XAI focado no Fenótipo Autista Feminino (FAF):
  • Probabilidade de TEA ajustada ao índice de camuflagem
  • Perfil de camuflagem CAT-Q por subescala (Assimilação / Compensação / Mascaramento)
  • Radar multimodal de evidências
  • Diagnóstico diferencial TEA vs TDAH vs Ansiedade vs TPB
  • Marcadores clínicos específicos do FAF
  • Timeline diagnóstica típica
  • Breakdown SHAP-like por modalidade
"""

import sys
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.auth import get_auth, initialize_session_state
from core.questionnaires import combined_camouflage_weight
from core.multimodal_fusion import (
    FusionInput, EyeTrackingFeatures, fuse, PHENOTYPE_SUBTYPES,
)

try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False

st.set_page_config(
    page_title="SpectrumIA — Fenótipo Multimodal",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_session_state()
auth = get_auth()

if not auth.is_authenticated():
    st.warning("🔐 Faça login para acessar a análise fenotípica.")
    if st.button("Ir para Login"):
        st.switch_page("pages/1_login.py")
    st.stop()

# ── Estilos ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.prob-high     { color:#e53935; font-size:2.4rem; font-weight:bold; }
.prob-moderate { color:#ffa000; font-size:2.4rem; font-weight:bold; }
.prob-low      { color:#43a047; font-size:2.4rem; font-weight:bold; }

.badge-faf     { background:#6a1b9a; color:white; padding:5px 14px; border-radius:14px; font-weight:600; }
.badge-classic { background:#0277bd; color:white; padding:5px 14px; border-radius:14px; font-weight:600; }
.badge-adhd    { background:#f57c00; color:white; padding:5px 14px; border-radius:14px; font-weight:600; }
.badge-other   { background:#546e7a; color:white; padding:5px 14px; border-radius:14px; font-weight:600; }

.faf-marker-card {
    background: linear-gradient(135deg, #f3e5f5 0%, #ede7f6 100%);
    border-left: 4px solid #7b1fa2;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
}
.faf-marker-card.present  { border-left-color: #e53935; background: linear-gradient(135deg, #ffebee 0%, #fce4ec 100%); }
.faf-marker-card.absent   { border-left-color: #43a047; background: linear-gradient(135deg, #f1f8e9 0%, #e8f5e9 100%); }

.section-header {
    background: linear-gradient(90deg, #6a1b9a22 0%, transparent 100%);
    border-left: 4px solid #7b1fa2;
    padding: 0.5rem 1rem;
    border-radius: 0 8px 8px 0;
    margin: 1.5rem 0 1rem 0;
}

.diff-dx-cell {
    padding: 8px;
    border-radius: 6px;
    text-align: center;
    font-size: 0.85rem;
}
.diff-high   { background:#ffcdd2; color:#b71c1c; font-weight:600; }
.diff-mod    { background:#fff9c4; color:#f57f17; font-weight:600; }
.diff-low    { background:#dcedc8; color:#33691e; font-weight:600; }

.contrib-pos { color:#e53935; font-weight:600; }
.contrib-neg { color:#43a047; font-weight:600; }

.timeline-step {
    display:flex; align-items:flex-start; margin-bottom:1rem;
}
.timeline-dot {
    width:14px; height:14px; border-radius:50%;
    margin-top:4px; margin-right:12px; flex-shrink:0;
}
.timeline-content { flex:1; }

.regulatory-footer {
    font-size:0.78rem; color:#888; text-align:center;
    border-top:1px solid #eee; padding-top:1rem; margin-top:2rem;
}
</style>
""", unsafe_allow_html=True)

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("# 🧬 Análise Fenotípica Multimodal")
st.markdown("*Neurotrace AI · Inteligência Artificial Explicável (XAI) · Foco no Fenótipo Autista Feminino*")
st.markdown("---")

# ── Coleta de dados de sessão ─────────────────────────────────────────────────
catq_result   = st.session_state.get("catq_result")
raadsr_result = st.session_state.get("raadsr_result")
gaze_metrics  = st.session_state.get("gaze_metrics", {})
assessment_results = st.session_state.get("assessment_results", {})

cw = combined_camouflage_weight(catq_result, raadsr_result)

et = None
if gaze_metrics or assessment_results:
    et = EyeTrackingFeatures(
        social_fixation_ratio=float(assessment_results.get("social_fixation_ratio",
                                   gaze_metrics.get("social_fixation_ratio", 0.0))),
        avg_saccade_amplitude=float(gaze_metrics.get("avg_saccade_amplitude", 0.0)),
        blink_rate_per_min=float(gaze_metrics.get("blink_rate_per_min", 0.0)),
        social_gaze_avoidance=float(gaze_metrics.get("social_gaze_avoidance", 0.0)),
        quality_score=float(assessment_results.get("quality_score",
                            gaze_metrics.get("quality_score", 0.5))),
    )

inp = FusionInput(
    eye_tracking=et,
    catq_camouflage_weight=cw,
    catq_total=catq_result.total_score if catq_result else None,
    raadsr_total=raadsr_result.total_score if raadsr_result else None,
    raadsr_risk_level=raadsr_result.risk_level if raadsr_result else None,
)

result = fuse(inp)

# ── Banner de completude ───────────────────────────────────────────────────────
completeness = result.data_completeness
if completeness < 0.30:
    st.warning(
        f"⚠️ Completude dos dados: {completeness:.0%} — "
        "Preencha os questionários e realize o assessment de eye-tracking para máxima precisão."
    )
elif completeness < 0.60:
    st.info(f"ℹ️ Completude dos dados: {completeness:.0%} — Resultado parcial.")
else:
    st.success(f"✅ Completude dos dados: {completeness:.0%} — Análise multimodal robusta.")

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 1 — PROBABILIDADE + FENÓTIPO + CONFIANÇA
# ═════════════════════════════════════════════════════════════════════════════
prob_pct = result.asd_probability * 100
if prob_pct >= 60:
    prob_class, prob_label, prob_icon = "prob-high", "ELEVADA", "🔴"
elif prob_pct >= 40:
    prob_class, prob_label, prob_icon = "prob-moderate", "MODERADA", "🟡"
else:
    prob_class, prob_label, prob_icon = "prob-low", "BAIXA", "🟢"

pt_label = PHENOTYPE_SUBTYPES.get(result.phenotype_subtype, result.phenotype_subtype)
if "faf" in result.phenotype_subtype:
    badge_class, badge_icon = "badge-faf", "💜"
elif "adhd" in result.phenotype_subtype:
    badge_class, badge_icon = "badge-adhd", "🔶"
elif "classic" in result.phenotype_subtype:
    badge_class, badge_icon = "badge-classic", "🔵"
else:
    badge_class, badge_icon = "badge-other", "⚪"

col1, col2, col3 = st.columns([1.2, 2, 1.2])

with col1:
    st.markdown("#### Probabilidade de TEA")
    st.markdown(f"<div class='{prob_class}'>{prob_pct:.1f}%</div>", unsafe_allow_html=True)
    st.markdown(f"**{prob_icon} {prob_label}**")
    st.progress(result.asd_probability)
    adjusted = 1 - result.camouflage_weight_used * 0.20
    st.caption(f"Limiar ajustado: {adjusted:.0%}")
    if result.camouflage_adjustment_applied:
        st.markdown("🎭 *Limiar reduzido por camuflagem detectada*")

with col2:
    st.markdown("#### Subtipo Fenotípico")
    st.markdown(
        f"<div style='margin:0.5rem 0'><span class='{badge_class}'>{badge_icon} {pt_label}</span></div>",
        unsafe_allow_html=True,
    )
    support_labels = {1: "Nível 1 — Requer suporte", 2: "Nível 2 — Requer suporte substancial",
                      3: "Nível 3 — Requer suporte muito substancial"}
    adhd_labels = {"low": "Baixo", "moderate": "Moderado", "high": "Alto"}

    st.markdown(f"""
| Campo | Valor |
|---|---|
| **Nível de Suporte (DSM-5-TR)** | {support_labels.get(result.functional_support_level, "—")} |
| **Fator de Confusão TDAH** | {adhd_labels.get(result.adhd_confusion_factor, result.adhd_confusion_factor)} |
| **Índice de Camuflagem** | {result.camouflage_weight_used:.1%} |
""")

with col3:
    st.markdown("#### Confiança do Modelo")
    st.progress(result.confidence)
    st.caption(f"{result.confidence:.1%}")
    st.markdown(f"**Completude:** {completeness:.0%}")
    missing_streams = 7 - sum([
        et is not None,
        catq_result is not None,
        raadsr_result is not None,
    ])
    if missing_streams > 0:
        st.caption(f"⬜ {missing_streams} fluxos de dados ausentes")

# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 2 — INTERPRETAÇÃO CLÍNICA
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>📋 Interpretação Clínica (XAI)</h3></div>', unsafe_allow_html=True)
st.markdown(result.interpretation)
st.info(f"**Recomendação:** {result.recommendation}")

# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 3 — RADAR MULTIMODAL DE EVIDÊNCIAS (Plotly)
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>📡 Radar Multimodal de Evidências</h3></div>', unsafe_allow_html=True)

available_contribs = [fc for fc in result.feature_contributions if fc.available]
all_names = [fc.name.split("(")[0].strip() for fc in result.feature_contributions]
all_values = []
for fc in result.feature_contributions:
    if fc.available:
        # Normalise contribution to 0–1 scale for radar
        all_values.append(round(min(1.0, max(0.0, 0.5 + fc.contribution)), 2))
    else:
        all_values.append(0.0)

if PLOTLY_OK and any(v > 0 for v in all_values):
    radar_labels = all_names + [all_names[0]]
    radar_values = all_values + [all_values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=radar_values,
        theta=radar_labels,
        fill="toself",
        fillcolor="rgba(106,27,154,0.15)",
        line=dict(color="#7b1fa2", width=2),
        name="Perfil Multimodal",
        hovertemplate="%{theta}: %{r:.2f}<extra></extra>",
    ))
    # Normative reference (0.5 = neutral)
    fig.add_trace(go.Scatterpolar(
        r=[0.5] * len(radar_labels),
        theta=radar_labels,
        line=dict(color="#bdbdbd", width=1, dash="dash"),
        name="Referência Neurotípica",
        hovertemplate="Referência: 0.50<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickvals=[0.25, 0.5, 0.75, 1.0],
                            ticktext=["0.25", "0.50", "0.75", "1.0"]),
        ),
        showlegend=True,
        legend=dict(orientation="h", y=-0.15),
        margin=dict(t=40, b=60, l=60, r=60),
        height=420,
        title=dict(text="Evidência ASD por Modalidade (0 = mínima, 1 = máxima)", font_size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Preencha os questionários e complete o assessment de eye-tracking para exibir o radar multimodal.")

# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 4 — PERFIL DE CAMUFLAGEM (CAT-Q por subescala)
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>🎭 Perfil de Camuflagem CAT-Q</h3></div>', unsafe_allow_html=True)

if catq_result and catq_result.subscale_scores:
    ss = catq_result.subscale_scores
    assim = ss.get("assimilation", 0)
    comp  = ss.get("compensation", 0)
    mask  = ss.get("masking", 0)

    # Thresholds (Hull et al. 2019): subscale max ~150/149/149
    ASSIM_MAX, COMP_MAX, MASK_MAX = 126, 161, 161

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        pct = assim / ASSIM_MAX
        st.markdown("**Assimilação**")
        st.caption("Imitar/copiar comportamentos sociais")
        st.progress(min(1.0, pct))
        st.markdown(f"**{assim:.0f}** / {ASSIM_MAX} &nbsp; `{pct:.0%}`")
        if pct > 0.65:
            st.error("Elevada ↑")
        elif pct > 0.40:
            st.warning("Moderada")
        else:
            st.success("Baixa")
    with col_b:
        pct = comp / COMP_MAX
        st.markdown("**Compensação**")
        st.caption("Aprender regras sociais explicitamente")
        st.progress(min(1.0, pct))
        st.markdown(f"**{comp:.0f}** / {COMP_MAX} &nbsp; `{pct:.0%}`")
        if pct > 0.65:
            st.error("Elevada ↑")
        elif pct > 0.40:
            st.warning("Moderada")
        else:
            st.success("Baixa")
    with col_c:
        pct = mask / MASK_MAX
        st.markdown("**Mascaramento**")
        st.caption("Suprimir traços autistas / forçar expressão neurotípica")
        st.progress(min(1.0, pct))
        st.markdown(f"**{mask:.0f}** / {MASK_MAX} &nbsp; `{pct:.0%}`")
        if pct > 0.65:
            st.error("Elevada ↑")
        elif pct > 0.40:
            st.warning("Moderada")
        else:
            st.success("Baixa")

    if PLOTLY_OK:
        fig_catq = go.Figure(go.Bar(
            x=["Assimilação", "Compensação", "Mascaramento"],
            y=[assim / ASSIM_MAX, comp / COMP_MAX, mask / MASK_MAX],
            marker_color=["#9c27b0", "#673ab7", "#3f51b5"],
            text=[f"{assim/ASSIM_MAX:.0%}", f"{comp/COMP_MAX:.0%}", f"{mask/MASK_MAX:.0%}"],
            textposition="auto",
        ))
        fig_catq.add_hline(y=0.65, line_dash="dash", line_color="#e53935",
                           annotation_text="Limiar clínico (Hull et al.)", annotation_position="top right")
        fig_catq.update_layout(
            yaxis=dict(range=[0, 1], tickformat=".0%", title="Pontuação Normalizada"),
            xaxis_title="Subescala CAT-Q",
            height=300, margin=dict(t=30, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_catq, use_container_width=True)

    with st.expander("ℹ️ Como interpretar as subescalas CAT-Q"):
        st.markdown("""
**Assimilação** — Estratégias de aprendizado ativo do comportamento social (imitação,
observação, ensaio). Pontuação elevada indica esforço cognitivo explícito para
navegar situações sociais — característica marcante do FAF.

**Compensação** — Uso de mecanismos compensatórios para disfarçar dificuldades
(preparação de frases, scripts sociais, análise pós-evento). Alta compensação
frequentemente mascara o déficit subjacente em avaliações clínicas convencionais.

**Mascaramento** — Supressão ativa de comportamentos autistas e forçamento de
expressão neurotípica. Alto mascaramento está associado a esgotamento autístico
(*autistic burnout*) e maior risco de diagnóstico tardio em mulheres.

*Referência: Hull et al. (2019). doi:10.1007/s10803-018-3821-5*
""")
else:
    st.info(
        "**CAT-Q não preenchido.** Preencha o questionário CAT-Q na aba Questionários "
        "para visualizar o perfil de camuflagem por subescala — essencial para detecção do FAF."
    )
    if st.button("📋 Ir para Questionários", key="btn_q_catq"):
        st.switch_page("pages/5_questionnaires.py")

# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 5 — MARCADORES CLÍNICOS DO FAF
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>💜 Marcadores Clínicos do Fenótipo Autista Feminino</h3></div>', unsafe_allow_html=True)

st.caption(
    "Sinais frequentemente ausentes em avaliações padrão por serem mais sutis ou "
    "atribuídos a outros diagnósticos. Baseado em revisão sistemática (Lai et al., 2015; "
    "Bargiela et al., 2016; Hull et al., 2020)."
)

# Detect markers from available data
is_faf = "faf" in result.phenotype_subtype
high_camouflage = result.camouflage_weight_used >= 0.55
low_social_fix = et is not None and et.social_fixation_ratio < 0.45
high_raadsr = raadsr_result is not None and raadsr_result.total_score >= 65

markers = [
    {
        "label": "Alto índice de camuflagem / mascaramento",
        "detail": "Esforço ativo para parecer neurotípica. Detectado via CAT-Q.",
        "detected": high_camouflage,
        "source": "CAT-Q",
    },
    {
        "label": "Fixação social atípica (não-ausente, mas desviada)",
        "detail": "Evitação de contato visual disfarçada por padrões de varredura aprendidos.",
        "detected": low_social_fix,
        "source": "Eye-Tracking",
    },
    {
        "label": "Traços autistas acima do limiar clínico (RAADS-R ≥ 65)",
        "detail": "Pontuação que excede o ponto de corte validado para TEA em adultos.",
        "detected": high_raadsr,
        "source": "RAADS-R",
    },
    {
        "label": "Subtipo FAF identificado pelo motor de fusão",
        "detail": "Combinação de probabilidade de TEA + alto mascaramento = perfil FAF.",
        "detected": is_faf,
        "source": "Neurotrace AI",
    },
    {
        "label": "Burnout autístico (histórico ou atual)",
        "detail": "Colapso de estratégias de mascaramento — pode ser gatilho para o diagnóstico tardio.",
        "detected": None,  # Não detectável automaticamente ainda
        "source": "Clínico (anamnese)",
    },
    {
        "label": "Diagnósticos prévios: TDAH, ansiedade, depressão, TPB",
        "detail": "Diagnósticos errôneos são 3–4× mais frequentes em mulheres autistas antes do diagnóstico correto.",
        "detected": None,
        "source": "Clínico (anamnese)",
    },
    {
        "label": "Hipersensibilidade sensorial",
        "detail": "Sons, texturas, luzes. Frequentemente não relatada espontaneamente por mulheres.",
        "detected": None,
        "source": "RAADS-R subescala / Clínico",
    },
    {
        "label": "Interesses específicos intensos (com temática social/humanística)",
        "detail": "Em mulheres, os interesses podem ser socialmente aceitos (animais, ficção, psicologia), dificultando reconhecimento.",
        "detected": None,
        "source": "Clínico (anamnese)",
    },
]

col_l, col_r = st.columns(2)
for i, m in enumerate(markers):
    col = col_l if i % 2 == 0 else col_r
    with col:
        if m["detected"] is True:
            css = "faf-marker-card present"
            icon = "🔴"
        elif m["detected"] is False:
            css = "faf-marker-card absent"
            icon = "🟢"
        else:
            css = "faf-marker-card"
            icon = "⚪"
        st.markdown(
            f"<div class='{css}'>"
            f"<b>{icon} {m['label']}</b><br>"
            f"<span style='font-size:0.85rem;color:#555'>{m['detail']}</span><br>"
            f"<span style='font-size:0.75rem;color:#888'>Fonte: {m['source']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 6 — DIAGNÓSTICO DIFERENCIAL
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>⚖️ Diagnóstico Diferencial</h3></div>', unsafe_allow_html=True)

st.caption("Padrões de sobreposição entre TEA (FAF), TDAH, Ansiedade Social e Transtorno de Personalidade Borderline (TPB) em mulheres adultas.")

diff_dx_data = {
    "Característica": [
        "Dificuldade de manutenção do contato visual",
        "Ansiedade social",
        "Dificuldade em amizades",
        "Rigidez cognitiva / pensamento inflexível",
        "Hiperfoco / interesses intensos",
        "Sensibilidade sensorial",
        "Mascaramento / camuflagem",
        "Regulação emocional prejudicada",
        "Impulsividade",
        "Medo de abandono",
    ],
    "TEA (FAF) 💜": ["Alto", "Alto", "Alto", "Alto", "Alto", "Alto", "Muito Alto", "Moderado", "Baixo–Mod.", "Baixo"],
    "TDAH 🔶": ["Baixo", "Moderado", "Moderado", "Moderado", "Alto (hiperfoco)", "Moderado", "Baixo", "Alto", "Alto", "Baixo"],
    "Ansiedade 🟡": ["Alto", "Muito Alto", "Moderado", "Baixo", "Baixo", "Moderado", "Moderado", "Alto", "Baixo", "Baixo"],
    "TPB 🔴": ["Variável", "Alto", "Alto", "Baixo", "Baixo", "Baixo", "Baixo", "Muito Alto", "Alto", "Muito Alto"],
}

# Colour map for values
def cell_class(val):
    if "Muito Alto" in val: return "diff-high"
    if "Alto" in val: return "diff-mod"
    return "diff-low"

# Build styled table via st.dataframe
import pandas as pd
df_diff = pd.DataFrame(diff_dx_data)

def color_cell(val):
    if "Muito Alto" in str(val): return "background-color:#ffcdd2; color:#b71c1c; font-weight:600"
    if "Alto" in str(val): return "background-color:#fff9c4; color:#f57f17; font-weight:600"
    return "background-color:#dcedc8; color:#33691e"

styled = df_diff.style.applymap(color_cell, subset=["TEA (FAF) 💜", "TDAH 🔶", "Ansiedade 🟡", "TPB 🔴"])
st.dataframe(styled, use_container_width=True, hide_index=True)

with st.expander("📚 Referências — Diagnóstico Diferencial"):
    st.markdown("""
- **Young et al. (2020)** — ADHD and ASD in women: differential diagnosis and comorbidity. *J Atten Disord*
- **Dell'Osso et al. (2018)** — Autism spectrum disorder and borderline personality disorder. *CNS Spectr*
- **Lai et al. (2015)** — Sex/gender differences and autism: setting the scene. *J Child Psychol Psychiatry*
- **Bargiela et al. (2016)** — The experiences of late-diagnosed women with autism spectrum conditions. *Mol Autism*
""")

# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 7 — TIMELINE DIAGNÓSTICA TÍPICA DO FAF
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>⏳ Trajetória Diagnóstica Típica — FAF</h3></div>', unsafe_allow_html=True)

st.caption("Média baseada em estudos populacionais: mulheres autistas recebem diagnóstico 4–8 anos mais tarde que homens (Rutherford et al., 2016).")

timeline_steps = [
    ("#4caf50", "Infância (0–12 anos)", "Sinais geralmente não percebidos. Alta performance escolar, mimetismo social intenso. Pode haver diagnóstico de ansiedade, TOC ou 'timidez'."),
    ("#ff9800", "Adolescência (12–18 anos)", "Aumento da demanda social → estratégias de mascaramento se intensificam. Diagnósticos comuns: depressão, transtorno alimentar, ansiedade social, TDAH."),
    ("#f44336", "Adulto jovem (18–30 anos)", "Colapso das estratégias de camuflagem em cenários de alta pressão (universidade, trabalho). Burnout autístico frequente. Busca por diagnóstico."),
    ("#9c27b0", "Diagnóstico (média: 35–40 anos em mulheres)", "Frequentemente após autodiagnóstico. Diagnósticos de TPB, bipolar ou depressão refratária podem preceder o diagnóstico de TEA."),
    ("#2196f3", "Pós-diagnóstico", "Ressignificação da história de vida. Redução de auto-culpa. Acesso a suporte adequado e acomodações."),
]

for color, title, desc in timeline_steps:
    st.markdown(
        f"<div class='timeline-step'>"
        f"<div class='timeline-dot' style='background:{color}'></div>"
        f"<div class='timeline-content'>"
        f"<b style='color:{color}'>{title}</b><br>"
        f"<span style='font-size:0.88rem;color:#444'>{desc}</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 8 — SHAP-LIKE BREAKDOWN
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>📊 Contribuição por Modalidade (SHAP-like)</h3></div>', unsafe_allow_html=True)

st.caption("Valores positivos (🔴) aumentam a probabilidade de TEA; negativos (🟢) a reduzem. Barras cinzas = dados ausentes.")

for fc in result.feature_contributions:
    c1, c2, c3 = st.columns([3, 1, 2])
    with c1:
        icon = "✅" if fc.available else "⬜"
        weight_text = " *(indisponível)*" if not fc.available else ""
        st.markdown(f"{icon} **{fc.name}**{weight_text}")
        if fc.note:
            st.caption(fc.note)
    with c2:
        if fc.available and fc.contribution != 0:
            sign = "+" if fc.contribution > 0 else ""
            css  = "contrib-pos" if fc.contribution > 0 else "contrib-neg"
            st.markdown(f"<span class='{css}'>{sign}{fc.contribution:.3f}</span>", unsafe_allow_html=True)
        else:
            st.markdown("—")
    with c3:
        if fc.available:
            direction = "🔴" if fc.contribution > 0 else "🟢"
            st.progress(min(1.0, abs(fc.contribution) * 3), text=direction)
        else:
            st.progress(0.0, text="sem dados")

# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 9 — ROADMAP NEUROTRACE AI
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h3>🔮 Roadmap Neurotrace AI</h3></div>', unsafe_allow_html=True)

roadmap = {
    "🫀 HRV / VFC (Wearable)": "Monitoramento autonômico via smartwatch — diferencia exaustão social de ansiedade primária. Ratio LF/HF elevado é biomarcador de disfunção autonômica em TEA.",
    "⌨️ Dinâmica de Digitação (Keystroke Dynamics)": "Fenotipagem passiva — coeficiente de variação do tempo de tecla como biomarcador sensório-motor, imune à camuflagem consciente.",
    "🗣️ Análise Linguística (PLN + Áudio)": "Micro-diários de áudio — detecta padrões de disfluência e camuflagem vocal. Razão UM/UH, anomalias pronominais e velocidade de fala.",
    "📍 Entropia de Mobilidade (GPS)": "Rotinas espaciais passivas — baixa entropia de localização como marcador de rigidez comportamental e necessidade de previsibilidade.",
    "😴 Sono / Ritmo Circadiano (Actimetria)": "WASO, fragmentação do sono e fusos de sono — correlacionados à desregulação autonômica e esgotamento em TEA.",
}

for feature, description in roadmap.items():
    with st.expander(feature):
        st.markdown(description)

# ═════════════════════════════════════════════════════════════════════════════
# NAVEGAÇÃO
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📋 Questionários", use_container_width=True):
        st.switch_page("pages/5_questionnaires.py")
with col2:
    if st.button("📹 Assessment Eye-Tracking", use_container_width=True):
        st.switch_page("pages/3_assessment.py")
with col3:
    if st.button("📊 Resultados Completos", use_container_width=True):
        st.switch_page("pages/4_results.py")

# ═════════════════════════════════════════════════════════════════════════════
# RODAPÉ REGULATÓRIO
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class='regulatory-footer'>
⚠️ <b>Aviso Regulatório:</b> Esta análise é produzida por um sistema de triagem baseado em IA (SaMD – Software as a Medical Device).
Resultados devem ser interpretados por médico psiquiatra ou neurologista certificado.<br>
Conformidade: LGPD · ANVISA RDC 657/2022 · Princípios XAI FAIR.<br>
Referências: Hull et al. (2019) CAT-Q · Ritvo et al. (2011) RAADS-R · Lai et al. (2015) Sex/Gender & ASD · Bargiela et al. (2016) Late-Diagnosed Women.
</div>
""", unsafe_allow_html=True)
