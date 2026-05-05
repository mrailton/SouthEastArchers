from flask import abort, render_template

from app.services import NewsService
from app.services.settings_service import SettingsService


class NewsDetailController:
    def __init__(self):
        super().__init__()
        self.news_service = NewsService
        self.settings_service = SettingsService

    def __call__(self, news_id):
        if not self.settings_service.get("news_enabled"):
            abort(404)
        news = self.news_service.get_article_by_id(news_id)
        if not news or not news.published:
            abort(404)
        return render_template("public/news_detail.html", news=news)
