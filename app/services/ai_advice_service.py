"""Premium bo'limidagi 5 ta shaxsiy maslahat (AI).

Uchta qoida butun modulni belgilaydi:

1. SAHIFA HECH QACHON AI GA BOG'LIQ EMAS. Maslahat alohida POST bilan so'raladi,
   natija bazaga yoziladi va keyin sahifada ko'rsatiladi. Tashqi xizmat o'lsa,
   natija sahifasi ochilaveradi.
2. HAR SO'ROV PUL. Javob bir marta yaratiladi va saqlanadi; muvaffaqiyatsizlik ham
   yoziladi (urinishlar soni bilan), kunlik umumiy chegara bor, endpoint esa IP
   bo'yicha cheklangan.
3. SO'ROVDA SHAXSIY MA'LUMOT YO'Q. Modelga faqat MBTI tipi va to'rt o'lchov foizi
   yuboriladi — ism, telegram, token, to'lov kodi va javoblar EMAS.

"Band qilish" naqshi navbatdagidek: API chaqirilishidan OLDIN qator `failed` holatida
yoziladi va commit qilinadi. Shunda jarayon so'rov o'rtasida o'lsa ham urinish
hisoblangan bo'ladi — aks holda uzilib qolgan har chaqiruv bepul bo'lib, tugmani
qayta bosish cheksiz pul sarflardi.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai import provider as ai_provider
from app.ai.provider import AiPermanentError, AiProvider, AiTemporaryError
from app.config import settings
from app.i18n import DEFAULT as DEFAULT_LANG
from app.i18n import normalize_lang
from app.models.ai_advice import (
    AI_ADVICE_PROMPT_VERSION,
    AI_ADVICE_STATUS_FAILED,
    AI_ADVICE_STATUS_READY,
    AiAdviceReport,
)
from app.models.personality import PersonalityTestSession
from app.services.personality_scoring import calculate_personality_result
from app.services.premium_access import has_premium_access
from app.timeutils import tashkent_day_start, utcnow

logger = logging.getLogger(__name__)

TITLE_MAX = 80
BODY_MAX = 600
# Model kelishilgan sondan ko'p bersa ortiqchasi tashlanadi, kam bersa javob
# rad etiladi: "3 ta maslahat" premium va'dasini bajarmaydi.
MIN_ITEMS_RATIO = 1.0

LANGUAGE_NAMES = {"uz": "o‘zbek (lotin yozuvida)", "ru": "русский"}

_JSON_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")

# Natija kodlari — shablon shularni matnga aylantiradi.
READY = "ready"
DISABLED = "disabled"
NOT_PREMIUM = "not_premium"
ALREADY = "already"
DAILY_LIMIT = "daily_limit"
ATTEMPTS_EXHAUSTED = "attempts_exhausted"
TEMPORARY_ERROR = "temporary"
PERMANENT_ERROR = "permanent"
INVALID_RESPONSE = "invalid_response"


@dataclass(frozen=True)
class AdviceItem:
    title: str
    body: str


@dataclass(frozen=True)
class AdviceState:
    """Natija sahifasi uchun tayyor ko'rinish."""

    enabled: bool
    items: list[AdviceItem] = field(default_factory=list)
    failed: bool = False
    can_generate: bool = False
    attempts_left: int = 0

    @property
    def has_items(self) -> bool:
        return bool(self.items)


def is_enabled() -> bool:
    return settings.ai_advice_configured


def resolve_language(language: str | None) -> str:
    return normalize_lang(language) or DEFAULT_LANG


def get_report(db: Session, session_id: int, language: str) -> AiAdviceReport | None:
    stmt = select(AiAdviceReport).where(
        AiAdviceReport.session_id == session_id,
        AiAdviceReport.language == resolve_language(language),
    )
    return db.scalar(stmt)


def items_from_report(report: AiAdviceReport | None) -> list[AdviceItem]:
    if report is None or not report.is_ready:
        return []
    parsed: list[AdviceItem] = []
    for raw in report.items:
        if not isinstance(raw, dict):
            continue
        title, body = raw.get("title"), raw.get("body")
        if isinstance(title, str) and isinstance(body, str) and body:
            parsed.append(AdviceItem(title=title, body=body))
    return parsed


def advice_state(db: Session, session: PersonalityTestSession, language: str) -> AdviceState:
    """Shablon uchun holat. Premium bo'lmasa funksiya umuman ko'rsatilmaydi."""
    if not is_enabled() or not has_premium_access(session):
        return AdviceState(enabled=False)
    report = get_report(db, session.id, language)
    items = items_from_report(report)
    attempts = report.attempts if report is not None else 0
    attempts_left = max(0, settings.ai_max_attempts - attempts)
    return AdviceState(
        enabled=True,
        items=items,
        failed=report is not None and not items,
        can_generate=not items and attempts_left > 0,
        attempts_left=attempts_left,
    )


# --- Yaratish ---


def generated_today(db: Session) -> int:
    """Bugun (Toshkent kuni) nechta sessiyaga javob yaratilgan.

    Bu API CHAQIRUVLARI soni emas, sessiyalar soni: bitta qator kun ichida
    `AI_MAX_ATTEMPTS` martagacha urinishi mumkin. Ya'ni eng yomon holatda
    chaqiruvlar soni AI_DAILY_LIMIT * AI_MAX_ATTEMPTS ga teng.
    """
    stmt = (
        select(func.count())
        .select_from(AiAdviceReport)
        .where(AiAdviceReport.updated_at >= tashkent_day_start())
    )
    return int(db.scalar(stmt) or 0)


def generate(
    db: Session,
    session: PersonalityTestSession,
    *,
    language: str,
    provider: AiProvider | None = None,
) -> str:
    """Maslahatlarni yaratadi va yozadi. Qaytadigan qiymat — natija kodi.

    DIQQAT: bu funksiya bir necha marta COMMIT qiladi. Tashqi chaqiruv soniyalab
    davom etadi va uni ochiq tranzaksiya ichida kutish ulanishni bekorga band qiladi.
    """
    if not is_enabled():
        return DISABLED
    if not has_premium_access(session):
        return NOT_PREMIUM

    lang = resolve_language(language)
    report = get_report(db, session.id, lang)
    if report is not None and report.is_ready:
        return ALREADY
    if report is not None and report.attempts >= settings.ai_max_attempts:
        return ATTEMPTS_EXHAUSTED
    if generated_today(db) >= settings.ai_daily_limit:
        logger.warning("AI maslahatlar kunlik chegarasi tugadi (%s)", settings.ai_daily_limit)
        return DAILY_LIMIT

    client = provider or ai_provider.build_provider()
    if client is None:
        return DISABLED

    report = _reserve(db, report, session_id=session.id, language=lang, model=client.model)

    try:
        result = client.complete(
            system=system_prompt(lang),
            prompt=user_prompt(session, lang),
            max_tokens=settings.ai_max_output_tokens,
        )
    except AiTemporaryError as exc:
        _fail(db, report, f"vaqtinchalik: {exc}")
        return TEMPORARY_ERROR
    except AiPermanentError as exc:
        # Urinishlar darhol tugatiladi: sozlama nuqsoni foydalanuvchining
        # byudjetidan yechilmasligi kerak.
        _fail(db, report, f"doimiy: {exc}", exhaust=True)
        return PERMANENT_ERROR
    except Exception as exc:  # provayder kutilmagan narsa qaytardi
        logger.exception("AI maslahat yaratishda kutilmagan xato")
        _fail(db, report, f"kutilmagan: {exc}")
        return TEMPORARY_ERROR

    items = parse_items(result.text, expected=settings.ai_advice_count)
    if items is None:
        _fail(db, report, "javob kutilgan JSON shaklida emas")
        return INVALID_RESPONSE

    report.status = AI_ADVICE_STATUS_READY
    report.items = [{"title": item.title, "body": item.body} for item in items]
    report.last_error = None
    report.input_tokens = result.input_tokens
    report.output_tokens = result.output_tokens
    report.updated_at = utcnow()
    db.commit()
    return READY


def _reserve(
    db: Session,
    report: AiAdviceReport | None,
    *,
    session_id: int,
    language: str,
    model: str,
) -> AiAdviceReport:
    """Chaqiruvdan OLDIN urinishni yozadi va commit qiladi."""
    now = utcnow()
    if report is None:
        report = AiAdviceReport(
            session_id=session_id,
            language=language,
            status=AI_ADVICE_STATUS_FAILED,
            model=model,
            prompt_version=AI_ADVICE_PROMPT_VERSION,
            items=[],
            attempts=0,
            created_at=now,
            updated_at=now,
        )
        db.add(report)
    report.status = AI_ADVICE_STATUS_FAILED
    report.model = model
    report.prompt_version = AI_ADVICE_PROMPT_VERSION
    report.attempts += 1
    report.last_error = "urinish tugallanmadi"
    report.updated_at = now
    db.commit()
    return report


def _fail(db: Session, report: AiAdviceReport, error: str, *, exhaust: bool = False) -> None:
    report.status = AI_ADVICE_STATUS_FAILED
    report.items = []
    report.last_error = error[:500]
    if exhaust:
        report.attempts = max(report.attempts, settings.ai_max_attempts)
    report.updated_at = utcnow()
    db.commit()


# --- So'rov matni ---


def system_prompt(language: str) -> str:
    language_name = LANGUAGE_NAMES.get(language, LANGUAGE_NAMES[DEFAULT_LANG])
    return (
        "Siz amaliy psixologiya asosida ish yuritadigan maslahatchisiz. "
        f"Javobni FAQAT {language_name} tilida yozasiz.\n"
        "Qoidalar:\n"
        "- Tibbiy yoki klinik tashxis qo'ymang, kasallik nomlarini ishlatmang.\n"
        "- Umumiy gaplardan qoching: har maslahat aynan shu xarakter tipiga tegishli "
        "va ertadan bajarib ko'rish mumkin bo'lgan aniq harakat bo'lsin.\n"
        "- Foydalanuvchiga «siz» deb murojaat qiling.\n"
        "- Javob FAQAT JSON bo'lsin, boshqa matnsiz."
    )


def user_prompt(session: PersonalityTestSession, language: str) -> str:
    """So'rov matni. Shaxsiy ma'lumot ATAYLAB kiritilmaydi."""
    result = calculate_personality_result(
        session.e_score,
        session.i_score,
        session.s_score,
        session.n_score,
        session.t_score,
        session.f_score,
        session.j_score,
        session.p_score,
    )
    scale = ", ".join(
        f"{left.upper()} {getattr(result, name).left_percent}% / "
        f"{right.upper()} {getattr(result, name).right_percent}%"
        for name, left, right in (("ei", "i", "e"), ("sn", "s", "n"), ("tf", "t", "f"), ("jp", "j", "p"))
    )
    count = settings.ai_advice_count
    return (
        f"MBTI tipi: {session.result_type}.\n"
        f"O'lchovlar: {scale}.\n\n"
        f"Shu tip uchun {count} ta maslahat yozing. Har biri: qisqa sarlavha "
        f"(ko'pi bilan {TITLE_MAX} belgi) va 2-3 jumlalik tushuntirish "
        f"(ko'pi bilan {BODY_MAX} belgi).\n"
        "Mavzular takrorlanmasin: kunlik odat, ish/o'qish, muloqot, energiya va "
        "qaror qabul qilish.\n\n"
        'Javob shakli: {"advice": [{"title": "...", "body": "..."}]}'
    )


# --- Javobni tekshirish ---


def parse_items(raw: str, *, expected: int) -> list[AdviceItem] | None:
    """Model javobini tekshiradi. None — javob yaroqsiz.

    Qisman javob QABUL QILINMAYDI: "5 ta maslahat" deb va'da berilgan joyda 2 tasini
    ko'rsatish premiumni buzilgandek ko'rsatardi.
    """
    payload = _load_json(raw)
    if payload is None:
        return None
    entries = payload.get("advice") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return None

    items: list[AdviceItem] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        title = _clean(entry.get("title"), TITLE_MAX)
        body = _clean(entry.get("body"), BODY_MAX)
        if not body:
            continue
        items.append(AdviceItem(title=title or f"{len(items) + 1}-maslahat", body=body))
        if len(items) == expected:
            break
    if len(items) < int(expected * MIN_ITEMS_RATIO):
        return None
    return items


def _load_json(raw: str) -> dict[str, Any] | None:
    text = _JSON_FENCE_RE.sub("", (raw or "").strip())
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _clean(value: object, limit: int) -> str:
    """Boshqaruv belgilarini olib tashlaydi va uzunlikni cheklaydi.

    Matn Jinja avtoescape bilan chiqadi, ya'ni HTML sifatida bajarilmaydi. Bu yerda
    esa ko'rinishni buzadigan narsalar olib tashlanadi: yo'nalish belgilari
    (RTL override) va nazoratdagi kodlar.
    """
    if not isinstance(value, str):
        return ""
    # Qator ko'chirish AVVAL probelga aylantiriladi: uni boshqaruv belgisi sifatida
    # olib tashlash ikki so'zni bir-biriga yopishtirib qo'yardi.
    spaced = value.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    stripped = "".join(ch for ch in spaced if unicodedata.category(ch) not in ("Cc", "Cf"))
    collapsed = _WHITESPACE_RE.sub(" ", stripped).strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[:limit].rstrip() + "…"
