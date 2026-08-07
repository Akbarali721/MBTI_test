from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from starlette.responses import Response

from app.templating import render_template_or_none

router = APIRouter(prefix="/relationship", tags=["relationship"])

# Shablon hali qo'shilmagan bo'lsa ham sahifa ochilishi kerak.
_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Munosabat testi — MBTI</title>
</head>
<body>
  <h1>Munosabat testi</h1>
  <p>Bu bo‘lim tayyorlanmoqda. Xarakter testi alohida mahsulot sifatida ishlaydi.</p>
  <p><a href="/personality">Xarakter testiga o‘tish</a></p>
</body>
</html>"""


@router.get("", response_class=HTMLResponse, response_model=None)
def relationship_placeholder(request: Request) -> Response:
    rendered = render_template_or_none(request, "relationship/placeholder.html")
    if rendered is not None:
        return rendered
    return HTMLResponse(_FALLBACK_HTML)
