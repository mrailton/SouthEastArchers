from app.db.pagination import Pagination


def test_pagination_pages_zero_per_page():
    page = Pagination(items=[], page=1, per_page=0, total=10)
    assert page.pages == 0


def test_pagination_prev_next_nums():
    page = Pagination(items=[1], page=2, per_page=1, total=3)
    assert page.has_prev is True
    assert page.has_next is True
    assert page.prev_num == 1
    assert page.next_num == 3


def test_pagination_prev_next_at_edges():
    first = Pagination(items=[1], page=1, per_page=1, total=1)
    assert first.prev_num is None
    assert first.next_num is None


def test_iter_pages_single_page():
    page = Pagination(items=[1], page=1, per_page=10, total=1)
    assert list(page.iter_pages()) == []


def test_iter_pages_many_pages_with_ellipsis():
    page = Pagination(items=[], page=10, per_page=1, total=20)
    pages = list(page.iter_pages(left_edge=1, left_current=1, right_current=1, right_edge=1))
    assert 1 in pages
    assert 20 in pages
    assert None in pages


def test_paginate_with_session(app, admin_user):
    from sqlalchemy import select

    from app import db
    from app.db.pagination import paginate
    from app.models import User

    stmt = select(User).order_by(User.id)
    page = paginate(db.session, stmt, page=1, per_page=5)
    assert page.per_page == 5
    assert page.total >= 1
    assert admin_user.id in {user.id for user in page.items}
