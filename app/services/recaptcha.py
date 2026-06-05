import httpx

from app.core.config import get_settings


async def verify_recaptcha(token: str) -> bool:
    settings = get_settings()
    if settings.is_testing:
        return True
    if not settings.recaptcha_private_key:
        return settings.app_debug
    if not token:
        return False
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": settings.recaptcha_private_key, "response": token},
            timeout=10,
        )
        data = response.json()
    return bool(data.get("success"))
