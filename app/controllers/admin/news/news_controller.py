from flask import render_template

from app.services import NewsService
from app.utils import permission_required


class NewsController:
    def __init__(self):
        super().__init__()
        self.service = NewsService

    @permission_required("news.read")
    def __call__(self):
        articles = self.service.get_all_articles()
        return render_template("admin/news.html", articles=articles)
