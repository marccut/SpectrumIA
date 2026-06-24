"""
SpectrumIA Stimuli Configuration

Defines estímulos para triagem de TEA com imagens estáticas de faces.
(Opção A — ideal para eye-tracking via webcam, precisão ~1-2° ângulo visual)

Base científica:
- Jones & Klin (2013): SAI em faces estáticas — principal biomarcador
- Frazier et al. (2018): Meta-análise 81% acurácia com paradigma de faces
- Klin et al. (2002): Padrões de fixação em TEA

Paradigma:
- 7 estímulos sociais (faces adultas + infantis) + 1 controle geométrico
- 6 segundos cada (padrão para face estática)
- 1 segundo ISI (inter-stimulus interval)
- Mistura de sexo (M/F) e grupo etário (adulto/criança)
- Emoções: neutro, feliz, medo (expressões com maior poder discriminativo)

Para substituir placeholders por imagens validadas:
- Adultos: Chicago Face Database (CFD) — https://chicagofaces.org/ (acesso livre para pesquisa)
- Crianças: Child Affective Facial Expression (CAFE) — https://www.cafe.nd.edu/
  (acesso gratuito mediante registro institucional)
- Alternativa adultos: NimStim — https://nimstim.talkbank.org/
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

# Allow imports from project root when running as __main__
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from models.schemas import AOIType  # canonical enum used across the project

# ─── Directories ─────────────────────────────────────────────────────────────
STIMULI_DIR = Path(__file__).parent
IMAGES_DIR = STIMULI_DIR / "images"

# ─── Timing parameters ───────────────────────────────────────────────────────
STIMULUS_DURATION_MS: int = 6000        # 6 s — padrão para face estática
ISI_DURATION_MS: int = 1000             # 1 s inter-stimulus interval
FIXATION_CROSS_DURATION_MS: int = 500   # 500 ms ponto de fixação antes de cada estímulo
IMAGE_SIZE: Tuple[int, int] = (800, 640)  # largura x altura dos estímulos

# ─── AOI coordinate templates (normalized 0.0–1.0) ───────────────────────────
# Formato: {AOIType: (x_min, y_min, x_max, y_max)}
# Baseado em proporções canônicas de retrato frontal normalizado.
# Para imagens do CFD/CAFE (800×640 px): converter com pixel = coord * dimensão.

# Adultos: proporções faciais padrão
ADULT_AOI_TEMPLATE: Dict[AOIType, Tuple[float, float, float, float]] = {
    AOIType.FACE_OVAL:  (0.20, 0.06, 0.80, 0.96),
    AOIType.EYES:       (0.12, 0.26, 0.88, 0.50),   # ambos os olhos combinados
    AOIType.NOSE:       (0.35, 0.46, 0.65, 0.66),
    AOIType.MOUTH:      (0.22, 0.63, 0.78, 0.83),
    AOIType.BACKGROUND: (0.00, 0.00, 1.00, 1.00),   # residual calculado em runtime
}

# Crianças: olhos relativamente maiores, fronte proporcionalmente maior
CHILD_AOI_TEMPLATE: Dict[AOIType, Tuple[float, float, float, float]] = {
    AOIType.FACE_OVAL:  (0.18, 0.08, 0.82, 0.94),
    AOIType.EYES:       (0.10, 0.28, 0.90, 0.52),
    AOIType.NOSE:       (0.36, 0.50, 0.64, 0.67),
    AOIType.MOUTH:      (0.24, 0.65, 0.76, 0.82),
    AOIType.BACKGROUND: (0.00, 0.00, 1.00, 1.00),
}

# Controle geométrico: sem regiões sociais definidas
GEOMETRIC_AOI_TEMPLATE: Dict[AOIType, Tuple[float, float, float, float]] = {
    AOIType.BACKGROUND: (0.00, 0.00, 1.00, 1.00),
}

_AOI_TEMPLATES = {
    "adult":     ADULT_AOI_TEMPLATE,
    "child":     CHILD_AOI_TEMPLATE,
    "geometric": GEOMETRIC_AOI_TEMPLATE,
}


# ─── Stimulus Definition ──────────────────────────────────────────────────────
@dataclass
class StimulusDefinition:
    """Defines a single stimulus for the assessment."""
    id: str
    name: str
    description: str
    type: str           # "face_adult" | "face_child" | "geometric"
    emotion: str        # "neutral" | "happy" | "fearful" | "geometric"
    sex: str            # "female" | "male" | "none"
    age_group: str      # "adult" | "child" | "none"
    filename: str       # PNG filename inside stimuli/images/
    duration_ms: int = STIMULUS_DURATION_MS
    aoi_template: str = "adult"   # "adult" | "child" | "geometric"
    # Metadata for traceability
    database_source: str = "placeholder"  # "placeholder" | "CFD" | "CAFE" | "NimStim"
    validated: bool = False               # True após substituição por imagem validada

    # ─── Derived properties ──────────────────────────────────────────────────
    @property
    def image_path(self) -> Path:
        return IMAGES_DIR / self.filename

    @property
    def image_exists(self) -> bool:
        return self.image_path.exists()

    @property
    def aoi_coords(self) -> Dict[AOIType, Tuple[float, float, float, float]]:
        """AOI coordinates normalized (0–1) for this stimulus type."""
        return _AOI_TEMPLATES.get(self.aoi_template, ADULT_AOI_TEMPLATE)

    @property
    def is_social(self) -> bool:
        return self.type in ("face_adult", "face_child")

    def to_legacy_dict(self) -> dict:
        """Backward-compatible dict for pages that still use the old format."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "duration_ms": self.duration_ms,
            "description": self.description,
            "image_path": str(self.image_path) if self.image_exists else None,
            "aoi_coords": {k.value: v for k, v in self.aoi_coords.items()},
            "is_social": self.is_social,
        }


# ─── Stimulus List ────────────────────────────────────────────────────────────
# 7 sociais + 1 geométrico = 8 estímulos
# Ordem fixa para reprodutibilidade durante validação.
# Em produção: randomizar por participante (contrabalaçar).

STIMULUS_LIST: List[StimulusDefinition] = [
    # ── Faces adultas ─────────────────────────────────────────────────────────
    StimulusDefinition(
        id="adult_neutral_f01",
        name="Rosto Adulto Neutro (F)",
        description="Face adulta feminina — expressão neutra",
        type="face_adult",
        emotion="neutral",
        sex="female",
        age_group="adult",
        filename="adult_neutral_f01.png",
        aoi_template="adult",
    ),
    StimulusDefinition(
        id="adult_neutral_m01",
        name="Rosto Adulto Neutro (M)",
        description="Face adulta masculina — expressão neutra",
        type="face_adult",
        emotion="neutral",
        sex="male",
        age_group="adult",
        filename="adult_neutral_m01.png",
        aoi_template="adult",
    ),
    StimulusDefinition(
        id="adult_happy_f01",
        name="Rosto Adulto Feliz (F)",
        description="Face adulta feminina — expressão de alegria",
        type="face_adult",
        emotion="happy",
        sex="female",
        age_group="adult",
        filename="adult_happy_f01.png",
        aoi_template="adult",
    ),
    StimulusDefinition(
        id="adult_fear_m01",
        name="Rosto Adulto com Medo (M)",
        description="Face adulta masculina — expressão de medo",
        type="face_adult",
        emotion="fearful",
        sex="male",
        age_group="adult",
        filename="adult_fear_m01.png",
        aoi_template="adult",
    ),
    # ── Faces infantis ────────────────────────────────────────────────────────
    StimulusDefinition(
        id="child_neutral_f01",
        name="Rosto Infantil Neutro (F)",
        description="Face infantil feminina — expressão neutra",
        type="face_child",
        emotion="neutral",
        sex="female",
        age_group="child",
        filename="child_neutral_f01.png",
        aoi_template="child",
    ),
    StimulusDefinition(
        id="child_neutral_m01",
        name="Rosto Infantil Neutro (M)",
        description="Face infantil masculino — expressão neutra",
        type="face_child",
        emotion="neutral",
        sex="male",
        age_group="child",
        filename="child_neutral_m01.png",
        aoi_template="child",
    ),
    StimulusDefinition(
        id="child_happy_f01",
        name="Rosto Infantil Feliz (F)",
        description="Face infantil feminina — expressão de alegria",
        type="face_child",
        emotion="happy",
        sex="female",
        age_group="child",
        filename="child_happy_f01.png",
        aoi_template="child",
    ),
    # ── Controle geométrico ───────────────────────────────────────────────────
    StimulusDefinition(
        id="geometric_control_01",
        name="Padrão Geométrico",
        description="Estímulo geométrico de controle (social vs. não-social)",
        type="geometric",
        emotion="geometric",
        sex="none",
        age_group="none",
        filename="geometric_control_01.png",
        aoi_template="geometric",
    ),
]


# ─── Helper functions ─────────────────────────────────────────────────────────
def get_stimulus_by_id(stimulus_id: str) -> Optional[StimulusDefinition]:
    """Retrieve a StimulusDefinition by ID."""
    return next((s for s in STIMULUS_LIST if s.id == stimulus_id), None)


def get_stimuli_for_assessment() -> List[StimulusDefinition]:
    """Return the ordered stimulus list for a full assessment session."""
    return STIMULUS_LIST.copy()


def stimuli_ready() -> bool:
    """True if all stimulus images exist on disk."""
    return all(s.image_exists for s in STIMULUS_LIST)


def missing_stimuli() -> List[str]:
    """Return filenames of missing stimulus images."""
    return [s.filename for s in STIMULUS_LIST if not s.image_exists]
