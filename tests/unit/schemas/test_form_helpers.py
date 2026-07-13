from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ValidationError

from app.schemas.form_helpers import (
    FormView,
    coerce_bool,
    coerce_datetime,
    coerce_int_list,
    coerce_optional_date,
    coerce_optional_decimal,
    multidict_to_dict,
    parse_form,
    pydantic_errors,
)
from app.utils.formdata import MultiDict


class SampleForm(BaseModel):
    name: str


def test_multidict_to_dict_multi_value():
    data = MultiDict()
    data.add("roles", "1")
    data.add("roles", "2")
    assert multidict_to_dict(data)["roles"] == ["1", "2"]


def test_parse_form_success_and_failure():
    raw = MultiDict()
    raw.add("name", "Alice")
    parsed, errors, values = parse_form(SampleForm, raw)
    assert parsed is not None
    assert parsed.name == "Alice"
    assert errors == {}

    bad = MultiDict()
    parsed, errors, _ = parse_form(SampleForm, bad)
    assert parsed is None
    assert "name" in errors


def test_pydantic_errors_format():
    try:
        SampleForm.model_validate({})
    except ValidationError as exc:
        errors = pydantic_errors(exc)
    assert "name" in errors


def test_form_view_field_access_and_errors_dict():
    form = FormView(values={"name": "Alice"}, errors={"name": ["Too short"]})
    assert form.errors == {"name": ["Too short"]}
    assert form.name.data == "Alice"


def test_coercion_helpers():
    assert coerce_bool("on") is True
    assert coerce_bool("") is False
    assert coerce_int_list(["1", "2"]) == [1, 2]
    assert coerce_int_list("") == []
    assert coerce_optional_date("2026-01-15") == date(2026, 1, 15)
    assert coerce_optional_date("") is None
    assert coerce_datetime("2026-01-15T10:00:00") == datetime(2026, 1, 15, 10, 0, 0)
    assert coerce_optional_decimal("2.50") == Decimal("2.50")
    assert coerce_optional_decimal("") is None
