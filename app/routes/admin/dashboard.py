from fastapi import APIRouter, Request

from app.dependencies import CurrentUser, require_perms
from app.services import admin
from app.templating import render

router = APIRouter(tags=["admin.dashboard"])


@router.get("/dashboard", name="admin.dashboard", dependencies=[require_perms("admin.dashboard.view")])
def dashboard(request: Request, user: CurrentUser):
    result = admin.get_dashboard_stats()
    if not result.success or result.data is None:
        return render(request, "errors/500.html", user=user, status_code=500)
    return render(request, "admin/dashboard.html", result.data, user=user)
