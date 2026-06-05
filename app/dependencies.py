from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Request
from starlette.datastructures import UploadFile

from app.exceptions import AlreadyAuthenticated, CsrfError, LoginRequired
from app.models.user import User
from app.utils.formdata import MultiDict, request_form_data


async def get_session_user(request: Request) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    from app.services import users

    return users.get_session_user_by_id(int(user_id))


async def require_auth(user: User | None = Depends(get_session_user)) -> User:
    if user is None:
        raise LoginRequired()
    return user


async def require_guest(user: User | None = Depends(get_session_user)) -> None:
    if user is not None:
        raise AlreadyAuthenticated()


CurrentUser = Annotated[User, Depends(require_auth)]
OptionalUser = Annotated[User | None, Depends(get_session_user)]


def require_perms(*permission_names: str):
    async def _dependency(user: CurrentUser) -> User:
        from app.policies import require_all_permissions

        require_all_permissions(user, *permission_names)
        return user

    return Depends(_dependency)


def get_csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def verify_csrf(request: Request, token: str | UploadFile | None) -> None:
    if token is not None and not isinstance(token, str):
        token = None
    session_token = request.session.get("csrf_token")
    if not session_token or not token or not secrets.compare_digest(session_token, token):
        raise CsrfError()


async def read_form_data(request: Request) -> MultiDict:
    return await request_form_data(request)


async def verify_csrf_form(request: Request, form_data: MultiDict = Depends(read_form_data)) -> MultiDict:
    verify_csrf(request, form_data.get("csrf_token"))
    return form_data


CsrfFormData = Annotated[MultiDict, Depends(verify_csrf_form)]
