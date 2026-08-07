"""AI provayderi — faqat tarmoq qatlami.

Bu modul na bazani, na mahsulot qoidalarini biladi: matn beradi, matn qaytaradi.
Shu sabab testlarda uni almashtirish oson va HECH BIR test tarmoqqa chiqmaydi.

Xatolar ATAYLAB ikkiga bo'lingan, chunki ular butunlay boshqacha muomala talab qiladi:

* `AiTemporaryError` — tarmoq, timeout, 429, 5xx. Qayta urinish MA'NOLI.
* `AiPermanentError` — noto'g'ri kalit, noto'g'ri so'rov, model rad etdi. Qayta
  urinish faqat pul sarflaydi, shuning uchun yozuv darhol "failed" bo'ladi.

Ikkisi bir xil qaralganda, noto'g'ri AI_API_KEY bilan har foydalanuvchi tugmani
uch marta bosib uch marta 401 olardi.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

ANTHROPIC_VERSION = "2023-06-01"
# Javob juda katta bo'lsa uni o'qishning ma'nosi yo'q: 5 ta maslahat bir necha KB.
MAX_RESPONSE_BYTES = 256 * 1024


class AiTemporaryError(Exception):
    """Vaqtinchalik nosozlik — keyinroq qayta urinish mumkin."""


class AiPermanentError(Exception):
    """Sozlama yoki so'rov nuqsoni — qayta urinish yordam bermaydi."""


@dataclass(frozen=True)
class AiResult:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class AiProvider(Protocol):
    """Testlar shu shaklga mos soxta obyekt beradi."""

    model: str

    def complete(self, *, system: str, prompt: str, max_tokens: int) -> AiResult: ...


class AnthropicProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def complete(self, *, system: str, prompt: str, max_tokens: int) -> AiResult:
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        try:
            response = httpx.post(
                f"{self._base_url}/v1/messages",
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            raise AiTemporaryError(f"vaqt tugadi: {exc}") from exc
        except httpx.HTTPError as exc:
            raise AiTemporaryError(f"tarmoq xatosi: {exc}") from exc

        self._raise_for_status(response)
        return self._parse(response)

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        # Javob matni logga TUSHMAYDI: unda so'rov nusxasi bo'lishi mumkin.
        detail = f"HTTP {response.status_code}"
        if response.status_code in (408, 409, 429) or response.status_code >= 500:
            raise AiTemporaryError(detail)
        if response.status_code in (401, 403):
            logger.error("AI kaliti rad etildi (%s) — AI_API_KEY ni tekshiring", response.status_code)
        raise AiPermanentError(detail)

    @staticmethod
    def _parse(response: httpx.Response) -> AiResult:
        if len(response.content) > MAX_RESPONSE_BYTES:
            raise AiPermanentError("javob juda katta")
        try:
            data: Any = response.json()
        except json.JSONDecodeError as exc:
            raise AiTemporaryError(f"javob JSON emas: {exc}") from exc
        if not isinstance(data, dict):
            raise AiTemporaryError("javob kutilgan shaklda emas")

        blocks = data.get("content")
        parts: list[str] = []
        if isinstance(blocks, list):
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text")
                    if isinstance(text, str):
                        parts.append(text)
        if not parts:
            # `stop_reason: max_tokens` da ham shu yo'l: bo'sh javob vaqtinchalik
            # deb qaraladi, chunki ko'pincha uzilish yoki chegaradan.
            raise AiTemporaryError("javobda matn yo'q")

        raw_usage = data.get("usage")
        usage: dict[str, Any] = raw_usage if isinstance(raw_usage, dict) else {}
        return AiResult(
            text="".join(parts),
            input_tokens=_as_int(usage.get("input_tokens")),
            output_tokens=_as_int(usage.get("output_tokens")),
        )


def _as_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def build_provider() -> AiProvider | None:
    """Kalit bo'lmasa None — chaqiruvchi funksiyani butunlay o'chiradi.

    Testlar aynan shu funksiyani almashtiradi.
    """
    if not settings.ai_advice_configured:
        return None
    return AnthropicProvider(
        api_key=settings.ai_api_key.strip(),
        model=settings.ai_model,
        base_url=settings.ai_base_url,
        timeout_seconds=float(settings.ai_timeout_seconds),
    )
