from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CsrfFormData, CurrentUser, require_perms
from app.routes.admin._helpers import flash_form_errors
from app.schemas.admin_forms import NewsForm
from app.schemas.form_helpers import parse_form
from app.services import news
from app.templating import flash, render

router = APIRouter(tags=["admin.news"])


@router.get("/news", name="admin.news", dependencies=[require_perms("news.read")])
def news_index(request: Request, user: CurrentUser):
    articles = news.get_all_articles()
    return render(request, "admin/news.html", {"news": articles}, user=user)


@router.get("/news/create", name="admin.create_news", dependencies=[require_perms("news.create")])
def create_news_page(request: Request, user: CurrentUser):
    return render(request, "admin/create_news.html", user=user)


@router.post("/news/create", name="admin.create_news_post", dependencies=[require_perms("news.create")])
def create_news_store(request: Request, user: CurrentUser, form_data: CsrfFormData):
    parsed, errors, _values = parse_form(NewsForm, form_data)
    if parsed:
        result = news.create_article(
            title=parsed.title,
            summary=parsed.summary,
            content=parsed.content,
            published=parsed.published,
        )
        if result.success:
            flash(request, "success", "News article created!")
            return RedirectResponse(url="/admin/news", status_code=303)
        flash(request, "error", result.message)
    else:
        flash_form_errors(request, errors)
    return render(request, "admin/create_news.html", user=user, status_code=422)


@router.get("/news/{news_id}/edit", name="admin.edit_news", dependencies=[require_perms("news.update")])
def edit_news_page(news_id: int, request: Request, user: CurrentUser):
    article = news.get_article_by_id(news_id)
    if not article:
        return render(request, "errors/404.html", user=user, status_code=404)
    return render(request, "admin/edit_news.html", {"news": article}, user=user)


@router.post("/news/{news_id}/edit", name="admin.edit_news_post", dependencies=[require_perms("news.update")])
def edit_news_store(news_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    article = news.get_article_by_id(news_id)
    if not article:
        return render(request, "errors/404.html", user=user, status_code=404)
    parsed, errors, _values = parse_form(NewsForm, form_data)
    if parsed:
        result = news.update_article(
            article,
            title=parsed.title,
            summary=parsed.summary,
            content=parsed.content,
            published=parsed.published,
        )
        if result.success:
            flash(request, "success", "News article updated!")
            return RedirectResponse(url="/admin/news", status_code=303)
        flash(request, "error", result.message)
    else:
        flash_form_errors(request, errors)
    return render(request, "admin/edit_news.html", {"news": article}, user=user, status_code=422)
