"""
SpectrumIA / Neurotrace AI — Gerador de Relatório Clínico PDF
=============================================================

Gera um relatório clínico em PDF a partir dos resultados da análise
fenotípica multimodal, incluindo:

  Página 1 — Sumário executivo
    • Cabeçalho institucional + metadados
    • Probabilidade de TEA + subtipo fenotípico
    • Índice de camuflagem e confiança do modelo
    • Interpretação clínica e recomendação

  Página 2 — Evidências multimodais
    • Contribuições SHAP-like por modalidade
    • Perfil CAT-Q por subescala (Assimilação / Compensação / Mascaramento)
    • Pontuação RAADS-R
    • Métricas de eye-tracking (se disponíveis)

  Página 3 — Contexto clínico
    • Marcadores clínicos do FAF detectados
    • Tabela de diagnóstico diferencial (TEA/TDAH/Ansiedade/TPB)

  Página 4 — Referências e Disclaimer
    • Referências científicas
    • Aviso regulatório (LGPD, ANVISA RDC 657/2022, XAI FAIR)

Uso:
    from core.pdf_report import generate_report_pdf
    pdf_bytes = generate_report_pdf(result, catq_result, raadsr_result, et)
    # pdf_bytes é um io.BytesIO pronto para st.download_button
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Paleta de cores SpectrumIA
# ─────────────────────────────────────────────────────────────────────────────
C_PURPLE     = colors.HexColor("#6a1b9a")
C_PURPLE_LT  = colors.HexColor("#ede7f6")
C_BLUE       = colors.HexColor("#0277bd")
C_RED        = colors.HexColor("#e53935")
C_ORANGE     = colors.HexColor("#f57c00")
C_GREEN      = colors.HexColor("#43a047")
C_GRAY_DK    = colors.HexColor("#424242")
C_GRAY_MD    = colors.HexColor("#757575")
C_GRAY_LT    = colors.HexColor("#f5f5f5")
C_WHITE      = colors.white
C_BLACK      = colors.black
C_BORDER     = colors.HexColor("#e0e0e0")


# ─────────────────────────────────────────────────────────────────────────────
# Flowable auxiliar: barra de progresso
# ─────────────────────────────────────────────────────────────────────────────
class ProgressBar(Flowable):
    """Barra de progresso horizontal simples."""

    def __init__(self, value: float, width: float = 10 * cm, height: float = 6,
                 color=C_PURPLE, bg=C_GRAY_LT):
        super().__init__()
        self._value  = min(1.0, max(0.0, value))
        self._width  = width
        self._height = height
        self._color  = color
        self._bg     = bg
        self.width   = width
        self.height  = height + 2

    def draw(self):
        self.canv.setFillColor(self._bg)
        self.canv.roundRect(0, 0, self._width, self._height, 2, fill=1, stroke=0)
        if self._value > 0:
            self.canv.setFillColor(self._color)
            self.canv.roundRect(0, 0, self._width * self._value, self._height, 2, fill=1, stroke=0)


# ─────────────────────────────────────────────────────────────────────────────
# Estilos tipográficos
# ─────────────────────────────────────────────────────────────────────────────
def _build_styles() -> dict:
    base = getSampleStyleSheet()

    def ps(name, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return {
        "title": ps("Title",
            fontName="Helvetica-Bold", fontSize=18,
            textColor=C_PURPLE, alignment=TA_CENTER, spaceAfter=4),
        "subtitle": ps("Subtitle",
            fontName="Helvetica", fontSize=10,
            textColor=C_GRAY_MD, alignment=TA_CENTER, spaceAfter=2),
        "section": ps("Section",
            fontName="Helvetica-Bold", fontSize=12,
            textColor=C_PURPLE, spaceBefore=14, spaceAfter=6,
            borderPad=4, leftIndent=0),
        "subsection": ps("Subsection",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=C_GRAY_DK, spaceBefore=8, spaceAfter=4),
        "body": ps("Body",
            fontName="Helvetica", fontSize=9,
            textColor=C_GRAY_DK, leading=13, alignment=TA_JUSTIFY),
        "body_bold": ps("BodyBold",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=C_GRAY_DK, leading=13),
        "small": ps("Small",
            fontName="Helvetica", fontSize=7.5,
            textColor=C_GRAY_MD, leading=11),
        "small_italic": ps("SmallItalic",
            fontName="Helvetica-Oblique", fontSize=7.5,
            textColor=C_GRAY_MD, leading=11),
        "label": ps("Label",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=C_GRAY_MD, spaceAfter=2),
        "prob_high": ps("ProbHigh",
            fontName="Helvetica-Bold", fontSize=26,
            textColor=C_RED, alignment=TA_CENTER),
        "prob_mod": ps("ProbMod",
            fontName="Helvetica-Bold", fontSize=26,
            textColor=C_ORANGE, alignment=TA_CENTER),
        "prob_low": ps("ProbLow",
            fontName="Helvetica-Bold", fontSize=26,
            textColor=C_GREEN, alignment=TA_CENTER),
        "table_header": ps("TableHeader",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=C_WHITE, alignment=TA_CENTER),
        "table_cell": ps("TableCell",
            fontName="Helvetica", fontSize=8,
            textColor=C_GRAY_DK, alignment=TA_LEFT),
        "table_cell_center": ps("TableCellC",
            fontName="Helvetica", fontSize=8,
            textColor=C_GRAY_DK, alignment=TA_CENTER),
        "disclaimer": ps("Disclaimer",
            fontName="Helvetica-Oblique", fontSize=7,
            textColor=C_GRAY_MD, alignment=TA_JUSTIFY, leading=10),
        "ref": ps("Ref",
            fontName="Helvetica", fontSize=7.5,
            textColor=C_GRAY_MD, leading=11, leftIndent=12),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────
def _hr(color=C_BORDER, thickness=0.5) -> HRFlowable:
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=4, spaceBefore=4)


def _section_title(text: str, styles: dict) -> list:
    return [
        Spacer(1, 4),
        _hr(C_PURPLE, 1.0),
        Paragraph(text, styles["section"]),
    ]


def _colored_box(text: str, bg: colors.Color, text_color=C_WHITE,
                 font="Helvetica-Bold", font_size=10) -> Table:
    """Caixa colorida de largura total com texto centralizado."""
    data = [[Paragraph(f'<font name="{font}" size="{font_size}" color="#{text_color.hexval()[2:]}">{text}</font>',
                       ParagraphStyle("BoxText", fontName=font, fontSize=font_size,
                                      textColor=text_color, alignment=TA_CENTER))]]
    t = Table(data, colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), bg),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return t


def _kv_table(rows: list[tuple], styles: dict,
              col_widths=(5 * cm, 11.5 * cm)) -> Table:
    """Tabela de duas colunas chave–valor."""
    data = [[Paragraph(k, styles["body_bold"]), Paragraph(v, styles["body"])]
            for k, v in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW",    (0, 0), (-1, -1), 0.3, C_BORDER),
    ]))
    return t


# ─────────────────────────────────────────────────────────────────────────────
# Cabeçalho e rodapé de páginas
# ─────────────────────────────────────────────────────────────────────────────
def _make_on_page(assessment_id: str, patient_label: str):
    """Retorna função de callback para cabeçalho/rodapé em cada página."""

    def on_page(canvas, doc):
        canvas.saveState()
        w, h = A4

        # Cabeçalho
        canvas.setFillColor(C_PURPLE)
        canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
        canvas.setFillColor(C_WHITE)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(1.5 * cm, h - 18, "SpectrumIA")
        canvas.setFont("Helvetica", 8)
        canvas.drawString(1.5 * cm, h - 26, "Neurotrace AI  |  Relatório de Triagem para TEA")
        canvas.setFont("Helvetica", 7.5)
        canvas.drawRightString(w - 1.5 * cm, h - 18, f"ID: {assessment_id}")
        canvas.drawRightString(w - 1.5 * cm, h - 26, patient_label)

        # Rodapé
        canvas.setFillColor(C_GRAY_LT)
        canvas.rect(0, 0, w, 18, fill=1, stroke=0)
        canvas.setFillColor(C_GRAY_MD)
        canvas.setFont("Helvetica", 6.5)
        canvas.drawString(1.5 * cm, 6,
            "DOCUMENTO CONFIDENCIAL — uso exclusivo por profissional de saúde habilitado | "
            "LGPD  |  ANVISA RDC 657/2022  |  XAI FAIR")
        canvas.drawRightString(w - 1.5 * cm, 6, f"Pag. {doc.page}")

        canvas.restoreState()

    return on_page


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 1 — Sumário Executivo
# ─────────────────────────────────────────────────────────────────────────────
def _page_summary(result, catq_result, raadsr_result, styles: dict,
                  patient_name: str, clinician: str) -> list:
    from core.multimodal_fusion import PHENOTYPE_SUBTYPES

    story = []
    prob_pct = result.asd_probability * 100
    pt_label = PHENOTYPE_SUBTYPES.get(result.phenotype_subtype, result.phenotype_subtype)

    # ── Cabeçalho do documento
    story.append(Spacer(1, 8))
    story.append(Paragraph("RELATÓRIO DE TRIAGEM MULTIMODAL PARA TEA", styles["title"]))
    story.append(Paragraph("Neurotrace AI · Motor de Fusão XAI · Foco no Fenótipo Autista Feminino", styles["subtitle"]))
    story.append(_hr())
    story.append(Spacer(1, 4))

    # ── Metadados
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    meta_rows = [
        ("Paciente:", patient_name or "Não informado"),
        ("Data/Hora:", now),
        ("Solicitante:", clinician or "Não informado"),
        ("Completude dos dados:", f"{result.data_completeness:.0%}"),
        ("Confiança do modelo:", f"{result.confidence:.0%}"),
    ]
    story.append(_kv_table(meta_rows, styles))
    story.append(Spacer(1, 10))

    # ── Resultado principal
    story += _section_title("RESULTADO PRINCIPAL", styles)

    prob_style = (styles["prob_high"] if prob_pct >= 60
                  else styles["prob_mod"] if prob_pct >= 40
                  else styles["prob_low"])
    prob_color = C_RED if prob_pct >= 60 else C_ORANGE if prob_pct >= 40 else C_GREEN
    level_label = "ELEVADA" if prob_pct >= 60 else "MODERADA" if prob_pct >= 40 else "BAIXA"

    # Tabela de 3 colunas: probabilidade | fenótipo | suporte
    support_map = {
        1: "Nivel 1\nRequer suporte",
        2: "Nivel 2\nRequer suporte substancial",
        3: "Nivel 3\nRequer suporte muito substancial",
    }
    adhd_map = {"low": "Baixo", "moderate": "Moderado", "high": "Alto"}

    main_data = [
        [
            Paragraph("Probabilidade de TEA", styles["label"]),
            Paragraph("Subtipo Fenotipico", styles["label"]),
            Paragraph("Nivel de Suporte (DSM-5-TR)", styles["label"]),
        ],
        [
            Paragraph(f"{prob_pct:.1f}%", prob_style),
            Paragraph(pt_label, ParagraphStyle("PhLabel", fontName="Helvetica-Bold",
                      fontSize=9, textColor=C_PURPLE, alignment=TA_CENTER, leading=12)),
            Paragraph(support_map.get(result.functional_support_level, "—"),
                      ParagraphStyle("SuppLabel", fontName="Helvetica", fontSize=9,
                      textColor=C_GRAY_DK, alignment=TA_CENTER, leading=12)),
        ],
        [
            Paragraph(f"({level_label})", ParagraphStyle("LvlLabel", fontName="Helvetica-Bold",
                      fontSize=9, textColor=prob_color, alignment=TA_CENTER)),
            Paragraph(f"Camuf.: {result.camouflage_weight_used:.0%}", styles["small"]),
            Paragraph(f"Fator TDAH: {adhd_map.get(result.adhd_confusion_factor, '—')}",
                      styles["small"]),
        ],
    ]
    main_table = Table(main_data, colWidths=[5.5 * cm, 8 * cm, 5 * cm])
    main_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_GRAY_LT),
        ("BACKGROUND",    (0, 1), (-1, 1), C_WHITE),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(main_table)
    story.append(Spacer(1, 6))

    # Barra de probabilidade
    story.append(Paragraph("Nivel de evidencia para TEA:", styles["label"]))
    story.append(ProgressBar(result.asd_probability, width=16.5 * cm, color=prob_color))
    story.append(Spacer(1, 2))
    adjusted_thresh = 1 - result.camouflage_weight_used * 0.20
    story.append(Paragraph(
        f"Limiar ajustado por camuflagem: {adjusted_thresh:.0%}"
        + (" (reducao por alto mascaramento detectado)" if result.camouflage_adjustment_applied else ""),
        styles["small_italic"],
    ))
    story.append(Spacer(1, 8))

    # ── Interpretação clínica
    story += _section_title("INTERPRETACAO CLINICA", styles)
    # Strip markdown bold markers for PDF
    interp_clean = result.interpretation.replace("**", "")
    story.append(Paragraph(interp_clean, styles["body"]))
    story.append(Spacer(1, 8))

    # Recomendação em destaque
    story.append(KeepTogether([
        Paragraph("RECOMENDACAO CLINICA", ParagraphStyle("RecLabel",
            fontName="Helvetica-Bold", fontSize=9, textColor=C_PURPLE, spaceAfter=4)),
        Table([[Paragraph(result.recommendation, styles["body"])]],
              colWidths=["100%"],
              style=TableStyle([
                  ("BACKGROUND",    (0, 0), (-1, -1), C_PURPLE_LT),
                  ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                  ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
                  ("TOPPADDING",    (0, 0), (-1, -1), 8),
                  ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                  ("LINEAFTER",     (0, 0), (0, -1), 3, C_PURPLE),
              ])),
    ]))

    return story


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 2 — Evidências Multimodais
# ─────────────────────────────────────────────────────────────────────────────
def _page_evidence(result, catq_result, raadsr_result, et, styles: dict) -> list:
    story = [PageBreak()]
    story.append(Spacer(1, 8))

    # ── Contribuições SHAP-like
    story += _section_title("CONTRIBUICOES MULTIMODAIS (SHAP-like)", styles)
    story.append(Paragraph(
        "Contribuicao de cada modalidade para a probabilidade de TEA. "
        "Positivo: aumenta probabilidade | Negativo: reduz probabilidade.",
        styles["small_italic"],
    ))
    story.append(Spacer(1, 6))

    shap_header = [
        Paragraph("Modalidade", styles["table_header"]),
        Paragraph("Status", styles["table_header"]),
        Paragraph("Contrib.", styles["table_header"]),
        Paragraph("Evidencia", styles["table_header"]),
        Paragraph("Nota", styles["table_header"]),
    ]
    shap_rows = [shap_header]
    for fc in result.feature_contributions:
        status = "Disponivel" if fc.available else "Ausente"
        contrib_str = f"{fc.contribution:+.3f}" if (fc.available and fc.contribution != 0) else "—"
        # Simple text bar
        bar_len = int(abs(fc.contribution) * 30)
        bar_char = "+" if fc.contribution > 0 else "-"
        bar_str = bar_char * min(bar_len, 20) if fc.available else ""
        shap_rows.append([
            Paragraph(fc.name, styles["table_cell"]),
            Paragraph(status, styles["table_cell_center"]),
            Paragraph(contrib_str, styles["table_cell_center"]),
            Paragraph(bar_str, ParagraphStyle("Bar", fontName="Courier", fontSize=7,
                      textColor=C_RED if fc.contribution > 0 else C_GREEN,
                      alignment=TA_LEFT)),
            Paragraph(fc.note or "—", styles["small"]),
        ])

    shap_table = Table(shap_rows, colWidths=[5.5 * cm, 2 * cm, 1.8 * cm, 2.5 * cm, 4.7 * cm])
    shap_style = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_PURPLE),
        ("BACKGROUND",    (0, 1), (-1, -1), C_WHITE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_GRAY_LT]),
        ("GRID",          (0, 0), (-1, -1), 0.3, C_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ])
    shap_table.setStyle(shap_style)
    story.append(shap_table)
    story.append(Spacer(1, 10))

    # ── CAT-Q por subescala
    story += _section_title("PERFIL DE CAMUFLAGEM — CAT-Q", styles)

    if catq_result and catq_result.subscale_scores:
        ss = catq_result.subscale_scores
        ASSIM_MAX, COMP_MAX, MASK_MAX = 126, 161, 161
        assim = ss.get("assimilation", 0)
        comp  = ss.get("compensation", 0)
        mask  = ss.get("masking", 0)

        catq_rows = [
            [Paragraph(h, styles["table_header"]) for h in
             ["Subescala", "Pontuacao", "Max", "Normalizado", "Interpretacao"]],
            [
                Paragraph("Assimilacao", styles["table_cell"]),
                Paragraph(f"{assim:.0f}", styles["table_cell_center"]),
                Paragraph(f"{ASSIM_MAX}", styles["table_cell_center"]),
                Paragraph(f"{assim/ASSIM_MAX:.0%}", styles["table_cell_center"]),
                Paragraph("Elevada" if assim/ASSIM_MAX > 0.65 else
                          "Moderada" if assim/ASSIM_MAX > 0.40 else "Baixa",
                          styles["table_cell_center"]),
            ],
            [
                Paragraph("Compensacao", styles["table_cell"]),
                Paragraph(f"{comp:.0f}", styles["table_cell_center"]),
                Paragraph(f"{COMP_MAX}", styles["table_cell_center"]),
                Paragraph(f"{comp/COMP_MAX:.0%}", styles["table_cell_center"]),
                Paragraph("Elevada" if comp/COMP_MAX > 0.65 else
                          "Moderada" if comp/COMP_MAX > 0.40 else "Baixa",
                          styles["table_cell_center"]),
            ],
            [
                Paragraph("Mascaramento", styles["table_cell"]),
                Paragraph(f"{mask:.0f}", styles["table_cell_center"]),
                Paragraph(f"{MASK_MAX}", styles["table_cell_center"]),
                Paragraph(f"{mask/MASK_MAX:.0%}", styles["table_cell_center"]),
                Paragraph("Elevado" if mask/MASK_MAX > 0.65 else
                          "Moderado" if mask/MASK_MAX > 0.40 else "Baixo",
                          styles["table_cell_center"]),
            ],
            [
                Paragraph("TOTAL CAT-Q", styles["body_bold"]),
                Paragraph(f"{catq_result.total_score:.0f}", styles["body_bold"]),
                Paragraph("448", styles["table_cell_center"]),
                Paragraph(f"{catq_result.total_score/448:.0%}", styles["table_cell_center"]),
                Paragraph(f"Peso de camuflagem: {catq_result.camouflage_weight:.0%}", styles["body_bold"]),
            ],
        ]
        catq_table = Table(catq_rows, colWidths=[4.5 * cm, 2.5 * cm, 1.5 * cm, 2.5 * cm, 5.5 * cm])
        catq_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), C_PURPLE),
            ("BACKGROUND",    (0, -1), (-1, -1), C_PURPLE_LT),
            ("ROWBACKGROUNDS",(0, 1), (-1, -2), [C_WHITE, C_GRAY_LT]),
            ("GRID",          (0, 0), (-1, -1), 0.3, C_BORDER),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ]))
        story.append(catq_table)
        story.append(Paragraph(
            "Limiar clinico CAT-Q: total >= 100 (Hull et al., 2019). "
            "Subescalas: Assimilacao (imitacao comportamental), "
            "Compensacao (scripts sociais aprendidos), "
            "Mascaramento (supressao de tracos autistas).",
            styles["small_italic"],
        ))
    else:
        story.append(Paragraph("CAT-Q nao preenchido. Instrumento essencial para deteccao do FAF.", styles["body"]))

    story.append(Spacer(1, 10))

    # ── RAADS-R
    story += _section_title("RAADS-R — ESCALA DE TRIAGEM AUTISTICA", styles)

    if raadsr_result:
        risk_map = {"low": "Baixo", "moderate": "Moderado", "high": "Alto"}
        raadsr_rows = [
            ("Pontuacao total:", f"{raadsr_result.total_score:.0f} / 240"),
            ("Nivel de risco:", risk_map.get(raadsr_result.risk_level, raadsr_result.risk_level)),
            ("Ponto de corte:", "65 (Ritvo et al., 2011)"),
            ("Interpretacao:", raadsr_result.interpretation),
        ]
        story.append(_kv_table(raadsr_rows, styles))

        if raadsr_result.subscale_scores:
            story.append(Spacer(1, 6))
            sub_header = [Paragraph(h, styles["table_header"]) for h in ["Subescala", "Pontuacao"]]
            sub_rows = [sub_header] + [
                [Paragraph(k.replace("_", " ").title(), styles["table_cell"]),
                 Paragraph(str(v), styles["table_cell_center"])]
                for k, v in raadsr_result.subscale_scores.items()
            ]
            sub_table = Table(sub_rows, colWidths=[10 * cm, 6.5 * cm])
            sub_table.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), C_PURPLE),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_GRAY_LT]),
                ("GRID",          (0, 0), (-1, -1), 0.3, C_BORDER),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ]))
            story.append(sub_table)
    else:
        story.append(Paragraph("RAADS-R nao preenchido.", styles["body"]))

    story.append(Spacer(1, 10))

    # ── Eye-tracking
    story += _section_title("METRICAS DE EYE-TRACKING", styles)
    if et:
        et_rows = [
            ("Fixacao social:", f"{et.social_fixation_ratio:.1%}  (referencia neurotipica: ~65%)"),
            ("Evitacao do olhar:", f"{et.social_gaze_avoidance:.1%}"),
            ("Amplitude de sacadas:", f"{et.avg_saccade_amplitude:.1f} graus"),
            ("Taxa de piscadas:", f"{et.blink_rate_per_min:.1f} / min"),
            ("Qualidade do sinal:", f"{et.quality_score:.1%}"),
        ]
        story.append(_kv_table(et_rows, styles))
    else:
        story.append(Paragraph("Assessment de eye-tracking nao realizado ou qualidade insuficiente.", styles["body"]))

    return story


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 3 — Contexto Clínico
# ─────────────────────────────────────────────────────────────────────────────
def _page_clinical(result, catq_result, raadsr_result, et, styles: dict) -> list:
    story = [PageBreak()]
    story.append(Spacer(1, 8))

    # ── Marcadores FAF
    story += _section_title("MARCADORES CLINICOS DO FENÓTIPO AUTISTA FEMININO (FAF)", styles)
    story.append(Paragraph(
        "Sinais frequentemente ausentes em avaliacoes padrao. Marcadores detectados "
        "automaticamente a partir dos dados disponiveis. Marcadores sem dados requerem "
        "avaliacao clinica presencial.",
        styles["small_italic"],
    ))
    story.append(Spacer(1, 6))

    high_camouflage = result.camouflage_weight_used >= 0.55
    low_social_fix  = et is not None and et.social_fixation_ratio < 0.45
    high_raadsr     = raadsr_result is not None and raadsr_result.total_score >= 65
    is_faf          = "faf" in result.phenotype_subtype

    markers = [
        ("Alto indice de camuflagem / mascaramento", "CAT-Q", high_camouflage),
        ("Fixacao social atipica (evitacao disfarçada)", "Eye-Tracking", low_social_fix),
        ("Tracos autistas acima do limiar RAADS-R (>= 65)", "RAADS-R", high_raadsr),
        ("Subtipo FAF identificado pelo motor multimodal", "Neurotrace AI", is_faf),
        ("Burnout autistico (historico ou atual)", "Clinico — anamnese", None),
        ("Diagnosticos previos: TDAH, ansiedade, depressao, TPB", "Clinico — anamnese", None),
        ("Hipersensibilidade sensorial", "RAADS-R / Clinico", None),
        ("Interesses especificos intensos (tematica social/humanistica)", "Clinico — anamnese", None),
    ]

    marker_header = [Paragraph(h, styles["table_header"]) for h in
                     ["Marcador", "Fonte", "Status"]]
    marker_rows = [marker_header]
    for label, source, detected in markers:
        if detected is True:
            status = "DETECTADO"
            status_color = C_RED
        elif detected is False:
            status = "Nao detectado"
            status_color = C_GREEN
        else:
            status = "Avaliacao clinica"
            status_color = C_GRAY_MD
        marker_rows.append([
            Paragraph(label, styles["table_cell"]),
            Paragraph(source, styles["small"]),
            Paragraph(status, ParagraphStyle("MStatus", fontName="Helvetica-Bold",
                      fontSize=8, textColor=status_color, alignment=TA_CENTER)),
        ])

    m_table = Table(marker_rows, colWidths=[8 * cm, 4 * cm, 4.5 * cm])
    m_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_PURPLE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_GRAY_LT]),
        ("GRID",          (0, 0), (-1, -1), 0.3, C_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(m_table)
    story.append(Spacer(1, 12))

    # ── Diagnóstico diferencial
    story += _section_title("DIAGNOSTICO DIFERENCIAL", styles)
    story.append(Paragraph(
        "Sobreposicao de caracteristicas em mulheres adultas. "
        "A=Alto · M=Moderado · B=Baixo · V=Variavel.",
        styles["small_italic"],
    ))
    story.append(Spacer(1, 6))

    dd_cols = ["Caracteristica", "TEA (FAF)", "TDAH", "Ansiedade", "TPB"]
    dd_data_raw = [
        ["Dificuldade de contato visual", "A", "B", "A", "V"],
        ["Ansiedade social", "A", "M", "MA", "A"],
        ["Dificuldade em amizades", "A", "M", "M", "A"],
        ["Rigidez cognitiva", "A", "M", "B", "B"],
        ["Hiperfoco / interesses intensos", "A", "A*", "B", "B"],
        ["Sensibilidade sensorial", "A", "M", "M", "B"],
        ["Mascaramento / camuflagem", "MA", "B", "M", "B"],
        ["Regulacao emocional prejudicada", "M", "A", "A", "MA"],
        ["Impulsividade", "B-M", "A", "B", "A"],
        ["Medo de abandono", "B", "B", "B", "MA"],
    ]

    dd_color_map = {
        "MA": colors.HexColor("#ffcdd2"),
        "A":  colors.HexColor("#fff9c4"),
        "M":  colors.HexColor("#e8f5e9"),
        "B":  colors.HexColor("#f5f5f5"),
        "B-M": colors.HexColor("#e8f5e9"),
        "V":  colors.HexColor("#fce4ec"),
        "A*": colors.HexColor("#fff3e0"),
    }

    dd_header = [Paragraph(c, styles["table_header"]) for c in dd_cols]
    dd_rows_table = [dd_header]
    dd_style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), C_PURPLE),
        ("GRID",          (0, 0), (-1, -1), 0.3, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]

    for i, row in enumerate(dd_data_raw, start=1):
        label = row[0]
        vals  = row[1:]
        table_row = [Paragraph(label, styles["table_cell"])]
        for j, v in enumerate(vals):
            table_row.append(Paragraph(v, styles["table_cell_center"]))
            bg = dd_color_map.get(v, C_WHITE)
            dd_style_cmds.append(("BACKGROUND", (j + 1, i), (j + 1, i), bg))
        dd_rows_table.append(table_row)

    dd_table = Table(dd_rows_table, colWidths=[6.5 * cm, 2.5 * cm, 2 * cm, 2.5 * cm, 2.5 * cm])
    dd_table.setStyle(TableStyle(dd_style_cmds))
    story.append(dd_table)
    story.append(Paragraph(
        "MA=Muito Alto  |  * Hiperfoco no TDAH tende a ser mais generalizado, "
        "no TEA mais restrito e intenso.  |  Referencia: Lai et al. (2015); Dell'Osso et al. (2018).",
        styles["small_italic"],
    ))

    return story


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 4 — Referências e Disclaimer
# ─────────────────────────────────────────────────────────────────────────────
def _page_references(styles: dict) -> list:
    story = [PageBreak()]
    story.append(Spacer(1, 8))

    story += _section_title("REFERENCIAS CIENTIFICAS", styles)

    refs = [
        "Hull, L. et al. (2019). Putting on my best normal: Social camouflaging in adults with autism spectrum conditions. "
        "Journal of Autism and Developmental Disorders, 49(9), 3527-3543. doi:10.1007/s10803-018-3821-5",

        "Ritvo, R.A. et al. (2011). The Ritvo Autism Asperger Diagnostic Scale-Revised (RAADS-R): "
        "A scale to assist the diagnosis of autism spectrum disorder in adults: an international validation study. "
        "Journal of Autism and Developmental Disorders, 41(8), 1076-1089. doi:10.1007/s10803-010-1133-5",

        "Lai, M.C. et al. (2015). Sex/gender differences and autism: Setting the scene for future research. "
        "Journal of Child Psychology and Psychiatry, 56(6), 614-620. doi:10.1111/jcpp.12413",

        "Bargiela, S. et al. (2016). The experiences of late-diagnosed women with autism spectrum conditions: "
        "An investigation of the female autism phenotype. Journal of Autism and Developmental Disorders, "
        "46(10), 3281-3294. doi:10.1007/s10803-016-2872-8",

        "Frazier, T.W. et al. (2018). A meta-analysis of gaze differences to social and nonsocial information "
        "between individuals with and without autism. JADD, 48(7), 2330-2345.",

        "Jones, W. & Klin, A. (2013). Attention to eyes is present but in decline in 2-6-month-old infants "
        "later diagnosed with autism. Nature, 504(7480), 427-431.",

        "Rutherford, M. et al. (2016). Gender ratio in a clinical population sample, age of diagnosis and "
        "duration of assessment in children and adults with autism spectrum disorder. "
        "Autism, 20(5), 628-634.",

        "Dell'Osso, L. et al. (2018). Borderline intellectual functioning and autism spectrum disorder: "
        "The misdiagnosis of adult patients. CNS Spectrums, 23(6), 370-374.",

        "Carpenter, K.L. et al. (2021). Digital behavioral phenotyping detects atypical pattern of facial "
        "expression in toddlers with autism. Autism Research, 14(6), 1210-1220.",
    ]

    for ref in refs:
        story.append(Paragraph(f"• {ref}", styles["ref"]))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 16))
    story += _section_title("AVISO REGULATORIO E LIMITACOES", styles)

    disclaimer_text = (
        "INSTRUMENTO DE TRIAGEM — NAO DIAGNOSTICO. Este relatorio e produzido por um sistema de software "
        "de apoio a decisao clinica baseado em inteligencia artificial (SaMD — Software as a Medical Device), "
        "desenvolvido em conformidade com os principios de IA Explicavel (XAI FAIR). "
        "OS RESULTADOS DESTE RELATORIO NAO CONSTITUEM DIAGNOSTICO MEDICO e devem ser interpretados "
        "exclusivamente por medico psiquiatra, neurologista ou neuropediatra certificado, com experiencia "
        "em Transtorno do Espectro Autista. "
        "Um resultado positivo na triagem deve ser seguido de avaliacao clinica presencial completa, "
        "incluindo instrumentos padronizados (ADOS-2, ADI-R) e historico desenvolvimental detalhado. "
        "Um resultado negativo nao exclui o diagnostico de TEA, especialmente em individuos com alto "
        "mascaramento ou dados incompletos. "
        "\n\n"
        "LGPD (Lei 13.709/2018): Os dados processados por este sistema sao de natureza sensivelmente "
        "pessoal (dado de saude). O processamento e realizado com base no consentimento expresso do titular "
        "e observa os principios de minimizacao, finalidade e seguranca previstos na LGPD. "
        "\n\n"
        "Conformidade: ANVISA RDC 657/2022 (SaMD) | LGPD | XAI FAIR Principles | DSM-5-TR (APA, 2022)."
    )
    story.append(Paragraph(disclaimer_text, styles["disclaimer"]))

    story.append(Spacer(1, 12))
    story.append(_hr())
    story.append(Paragraph(
        "SpectrumIA / Neurotrace AI — Sistema de Triagem Multimodal para TEA  |  "
        "Desenvolvido para uso clinico supervisionado",
        styles["small"],
    ))

    return story


# ─────────────────────────────────────────────────────────────────────────────
# API PÚBLICA
# ─────────────────────────────────────────────────────────────────────────────
def generate_report_pdf(
    result,
    catq_result=None,
    raadsr_result=None,
    et=None,
    patient_name: str = "",
    clinician: str = "",
    assessment_id: str = "",
) -> io.BytesIO:
    """
    Gera o relatório clínico PDF em memória.

    Parâmetros
    ----------
    result       : FusionResult — saída do motor de fusão multimodal
    catq_result  : QuestionnaireResult | None
    raadsr_result: QuestionnaireResult | None
    et           : EyeTrackingFeatures | None
    patient_name : str — nome do paciente (exibido no relatório)
    clinician    : str — nome do clínico solicitante
    assessment_id: str — identificador único da sessão

    Retorno
    -------
    io.BytesIO pronto para st.download_button(data=...)
    """
    if not assessment_id:
        assessment_id = datetime.now().strftime("SA-%Y%m%d-%H%M%S")

    patient_label = f"Paciente: {patient_name}" if patient_name else "Paciente: Anonimo"

    styles = _build_styles()
    on_page = _make_on_page(assessment_id, patient_label)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2.2 * cm,
        bottomMargin=1.5 * cm,
        title=f"SpectrumIA — Relatório de Triagem TEA — {assessment_id}",
        author="SpectrumIA / Neurotrace AI",
        subject="Triagem Multimodal para Transtorno do Espectro Autista",
    )

    story = []
    story += _page_summary(result, catq_result, raadsr_result, styles, patient_name, clinician)
    story += _page_evidence(result, catq_result, raadsr_result, et, styles)
    story += _page_clinical(result, catq_result, raadsr_result, et, styles)
    story += _page_references(styles)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

    buf.seek(0)
    logger.info("PDF report generated: %s (%d bytes)", assessment_id, buf.getbuffer().nbytes)
    return buf
