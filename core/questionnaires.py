"""
SpectrumIA / Neurotrace AI — Psychometric Questionnaire Engine
==============================================================

Implements digitised versions of the validated screening instruments
recommended in the Neurotrace AI architecture document:

  • CAT-Q  — Camouflaging Autistic Traits Questionnaire (64 items, 3 factors)
  • RAADS-R — Ritvo Autism Asperger Diagnostic Scale – Revised (80 items, 4 sub-scales)

Both instruments are used as *calibration filters* for the multimodal AI engine:
high masking/compensation scores adjust detection thresholds so that subtle
autistic presentations are not missed due to learned social camouflage.

References
----------
CAT-Q:  Hull et al. (2019) – doi:10.1007/s10803-018-3821-5
RAADS-R: Ritvo et al. (2011) – doi:10.1007/s10803-010-1133-5
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class QuestionItem:
    id: int
    text: str
    subscale: str
    reverse_scored: bool = False


@dataclass
class QuestionnaireResult:
    name: str
    total_score: float
    subscale_scores: Dict[str, float]
    interpretation: str
    risk_level: str          # "low" | "moderate" | "high"
    camouflage_weight: float  # 0.0–1.0 used by multimodal fusion engine
    raw_responses: Dict[int, int] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# CAT-Q  (Camouflaging Autistic Traits Questionnaire)
# ─────────────────────────────────────────────────────────────────────────────

CATQ_ITEMS: List[QuestionItem] = [
    # --- Assimilation (items 1-21) ---
    QuestionItem(1,  "Eu estudo o comportamento das outras pessoas para aprender como devo agir em situações sociais.", "assimilation"),
    QuestionItem(2,  "Em situações sociais, eu não sei bem como agir, então eu imito o que as outras pessoas fazem.", "assimilation"),
    QuestionItem(3,  "Eu me espelho em outras pessoas para aprender como me comunicar com os outros.", "assimilation"),
    QuestionItem(4,  "Eu aprendo como devo me comportar em situações sociais imitando outras pessoas.", "assimilation"),
    QuestionItem(5,  "Quando estou em situações sociais, eu copio as expressões e gestos das pessoas ao meu redor.", "assimilation"),
    QuestionItem(6,  "Eu ajusto como me comporto dependendo das pessoas com quem estou.", "assimilation"),
    QuestionItem(7,  "Eu mudo minha linguagem corporal ou tom de voz dependendo de com quem estou falando.", "assimilation"),
    QuestionItem(8,  "Eu uso o mesmo estilo de comunicação com todos.", "assimilation", reverse_scored=True),
    QuestionItem(9,  "Eu aprendo expressões sociais (piadas, frases-feitas) pela observação dos outros.", "assimilation"),
    QuestionItem(10, "Eu estudo a linguagem corporal das pessoas para entender o que elas realmente querem dizer.", "assimilation"),
    QuestionItem(11, "Em situações sociais, eu observo as pessoas ao meu redor para saber como me comportar.", "assimilation"),
    QuestionItem(12, "Eu aprendo as regras sociais 'explicitamente', não intuitivamente.", "assimilation"),
    QuestionItem(13, "Eu me preparo para interações sociais praticando ou ensaiando o que vou dizer.", "assimilation"),
    QuestionItem(14, "Eu reflito sobre situações sociais para identificar o que fiz de errado.", "assimilation"),
    QuestionItem(15, "Em situações sociais, eu frequentemente imito o humor ou a atitude emocional dos outros.", "assimilation"),
    QuestionItem(16, "Eu adapto meu senso de humor ao das pessoas com quem estou.", "assimilation"),
    QuestionItem(17, "Eu observo e analiso como as pessoas interagem umas com as outras.", "assimilation"),
    QuestionItem(18, "Eu frequentemente leio sobre como o comportamento humano funciona.", "assimilation"),
    QuestionItem(19, "Eu pesquiso como me comportar em situações sociais.", "assimilation"),
    QuestionItem(20, "Em grupos, eu imito o comportamento da pessoa mais dominante.", "assimilation"),
    QuestionItem(21, "Eu pratico certas expressões faciais para que pareçam naturais.", "assimilation"),

    # --- Mascaramento (items 22-42) ---
    QuestionItem(22, "Antes de interações sociais, eu pratico o que vou dizer.", "masking"),
    QuestionItem(23, "Em situações sociais, eu escondo meu verdadeiro eu.", "masking"),
    QuestionItem(24, "Eu finjo ser mais positivo do que realmente estou.", "masking"),
    QuestionItem(25, "Eu finjo estar interessado em coisas que não me interessam para agradar os outros.", "masking"),
    QuestionItem(26, "Eu me esforço para manter contato visual mesmo que não queira.", "masking"),
    QuestionItem(27, "Eu finjo que entendi uma piada mesmo quando não entendi.", "masking"),
    QuestionItem(28, "Quando interajo com os outros, me sinto como se estivesse representando um papel.", "masking"),
    QuestionItem(29, "Eu esforço-me para parecer 'normal'.", "masking"),
    QuestionItem(30, "Eu me comporto de forma diferente em público e quando estou sozinho.", "masking"),
    QuestionItem(31, "Eu supresso comportamentos que sei que são estranhos para os outros.", "masking"),
    QuestionItem(32, "Eu tenho uma 'persona social' que uso em público.", "masking"),
    QuestionItem(33, "Eu evito falar sobre meus interesses para não entediar os outros.", "masking"),
    QuestionItem(34, "Eu forço expressões faciais em situações sociais para corresponder ao que é esperado.", "masking"),
    QuestionItem(35, "Eu oculto o quanto é difícil para mim lidar com situações sociais.", "masking"),
    QuestionItem(36, "Eu fingiu estar bem quando não estou.", "masking"),
    QuestionItem(37, "Eu escondo minha ansiedade em situações sociais.", "masking"),
    QuestionItem(38, "As pessoas não percebem que estou confuso sobre o que fazer em situações sociais.", "masking"),
    QuestionItem(39, "Eu sempre me comporto bem em público, mesmo que seja muito esforço.", "masking"),
    QuestionItem(40, "Eu consigo que as pessoas não notem minhas dificuldades em lidar com situações sociais.", "masking"),
    QuestionItem(41, "Eu raramente revelo a minha ansiedade social.", "masking"),
    QuestionItem(42, "Eu me faço de entendido quando na verdade estou confuso.", "masking"),

    # --- Compensação (items 43-64) ---
    QuestionItem(43, "Eu desenvolvi estratégias pessoais para lidar com situações sociais difíceis.", "compensation"),
    QuestionItem(44, "Eu aprendi as 'regras' de conversação por análise racional.", "compensation"),
    QuestionItem(45, "Eu uso roteiros sociais memorizados em conversas.", "compensation"),
    QuestionItem(46, "Eu desenvolvi um conjunto de regras para situações sociais.", "compensation"),
    QuestionItem(47, "Eu consigo disfarçar minhas dificuldades em situações sociais.", "compensation"),
    QuestionItem(48, "Eu planejo com antecedência o que vou dizer em conversas.", "compensation"),
    QuestionItem(49, "Eu me sinto sobrecarregado depois de interações sociais.", "compensation"),
    QuestionItem(50, "Eu aprendi quais expressões faciais usar em situações específicas.", "compensation"),
    QuestionItem(51, "Eu uso técnicas aprendidas para parecer mais confiante do que sou.", "compensation"),
    QuestionItem(52, "Eu pesquiso explicitamente convenções sociais para aplicá-las.", "compensation"),
    QuestionItem(53, "Eu sei como agir em situações sociais, mas não entendo instintivamente por quê.", "compensation"),
    QuestionItem(54, "Eu gerencio meu comportamento em situações sociais para parecer aceitável.", "compensation"),
    QuestionItem(55, "Eu mantenho um contato visual calculado, não natural.", "compensation"),
    QuestionItem(56, "Eu monitoro minha linguagem corporal para que pareça apropriada.", "compensation"),
    QuestionItem(57, "Eu sinto que exerço um esforço enorme nas interações sociais.", "compensation"),
    QuestionItem(58, "Depois de interações sociais, eu preciso de tempo a sós para me recuperar.", "compensation"),
    QuestionItem(59, "Fazer coisas que a maioria das pessoas acha fácil socialmente me esgota.", "compensation"),
    QuestionItem(60, "Situações sociais me cansam mais do que a maioria das pessoas.", "compensation"),
    QuestionItem(61, "Eu sinto que tenho que 'ligar' o meu cérebro social quando estou com pessoas.", "compensation"),
    QuestionItem(62, "Minhas habilidades sociais foram desenvolvidas por esforço consciente.", "compensation"),
    QuestionItem(63, "Eu me sinto como uma pessoa diferente quando estou com diferentes grupos de pessoas.", "compensation"),
    QuestionItem(64, "Depois de eventos sociais, analiso o que disse para ver se cometi erros.", "compensation"),
]

CATQ_SUBSCALE_RANGES = {
    "assimilation": (1, 21),
    "masking": (22, 42),
    "compensation": (43, 64),
}

CATQ_CLINICAL_THRESHOLD = 100  # Scores ≥100 indicate significant camouflage
CATQ_SCALE = 7                  # 1–7 Likert


def score_catq(responses: Dict[int, int]) -> QuestionnaireResult:
    """
    Score the CAT-Q from a dict of {item_id: likert_score (1-7)}.

    Returns a QuestionnaireResult with total, subscale scores and a
    camouflage_weight (0–1) used by the multimodal fusion engine.
    """
    subscale_totals: Dict[str, float] = {"assimilation": 0, "masking": 0, "compensation": 0}
    subscale_counts: Dict[str, int] = {"assimilation": 0, "masking": 0, "compensation": 0}
    total = 0.0

    for item in CATQ_ITEMS:
        score = responses.get(item.id)
        if score is None:
            continue
        # Reverse-scored items: (scale + 1) - score
        if item.reverse_scored:
            score = (CATQ_SCALE + 1) - score
        subscale_totals[item.subscale] += score
        subscale_counts[item.subscale] += 1
        total += score

    subscale_scores = {
        k: round(v, 1) for k, v in subscale_totals.items()
    }

    # Normalise camouflage weight to 0–1 (max possible = 64 * 7 = 448)
    max_score = len(CATQ_ITEMS) * CATQ_SCALE
    camouflage_weight = min(total / max_score, 1.0) if max_score else 0.0

    # Clinical interpretation
    if total >= 130:
        risk_level = "high"
        interpretation = (
            "Escores muito elevados de camuflagem (≥130). "
            "Alta probabilidade de FAF (Fenótipo Autista Feminino) com mascaramento significativo. "
            "O limiar de detecção do motor multimodal será ajustado para maior sensibilidade."
        )
    elif total >= CATQ_CLINICAL_THRESHOLD:
        risk_level = "moderate"
        interpretation = (
            f"Camuflagem significativa (score={total:.0f}, limiar={CATQ_CLINICAL_THRESHOLD}). "
            "Sugestivo de estratégias compensatórias ativas. Avaliação multimodal recomendada."
        )
    else:
        risk_level = "low"
        interpretation = (
            f"Níveis de camuflagem dentro do esperado para a população geral (score={total:.0f}). "
            "Análise multimodal prossegue com parâmetros padrão."
        )

    logger.info(
        "CAT-Q scored: total=%.1f risk=%s camouflage_weight=%.3f",
        total, risk_level, camouflage_weight,
    )

    return QuestionnaireResult(
        name="CAT-Q",
        total_score=round(total, 1),
        subscale_scores=subscale_scores,
        interpretation=interpretation,
        risk_level=risk_level,
        camouflage_weight=round(camouflage_weight, 3),
        raw_responses=responses,
    )


# ─────────────────────────────────────────────────────────────────────────────
# RAADS-R  (Ritvo Autism Asperger Diagnostic Scale – Revised)
# ─────────────────────────────────────────────────────────────────────────────

RAADSR_ITEMS: List[QuestionItem] = [
    # Language (items 1-7)
    QuestionItem(1,  "Quando as pessoas usam meu nome em conversas, isso não me chama a atenção.", "language"),
    QuestionItem(2,  "Quando estava na escola, eu sentia que as outras crianças sabiam fazer coisas que eu não sabia.", "language"),
    QuestionItem(3,  "Quando falo muito, tento parar antes que as pessoas fiquem entediadas.", "language"),
    QuestionItem(4,  "Eu me incomodo muito quando as regras de etiqueta são violadas.", "language"),
    QuestionItem(5,  "Eu costumo interpretar as falas das pessoas ao pé da letra, não metaforicamente.", "language"),
    QuestionItem(6,  "Às vezes, palavras ou frases ficam repetindo-se em minha mente.", "language"),
    QuestionItem(7,  "Muitas vezes não sei o que dizer quando as pessoas me cumprimentam.", "language"),

    # Social relatedness (items 8-31)
    QuestionItem(8,  "Eu me comporto da mesma forma em todas as situações sociais.", "social"),
    QuestionItem(9,  "Fazer amigos é muito difícil para mim.", "social"),
    QuestionItem(10, "Eu não me incomodo se minha rotina diária é alterada.", "social", reverse_scored=True),
    QuestionItem(11, "Em conversas, eu tenho dificuldade em descobrir a hora certa de falar.", "social"),
    QuestionItem(12, "Às vezes não sei como agir com outras pessoas.", "social"),
    QuestionItem(13, "Eu sou considerado estranho e excêntrico pelos outros.", "social"),
    QuestionItem(14, "Eu não sei como fazer amizades.", "social"),
    QuestionItem(15, "Me relaciono melhor com crianças ou pessoas mais velhas do que com pessoas da minha idade.", "social"),
    QuestionItem(16, "Eu costumo falar sobre as mesmas coisas repetidamente com outras pessoas.", "social"),
    QuestionItem(17, "Em interações sociais, eu não sei bem quando é minha vez de falar.", "social"),
    QuestionItem(18, "Às vezes falo muito sobre um assunto que me interessa.", "social"),
    QuestionItem(19, "Eu não entendo quando é esperado que eu ria numa conversa.", "social"),
    QuestionItem(20, "Eu tenho dificuldade em entender as 'regras' não escritas dos grupos sociais.", "social"),
    QuestionItem(21, "Eu evito situações sociais sempre que posso.", "social"),
    QuestionItem(22, "Quando estou em grupos sociais, eu prefiro observar a participar.", "social"),
    QuestionItem(23, "As pessoas me dizem que sou inocente demais e que facilmente sou enganado.", "social"),
    QuestionItem(24, "Eu prefiro fazer as coisas do mesmo jeito repetidamente.", "social"),
    QuestionItem(25, "Eu não sei como iniciar ou terminar uma conversa.", "social"),
    QuestionItem(26, "Me sinto sobrecarregado em situações sociais, especialmente quando há muito barulho ou movimento.", "social"),
    QuestionItem(27, "Eu tenho rituais que preciso realizar mesmo sabendo que outros os consideram estranhos.", "social"),
    QuestionItem(28, "Eu me sinto muito angustiado quando as coisas mudam de forma inesperada.", "social"),
    QuestionItem(29, "Me relaciono melhor com animais do que com pessoas.", "social"),
    QuestionItem(30, "Não consigo descobrir o que estão pensando somente ao olhar para elas.", "social"),
    QuestionItem(31, "Tenho dificuldade em reconhecer a face das pessoas.", "social"),

    # Sensory motor (items 32-49)
    QuestionItem(32, "Quando crianças brincam juntas, eu preferia observar a participar.", "sensory_motor"),
    QuestionItem(33, "Eu tenho dificuldade em saber quando preciso ir ao banheiro até que já seja urgente.", "sensory_motor"),
    QuestionItem(34, "Eu faço balanceios com o corpo, batidas nos dedos ou outros movimentos repetitivos.", "sensory_motor"),
    QuestionItem(35, "Eu tenho padrões muito rigorosos de comportamento que me perturbam se alterados.", "sensory_motor"),
    QuestionItem(36, "Eu sou muito sensível ao toque.", "sensory_motor"),
    QuestionItem(37, "Barulhos que outros ignoram me incomodam muito.", "sensory_motor"),
    QuestionItem(38, "Algumas texturas de tecido me incomodam muito.", "sensory_motor"),
    QuestionItem(39, "Luzes brilhantes ou cintilantes me incomodam muito.", "sensory_motor"),
    QuestionItem(40, "Eu tenho pouca coordenação motora.", "sensory_motor"),
    QuestionItem(41, "Tenho dificuldade em julgar a distância ou a velocidade de objetos.", "sensory_motor"),
    QuestionItem(42, "Eu ando nas pontas dos pés.", "sensory_motor"),
    QuestionItem(43, "Certos cheiros me incomodam mais do que a maioria das pessoas.", "sensory_motor"),
    QuestionItem(44, "Eu tenho dificuldade em sentir dor.", "sensory_motor"),
    QuestionItem(45, "Eu tenho problemas em filtrar sons de fundo quando estou falando com alguém.", "sensory_motor"),
    QuestionItem(46, "Meus sentidos são mais agudos do que os da maioria das pessoas.", "sensory_motor"),
    QuestionItem(47, "Eu tenho padrões incomuns de fala (muito alto, muito baixo, ritmo atípico).", "sensory_motor"),
    QuestionItem(48, "Minha linguagem corporal é difícil de entender para os outros.", "sensory_motor"),
    QuestionItem(49, "Eu tenho dificuldade em integrar o que estou ouvindo e o que estou vendo ao mesmo tempo.", "sensory_motor"),

    # Circumscribed interests (items 50-64)
    QuestionItem(50, "Tenho interesses muito intensos que são incomuns para a maioria das pessoas.", "circumscribed_interests"),
    QuestionItem(51, "Quando me interesso por algo, me concentro completamente nisso.", "circumscribed_interests"),
    QuestionItem(52, "Memorizo facilmente informações sobre tópicos que me interessam.", "circumscribed_interests"),
    QuestionItem(53, "Eu preciso saber tudo sobre determinados assuntos que me interessam.", "circumscribed_interests"),
    QuestionItem(54, "Fico frustrado quando conversas mudam de assunto para algo que não me interessa.", "circumscribed_interests"),
    QuestionItem(55, "Sei mais sobre meus tópicos de interesse do que a maioria das pessoas.", "circumscribed_interests"),
    QuestionItem(56, "Tenho coleções de objetos ou listas de tópicos específicos.", "circumscribed_interests"),
    QuestionItem(57, "Organizo e categorizo coisas com muito rigor.", "circumscribed_interests"),
    QuestionItem(58, "Me incomoda muito quando alguém mexe nas minhas coisas.", "circumscribed_interests"),
    QuestionItem(59, "Eu tenho interesses muito específicos e intensos que mudaram ao longo dos anos.", "circumscribed_interests"),
    QuestionItem(60, "Aprendo melhor por meio de rotinas repetitivas.", "circumscribed_interests"),
    QuestionItem(61, "Sigo rotinas rigorosas mesmo quando elas não são mais necessárias.", "circumscribed_interests"),
    QuestionItem(62, "Fico muito perturbado com mudanças de planos.", "circumscribed_interests"),
    QuestionItem(63, "Tenho dificuldade em começar tarefas sem um plano claro.", "circumscribed_interests"),
    QuestionItem(64, "Prefiro ambientes previsíveis e estruturados.", "circumscribed_interests"),

    # Items 65-80 (mixed)
    QuestionItem(65, "Às vezes tenho pensamentos que são muito perturbadores e que não quero ter.", "social"),
    QuestionItem(66, "Eu realmente me importo com as pessoas ao meu redor.", "social", reverse_scored=True),
    QuestionItem(67, "Tenho uma habilidade especial em encontrar padrões.", "circumscribed_interests"),
    QuestionItem(68, "Eu tinha ou tenho interesse muito intenso em certos tópicos.", "circumscribed_interests"),
    QuestionItem(69, "Tenho dificuldade em entender o ponto de vista dos outros.", "social"),
    QuestionItem(70, "Às vezes fico tão focado em uma coisa que esqueço do tempo.", "circumscribed_interests"),
    QuestionItem(71, "Quando estou em um ambiente novo ou barulhento, fico muito sobrecarregado.", "sensory_motor"),
    QuestionItem(72, "Eu me sinto diferente das outras pessoas de uma forma que é difícil de descrever.", "social"),
    QuestionItem(73, "Outras pessoas parecem ter um 'manual' social que nunca recebi.", "social"),
    QuestionItem(74, "Em situações sociais, às vezes digo coisas inapropriadas sem perceber.", "language"),
    QuestionItem(75, "Tenho dificuldade em falar quando estou emocionalmente sobrecarregado.", "language"),
    QuestionItem(76, "Frequentemente repito frases ou sons sem motivo aparente.", "language"),
    QuestionItem(77, "Prefiro comunicação por escrito à verbal.", "language"),
    QuestionItem(78, "Eu me sinto mais à vontade em relacionamentos online.", "social"),
    QuestionItem(79, "Meu mundo interior é muito mais rico do que minha vida social exterior.", "social"),
    QuestionItem(80, "Situações sociais me esgotam mesmo quando parecem ir bem.", "social"),
]

RAADSR_CLINICAL_THRESHOLD = 65
RAADSR_SCALE = 3   # 0–3 (unlike CATQ's 1–7)


def score_raadsr(responses: Dict[int, int]) -> QuestionnaireResult:
    """
    Score the RAADS-R from {item_id: score (0-3)}.

    Score key:
      0 = Never true
      1 = True only when I was younger than 16
      2 = True only now
      3 = True now and when I was young

    Returns QuestionnaireResult.  Scores ≥65 are in the autistic range.
    """
    subscale_totals: Dict[str, float] = {
        "language": 0,
        "social": 0,
        "sensory_motor": 0,
        "circumscribed_interests": 0,
    }
    total = 0.0

    for item in RAADSR_ITEMS:
        score = responses.get(item.id)
        if score is None:
            continue
        if item.reverse_scored:
            score = RAADSR_SCALE - score
        subscale_totals[item.subscale] = subscale_totals.get(item.subscale, 0) + score
        total += score

    max_score = len(RAADSR_ITEMS) * RAADSR_SCALE
    camouflage_weight = min(total / max_score, 1.0) if max_score else 0.0

    if total >= 100:
        risk_level = "high"
        interpretation = (
            f"Score RAADS-R = {total:.0f}. Fortemente sugestivo de Transtorno do Espectro Autista. "
            "Avaliação clínica presencial com especialista é indicada."
        )
    elif total >= RAADSR_CLINICAL_THRESHOLD:
        risk_level = "moderate"
        interpretation = (
            f"Score RAADS-R = {total:.0f} (limiar clínico = {RAADSR_CLINICAL_THRESHOLD}). "
            "Resultado sugestivo. Integração com dados multimodais e avaliação clínica recomendada."
        )
    else:
        risk_level = "low"
        interpretation = (
            f"Score RAADS-R = {total:.0f}, abaixo do limiar clínico ({RAADSR_CLINICAL_THRESHOLD}). "
            "Análise multimodal continua; resultado não exclui TEA com alto mascaramento."
        )

    logger.info(
        "RAADS-R scored: total=%.1f risk=%s camouflage_weight=%.3f",
        total, risk_level, camouflage_weight,
    )

    return QuestionnaireResult(
        name="RAADS-R",
        total_score=round(total, 1),
        subscale_scores={k: round(v, 1) for k, v in subscale_totals.items()},
        interpretation=interpretation,
        risk_level=risk_level,
        camouflage_weight=round(camouflage_weight, 3),
        raw_responses=responses,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Combined scoring helper
# ─────────────────────────────────────────────────────────────────────────────

def combined_camouflage_weight(
    catq_result: Optional[QuestionnaireResult],
    raadsr_result: Optional[QuestionnaireResult],
) -> float:
    """
    Compute a single camouflage weight (0–1) from one or both questionnaires.

    Used by the multimodal fusion engine to adjust eye-tracking and
    physiological thresholds: a high camouflage weight lowers the
    detection threshold so masked presentations are not missed.

    CAT-Q receives 2/3 weight because it measures camouflage directly;
    RAADS-R receives 1/3 weight (it measures autistic traits broadly).
    """
    weights: List[Tuple[float, float]] = []

    if catq_result:
        weights.append((catq_result.camouflage_weight, 2.0))
    if raadsr_result:
        weights.append((raadsr_result.camouflage_weight, 1.0))

    if not weights:
        return 0.5  # neutral when no questionnaire data

    total_w = sum(w for _, w in weights)
    return round(sum(cw * w for cw, w in weights) / total_w, 3)
