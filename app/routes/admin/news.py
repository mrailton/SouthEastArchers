from flask import flash, redirect, render_template, request, url_for

from app import db
from app.models import News
from app.utils.datetime_utils import utc_now

from . import admin_required, bp


@bp.route("/news")
@admin_required
def news():
    articles = News.query.order_by(News.created_at.desc()).all()
    return render_template("admin/news.html", articles=articles)


@bp.route("/news/create", methods=["GET", "POST"])
@admin_required
def create_news():
    if request.method == "POST":
        article = News(
            title=request.form.get("title"),
            summary=request.form.get("summary"),
            content=request.form.get("content"),
            published=request.form.get("published") == "on",
        )

        if article.published:
            article.published_at = utc_now()

        db.session.add(article)
        db.session.commit()

        flash("News article created!", "success")
        return redirect(url_for("admin.news"))

    return render_template("admin/create_news.html")


@bp.route("/news/<int:news_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_news(news_id):
    news = db.session.get(News, news_id)
    if not news:
        from flask import abort

        abort(404)

    if request.method == "POST":
        news.title = request.form.get("title")
        news.summary = request.form.get("summary")
        news.content = request.form.get("content")
        news.published = request.form.get("published") == "on"

        if news.published and not news.published_at:
            news.published_at = utc_now()

        db.session.commit()
        flash("News article updated successfully!", "success")
        return redirect(url_for("admin.news"))

    return render_template("admin/edit_news.html", news=news)
