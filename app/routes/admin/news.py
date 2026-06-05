from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, require_perms, verify_csrf
from app.forms.admin_forms import NewsForm
from app.routes.admin._helpers import flash_form_errors
from app.services.news_service import NewsService
from app.templating import flash, render
from app.utils.formdata import request_form_data

router = APIRouter(tags=["admin.news"])


@router.get("/news", name="admin.news", dependencies=[require_perms("news.read")])
async def news_index(request: Request, db: DbSession, user: CurrentUser):
    articles = NewsService.get_all_articles()
    return render(request, "admin/news.html", {"news": articles}, user=user, db=db)


@router.get("/news/create", name="admin.create_news", dependencies=[require_perms("news.create")])
async def create_news_page(request: Request, db: DbSession, user: CurrentUser):
    form = NewsForm()
    return render(request, "admin/create_news.html", {"form": form}, user=user, db=db)


@router.post("/news/create", name="admin.create_news_post", dependencies=[require_perms("news.create")])
async def create_news_store(request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    form = NewsForm(formdata=form_data)
    if form.validate():
        result = NewsService.create_article(
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data,
            published=form.published.data,
        )
        if result.success:
            flash(request, "success", "News article created!")
            return RedirectResponse(url="/admin/news", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, form)
    return render(request, "admin/create_news.html", {"form": form}, user=user, db=db, status_code=422)


@router.get("/news/{news_id}/edit", name="admin.edit_news", dependencies=[require_perms("news.update")])
async def edit_news_page(news_id: int, request: Request, db: DbSession, user: CurrentUser):
    article = NewsService.get_article_by_id(news_id)
    if not article:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = NewsForm(obj=article)
    return render(request, "admin/edit_news.html", {"form": form, "news": article}, user=user, db=db)


@router.post("/news/{news_id}/edit", name="admin.edit_news_post", dependencies=[require_perms("news.update")])
async def edit_news_store(news_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    article = NewsService.get_article_by_id(news_id)
    if not article:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = NewsForm(formdata=form_data, obj=article)
    if form.validate():
        result = NewsService.update_article(
            article,
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data,
            published=form.published.data,
        )
        if result.success:
            flash(request, "success", "News article updated!")
            return RedirectResponse(url="/admin/news", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, form)
    return render(request, "admin/edit_news.html", {"form": form, "news": article}, user=user, db=db, status_code=422)
