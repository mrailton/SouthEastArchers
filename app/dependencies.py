from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User


class LoginRequired(Exception):
    pass


DbSession = Annotated[Session, Depends(get_db)]


async def get_session_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    from app.repositories import UserRepository

    return UserRepository.get_by_id(int(user_id))


async def require_auth(user: User | None = Depends(get_session_user)) -> User:
    if user is None:
        raise LoginRequired()
    return user


async def require_guest(user: User | None = Depends(get_session_user)) -> None:
    if user is not None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/member/dashboard"})


CurrentUser = Annotated[User, Depends(require_auth)]
OptionalUser = Annotated[User | None, Depends(get_session_user)]


def get_csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def verify_csrf(request: Request, token: str | None) -> None:
    session_token = request.session.get("csrf_token")
    if not session_token or not token or token != session_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token mismatch")
