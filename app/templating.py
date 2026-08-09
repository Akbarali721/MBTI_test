import hashlib
from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import _TemplateResponse

from app.i18n import (
    LANG_COOKIE_KEY,
    LANG_COOKIE_MAX_AGE,
    LANG_QUERY_KEY,
    language_links,
    normalize_lang,
    resolve_lang,
)
from app.i18n import t as translate
from app.paths import STATIC_DIR, TEMPLATES_DIR


def _relative_url_for(request: Request):
    def url_for(name: str, /, **path_params: Any) -> str:
        url = request.url_for(name, **path_params)
        if url.query:
            return f"{url.path}?{url.query}"
        return url.path

    return url_for


@lru_cache(maxsize=256)
def _fingerprint(rel_path: str, _mtime_ns: int, _size: int) -> str:
    """Fayl mazmunidan qisqa kesh-buster. mtime/size kesh kalitida — fayl
    o'zgarsa qiymat o'zi yangilanadi."""
    digest = hashlib.sha256((STATIC_DIR / rel_path).read_bytes()).hexdigest()
    return digest[:10]


def asset_url(path: str) -> str:
    """/static ostidagi faylga versiyalangan manzil: {{ asset_url('css/personality.css') }}."""
    rel_path = path.strip("/")
    full_path = STATIC_DIR / rel_path
    try:
        stat = full_path.stat()
    except OSError:
        # Fayl yo'q bo'lsa ham sahifa render bo'lsin (404 brauzerda ko'rinadi).
        return f"/static/{rel_path}"
    return f"/static/{rel_path}?v={_fingerprint(rel_path, stat.st_mtime_ns, stat.st_size)}"


class MBTIJinja2Templates(Jinja2Templates):
    def TemplateResponse(
        self,
        request: Request,
        name: str,
        context: dict[str, Any] | None = None,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background=None,
    ) -> _TemplateResponse:
        ctx = dict(context or {})
        ctx.setdefault("request", request)
        ctx["url_for"] = _relative_url_for(request)
        lang = resolve_lang(request)
        ctx.setdefault("lang", lang)
        ctx.setdefault("t", lambda key, **kwargs: translate(key, lang, **kwargs))
        ctx.setdefault("language_links", language_links(request, lang))
        ctx.setdefault("asset_url", asset_url)
        response = super().TemplateResponse(
            request,
            name,
            ctx,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )
        if normalize_lang(request.query_params.get(LANG_QUERY_KEY)) == lang:
            # ?lang= bilan kelgan tanlov keyingi sahifalarda ham saqlanadi.
            response.set_cookie(
                LANG_COOKIE_KEY,
                lang,
                max_age=LANG_COOKIE_MAX_AGE,
                httponly=False,
                samesite="lax",
            )
        return response


templates = MBTIJinja2Templates(directory=str(TEMPLATES_DIR))


def render_template_or_none(
    request: Request,
    name: str,
    context: dict[str, Any] | None = None,
    *,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
) -> Response | None:
    """Shablon mavjud bo'lsa render qiladi, aks holda None.

    Chaqiruvchi zaxira javob bera olishi uchun kerak: xato sahifalari va
    placeholder'lar shabloni loyihada hali bo'lmasligi mumkin.
    """
    try:
        return templates.TemplateResponse(
            request,
            name,
            context,
            status_code=status_code,
            headers=headers,
        )
    except TemplateNotFound:
        return None
