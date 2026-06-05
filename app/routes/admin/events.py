from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, require_perms, verify_csrf
from app.forms.admin_forms import EventForm
from app.routes.admin._helpers import flash_form_errors
from app.services.event_service import EventService
from app.templating import flash, render
from app.utils.formdata import request_form_data

router = APIRouter(tags=["admin.events"])


@router.get("/events", name="admin.events", dependencies=[require_perms("events.read")])
async def events_index(request: Request, db: DbSession, user: CurrentUser):
    events = EventService.get_all_events()
    return render(request, "admin/events.html", {"events": events}, user=user, db=db)


@router.get("/events/create", name="admin.create_event", dependencies=[require_perms("events.create")])
async def create_event_page(request: Request, db: DbSession, user: CurrentUser):
    form = EventForm()
    return render(request, "admin/create_event.html", {"form": form}, user=user, db=db)


@router.post("/events/create", name="admin.create_event_post", dependencies=[require_perms("events.create")])
async def create_event_store(request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    form = EventForm(formdata=form_data)
    if form.validate():
        result = EventService.create_event(
            title=form.title.data,
            start_date=form.start_date.data,
            description=form.description.data,
            location=form.location.data,
            published=form.published.data,
        )
        if result.success:
            flash(request, "success", "Event created!")
            return RedirectResponse(url="/admin/events", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, form)
    return render(request, "admin/create_event.html", {"form": form}, user=user, db=db, status_code=422)


@router.get("/events/{event_id}/edit", name="admin.edit_event", dependencies=[require_perms("events.update")])
async def edit_event_page(event_id: int, request: Request, db: DbSession, user: CurrentUser):
    event = EventService.get_event_by_id(event_id)
    if not event:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = EventForm(obj=event)
    return render(request, "admin/edit_event.html", {"form": form, "event": event}, user=user, db=db)


@router.post("/events/{event_id}/edit", name="admin.edit_event_post", dependencies=[require_perms("events.update")])
async def edit_event_store(event_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    event = EventService.get_event_by_id(event_id)
    if not event:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = EventForm(formdata=form_data, obj=event)
    if form.validate():
        result = EventService.update_event(
            event,
            title=form.title.data,
            start_date=form.start_date.data,
            description=form.description.data,
            location=form.location.data,
            published=form.published.data,
        )
        if result.success:
            flash(request, "success", "Event updated!")
            return RedirectResponse(url="/admin/events", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, form)
    return render(request, "admin/edit_event.html", {"form": form, "event": event}, user=user, db=db, status_code=422)
