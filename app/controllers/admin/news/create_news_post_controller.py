from flask import flash, redirect, render_template, url_for

from app.forms import NewsForm
from app.services import NewsService
from app.utils import permission_required


class CreateNewsPostController:
    def __init__(self):
        super().__init__()
        self.service = NewsService

    @permission_required("news.create")
    def __call__(self):
        form = NewsForm()

        if form.validate_on_submit():
            result = self.service.create_article(
                title=form.title.data,
                summary=form.summary.data,
                content=form.content.data,
                published=form.published.data,
            )

            if not result.success:
                flash(result.message, "error")
                return render_template("admin/create_news.html", form=form)

            flash("News article created!", "success")
            return redirect(url_for("admin.news"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("admin/create_news.html", form=NewsForm())
