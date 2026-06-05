from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from app.services import health as health_service

router = APIRouter(tags=["health"])


@router.get("/health", name="health", response_model=None)
async def health() -> Response | dict[str, str]:
    if health_service.check_database():
        return {"status": "ok"}
    return JSONResponse({"status": "error"}, status_code=500)
