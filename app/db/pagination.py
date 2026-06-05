from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Query, Session

T = TypeVar("T")


@dataclass
class Pagination:
    items: list
    page: int
    per_page: int
    total: int

    @property
    def pages(self) -> int:
        if self.per_page == 0:
            return 0
        return ceil(self.total / self.per_page)

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def prev_num(self) -> int | None:
        return self.page - 1 if self.has_prev else None

    @property
    def next_num(self) -> int | None:
        return self.page + 1 if self.has_next else None

    def iter_pages(
        self,
        left_edge: int = 2,
        left_current: int = 2,
        right_current: int = 5,
        right_edge: int = 2,
    ):
        last = self.pages
        if last <= 1:
            return
        for page in range(1, min(left_edge, last) + 1):
            yield page
        if self.page - left_current > left_edge + 1:
            yield None
        for page in range(max(self.page - left_current, left_edge + 1), min(self.page + right_current, last + 1)):
            yield page
        if self.page + right_current < last - right_edge:
            yield None
        for page in range(max(last - right_edge + 1, self.page + right_current + 1), last + 1):
            yield page


def paginate(session: Session, stmt: Select[tuple[T]], *, page: int = 1, per_page: int = 20) -> Pagination:
    page = max(page, 1)
    per_page = max(per_page, 1)
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = list(session.scalars(stmt.offset((page - 1) * per_page).limit(per_page)).all())
    return Pagination(items=items, page=page, per_page=per_page, total=total)


def paginate_query(query: Query, *, page: int = 1, per_page: int = 20) -> Pagination:
    page = max(page, 1)
    per_page = max(per_page, 1)
    total = query.order_by(None).count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return Pagination(items=items, page=page, per_page=per_page, total=total)
