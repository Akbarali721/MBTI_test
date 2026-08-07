"""Premium natijani PDF hisobot sifatida tayyorlaydi.

Shriftlar `app/pdf/fonts/` da subset qilingan Inter (lotin + kirill) — reportlab'ning
o'rnatilgan shriftlarida kirill ham, o'zbek tutuq belgisi ham yo'q.
Shriftlar `scripts/fetch_pdf_fonts.py` bilan yangilanadi.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

logger = logging.getLogger(__name__)

FONT_DIR = Path(__file__).resolve().parent / "fonts"
FONT_REGULAR = "InterPDF"
FONT_BOLD = "InterPDF-Bold"

NAVY = colors.HexColor("#0b2348")
GOLD = colors.HexColor("#8a5c10")
MUTED = colors.HexColor("#5f6877")
TRACK = colors.HexColor("#e9dfd0")
INK = colors.HexColor("#10213c")

_fonts_registered = False


def _register_fonts() -> bool:
    """Shriftlar yo'q bo'lsa PDF umuman tuzilmasin — yarim buzuq fayl bermaymiz."""
    global _fonts_registered
    if _fonts_registered:
        return True
    regular = FONT_DIR / "Inter-Regular.ttf"
    bold = FONT_DIR / "Inter-Bold.ttf"
    if not regular.exists() or not bold.exists():
        logger.error("PDF shriftlari topilmadi: %s — scripts/fetch_pdf_fonts.py ni ishga tushiring", FONT_DIR)
        return False
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(regular)))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold)))
    _fonts_registered = True
    return True


def fonts_available() -> bool:
    return _register_fonts()


@dataclass(frozen=True)
class PdfSection:
    title: str
    body: str


@dataclass(frozen=True)
class PdfDimension:
    left_label: str
    left_percent: int
    right_label: str
    right_percent: int


@dataclass(frozen=True)
class PdfReport:
    """Shablonga bog'liq bo'lmagan ma'lumot — router yig'adi, bu modul chizadi."""

    brand: str
    result_type: str
    title: str
    short_description: str
    strengths: list[str]
    challenges: list[str]
    dimensions: list[PdfDimension]
    sections: list[PdfSection]
    strengths_label: str
    challenges_label: str
    dimensions_label: str
    footer_note: str
    generated_label: str
    generated_at: datetime
    share_url: str | None = None


class DimensionBar(Flowable):
    """Ikki qutbli chiziq: chap ulush oltin, o'ng ulush och rangda."""

    def __init__(self, left_percent: int, width: float, height: float = 5 * mm) -> None:
        super().__init__()
        self.left_percent = max(0, min(100, left_percent))
        self.width = width
        self.height = height

    def draw(self) -> None:
        canvas = self.canv
        radius = self.height / 2
        canvas.setFillColor(TRACK)
        canvas.roundRect(0, 0, self.width, self.height, radius, stroke=0, fill=1)
        filled = self.width * self.left_percent / 100
        if filled > 0:
            canvas.setFillColor(NAVY)
            canvas.roundRect(0, 0, max(filled, radius * 2), self.height, radius, stroke=0, fill=1)


def _styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle(
        "body",
        fontName=FONT_REGULAR,
        fontSize=10.5,
        leading=15.5,
        textColor=INK,
        alignment=TA_LEFT,
    )
    return {
        "body": base,
        "brand": ParagraphStyle(
            "brand", parent=base, fontName=FONT_BOLD, fontSize=9, textColor=GOLD, leading=12
        ),
        "title": ParagraphStyle(
            "title", parent=base, fontName=FONT_BOLD, fontSize=23, leading=27, textColor=NAVY, spaceAfter=2
        ),
        "type": ParagraphStyle(
            "type", parent=base, fontName=FONT_BOLD, fontSize=11, textColor=GOLD, spaceAfter=10
        ),
        "section": ParagraphStyle(
            "section",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=8.5,
            textColor=MUTED,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "dimension": ParagraphStyle("dimension", parent=base, fontSize=9, textColor=MUTED, spaceAfter=2),
        "footer": ParagraphStyle("footer", parent=base, fontSize=8.5, textColor=MUTED, leading=12),
    }


def _bullet_list(items: list[str], style: ParagraphStyle) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(item, style), leftIndent=10) for item in items],
        bulletType="bullet",
        bulletFontName=FONT_REGULAR,
        bulletFontSize=8,
        bulletColor=GOLD,
        leftIndent=12,
        spaceBefore=0,
    )


def _dimension_block(report: PdfReport, styles: dict[str, ParagraphStyle], width: float) -> list[Flowable]:
    blocks: list[Flowable] = []
    for pair in report.dimensions:
        label = f"{pair.left_label} {pair.left_percent}% · {pair.right_label} {pair.right_percent}%"
        blocks.append(Paragraph(label, styles["dimension"]))
        blocks.append(DimensionBar(pair.left_percent, width))
        blocks.append(Spacer(1, 5 * mm))
    return blocks


def build_result_pdf(report: PdfReport) -> bytes | None:
    """Hisobotni PDF baytlariga aylantiradi; shriftlar yo'q bo'lsa None qaytaradi."""
    if not _register_fonts():
        return None

    buffer = BytesIO()
    margin = 18 * mm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title=f"{report.result_type} — {report.title}",
        author=report.brand,
        subject=report.brand,
    )
    styles = _styles()
    content_width = doc.width
    story: list[Flowable] = [
        Paragraph(report.brand.upper(), styles["brand"]),
        Spacer(1, 6 * mm),
        Paragraph(report.title, styles["title"]),
        Paragraph(report.result_type, styles["type"]),
        Paragraph(report.short_description, styles["body"]),
    ]

    if report.strengths:
        story.append(Paragraph(report.strengths_label, styles["section"]))
        story.append(_bullet_list(report.strengths, styles["body"]))
    if report.challenges:
        story.append(Paragraph(report.challenges_label, styles["section"]))
        story.append(_bullet_list(report.challenges, styles["body"]))

    story.append(Paragraph(report.dimensions_label, styles["section"]))
    story.extend(_dimension_block(report, styles, content_width))

    if report.sections:
        story.append(PageBreak())
        for section in report.sections:
            story.append(
                KeepTogether(
                    [
                        Paragraph(section.title, styles["section"]),
                        Paragraph(section.body, styles["body"]),
                    ]
                )
            )

    story.append(Spacer(1, 10 * mm))
    footer = report.footer_note
    if report.share_url:
        footer = f"{footer}<br/>{report.share_url}"
    stamp = report.generated_at.strftime("%d.%m.%Y")
    story.append(Paragraph(f"{footer}<br/>{report.generated_label} {stamp}", styles["footer"]))

    doc.build(story)
    return buffer.getvalue()


def pdf_filename(result_type: str, brand_slug: str = "xarakter-testi") -> str:
    return f"{brand_slug}-{result_type.lower()}.pdf"
