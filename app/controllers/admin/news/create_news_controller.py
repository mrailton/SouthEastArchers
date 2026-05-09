from flask import render_template

from app.forms import NewsForm
from app.utils import permission_required


class CreateNewsController:
    @permission_required("news.create")
    def __call__(self):
        return render_template("admin/create_news.html", form=NewsForm())
