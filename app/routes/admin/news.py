from flask import abort, flash, redirect, render_template, request, url_for

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
    if request.method == "POST":
        NewsService.create_article(
            title=request.form.get("title"),
            summary=request.form.get("summary"),
            content=request.form.get("content"),
            published=request.form.get("published") == "on",
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
        NewsService.update_article(
            article=news,
            title=request.form.get("title"),
            summary=request.form.get("summary"),
            content=request.form.get("content"),
            published=request.form.get("published") == "on",
        )

        flash("News article updated successfully!", "success")
        return redirect(url_for("admin.news"))

    return render_template("admin/edit_news.html", news=news)
