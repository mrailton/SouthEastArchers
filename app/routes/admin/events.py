from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, require_perms, verify_csrf
from app.routes.admin._helpers import flash_form_errors
from app.schemas.admin_forms import EventForm
from app.schemas.form_helpers import parse_form
from app.services import events
from app.templating import flash, render
from app.utils.formdata import request_form_data

router = APIRouter(tags=["admin.events"])


@router.get("/events", name="admin.events", dependencies=[require_perms("events.read")])
async def events_index(request: Request, db: DbSession, user: CurrentUser):
    event_list = events.get_all_events()
    return render(request, "admin/events.html", {"events": event_list}, user=user)


@router.get("/events/create", name="admin.create_event", dependencies=[require_perms("events.create")])
async def create_event_page(request: Request, db: DbSession, user: CurrentUser):
    return render(request, "admin/create_event.html", user=user)


@router.post("/events/create", name="admin.create_event_post", dependencies=[require_perms("events.create")])
async def create_event_store(request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    parsed, errors, _values = parse_form(EventForm, form_data)
    if parsed:
        result = events.create_event(
            title=parsed.title,
            start_date=parsed.start_date,
            description=parsed.description,
            location=parsed.location,
            published=parsed.published,
        )
        if result.success:
            flash(request, "success", "Event created!")
            return RedirectResponse(url="/admin/events", status_code=303)
        flash(request, "error", result.message)
    else:
        flash_form_errors(request, errors)
    return render(request, "admin/create_event.html", user=user, status_code=422)


@router.get("/events/{event_id}/edit", name="admin.edit_event", dependencies=[require_perms("events.update")])
async def edit_event_page(event_id: int, request: Request, db: DbSession, user: CurrentUser):
    event = events.get_event_by_id(event_id)
    if not event:
        return render(request, "errors/404.html", user=user, status_code=404)
    return render(request, "admin/edit_event.html", {"event": event}, user=user)


@router.post("/events/{event_id}/edit", name="admin.edit_event_post", dependencies=[require_perms("events.update")])
async def edit_event_store(event_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    event = events.get_event_by_id(event_id)
    if not event:
        return render(request, "errors/404.html", user=user, status_code=404)
    parsed, errors, _values = parse_form(EventForm, form_data)
    if parsed:
        result = events.update_event(
            event,
            title=parsed.title,
            start_date=parsed.start_date,
            description=parsed.description,
            location=parsed.location,
            published=parsed.published,
        )
        if result.success:
            flash(request, "success", "Event updated!")
            return RedirectResponse(url="/admin/events", status_code=303)
        flash(request, "error", result.message)
    else:
        flash_form_errors(request, errors)
    return render(request, "admin/edit_event.html", {"event": event}, user=user, status_code=422)
