from flask import abort, flash, redirect, render_template, url_for

from app.forms import NewsForm
from app.services import NewsService

from . import admin_required, bp


@bp.route("/news")
@admin_required
def news():
    articles = NewsService.get_all_articles()
    return render_template("admin/news.html", articles=articles)


@bp.route("/news/create", methods=["GET", "POST"])
@admin_required
def create_news():
    form = NewsForm()

    if form.validate_on_submit():
        NewsService.create_article(
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data,
            published=form.published.data,
        )

        flash("News article created!", "success")
        return redirect(url_for("admin.news"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/create_news.html", form=form)


@bp.route("/news/<int:news_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_news(news_id):
    news = NewsService.get_article_by_id(news_id)
    if not news:
        abort(404)

    form = NewsForm(obj=news)

    if form.validate_on_submit():
        NewsService.update_article(
            article=news,
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data,
            published=form.published.data,
        )

        flash("News article updated successfully!", "success")
        return redirect(url_for("admin.news"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/edit_news.html", news=news, form=form)
