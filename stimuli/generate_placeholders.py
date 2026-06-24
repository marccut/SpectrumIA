"""
SpectrumIA — Gerador de Estímulos Placeholder

Cria imagens esquemáticas (faces desenhadas com PIL) para desenvolvimento
e testes do pipeline de eye-tracking.

⚠️  SUBSTITUIR por imagens de bancos validados antes dos testes clínicos:
    • Adultos : Chicago Face Database (CFD)
                https://chicagofaces.org/
                Acesso livre para pesquisa acadêmica (sem registro)
    • Crianças: Child Affective Facial Expression (CAFE)
                https://www.cafe.nd.edu/
                Acesso gratuito mediante registro institucional
    • Alternativa adultos: NimStim Set of Facial Expressions
                https://nimstim.talkbank.org/

Uso:
    cd /path/to/spectrumia
    python stimuli/generate_placeholders.py
"""

from pathlib import Path
import sys

# Allow running from any directory
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow não encontrado. Instalando...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "--quiet"])
    from PIL import Image, ImageDraw, ImageFont

from stimuli.stimuli_config import (
    STIMULUS_LIST, IMAGES_DIR, IMAGE_SIZE,
    ADULT_AOI_TEMPLATE, CHILD_AOI_TEMPLATE,
)
from models.schemas import AOIType

# ─── Paleta de cores ──────────────────────────────────────────────────────────
BG_COLOR = (245, 240, 235)        # fundo bege claro

SKIN_TONES = {
    "female": (240, 210, 195),    # tom de pele feminino (mais claro)
    "male":   (220, 185, 165),    # tom de pele masculino (mais escuro)
    "none":   (200, 215, 230),
}

EMOTION_MOUTH_COLORS = {
    "neutral":  (80, 60, 60),
    "happy":    (30, 140, 60),
    "fearful":  (180, 50, 50),
    "geometric": (70, 110, 200),
}

AOI_OVERLAY_COLORS = {
    AOIType.EYES:       (255, 200, 0, 35),    # amarelo translúcido
    AOIType.MOUTH:      (0, 180, 255, 35),    # azul translúcido
    AOIType.NOSE:       (180, 0, 180, 20),    # roxo translúcido
    AOIType.FACE_OVAL:  (0, 200, 100, 10),    # verde translúcido
}


# ─── Funções de desenho ───────────────────────────────────────────────────────

def draw_aoi_overlays(
    overlay: ImageDraw,
    W: int, H: int,
    aoi_template: dict,
    show_labels: bool = True,
):
    """Desenha as regiões de AOI como retângulos translúcidos (para debug visual)."""
    for aoi_type, (x1, y1, x2, y2) in aoi_template.items():
        if aoi_type == AOIType.BACKGROUND:
            continue
        color = AOI_OVERLAY_COLORS.get(aoi_type, (180, 180, 180, 20))
        px1, py1 = int(x1 * W), int(y1 * H)
        px2, py2 = int(x2 * W), int(y2 * H)
        overlay.rectangle([px1, py1, px2, py2], fill=color, outline=color[:3])
        if show_labels:
            overlay.text((px1 + 4, py1 + 2), aoi_type.value, fill=(60, 60, 60))


def draw_schematic_face(
    draw: ImageDraw,
    W: int, H: int,
    emotion: str,
    sex: str,
    age_group: str,
):
    """Desenha uma face esquemática que respeita as coordenadas de AOI."""
    skin = SKIN_TONES.get(sex, SKIN_TONES["female"])
    is_child = age_group == "child"

    # — Óvalo facial —
    draw.ellipse(
        [int(W * 0.20), int(H * 0.06), int(W * 0.80), int(H * 0.96)],
        fill=skin,
        outline=(90, 65, 55),
        width=3,
    )

    # — Regiões dos olhos —
    if is_child:
        eye_y1, eye_y2 = int(H * 0.28), int(H * 0.52)
        le_x1, le_x2 = int(W * 0.10), int(W * 0.44)
        re_x1, re_x2 = int(W * 0.56), int(W * 0.90)
    else:
        eye_y1, eye_y2 = int(H * 0.26), int(H * 0.50)
        le_x1, le_x2 = int(W * 0.12), int(W * 0.44)
        re_x1, re_x2 = int(W * 0.56), int(W * 0.88)

    # Branco dos olhos
    for x1, x2 in [(le_x1, le_x2), (re_x1, re_x2)]:
        draw.ellipse([x1, eye_y1, x2, eye_y2], fill=(255, 255, 255), outline=(40, 40, 40), width=2)

    # Pupilas
    pupil_r = max(int((eye_y2 - eye_y1) * 0.30), 8)
    c_y = (eye_y1 + eye_y2) // 2
    for cx in [(le_x1 + le_x2) // 2, (re_x1 + re_x2) // 2]:
        # Iris
        iris_r = pupil_r + 4
        draw.ellipse(
            [cx - iris_r, c_y - iris_r, cx + iris_r, c_y + iris_r],
            fill=(70, 100, 160) if sex == "female" else (55, 75, 110),
        )
        # Pupila
        draw.ellipse(
            [cx - pupil_r, c_y - pupil_r, cx + pupil_r, c_y + pupil_r],
            fill=(20, 15, 15),
        )

    # — Nariz —
    nose_cx = W // 2
    nose_cy = int(H * 0.565) if not is_child else int(H * 0.585)
    nose_r = int(W * 0.035)
    draw.ellipse(
        [nose_cx - nose_r, nose_cy - nose_r * 2, nose_cx + nose_r, nose_cy],
        fill=skin,
        outline=(130, 95, 85),
        width=2,
    )

    # — Boca —
    mouth_color = EMOTION_MOUTH_COLORS.get(emotion, EMOTION_MOUTH_COLORS["neutral"])
    mx1 = int(W * 0.27)
    mx2 = int(W * 0.73)
    mouth_cy_frac = 0.72 if not is_child else 0.73

    if emotion == "happy":
        my1 = int(H * (mouth_cy_frac - 0.06))
        my2 = int(H * (mouth_cy_frac + 0.06))
        draw.arc([mx1, my1, mx2, my2], start=0, end=180, fill=mouth_color, width=5)
        # Dentes
        teeth_x = (mx1 + mx2) // 2
        draw.rectangle(
            [teeth_x - 20, my1 + 10, teeth_x + 20, my1 + 25],
            fill=(250, 250, 250),
        )
    elif emotion == "fearful":
        my1 = int(H * (mouth_cy_frac - 0.04))
        my2 = int(H * (mouth_cy_frac + 0.04))
        draw.arc([mx1, my1, mx2, my2], start=180, end=360, fill=mouth_color, width=4)
        # Sourcils froncés
        brow_y = eye_y1 - 15
        draw.line([(le_x1, brow_y + 8), (le_x2, brow_y)], fill=(60, 40, 40), width=5)
        draw.line([(re_x1, brow_y), (re_x2, brow_y + 8)], fill=(60, 40, 40), width=5)
    else:  # neutral
        my = int(H * mouth_cy_frac)
        draw.line([(mx1, my), (mx2, my)], fill=mouth_color, width=4)


def draw_geometric_control(draw: ImageDraw, W: int, H: int):
    """Desenha padrão geométrico para estímulo de controle."""
    palette = [
        (70, 110, 200),
        (200, 70, 110),
        (70, 200, 110),
        (200, 170, 70),
    ]
    quads = [
        (80, 60, 380, 300),
        (420, 60, 720, 300),
        (80, 340, 380, 580),
        (420, 340, 720, 580),
    ]
    for i, (x1, y1, x2, y2) in enumerate(quads):
        draw.rectangle([x1, y1, x2, y2], fill=palette[i], outline=(255, 255, 255), width=3)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        r = min(x2 - x1, y2 - y1) // 4
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=palette[(i + 2) % 4],
            width=3,
        )


def generate_placeholder(stimulus) -> Path:
    """Gera uma imagem placeholder para um StimulusDefinition."""
    W, H = IMAGE_SIZE
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    if stimulus.type == "geometric":
        draw_geometric_control(draw, W, H)
    else:
        draw_schematic_face(draw, W, H, stimulus.emotion, stimulus.sex, stimulus.age_group)

    # Sobreposição de AOIs (RGBA over RGB via compositing)
    overlay_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay_img)
    aoi_template = stimulus.aoi_coords
    draw_aoi_overlays(overlay_draw, W, H, aoi_template)
    img_rgba = img.convert("RGBA")
    img_rgba.alpha_composite(overlay_img)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Legenda
    draw.rectangle([0, H - 32, W, H], fill=(240, 240, 240))
    draw.text(
        (8, H - 22),
        "⚠ PLACEHOLDER — Substituir por CFD/CAFE antes de testes clínicos",
        fill=(180, 40, 40),
    )
    draw.rectangle([0, 0, W, 26], fill=(240, 240, 240))
    draw.text(
        (8, 6),
        f"[TESTE] {stimulus.name}  |  {stimulus.emotion}  |  {stimulus.duration_ms // 1000}s",
        fill=(60, 60, 60),
    )

    output_path = IMAGES_DIR / stimulus.filename
    img.save(output_path, "PNG", optimize=True)
    return output_path


# ─── Entrypoint ───────────────────────────────────────────────────────────────

def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nGerando {len(STIMULUS_LIST)} estímulos placeholder em:\n  {IMAGES_DIR}\n")
    for stim in STIMULUS_LIST:
        path = generate_placeholder(stim)
        status = "✓" if path.exists() else "✗"
        print(f"  {status}  {path.name}  ({stim.name})")
    print(f"\nConcluído. {len(STIMULUS_LIST)} imagens criadas.")
    print("\nPróximos passos:")
    print("  1. Solicitar acesso ao CFD: https://chicagofaces.org/")
    print("  2. Solicitar acesso ao CAFE: https://www.cafe.nd.edu/")
    print("  3. Substituir arquivos em stimuli/images/ mantendo os mesmos nomes")
    print("  4. Atualizar 'database_source' e 'validated=True' em stimuli_config.py")


if __name__ == "__main__":
    main()
