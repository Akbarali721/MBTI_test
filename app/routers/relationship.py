"""Juftlik mosligi: ikki xarakter tipini solishtirish.

Natija manzili tiplardan hosil bo'ladi (`/relationship/INFP-ESTJ`), shuning uchun uni
ulashish mumkin va u hech qanday sessiyaga bog'lanmaydi — shaxsiy ma'lumot chiqmaydi.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.dependencies import get_db_session
from app.i18n import resolve_lang
from app.models.enums import PersonalitySessionStatus
from app.personality.session_binding import get_bound_session
from app.repositories.personality_repository import PersonalityRepository
from app.services.compatibility import (
    ALL_TYPES,
    compare_types,
    normalize_type,
    pair_slug,
    parse_pair_slug,
)
from app.templating import templates

router = APIRouter(prefix="/relationship", tags=["relationship"])


def _own_type(request: Request, db: Session) -> str | None:
    """Tugallangan sessiyasi bor tashrifchi uchun o'z tipi oldindan tanlangan bo'ladi."""
    session = get_bound_session(request, db)
    if session is None or session.status != PersonalitySessionStatus.COMPLETED:
        return None
    return normalize_type(session.result_type)


def _render_form(request: Request, *, own_type: str | None, error: str | None = None) -> Response:
    return templates.TemplateResponse(
        request,
        "relationship/index.html",
        {"all_types": ALL_TYPES, "own_type": own_type, "error": error},
        status_code=400 if error else 200,
    )


@router.get("", response_class=HTMLResponse, response_model=None)
def relationship_index(request: Request, db: Session = Depends(get_db_session)) -> Response:
    return _render_form(request, own_type=_own_type(request, db))


@router.post("/compare", response_model=None)
def relationship_compare(
    request: Request,
    db: Session = Depends(get_db_session),
    left_type: str = Form(default=""),
    right_type: str = Form(default=""),
) -> Response:
    left, right = normalize_type(left_type), normalize_type(right_type)
    if left is None or right is None:
        return _render_form(request, own_type=_own_type(request, db), error="invalid_type")
    # POST-redirect-GET: natija manzili ulashiladigan bo'lishi kerak.
    return RedirectResponse(url=f"/relationship/{pair_slug(left, right)}", status_code=303)


@router.get("/{pair}", response_class=HTMLResponse, response_model=None)
def relationship_result(
    request: Request,
    pair: str,
    db: Session = Depends(get_db_session),
) -> Response:
    parsed = parse_pair_slug(pair)
    if parsed is None:
        raise StarletteHTTPException(status_code=404)
    left, right = parsed

    lang = resolve_lang(request)
    repo = PersonalityRepository(db)
    left_content = repo.get_result_content(left, lang)
    right_content = repo.get_result_content(right, lang)

    return templates.TemplateResponse(
        request,
        "relationship/result.html",
        {
            "compatibility": compare_types(left, right),
            "left_title": left_content.title if left_content else left,
            "right_title": right_content.title if right_content else right,
            "own_type": _own_type(request, db),
        },
    )
