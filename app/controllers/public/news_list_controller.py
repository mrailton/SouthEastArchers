from flask import abort, render_template

from app.services import NewsService
from app.services.settings_service import SettingsService


class NewsListController:
    def __init__(self):
        super().__init__()
        self.news_service = NewsService
        self.settings_service = SettingsService

    def __call__(self):
        if not self.settings_service.get("news_enabled"):
            abort(404)
        news = self.news_service.get_published_articles()
        return render_template("public/news.html", news=news)
