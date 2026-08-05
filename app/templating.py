from collections.abc import Mapping
from typing import Any

from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import Response

from app.paths import TEMPLATES_DIR


def _relative_url_for(request: Request):
    def url_for(name: str, /, **path_params: Any) -> str:
        url = request.url_for(name, **path_params)
        if url.query:
            return f"{url.path}?{url.query}"
        return url.path

    return url_for


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
    ) -> Response:
        ctx = dict(context or {})
        ctx.setdefault("request", request)
        ctx["url_for"] = _relative_url_for(request)
        return super().TemplateResponse(
            request,
            name,
            ctx,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )


templates = MBTIJinja2Templates(directory=str(TEMPLATES_DIR))
