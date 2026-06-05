from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.routes import admin, auth, health, member, payment, public

api_router = APIRouter(dependencies=[Depends(get_db)])
api_router.include_router(health.router)
api_router.include_router(public.router)
api_router.include_router(auth.router)
api_router.include_router(member.router)
api_router.include_router(payment.router)
api_router.include_router(admin.router)
