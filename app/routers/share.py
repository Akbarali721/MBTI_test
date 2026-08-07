"""Ommaviy, anonim natija sahifasi — ulashish uchun.

Bu yerda sessiya cookie'si talab qilinmaydi va shaxsiy hech narsa ko'rsatilmaydi:
faqat xarakter tipi, uning umumiy tavsifi va o'lchov foizlari. Premium bo'limlar,
to'lov ma'lumotlari va Telegram identifikatorlari bu sahifaga umuman chiqmaydi.
"""

from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.dependencies import get_db_session
from app.i18n import resolve_lang
from app.personality.share_code import find_shared_session, og_image_path
from app.repositories.personality_repository import PersonalityRepository
from app.services.personality_scoring import calculate_personality_result
from app.services.referral_service import REFERRAL_QUERY_KEY
from app.templating import templates

router = APIRouter(prefix="/r", tags=["share"])


@router.get("/{share_code}", response_class=HTMLResponse, response_model=None)
def shared_result(
    request: Request,
    share_code: str,
    db: Session = Depends(get_db_session),
) -> Response:
    session = find_shared_session(db, share_code)
    if session is None or not session.result_type:
        raise StarletteHTTPException(status_code=404)

    lang = resolve_lang(request)
    repo = PersonalityRepository(db)
    content = repo.get_result_content(session.result_type, lang)
    if content is None:
        raise StarletteHTTPException(status_code=404)

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

    return templates.TemplateResponse(
        request,
        "share/result.html",
        {
            "result_type": session.result_type,
            "content": content,
            "result": result,
            "strengths": repo.parse_json_list(content.free_strengths),
            "og_image_url": f"{str(request.base_url).rstrip('/')}{og_image_path(session.result_type)}",
            # Ulashish havolasining O'ZI referal havolasi: allaqachon tarqatilgan
            # havolalar ham egasiga mukofot keltira boshlaydi.
            "start_url": _start_url(session.share_code),
        },
    )


def _start_url(share_code: str | None) -> str:
    if not share_code:
        return "/personality"
    return f"/personality?{REFERRAL_QUERY_KEY}={quote(share_code, safe='')}"
