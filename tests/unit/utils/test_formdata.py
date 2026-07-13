from app.utils.formdata import MultiDict, parse_visitors_from_form


def test_multidict_getlist_and_contains():
    data = MultiDict()
    data.add("roles", "1")
    data.add("roles", "2")
    assert "roles" in data
    assert data.getlist("roles") == ["1", "2"]
    assert data.get("missing") is None


def test_multidict_items():
    data = MultiDict()
    data.add("a", "1")
    data.add("b", "2")
    assert list(data.items()) == [("a", "1"), ("b", "2")]


def test_parse_visitors_from_form_complete_rows():
    data = MultiDict()
    data.add("visitor_name", "Alice")
    data.add("visitor_club", "Other Club")
    data.add("visitor_affiliation", "AI")
    data.add("visitor_payment_method", "cash")
    visitors = parse_visitors_from_form(data)
    assert visitors == [
        {
            "name": "Alice",
            "club": "Other Club",
            "affiliation": "AI",
            "payment_method": "cash",
        }
    ]


def test_parse_visitors_from_form_skips_incomplete_rows():
    data = MultiDict()
    data.add("visitor_name", "Bob")
    data.add("visitor_club", "")
    assert parse_visitors_from_form(data) == []


def test_parse_visitors_from_plain_dict_returns_empty():
    assert parse_visitors_from_form({"visitor_name": "X"}) == []
