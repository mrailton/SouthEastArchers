from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.dependencies import DbSession

router = APIRouter(tags=["health"])


@router.get("/health", name="health", response_model=None)
async def health(db: DbSession) -> Response | dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        return JSONResponse({"status": "error"}, status_code=500)
