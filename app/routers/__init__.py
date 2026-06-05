from fastapi import APIRouter

from app.routers import admin, auth, health, member, payment, public

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(public.router)
api_router.include_router(auth.router)
api_router.include_router(member.router)
api_router.include_router(payment.router)
api_router.include_router(admin.router)
