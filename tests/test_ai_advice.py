"""Premium bo'limidagi AI maslahatlar.

HECH BIR test tarmoqqa chiqmaydi: provayder soxta obyekt bilan almashtiriladi.
Testlarning katta qismi "pul sarflanmasligi kerak" holatlariga tegishli.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.ai.provider import AiPermanentError, AiResult, AiTemporaryError
from app.config import settings
from app.models.ai_advice import AI_ADVICE_STATUS_READY, AiAdviceReport
from app.services import ai_advice_service
from tests.helpers import complete_session, db_session, session_by_token

API_KEY = "sinov-kaliti"


class FakeProvider:
    """`AiProvider` protokoliga mos soxta provayder."""

    model = "sinov-modeli"

    def __init__(self, *responses: object) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, str]] = []

    def complete(self, *, system: str, prompt: str, max_tokens: int) -> AiResult:
        self.calls.append({"system": system, "prompt": prompt})
        response = self._responses.pop(0) if self._responses else self._responses
        if isinstance(response, Exception):
            raise response
        if isinstance(response, AiResult):
            return response
        return AiResult(text=str(response), input_tokens=120, output_tokens=340)


def advice_json(count: int = 5, *, body: str = "Ertadan boshlab shu qadamni bajaring.") -> str:
    return json.dumps(
        {"advice": [{"title": f"{i + 1}-qadam", "body": body} for i in range(count)]},
        ensure_ascii=False,
    )


@pytest.fixture()
def ai_enabled(monkeypatch):
    monkeypatch.setattr(settings, "ai_api_key", API_KEY)
    return API_KEY


def premium_session(client, *, trial: bool = False) -> str:
    token = complete_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        if trial:
            session.premium_until = datetime.now(timezone.utc) + timedelta(days=3)
        else:
            session.is_premium = True
        db.commit()
    return token


def install(monkeypatch, provider: FakeProvider) -> FakeProvider:
    monkeypatch.setattr("app.ai.provider.build_provider", lambda: provider)
    return provider


def report_for(client, token: str) -> AiAdviceReport | None:
    with db_session(client) as db:
        session_id = session_by_token(db, token).id
        return db.scalar(select(AiAdviceReport).where(AiAdviceReport.session_id == session_id))


# --------------------------- o'chiq holat ---------------------------


def test_without_an_api_key_the_block_is_absent_and_nothing_is_written(client, monkeypatch):
    monkeypatch.setattr(settings, "ai_api_key", "")
    token = premium_session(client)

    page = client.get(f"/personality/result/{token}")
    assert "ai-advice" not in page.text

    posted = client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    assert posted.status_code == 303
    assert report_for(client, token) is None


def test_a_free_session_cannot_trigger_a_paid_call(client, ai_enabled, monkeypatch):
    """Fail-closed: premium bo'lmasa tashqi chaqiruv umuman bo'lmaydi."""
    provider = install(monkeypatch, FakeProvider(advice_json()))
    token = complete_session(client)

    page = client.get(f"/personality/result/{token}")
    assert "ai-advice" not in page.text

    client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    assert provider.calls == []
    assert report_for(client, token) is None


# --------------------------- muvaffaqiyatli yo'l ---------------------------


def test_a_premium_user_gets_five_advices_on_the_page(client, ai_enabled, monkeypatch):
    provider = install(monkeypatch, FakeProvider(advice_json()))
    token = premium_session(client)

    assert client.get(f"/personality/result/{token}").text.count("mbti-ai-advice__item") == 0

    posted = client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    assert posted.status_code == 303
    assert "notice=ready" in posted.headers["location"]

    page = client.get(f"/personality/result/{token}?notice=ready")
    assert page.text.count("mbti-ai-advice__item") == 5
    assert "1-qadam" in page.text
    assert len(provider.calls) == 1

    report = report_for(client, token)
    assert report.status == AI_ADVICE_STATUS_READY
    assert report.output_tokens == 340
    assert report.model == "sinov-modeli"


def test_a_trial_user_also_gets_advice(client, ai_enabled, monkeypatch):
    install(monkeypatch, FakeProvider(advice_json()))
    token = premium_session(client, trial=True)

    client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    assert report_for(client, token).status == AI_ADVICE_STATUS_READY


def test_a_ready_report_is_never_regenerated(client, ai_enabled, monkeypatch):
    """Ikkinchi bosish pul sarflamasligi kerak."""
    provider = install(monkeypatch, FakeProvider(advice_json(), advice_json()))
    token = premium_session(client)

    client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)

    assert len(provider.calls) == 1


def test_russian_and_uzbek_reports_live_side_by_side(client, ai_enabled, monkeypatch):
    provider = install(monkeypatch, FakeProvider(advice_json(), advice_json()))
    token = premium_session(client)

    client.post(f"/personality/result/{token}/ai-advice?lang=uz", follow_redirects=False)
    client.post(f"/personality/result/{token}/ai-advice?lang=ru", follow_redirects=False)

    assert len(provider.calls) == 2
    with db_session(client) as db:
        session_id = session_by_token(db, token).id
        languages = set(
            db.scalars(select(AiAdviceReport.language).where(AiAdviceReport.session_id == session_id))
        )
    assert languages == {"uz", "ru"}


# --------------------------- xatolar ---------------------------


def test_a_temporary_error_counts_one_attempt_and_allows_a_retry(client, ai_enabled, monkeypatch):
    provider = install(monkeypatch, FakeProvider(AiTemporaryError("timeout"), advice_json()))
    token = premium_session(client)

    first = client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    assert "notice=temporary" in first.headers["location"]
    assert report_for(client, token).attempts == 1

    page = client.get(f"/personality/result/{token}?notice=temporary")
    assert "ai-advice" in page.text  # tugma qoladi

    client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    assert report_for(client, token).status == AI_ADVICE_STATUS_READY
    assert len(provider.calls) == 2


def test_a_permanent_error_stops_retrying_immediately(client, ai_enabled, monkeypatch):
    """Noto'g'ri kalit har foydalanuvchidan uch marta pul yechmasligi kerak."""
    provider = install(monkeypatch, FakeProvider(AiPermanentError("HTTP 401")))
    token = premium_session(client)

    posted = client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    assert "notice=permanent" in posted.headers["location"]
    assert report_for(client, token).attempts >= settings.ai_max_attempts

    client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    assert len(provider.calls) == 1


def test_attempts_are_capped(client, ai_enabled, monkeypatch):
    provider = install(monkeypatch, FakeProvider(*[AiTemporaryError("uzildi")] * 10))
    token = premium_session(client)

    for _ in range(settings.ai_max_attempts + 2):
        client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)

    assert len(provider.calls) == settings.ai_max_attempts


def test_a_partial_answer_is_rejected_rather_than_shown(client, ai_enabled, monkeypatch):
    """«5 ta maslahat» deb va'da berilgan joyda 2 tasini ko'rsatib bo'lmaydi."""
    install(monkeypatch, FakeProvider(advice_json(count=2)))
    token = premium_session(client)

    posted = client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    assert "notice=invalid_response" in posted.headers["location"]
    report = report_for(client, token)
    assert report.status != AI_ADVICE_STATUS_READY
    assert report.items == []


def test_a_non_json_answer_is_rejected(client, ai_enabled, monkeypatch):
    install(monkeypatch, FakeProvider("Salom! Mana maslahatlar: birinchidan..."))
    token = premium_session(client)

    posted = client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    assert "notice=invalid_response" in posted.headers["location"]


def test_an_unexpected_provider_crash_does_not_break_the_page(client, ai_enabled, monkeypatch):
    install(monkeypatch, FakeProvider(RuntimeError("provayder yiqildi")))
    token = premium_session(client)

    posted = client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    assert posted.status_code == 303
    assert client.get(f"/personality/result/{token}").status_code == 200


def test_the_daily_limit_blocks_new_sessions(client, ai_enabled, monkeypatch):
    provider = install(monkeypatch, FakeProvider(advice_json(), advice_json()))
    monkeypatch.setattr(settings, "ai_daily_limit", 1)

    first = premium_session(client)
    client.post(f"/personality/result/{first}/ai-advice", follow_redirects=False)

    client.cookies.clear()
    second = premium_session(client)
    posted = client.post(f"/personality/result/{second}/ai-advice", follow_redirects=False)

    assert "notice=daily_limit" in posted.headers["location"]
    assert len(provider.calls) == 1


# --------------------------- so'rov va javob tarkibi ---------------------------


def test_the_prompt_carries_no_personal_data(client, ai_enabled, monkeypatch):
    provider = install(monkeypatch, FakeProvider(advice_json()))
    token = premium_session(client)
    with db_session(client) as db:
        session = session_by_token(db, token)
        session.telegram_username = "maxfiy_user"
        session.telegram_first_name = "Maxfiy Ism"
        payment_code = session.payment_code
        db.commit()

    client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)

    sent = provider.calls[0]["prompt"] + provider.calls[0]["system"]
    for secret in (token, payment_code, "maxfiy_user", "Maxfiy Ism"):
        assert secret not in sent
    with db_session(client) as db:
        assert session_by_token(db, token).result_type in sent


def test_model_output_is_escaped_on_the_page(client, ai_enabled, monkeypatch):
    payload = json.dumps(
        {
            "advice": [
                {"title": "<script>alert(1)</script>", "body": "a < b & c <img src=x onerror=alert(2)>"}
                for _ in range(5)
            ]
        }
    )
    install(monkeypatch, FakeProvider(payload))
    token = premium_session(client)

    client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)
    page = client.get(f"/personality/result/{token}")

    # Belgilar QOLADI, lekin teg sifatida emas: brauzer ularni matn deb ko'rsatadi.
    assert "<script>alert(1)</script>" not in page.text
    assert "<img src=x" not in page.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page.text
    assert "&lt;img src=x onerror=alert(2)&gt;" in page.text


def test_overlong_text_is_trimmed_and_control_characters_removed():
    raw = json.dumps(
        {"advice": [{"title": "T" * 200, "body": "birinchi\nikkinchi​ qator " + "x" * 900} for _ in range(5)]}
    )
    items = ai_advice_service.parse_items(raw, expected=5)

    assert items is not None
    assert len(items[0].title) <= ai_advice_service.TITLE_MAX + 1
    assert len(items[0].body) <= ai_advice_service.BODY_MAX + 1
    assert "" not in items[0].body
    assert "birinchi ikkinchi" in items[0].body


def test_a_fenced_json_block_is_still_parsed():
    raw = "```json\n" + advice_json() + "\n```"
    assert ai_advice_service.parse_items(raw, expected=5) is not None


def test_extra_items_are_dropped_to_the_configured_count():
    items = ai_advice_service.parse_items(advice_json(count=9), expected=5)
    assert items is not None and len(items) == 5


# --------------------------- PDF ---------------------------


def test_the_pdf_includes_the_advice_when_it_exists(client, ai_enabled, monkeypatch):
    from io import BytesIO

    from pypdf import PdfReader

    install(monkeypatch, FakeProvider(advice_json(body="Har kuni ertalab R&D daftarini oching.")))
    token = premium_session(client)
    client.post(f"/personality/result/{token}/ai-advice", follow_redirects=False)

    response = client.get(f"/personality/result/{token}/pdf")
    assert response.status_code == 200

    text = "".join(page.extract_text() or "" for page in PdfReader(BytesIO(response.content)).pages)
    # "&" reportlab uchun XML belgisi: escape qilinmasa hisobot umuman yig'ilmasdi.
    assert "R&D" in text
    assert "1-qadam" in text
