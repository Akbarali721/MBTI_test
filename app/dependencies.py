from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db


def require_admin(request: Request) -> None:
    if request.session.get("admin_authenticated") is not True:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"},
        )


def verify_admin_credentials(username: str, password: str) -> bool:
    return username == settings.admin_username and password == settings.admin_password
