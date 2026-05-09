from flask import abort, render_template

from app.services import NewsService
from app.services.settings_service import SettingsService


class NewsListController:
    def __call__(self):
        if not SettingsService.get("news_enabled"):
            abort(404)
        news = NewsService.get_published_articles()
        return render_template("public/news.html", news=news)
