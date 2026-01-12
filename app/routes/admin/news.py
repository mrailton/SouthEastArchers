from flask import abort, flash, redirect, render_template, request, url_for

from app.schemas import NewsSchema
from app.services import NewsService
from app.utils.pydantic_helpers import validate_request

from . import admin_required, bp


@bp.route("/news")
@admin_required
def news():
    articles = NewsService.get_all_articles()
    return render_template("admin/news.html", articles=articles)


@bp.route("/news/create", methods=["GET", "POST"])
@admin_required
def create_news():
    if request.method == "POST":
        validated, errors = validate_request(NewsSchema, request)

        if errors or validated is None:
            for field, error in (errors or {}).items():
                flash(error, "error")
            return render_template("admin/create_news.html")

        NewsService.create_article(
            title=validated.title,
            summary=validated.summary,
            content=validated.content,
            published=validated.published,
        )

        flash("News article created!", "success")
        return redirect(url_for("admin.news"))

    return render_template("admin/create_news.html")


@bp.route("/news/<int:news_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_news(news_id):
    news = NewsService.get_article_by_id(news_id)
    if not news:
        abort(404)

    if request.method == "POST":
        validated, errors = validate_request(NewsSchema, request)

        if errors or validated is None:
            for field, error in (errors or {}).items():
                flash(error, "error")
            return render_template("admin/edit_news.html", news=news)

        NewsService.update_article(
            article=news,
            title=validated.title,
            summary=validated.summary,
            content=validated.content,
            published=validated.published,
        )

        flash("News article updated successfully!", "success")
        return redirect(url_for("admin.news"))

    return render_template("admin/edit_news.html", news=news)
