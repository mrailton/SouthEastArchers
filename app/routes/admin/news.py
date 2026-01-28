from flask import abort, flash, redirect, render_template, url_for

from app.forms import NewsForm
from app.services import NewsService
from app.utils.decorators import permission_required

from . import bp


@bp.get("/news")
@permission_required("news.read")
def news():
    articles = NewsService.get_all_articles()
    return render_template("admin/news.html", articles=articles)


@bp.get("/news/create")
@permission_required("news.create")
def create_news():
    """Display news creation form"""
    return render_template("admin/create_news.html", form=NewsForm())


@bp.post("/news/create")
@permission_required("news.create")
def create_news_post():
    """Handle news creation form submission"""
    form = NewsForm()

    if form.validate_on_submit():
        article, error = NewsService.create_article(
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data,
            published=form.published.data,
        )

        if error:
            flash(error, "error")
            return render_template("admin/create_news.html", form=form)

        flash("News article created!", "success")
        return redirect(url_for("admin.news"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/create_news.html", form=NewsForm())


@bp.get("/news/<int:news_id>/edit")
@permission_required("news.update")
def edit_news(news_id):
    """Display news edit form"""
    news = NewsService.get_article_by_id(news_id)
    if not news:
        abort(404)

    return render_template("admin/edit_news.html", news=news, form=NewsForm(obj=news))


@bp.post("/news/<int:news_id>/edit")
@permission_required("news.update")
def edit_news_post(news_id):
    """Handle news edit form submission"""
    news = NewsService.get_article_by_id(news_id)
    if not news:
        abort(404)

    form = NewsForm(obj=news)

    if form.validate_on_submit():
        success, error = NewsService.update_article(
            article=news,
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data,
            published=form.published.data,
        )

        if not success:
            flash(error or "An error occurred while updating the article.", "error")
            return render_template("admin/edit_news.html", news=news, form=form)

        flash("News article updated successfully!", "success")
        return redirect(url_for("admin.news"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/edit_news.html", news=news, form=NewsForm(obj=news))
