from fastapi import APIRouter

from app.routes.admin import dashboard, events, finance, members, news, payments, roles, settings, shoots

router = APIRouter(prefix="/admin")
router.include_router(dashboard.router)
router.include_router(members.router)
router.include_router(payments.router)
router.include_router(shoots.router)
router.include_router(events.router)
router.include_router(news.router)
router.include_router(finance.router)
router.include_router(settings.router)
router.include_router(roles.router)
