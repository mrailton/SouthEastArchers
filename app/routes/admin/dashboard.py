from fastapi import APIRouter, Request

from app.dependencies import CurrentUser, DbSession, require_perms
from app.services.admin_service import AdminService
from app.templating import render

router = APIRouter(tags=["admin.dashboard"])


@router.get("/dashboard", name="admin.dashboard", dependencies=[require_perms("admin.dashboard.view")])
async def dashboard(request: Request, db: DbSession, user: CurrentUser):
    result = AdminService.get_dashboard_stats()
    assert result.data is not None
    return render(request, "admin/dashboard.html", result.data, user=user, db=db)
