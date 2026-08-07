"""Jamoa / HR rejimi.

Ikki kod ajratilgan: invite_code xodimlarga tarqaladi, manage_code faqat egasida
qoladi. Panelga faqat manage_code bilan kiriladi, ya'ni taklif havolasini olgan
xodim boshqalarning natijasini ko'ra olmaydi.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.dependencies import get_db_session
from app.models.enums import PersonalitySessionStatus
from app.personality.session_binding import get_bound_session
from app.services.team_service import (
    MAX_MEMBERS,
    add_member,
    composition,
    create_team,
    team_by_invite,
    team_by_manage,
)
from app.templating import templates

router = APIRouter(prefix="/team", tags=["team"])


def _absolute(request: Request, path: str) -> str:
    return f"{str(request.base_url).rstrip('/')}{path}"


@router.get("", response_class=HTMLResponse, response_model=None)
def team_index(request: Request) -> Response:
    return templates.TemplateResponse(request, "team/index.html", {"error": None})


@router.post("/create", response_model=None)
def team_create(
    request: Request,
    db: Session = Depends(get_db_session),
    name: str = Form(default=""),
) -> Response:
    try:
        team = create_team(db, name)
    except ValueError:
        return templates.TemplateResponse(
            request, "team/index.html", {"error": "empty_name"}, status_code=400
        )
    return RedirectResponse(url=f"/team/manage/{team.manage_code}", status_code=303)


@router.get("/manage/{manage_code}", response_class=HTMLResponse, response_model=None)
def team_dashboard(
    request: Request,
    manage_code: str,
    db: Session = Depends(get_db_session),
) -> Response:
    team = team_by_manage(db, manage_code)
    if team is None:
        raise StarletteHTTPException(status_code=404)
    return templates.TemplateResponse(
        request,
        "team/dashboard.html",
        {
            "team": team,
            "composition": composition(db, team),
            "invite_url": _absolute(request, f"/team/join/{team.invite_code}"),
            "max_members": MAX_MEMBERS,
        },
    )


@router.get("/join/{invite_code}", response_class=HTMLResponse, response_model=None)
def team_join_form(
    request: Request,
    invite_code: str,
    db: Session = Depends(get_db_session),
) -> Response:
    team = team_by_invite(db, invite_code)
    if team is None:
        raise StarletteHTTPException(status_code=404)

    session = get_bound_session(request, db)
    completed = session if session and session.status == PersonalitySessionStatus.COMPLETED else None
    return templates.TemplateResponse(
        request,
        "team/join.html",
        {
            "team": team,
            "invite_code": invite_code,
            "has_result": completed is not None,
            "result_type": completed.result_type if completed else None,
            "error": None,
        },
    )


@router.post("/join/{invite_code}", response_model=None)
def team_join(
    request: Request,
    invite_code: str,
    db: Session = Depends(get_db_session),
    display_name: str = Form(default=""),
) -> Response:
    team = team_by_invite(db, invite_code)
    if team is None:
        raise StarletteHTTPException(status_code=404)

    session = get_bound_session(request, db)
    if session is None or session.status != PersonalitySessionStatus.COMPLETED:
        # Testni tugatmagan odam jamoaga qo'shila olmaydi — panelda bo'sh qator paydo bo'lmasin.
        return RedirectResponse(url="/personality", status_code=303)

    if add_member(db, team, session, display_name) is None:
        return templates.TemplateResponse(
            request,
            "team/join.html",
            {
                "team": team,
                "invite_code": invite_code,
                "has_result": True,
                "result_type": session.result_type,
                "error": "team_full",
            },
            status_code=400,
        )
    return RedirectResponse(url=f"/team/joined/{invite_code}", status_code=303)


@router.get("/joined/{invite_code}", response_class=HTMLResponse, response_model=None)
def team_joined(
    request: Request,
    invite_code: str,
    db: Session = Depends(get_db_session),
) -> Response:
    team = team_by_invite(db, invite_code)
    if team is None:
        raise StarletteHTTPException(status_code=404)
    return templates.TemplateResponse(request, "team/joined.html", {"team": team})
