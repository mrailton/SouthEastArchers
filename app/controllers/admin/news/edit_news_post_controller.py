from flask import abort, flash, redirect, render_template, url_for

from app.forms import NewsForm
from app.services import NewsService
from app.utils import permission_required


class EditNewsPostController:
    def __init__(self):
        super().__init__()
        self.service = NewsService

    @permission_required("news.update")
    def __call__(self, news_id):
        news = self.service.get_article_by_id(news_id)
        if not news:
            abort(404)

        form = NewsForm(obj=news)

        if form.validate_on_submit():
            result = self.service.update_article(
                article=news,
                title=form.title.data,
                summary=form.summary.data,
                content=form.content.data,
                published=form.published.data,
            )

            if not result.success:
                flash(result.message or "An error occurred while updating the article.", "error")
                return render_template("admin/edit_news.html", news=news, form=form)

            flash("News article updated successfully!", "success")
            return redirect(url_for("admin.news"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("admin/edit_news.html", news=news, form=NewsForm(obj=news))
