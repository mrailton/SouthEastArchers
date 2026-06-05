from __future__ import annotations

from collections.abc import Mapping


class MultiDict:
    """Minimal multidict for WTForms (replaces Werkzeug in form parsing)."""

    def __init__(self) -> None:
        self._store: dict[str, list[str]] = {}

    def add(self, key: str, value: str) -> None:
        self._store.setdefault(key, []).append(value)

    def get(self, key: str, default: str | None = None) -> str | None:
        values = self._store.get(key)
        if not values:
            return default
        return values[0]

    def getlist(self, key: str) -> list[str]:
        return list(self._store.get(key, []))

    def __contains__(self, key: object) -> bool:
        return key in self._store

    def keys(self):
        return self._store.keys()

    def items(self):
        for key, values in self._store.items():
            for value in values:
                yield key, value


async def request_form_data(request) -> MultiDict:
    form = await request.form()
    data = MultiDict()
    for key, value in form.multi_items():
        data.add(key, str(value))
    return data


def parse_visitors_from_form(form_data: MultiDict | Mapping[str, object]) -> list[dict]:
    if isinstance(form_data, MultiDict):
        names = form_data.getlist("visitor_name")
        clubs = form_data.getlist("visitor_club")
        affiliations = form_data.getlist("visitor_affiliation")
        payment_methods = form_data.getlist("visitor_payment_method")
    else:
        return []

    visitors = []
    for i in range(len(names)):
        name = names[i].strip() if i < len(names) else ""
        club = clubs[i].strip() if i < len(clubs) else ""
        affiliation = affiliations[i] if i < len(affiliations) else ""
        payment_method = payment_methods[i] if i < len(payment_methods) else ""
        if name and club and affiliation and payment_method:
            visitors.append(
                {
                    "name": name,
                    "club": club,
                    "affiliation": affiliation,
                    "payment_method": payment_method,
                }
            )
    return visitors
