from fastapi import APIRouter, Request

from app.dependencies import OptionalUser
from app.services import events as event_service
from app.services import news as news_service
from app.services import settings
from app.templating import render

router = APIRouter(tags=["public"])


@router.get("/", name="public.index")
async def index(request: Request, user: OptionalUser):
    return render(request, "public/index.html", user=user)


@router.get("/about", name="public.about")
async def about(request: Request, user: OptionalUser):
    return render(request, "public/about.html", user=user)


@router.get("/membership", name="public.membership")
async def membership(request: Request, user: OptionalUser):
    return render(request, "public/membership.html", user=user)


@router.get("/news", name="public.news_list")
async def news_list(request: Request, user: OptionalUser):
    if not settings.get("news_enabled"):
        return render(request, "errors/404.html", user=user, status_code=404)
    articles = news_service.get_published_articles()
    return render(request, "public/news.html", {"news": articles}, user=user)


@router.get("/news/{news_id}", name="public.news_detail")
async def news_detail(news_id: int, request: Request, user: OptionalUser):
    if not settings.get("news_enabled"):
        return render(request, "errors/404.html", user=user, status_code=404)
    article = news_service.get_article_by_id(news_id)
    if not article or not article.published:
        return render(request, "errors/404.html", user=user, status_code=404)
    return render(request, "public/news_detail.html", {"news": article}, user=user)


@router.get("/events", name="public.events")
async def events(request: Request, user: OptionalUser):
    if not settings.get("events_enabled"):
        return render(request, "errors/404.html", user=user, status_code=404)
    upcoming = event_service.get_upcoming_published_events()
    return render(request, "public/events.html", {"events": upcoming}, user=user)
