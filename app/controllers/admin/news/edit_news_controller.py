from flask import abort, render_template

from app.forms import NewsForm
from app.services import NewsService
from app.utils import permission_required


class EditNewsController:
    def __init__(self):
        super().__init__()
        self.service = NewsService

    @permission_required("news.update")
    def __call__(self, news_id):
        news = self.service.get_article_by_id(news_id)
        if not news:
            abort(404)

        return render_template("admin/edit_news.html", news=news, form=NewsForm(obj=news))
