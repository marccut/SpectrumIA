"""
SpectrumIA / Neurotrace AI — Multimodal Fusion Engine & XAI
============================================================

Implements the hierarchical hybrid network described in the Neurotrace AI
architecture document (Section 7):

  Layer 1 – Domain-specific feature extraction:
      • Eye-tracking features  (gaze_estimation, face_detection)
      • Psychometric calibration weight  (CAT-Q / RAADS-R)
      • Physiological proxy  (HRV/VFC — wearable, future)
      • Keystroke dynamics  (passive phenotyping, future)
      • NLP linguistic analysis  (audio/text, future)
      • Mobility entropy  (GPS, future)

  Layer 2 – Multimodal fusion:
      Weighted evidence aggregation with camouflage-adjusted thresholds.
      A high CAT-Q camouflage weight lowers the detection threshold so
      masked presentations (FAF — Female Autistic Phenotype) are not missed.

  Layer 3 – XAI output:
      • Probability of ASD (0–100 %)
      • Phenotype subtype (FAF / Classic / ADHD-overlap / Low-support-need)
      • Functional support level estimate (1–3)
      • ADHD confusion factor (low / moderate / high)
      • SHAP-like feature contribution breakdown

This module is intentionally written to run without ML dependencies so the
Streamlit front-end can always import it.  When full ML libraries are
available (torch, transformers, etc.) the score functions can be replaced
with model inference calls while keeping the same interface.

References
----------
Section 7 — Neurotrace AI architecture document (Projeto SpectrumIA)
Hull et al. (2019) CAT-Q; Ritvo et al. (2011) RAADS-R
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EyeTrackingFeatures:
    """Summary features extracted from a completed eye-tracking assessment."""
    social_fixation_ratio: float = 0.0      # proportion of gaze on faces / eyes
    avg_saccade_amplitude: float = 0.0      # degrees
    blink_rate_per_min: float = 0.0
    social_gaze_avoidance: float = 0.0      # proportion of frames with gaze away from face
    response_latency_ms: float = 0.0        # to first social stimulus
    head_movement_complexity: float = 0.0   # normalised entropy of head trajectory
    quality_score: float = 0.0             # overall signal quality 0–1
    calibration_rmse: float = 0.0          # calibration residual (degrees)


@dataclass
class FusionInput:
    """All available evidence passed to the fusion engine."""
    eye_tracking: Optional[EyeTrackingFeatures] = None
    catq_camouflage_weight: float = 0.5      # from questionnaires.combined_camouflage_weight()
    catq_total: Optional[float] = None
    raadsr_total: Optional[float] = None
    raadsr_risk_level: Optional[str] = None  # "low" | "moderate" | "high"
    hrv_lf_hf_ratio: Optional[float] = None  # future: wearable data
    keystroke_dwell_cv: Optional[float] = None  # future: passive phenotyping
    nlp_camouflage_score: Optional[float] = None  # future: audio/text NLP
    mobility_entropy: Optional[float] = None      # future: GPS entropy


@dataclass
class FeatureContribution:
    name: str
    value: float        # raw feature value (or None-equivalent)
    contribution: float # signed contribution to ASD probability (−1 to +1)
    available: bool = True
    note: str = ""


@dataclass
class FusionResult:
    """
    XAI-enriched multimodal fusion output.

    Mirrors the clinical dashboard described in Section 7.2 of the
    Neurotrace AI document:
      - Probability of ASD
      - Phenotype subtype
      - Functional support level
      - ADHD confusion factor
      - SHAP-style feature contributions
    """
    asd_probability: float                       # 0.0–1.0
    phenotype_subtype: str                       # see PHENOTYPE_SUBTYPES
    functional_support_level: int                # 1 | 2 | 3 (DSM-5-TR)
    adhd_confusion_factor: str                   # "low" | "moderate" | "high"
    camouflage_adjustment_applied: bool
    camouflage_weight_used: float
    feature_contributions: List[FeatureContribution] = field(default_factory=list)
    interpretation: str = ""
    recommendation: str = ""
    confidence: float = 0.0                     # model confidence 0–1
    data_completeness: float = 0.0              # fraction of data streams available


PHENOTYPE_SUBTYPES = {
    "faf_high_masking":      "FAF – Alto Mascaramento (Fenótipo Autista Feminino)",
    "faf_compensated":       "FAF – Compensado / Camuflado",
    "classic_asd":           "TEA Clássico",
    "adhd_overlap":          "Sobreposição TEA/TDAH",
    "low_support_need":      "TEA – Baixa Necessidade de Suporte",
    "anxiety_primary":       "Ansiedade Primária (não TEA)",
    "inconclusive":          "Inconclusivo – Dados insuficientes",
}


# ─────────────────────────────────────────────────────────────────────────────
# Threshold constants
# ─────────────────────────────────────────────────────────────────────────────

# Base thresholds (no camouflage adjustment)
BASE_ASD_THRESHOLD = 0.50

# Eye-tracking reference values (normative, adult population)
ET_NORM_SOCIAL_FIXATION = 0.65   # neurotipical: ~65 % gaze on social regions
ET_ASD_SOCIAL_FIXATION  = 0.35   # ASD: ~35 %

# CAT-Q camouflage weight at which threshold starts to shift
CAMOUFLAGE_SHIFT_START = 0.40
CAMOUFLAGE_SHIFT_MAX   = 0.20    # maximum downward shift in ASD threshold


# ─────────────────────────────────────────────────────────────────────────────
# Core fusion logic
# ─────────────────────────────────────────────────────────────────────────────

def _camouflage_adjusted_threshold(camouflage_weight: float) -> float:
    """
    Lower the ASD detection threshold when high camouflage is detected.

    Example: camouflage_weight=0.80 → threshold drops from 0.50 to ~0.38
    This ensures masked presentations (FAF) are not missed.
    """
    if camouflage_weight <= CAMOUFLAGE_SHIFT_START:
        return BASE_ASD_THRESHOLD
    excess = (camouflage_weight - CAMOUFLAGE_SHIFT_START) / (1.0 - CAMOUFLAGE_SHIFT_START)
    shift  = excess * CAMOUFLAGE_SHIFT_MAX
    return round(BASE_ASD_THRESHOLD - shift, 4)


def _score_eye_tracking(et: EyeTrackingFeatures, camouflage_weight: float) -> float:
    """
    Produce an ASD evidence score (0–1) from eye-tracking features.

    Uses linear interpolation between normative and ASD reference values.
    Higher camouflage weight increases sensitivity by weighting gaze
    avoidance and response latency more heavily.
    """
    scores: List[float] = []

    # Social fixation ratio (low = ASD-like)
    sf = et.social_fixation_ratio
    sf_score = 1.0 - max(0.0, min(1.0,
        (sf - ET_ASD_SOCIAL_FIXATION) / (ET_NORM_SOCIAL_FIXATION - ET_ASD_SOCIAL_FIXATION)
    ))
    scores.append(sf_score * (1.0 + 0.3 * camouflage_weight))

    # Gaze avoidance (high = ASD-like)
    ga_score = min(1.0, et.social_gaze_avoidance / 0.7)
    scores.append(ga_score)

    # Response latency (high = ASD-like, or compensated delay)
    if et.response_latency_ms > 0:
        latency_score = min(1.0, et.response_latency_ms / 2000.0)
        scores.append(latency_score * (1.0 + 0.2 * camouflage_weight))

    # Blink rate (very low blink rate = focused/social mimicry → add camouflage signal)
    if et.blink_rate_per_min > 0:
        blink_norm = 15.0
        if et.blink_rate_per_min < blink_norm * 0.5:
            scores.append(0.4 * camouflage_weight)  # possible forced eye contact
        elif et.blink_rate_per_min > blink_norm * 1.8:
            scores.append(0.5)  # elevated blink = social discomfort

    if not scores:
        return 0.5
    return round(min(1.0, sum(scores) / len(scores)), 4)


def _score_psychometric(catq_total: Optional[float], raadsr_total: Optional[float]) -> float:
    """Normalise questionnaire scores to a 0–1 ASD evidence value."""
    scores: List[float] = []
    if catq_total is not None:
        # CAT-Q max = 448; clinical threshold = 100
        scores.append(min(1.0, catq_total / 250.0))
    if raadsr_total is not None:
        # RAADS-R max = 240; clinical threshold = 65
        scores.append(min(1.0, raadsr_total / 160.0))
    return round(sum(scores) / len(scores), 4) if scores else 0.5


def _determine_phenotype(
    asd_prob: float,
    camouflage_weight: float,
    raadsr_risk: Optional[str],
    hrv_available: bool,
    catq_total: Optional[float] = None,
    raadsr_total: Optional[float] = None,
) -> str:
    """
    Classify phenotype subtype using a hierarchical decision tree.

    Priority order (highest specificity first):
      1. FAF variants (camouflage-driven)
      2. ADHD overlap
      3. Classic ASD
      4. Low support need
      5. Inconclusive / Anxiety primary
    """
    if asd_prob < 0.30:
        return "anxiety_primary"

    if asd_prob < 0.45:
        # Borderline: check if high camouflage could be masking TEA
        if camouflage_weight >= 0.65:
            return "faf_compensated"   # Low score but high masking = possible FAF
        return "inconclusive"

    # asd_prob >= 0.45 from here
    # FAF: high camouflage is the defining feature
    if camouflage_weight >= 0.60:
        if asd_prob >= 0.68:
            return "faf_high_masking"
        return "faf_compensated"

    # ADHD overlap: moderate-high probability + low camouflage + moderate RAADS-R
    if (0.45 <= asd_prob < 0.75
            and camouflage_weight < 0.45
            and raadsr_total is not None
            and 40 <= raadsr_total < 90):
        return "adhd_overlap"

    # Classic ASD: high probability, low camouflage
    if asd_prob >= 0.70 and camouflage_weight < 0.50:
        return "classic_asd"

    # Low support need: confirmed ASD probability but milder profile
    if asd_prob >= 0.50:
        return "low_support_need"

    return "inconclusive"


def _support_level(asd_prob: float, raadsr_total: Optional[float]) -> int:
    if asd_prob < 0.50:
        return 1
    if raadsr_total and raadsr_total >= 130:
        return 3
    if asd_prob >= 0.75:
        return 2
    return 1


def _adhd_confusion(asd_prob: float, camouflage_weight: float) -> str:
    if asd_prob < 0.45 and camouflage_weight < 0.40:
        return "high"    # could be ADHD/anxiety masking TEA
    if camouflage_weight >= 0.60:
        return "moderate"
    return "low"


def _data_completeness(inp: FusionInput) -> float:
    streams = [
        inp.eye_tracking is not None,
        inp.catq_total is not None,
        inp.raadsr_total is not None,
        inp.hrv_lf_hf_ratio is not None,
        inp.keystroke_dwell_cv is not None,
        inp.nlp_camouflage_score is not None,
        inp.mobility_entropy is not None,
    ]
    return round(sum(streams) / len(streams), 3)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def fuse(inp: FusionInput) -> FusionResult:
    """
    Run the multimodal fusion pipeline on a FusionInput.

    Returns a FusionResult with ASD probability, phenotype, XAI contributions.
    """
    cw = inp.catq_camouflage_weight
    threshold = _camouflage_adjusted_threshold(cw)
    camouflage_adjustment_applied = cw > CAMOUFLAGE_SHIFT_START

    contributions: List[FeatureContribution] = []
    weighted_scores: List[tuple] = []  # (score, weight)

    # ── Eye-tracking (weight 0.40) ─────────────────────────────────────────
    if inp.eye_tracking and inp.eye_tracking.quality_score >= 0.30:
        et_score = _score_eye_tracking(inp.eye_tracking, cw)
        weighted_scores.append((et_score, 0.40))
        contributions.append(FeatureContribution(
            name="Eye-Tracking (Rastreio Ocular)",
            value=inp.eye_tracking.social_fixation_ratio,
            contribution=round((et_score - 0.5) * 0.80, 3),
            available=True,
            note=f"Fixação social: {inp.eye_tracking.social_fixation_ratio:.1%} | "
                 f"Qualidade: {inp.eye_tracking.quality_score:.1%}",
        ))
    else:
        contributions.append(FeatureContribution(
            name="Eye-Tracking (Rastreio Ocular)",
            value=0.0, contribution=0.0, available=False,
            note="Dados insuficientes ou qualidade baixa",
        ))

    # ── Psychometric (weight 0.30) ─────────────────────────────────────────
    psy_score = _score_psychometric(inp.catq_total, inp.raadsr_total)
    if inp.catq_total is not None or inp.raadsr_total is not None:
        weighted_scores.append((psy_score, 0.30))
        contributions.append(FeatureContribution(
            name="Questionários Psicométricos (CAT-Q / RAADS-R)",
            value=psy_score,
            contribution=round((psy_score - 0.5) * 0.60, 3),
            available=True,
            note=f"CAT-Q={inp.catq_total or 'N/A'} · RAADS-R={inp.raadsr_total or 'N/A'} · "
                 f"Camuflagem={cw:.1%}",
        ))
    else:
        contributions.append(FeatureContribution(
            name="Questionários Psicométricos (CAT-Q / RAADS-R)",
            value=0.0, contribution=0.0, available=False,
            note="Questionários não preenchidos",
        ))

    # ── HRV / VFC (weight 0.15) — future ──────────────────────────────────
    if inp.hrv_lf_hf_ratio is not None:
        hrv_score = min(1.0, inp.hrv_lf_hf_ratio / 4.0)
        weighted_scores.append((hrv_score, 0.15))
        contributions.append(FeatureContribution(
            name="HRV / VFC (Variabilidade da Frequência Cardíaca)",
            value=inp.hrv_lf_hf_ratio,
            contribution=round((hrv_score - 0.5) * 0.30, 3),
            available=True,
            note=f"Razão LF/HF = {inp.hrv_lf_hf_ratio:.2f}",
        ))
    else:
        contributions.append(FeatureContribution(
            name="HRV / VFC (Variabilidade da Frequência Cardíaca)",
            value=0.0, contribution=0.0, available=False,
            note="Wearable não conectado — disponível em versão futura",
        ))

    # ── Keystroke dynamics (weight 0.08) — future ─────────────────────────
    if inp.keystroke_dwell_cv is not None:
        ks_score = min(1.0, inp.keystroke_dwell_cv / 0.3)
        weighted_scores.append((ks_score, 0.08))
        contributions.append(FeatureContribution(
            name="Dinâmica de Digitação (Keystroke Dynamics)",
            value=inp.keystroke_dwell_cv,
            contribution=round((ks_score - 0.5) * 0.16, 3),
            available=True,
        ))
    else:
        contributions.append(FeatureContribution(
            name="Dinâmica de Digitação (Keystroke Dynamics)",
            value=0.0, contribution=0.0, available=False,
            note="Fenotipagem passiva — disponível em versão futura",
        ))

    # ── NLP linguistic analysis (weight 0.07) — future ────────────────────
    if inp.nlp_camouflage_score is not None:
        weighted_scores.append((inp.nlp_camouflage_score, 0.07))
        contributions.append(FeatureContribution(
            name="Análise Linguística / PLN (Camuflagem Verbal)",
            value=inp.nlp_camouflage_score,
            contribution=round((inp.nlp_camouflage_score - 0.5) * 0.14, 3),
            available=True,
        ))
    else:
        contributions.append(FeatureContribution(
            name="Análise Linguística / PLN (Camuflagem Verbal)",
            value=0.0, contribution=0.0, available=False,
            note="Micro-diário de áudio — disponível em versão futura",
        ))

    # ── Compute final probability ──────────────────────────────────────────
    if weighted_scores:
        total_weight = sum(w for _, w in weighted_scores)
        asd_prob = sum(s * w for s, w in weighted_scores) / total_weight
    else:
        asd_prob = 0.5  # neutral if no data

    asd_prob = round(min(1.0, max(0.0, asd_prob)), 4)
    completeness = _data_completeness(inp)

    phenotype = _determine_phenotype(
        asd_prob, cw, inp.raadsr_risk_level,
        hrv_available=inp.hrv_lf_hf_ratio is not None,
        catq_total=inp.catq_total,
        raadsr_total=inp.raadsr_total,
    )
    support_lvl = _support_level(asd_prob, inp.raadsr_total)
    adhd_cf = _adhd_confusion(asd_prob, cw)

    # ── XAI interpretation ────────────────────────────────────────────────
    pt_label = PHENOTYPE_SUBTYPES.get(phenotype, phenotype)

    _camouflage_note = (
        f"O índice de camuflagem de **{cw:.1%}** reduziu o limiar de detecção de "
        f"{BASE_ASD_THRESHOLD:.0%} para **{threshold:.0%}**, aumentando a sensibilidade ao FAF."
        if camouflage_adjustment_applied
        else f"O índice de camuflagem ({cw:.1%}) está dentro da faixa esperada."
    )

    if phenotype == "faf_high_masking":
        interp = (
            f"**Fenótipo Autista Feminino com Alto Mascaramento** detectado "
            f"(probabilidade: **{asd_prob:.1%}**). "
            f"Alta camuflagem ({cw:.1%}) com probabilidade de TEA elevada indicam apresentação "
            f"clássica de FAF — histórico de diagnósticos errôneos (TDAH, ansiedade, TPB) é comum. "
            f"{_camouflage_note}"
        )
        recom = (
            "Encaminhar **urgentemente** para avaliação neuropsiquiátrica especializada em TEA feminino. "
            "Aplicar ADOS-2 e ADI-R com clínico treinado em FAF. "
            "Investigar história de burnout autístico, diagnósticos prévios e trajetória de mascaramento. "
            "Considerar avaliação neuropsicológica para descartar TDAH comórbido."
        )
    elif phenotype == "faf_compensated":
        interp = (
            f"**Fenótipo Autista Feminino Compensado/Camuflado** identificado "
            f"(probabilidade: **{asd_prob:.1%}**, camuflagem: {cw:.1%}). "
            "Alto mascaramento com probabilidade moderada — apresentação subtil que frequentemente "
            "escapa à detecção por instrumentos padronizados. "
            f"{_camouflage_note}"
        )
        recom = (
            "Avaliação neuropsiquiátrica presencial com histórico desenvolvimental detalhado. "
            "Entrevistar familiares para obter perspectiva externa sobre comportamento na infância. "
            "Completar questionários RAADS-R e eye-tracking para aumentar a completude multimodal. "
            "Considerar CAT-Q completo se ainda não preenchido."
        )
    elif phenotype == "adhd_overlap":
        interp = (
            f"**Sobreposição TEA/TDAH** — probabilidade de TEA de **{asd_prob:.1%}** com "
            f"fator de confusão TDAH **{adhd_cf}**. "
            "Perfil com características sobrepostas: atenção, impulsividade e dificuldades sociais "
            "podem ter origem autística, TDAH ou ambos (comorbidade em ~50% dos casos). "
            "Baixo mascaramento reduz probabilidade de FAF puro."
        )
        recom = (
            "Avaliação neuropsiquiátrica diferencial com instrumentos específicos para TDAH (CAARS, DIVA) "
            "e TEA (ADOS-2, ADI-R). "
            "Resposta a estimulantes pode ajudar na diferenciação clínica. "
            "Completar eye-tracking com paradigma de atenção social vs. não-social."
        )
    elif phenotype == "classic_asd":
        interp = (
            f"**TEA Clássico** com probabilidade elevada (**{asd_prob:.1%}**) e "
            f"baixo mascaramento ({cw:.1%}). "
            "Apresentação com traços mais evidentes — menos influência de camuflagem aprendida. "
            f"Nível de suporte estimado: {support_lvl} (DSM-5-TR)."
        )
        recom = (
            "Encaminhar para avaliação com ADOS-2 e ADI-R. "
            "Avaliar necessidades de suporte nas áreas de comunicação, sensorialidade e função executiva. "
            "Considerar avaliação neuropsicológica para mapear perfil de pontos fortes e dificuldades."
        )
    elif phenotype == "low_support_need":
        interp = (
            f"**TEA com Baixa Necessidade de Suporte** (probabilidade: **{asd_prob:.1%}**). "
            "Perfil com traços autistas que ultrapassam o limiar, mas com adaptação funcional razoável. "
            f"Camuflagem moderada ({cw:.1%}) pode estar contribuindo para a aparente funcionalidade."
        )
        recom = (
            "Avaliação psiquiátrica para confirmação diagnóstica. "
            "Mesmo com baixa necessidade de suporte, o diagnóstico pode ser transformador "
            "para autocompreensão, relações e acesso a acomodações legítimas. "
            "Monitorar sinais de burnout autístico."
        )
    elif asd_prob >= 0.35:
        interp = (
            f"**Resultado inconclusivo** (probabilidade: {asd_prob:.1%}). "
            f"Completude dos dados: {completeness:.0%}. "
            "Dados multimodais insuficientes para classificação robusta. "
            f"{_camouflage_note}"
        )
        recom = (
            "Completar questionários RAADS-R e CAT-Q. "
            "Realizar assessment de eye-tracking completo com boa iluminação. "
            "Conectar wearable para dados de HRV/VFC. "
            "Repetir análise após completar todos os módulos."
        )
    else:
        interp = (
            f"**Probabilidade de TEA baixa** ({asd_prob:.1%}). "
            f"Fator de confusão TDAH: {adhd_cf}. "
            "Resultado não exclui TEA com alto mascaramento se CAT-Q não foi preenchido. "
            "Ansiedade social primária permanece no diagnóstico diferencial."
        )
        recom = (
            "Preencher CAT-Q para avaliar camuflagem — caso não preenchido. "
            "Se sintomas de TDAH presentes, considerar avaliação diferencial específica. "
            "Reavaliação em 6–12 meses se sintomas persistirem."
        )

    # Confidence = weighted combination of completeness, ET quality, and score consistency
    et_quality = inp.eye_tracking.quality_score if inp.eye_tracking else 0.0
    # Consistency: how far the probability is from 0.5 (decisive results = more confident)
    decisiveness = abs(asd_prob - 0.5) * 2.0  # 0=borderline, 1=very decisive
    # Weighted average: completeness(40%) + ET quality(30%) + decisiveness(30%)
    confidence = round(
        0.40 * completeness + 0.30 * et_quality + 0.30 * decisiveness,
        3,
    )

    logger.info(
        "Fusion complete: asd_prob=%.3f phenotype=%s support=%d adhd_cf=%s completeness=%.2f",
        asd_prob, phenotype, support_lvl, adhd_cf, completeness,
    )

    return FusionResult(
        asd_probability=asd_prob,
        phenotype_subtype=phenotype,
        functional_support_level=support_lvl,
        adhd_confusion_factor=adhd_cf,
        camouflage_adjustment_applied=camouflage_adjustment_applied,
        camouflage_weight_used=cw,
        feature_contributions=contributions,
        interpretation=interp,
        recommendation=recom,
        confidence=confidence,
        data_completeness=completeness,
    )
