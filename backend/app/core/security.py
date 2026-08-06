import jwt
from fastapi import Depends, HTTPException, Request

from app.core.config import settings


def get_current_user_id(request: Request) -> str:
    """Возвращает user_id (UUID из Supabase auth.users).

    В dev-режиме без настроенного Supabase можно подставить пользователя
    заголовком X-Debug-User — чтобы избранное и профиль работали локально.
    """
    if settings.env == "dev" and not settings.supabase_jwt_secret:
        debug_user = request.headers.get("X-Debug-User")
        if debug_user:
            return debug_user
        raise HTTPException(401, "Auth не настроен: задай SUPABASE_JWT_SECRET или заголовок X-Debug-User")

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Нужен заголовок Authorization: Bearer <jwt>")
    token = auth.removeprefix("Bearer ")
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"Невалидный токен: {e}") from e
    return payload["sub"]


def require_admin_key(request: Request) -> None:
    if request.headers.get("X-Admin-Key") != settings.admin_api_key:
        raise HTTPException(403, "Неверный X-Admin-Key")


CurrentUser = Depends(get_current_user_id)
