from fastapi import APIRouter, Request

from app.core.settings import get_setting
from app.dependencies import DbSession, OptionalUser
from app.services import events as event_service
from app.services import news as news_service
from app.templating import render

router = APIRouter(tags=["public"])


@router.get("/", name="public.index")
async def index(request: Request, db: DbSession, user: OptionalUser):
    return render(request, "public/index.html", user=user, db=db)


@router.get("/about", name="public.about")
async def about(request: Request, db: DbSession, user: OptionalUser):
    return render(request, "public/about.html", user=user, db=db)


@router.get("/membership", name="public.membership")
async def membership(request: Request, db: DbSession, user: OptionalUser):
    return render(request, "public/membership.html", user=user, db=db)


@router.get("/news", name="public.news_list")
async def news_list(request: Request, db: DbSession, user: OptionalUser):
    if not get_setting(db, "news_enabled"):
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    articles = news_service.get_published_articles(db)
    return render(request, "public/news.html", {"news": articles}, user=user, db=db)


@router.get("/news/{news_id}", name="public.news_detail")
async def news_detail(news_id: int, request: Request, db: DbSession, user: OptionalUser):
    if not get_setting(db, "news_enabled"):
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    article = news_service.get_article_by_id(news_id, db=db)
    if not article or not article.published:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    return render(request, "public/news_detail.html", {"news": article}, user=user, db=db)


@router.get("/events", name="public.events")
async def events(request: Request, db: DbSession, user: OptionalUser):
    if not get_setting(db, "events_enabled"):
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    upcoming = event_service.get_upcoming_published_events(db)
    return render(request, "public/events.html", {"events": upcoming}, user=user, db=db)
