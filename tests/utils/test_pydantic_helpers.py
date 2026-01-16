"""Tests for pydantic_helpers"""

from typing import Optional

from pydantic import BaseModel, Field
from werkzeug.datastructures import ImmutableMultiDict

from app.utils.pydantic_helpers import (
    _get_list_fields,
    _parse_validation_errors,
    _process_form_value,
    _set_default_booleans,
    validate_dict,
    validate_request,
)


class SimpleSchema(BaseModel):
    name: str
    age: int
    active: bool = False


class SchemaWithLists(BaseModel):
    tags: list[str]
    ids: list[int]
    name: str


class SchemaWithOptionalList(BaseModel):
    tags: Optional[list[str]] = None
    name: str


class SchemaWithMixedFields(BaseModel):
    name: str
    age: int = 0
    active: bool = False
    tags: list[str] = []
    scores: Optional[list[int]] = None


class SchemaWithValidation(BaseModel):
    email: str = Field(..., min_length=5)
    age: int = Field(..., ge=0, le=120)


# TestGetListFields


def test_get_list_fields_no_lists():
    """Test that schemas without list fields return empty set"""
    result = _get_list_fields(SimpleSchema)
    assert result == set()


def test_get_list_fields_identifies_lists():
    """Test that list fields are correctly identified"""
    result = _get_list_fields(SchemaWithLists)
    assert result == {"tags", "ids"}


def test_get_list_fields_identifies_optional_list():
    """Test that Optional[list] fields are identified"""
    result = _get_list_fields(SchemaWithOptionalList)
    assert result == {"tags"}


def test_get_list_fields_mixed_schema():
    """Test schema with both list and non-list fields"""
    result = _get_list_fields(SchemaWithMixedFields)
    assert result == {"tags", "scores"}


def test_get_list_fields_handles_missing_model_fields():
    """Test that schemas without model_fields attribute return empty set"""

    class FakeSchema:
        pass

    result = _get_list_fields(FakeSchema)
    assert result == set()


# TestProcessFormValue


def test_process_form_value_single_non_list():
    key, value = _process_form_value("name", ["John"], set())
    assert key == "name"
    assert value == "John"


def test_process_form_value_multiple_values_creates_list():
    key, value = _process_form_value("tags", ["tag1", "tag2"], set())
    assert key == "tags"
    assert value == ["tag1", "tag2"]


def test_process_form_value_list_field_single_value():
    key, value = _process_form_value("tags", ["tag1"], {"tags"})
    assert key == "tags"
    assert value == ["tag1"]


def test_process_form_value_array_bracket_notation():
    key, value = _process_form_value("tags[]", ["tag1", "tag2"], set())
    assert key == "tags"
    assert value == ["tag1", "tag2"]


def test_process_form_value_integer_list_conversion():
    key, value = _process_form_value("ids", ["1", "2", "3"], {"ids"})
    assert key == "ids"
    assert value == [1, 2, 3]


def test_process_form_value_mixed_integer_string_list():
    key, value = _process_form_value("mixed", ["1", "not_a_number"], {"mixed"})
    assert key == "mixed"
    assert value == ["1", "not_a_number"]


def test_process_form_value_checkbox_on_value():
    key, value = _process_form_value("active", ["on"], set())
    assert key == "active"
    assert value is True


def test_process_form_value_empty_values_filtered():
    key, value = _process_form_value("tags", ["tag1", "", "tag2"], {"tags"})
    assert key == "tags"
    assert value == ["tag1", "tag2"]


# TestSetDefaultBooleans


def test_set_default_booleans_sets_missing_boolean_to_false():
    data = {"name": "John", "age": 30}
    _set_default_booleans(SimpleSchema, data)
    assert data["active"] is False


def test_set_default_booleans_does_not_override_existing_boolean():
    data = {"name": "John", "age": 30, "active": True}
    _set_default_booleans(SimpleSchema, data)
    assert data["active"] is True


def test_set_default_booleans_handles_multiple_boolean_fields():

    class MultiBoolSchema(BaseModel):
        active: bool
        verified: bool
        deleted: bool = False

    data = {"verified": True}
    _set_default_booleans(MultiBoolSchema, data)
    assert data["active"] is False
    assert data["verified"] is True
    assert data["deleted"] is False


def test_set_default_booleans_ignores_non_boolean_fields():
    data = {"name": "John"}
    _set_default_booleans(SimpleSchema, data)
    assert "name" in data
    assert "age" not in data


def test_set_default_booleans_handles_schema_without_model_fields():

    class FakeSchema:
        pass

    data = {"name": "John"}
    _set_default_booleans(FakeSchema, data)
    assert data == {"name": "John"}


# TestParseValidationErrors


def test_parse_validation_errors_single_field():
    try:
        SimpleSchema(name="John", age="not_a_number")
    except Exception as e:
        errors = _parse_validation_errors(e)
        assert "age" in errors
        assert isinstance(errors["age"], str)


def test_parse_validation_errors_multiple_fields():
    try:
        SimpleSchema(name=123, age="invalid")
    except Exception as e:
        errors = _parse_validation_errors(e)
        assert "name" in errors
        assert "age" in errors


def test_parse_validation_errors_missing_required_field():
    try:
        SimpleSchema(name="John")
    except Exception as e:
        errors = _parse_validation_errors(e)
        assert "age" in errors


def test_parse_validation_errors_messages_are_strings():
    try:
        SchemaWithValidation(email="ab", age=150)
    except Exception as e:
        errors = _parse_validation_errors(e)
        for field, message in errors.items():
            assert isinstance(message, str)


# TestValidateRequest


def test_validate_request_valid_simple_form(app):
    with app.test_request_context(
        "/",
        method="POST",
        data={"name": "John Doe", "age": "30", "active": "on"},
    ):
        from flask import request

        validated, errors = validate_request(SimpleSchema, request)
        assert errors is None
        assert validated is not None
        assert validated.name == "John Doe"
        assert validated.age == 30
        assert validated.active is True


def test_validate_request_missing_checkbox(app):
    with app.test_request_context(
        "/",
        method="POST",
        data={"name": "John Doe", "age": "30"},
    ):
        from flask import request

        validated, errors = validate_request(SimpleSchema, request)
        assert errors is None
        assert validated is not None
        assert validated.active is False


def test_validate_request_list_fields(app):
    with app.test_request_context(
        "/",
        method="POST",
        data=ImmutableMultiDict(
            [
                ("name", "Test"),
                ("tags", "tag1"),
                ("tags", "tag2"),
                ("ids", "1"),
                ("ids", "2"),
            ]
        ),
    ):
        from flask import request

        validated, errors = validate_request(SchemaWithLists, request)
        assert errors is None
        assert validated is not None
        assert validated.tags == ["tag1", "tag2"]
        assert validated.ids == [1, 2]


def test_validate_request_array_bracket_notation(app):
    with app.test_request_context(
        "/",
        method="POST",
        data=ImmutableMultiDict(
            [
                ("name", "Test"),
                ("tags[]", "tag1"),
                ("tags[]", "tag2"),
            ]
        ),
    ):
        from flask import request

        validated, errors = validate_request(SchemaWithOptionalList, request)
        assert errors is None
        assert validated is not None
        assert validated.tags == ["tag1", "tag2"]


def test_validate_request_returns_errors_for_invalid_data(app):
    with app.test_request_context(
        "/",
        method="POST",
        data={"name": "John", "age": "invalid"},
    ):
        from flask import request

        validated, errors = validate_request(SimpleSchema, request)
        assert validated is None
        assert errors is not None
        assert "age" in errors


def test_validate_request_returns_errors_for_missing_required_fields(app):
    with app.test_request_context(
        "/",
        method="POST",
        data={"age": "30"},
    ):
        from flask import request

        validated, errors = validate_request(SimpleSchema, request)
        assert validated is None
        assert errors is not None
        assert "name" in errors


def test_validate_request_complex_mixed_fields(app):
    with app.test_request_context(
        "/",
        method="POST",
        data=ImmutableMultiDict(
            [
                ("name", "John"),
                ("age", "25"),
                ("active", "on"),
                ("tags[]", "tag1"),
                ("tags[]", "tag2"),
                ("scores[]", "95"),
                ("scores[]", "87"),
            ]
        ),
    ):
        from flask import request

        validated, errors = validate_request(SchemaWithMixedFields, request)
        assert errors is None
        assert validated is not None
        assert validated.name == "John"
        assert validated.age == 25
        assert validated.active is True
        assert validated.tags == ["tag1", "tag2"]
        assert validated.scores == [95, 87]


# TestValidateDict


def test_validate_dict_valid():
    data = {"name": "John Doe", "age": 30, "active": True}
    validated, errors = validate_dict(SimpleSchema, data)
    assert errors is None
    assert validated is not None
    assert validated.name == "John Doe"
    assert validated.age == 30
    assert validated.active is True


def test_validate_dict_default_values():
    data = {"name": "John", "age": 30}
    validated, errors = validate_dict(SimpleSchema, data)
    assert errors is None
    assert validated is not None
    assert validated.active is False


def test_validate_dict_with_lists():
    data = {"name": "Test", "tags": ["tag1", "tag2"], "ids": [1, 2, 3]}
    validated, errors = validate_dict(SchemaWithLists, data)
    assert errors is None
    assert validated is not None
    assert validated.tags == ["tag1", "tag2"]
    assert validated.ids == [1, 2, 3]


def test_validate_dict_invalid_dict():
    data = {"name": "John", "age": "not_a_number"}
    validated, errors = validate_dict(SimpleSchema, data)
    assert validated is None
    assert errors is not None
    assert "age" in errors


def test_validate_dict_missing_required_fields():
    data = {"name": "John"}
    validated, errors = validate_dict(SimpleSchema, data)
    assert validated is None
    assert errors is not None
    assert "age" in errors


def test_validate_dict_field_rules():
    data = {"email": "test@example.com", "age": 25}
    validated, errors = validate_dict(SchemaWithValidation, data)
    assert errors is None
    assert validated is not None
    assert validated.email == "test@example.com"
    assert validated.age == 25


def test_validate_dict_field_validation_failures():
    data = {"email": "ab", "age": 150}
    validated, errors = validate_dict(SchemaWithValidation, data)
    assert validated is None
    assert errors is not None
    assert "email" in errors or "age" in errors


def test_validate_dict_empty_optional_list():
    data = {"name": "Test"}
    validated, errors = validate_dict(SchemaWithOptionalList, data)
    assert errors is None
    assert validated is not None
    assert validated.tags is None
