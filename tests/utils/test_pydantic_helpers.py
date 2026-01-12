"""Tests for pydantic_helpers"""

from typing import Optional

import pytest
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


class TestGetListFields:
    def test_returns_empty_set_for_schema_without_lists(self):
        """Test that schemas without list fields return empty set"""
        result = _get_list_fields(SimpleSchema)
        assert result == set()

    def test_identifies_list_fields(self):
        """Test that list fields are correctly identified"""
        result = _get_list_fields(SchemaWithLists)
        assert result == {"tags", "ids"}

    def test_identifies_optional_list_fields(self):
        """Test that Optional[list] fields are identified"""
        result = _get_list_fields(SchemaWithOptionalList)
        assert result == {"tags"}

    def test_mixed_schema_with_lists_and_non_lists(self):
        """Test schema with both list and non-list fields"""
        result = _get_list_fields(SchemaWithMixedFields)
        assert result == {"tags", "scores"}

    def test_handles_schema_without_model_fields(self):
        """Test that schemas without model_fields attribute return empty set"""
        class FakeSchema:
            pass

        result = _get_list_fields(FakeSchema)
        assert result == set()


class TestProcessFormValue:
    def test_single_value_non_list_field(self):
        """Test processing single value for non-list field"""
        key, value = _process_form_value("name", ["John"], set())
        assert key == "name"
        assert value == "John"

    def test_multiple_values_creates_list(self):
        """Test that multiple values create a list"""
        key, value = _process_form_value("tags", ["tag1", "tag2"], set())
        assert key == "tags"
        assert value == ["tag1", "tag2"]

    def test_list_field_with_single_value(self):
        """Test that list field with single value returns list"""
        key, value = _process_form_value("tags", ["tag1"], {"tags"})
        assert key == "tags"
        assert value == ["tag1"]

    def test_array_bracket_notation(self):
        """Test that fields ending with [] are treated as lists"""
        key, value = _process_form_value("tags[]", ["tag1", "tag2"], set())
        assert key == "tags"
        assert value == ["tag1", "tag2"]

    def test_integer_list_conversion(self):
        """Test that numeric strings are converted to integers in lists"""
        key, value = _process_form_value("ids", ["1", "2", "3"], {"ids"})
        assert key == "ids"
        assert value == [1, 2, 3]

    def test_mixed_integer_string_list(self):
        """Test that non-numeric values prevent integer conversion"""
        key, value = _process_form_value("mixed", ["1", "not_a_number"], {"mixed"})
        assert key == "mixed"
        assert value == ["1", "not_a_number"]

    def test_checkbox_on_value(self):
        """Test that 'on' value is converted to True"""
        key, value = _process_form_value("active", ["on"], set())
        assert key == "active"
        assert value is True

    def test_empty_values_filtered_from_list(self):
        """Test that empty strings are filtered from lists"""
        key, value = _process_form_value("tags", ["tag1", "", "tag2"], {"tags"})
        assert key == "tags"
        assert value == ["tag1", "tag2"]


class TestSetDefaultBooleans:
    def test_sets_missing_boolean_to_false(self):
        """Test that missing boolean fields are set to False"""
        data = {"name": "John", "age": 30}
        _set_default_booleans(SimpleSchema, data)
        assert data["active"] is False

    def test_does_not_override_existing_boolean(self):
        """Test that existing boolean values are not changed"""
        data = {"name": "John", "age": 30, "active": True}
        _set_default_booleans(SimpleSchema, data)
        assert data["active"] is True

    def test_handles_multiple_boolean_fields(self):
        """Test handling of multiple boolean fields"""
        class MultiBoolSchema(BaseModel):
            active: bool
            verified: bool
            deleted: bool = False

        data = {"verified": True}
        _set_default_booleans(MultiBoolSchema, data)
        assert data["active"] is False
        assert data["verified"] is True
        assert data["deleted"] is False

    def test_ignores_non_boolean_fields(self):
        """Test that non-boolean fields are not modified"""
        data = {"name": "John"}
        _set_default_booleans(SimpleSchema, data)
        assert "name" in data
        assert "age" not in data

    def test_handles_schema_without_model_fields(self):
        """Test that schemas without model_fields attribute are handled gracefully"""
        class FakeSchema:
            pass

        data = {"name": "John"}
        _set_default_booleans(FakeSchema, data)
        assert data == {"name": "John"}


class TestParseValidationErrors:
    def test_parses_single_field_error(self):
        """Test parsing single field validation error"""
        try:
            SimpleSchema(name="John", age="not_a_number")
        except Exception as e:
            errors = _parse_validation_errors(e)
            assert "age" in errors
            assert isinstance(errors["age"], str)

    def test_parses_multiple_field_errors(self):
        """Test parsing multiple field validation errors"""
        try:
            SimpleSchema(name=123, age="invalid")
        except Exception as e:
            errors = _parse_validation_errors(e)
            assert "name" in errors
            assert "age" in errors

    def test_parses_missing_required_field_error(self):
        """Test parsing missing required field error"""
        try:
            SimpleSchema(name="John")
        except Exception as e:
            errors = _parse_validation_errors(e)
            assert "age" in errors

    def test_error_messages_are_strings(self):
        """Test that error messages are strings"""
        try:
            SchemaWithValidation(email="ab", age=150)
        except Exception as e:
            errors = _parse_validation_errors(e)
            for field, message in errors.items():
                assert isinstance(message, str)


class TestValidateRequest:
    def test_validates_simple_form_data(self, app):
        """Test validation of simple form data"""
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

    def test_handles_missing_checkbox(self, app):
        """Test that unchecked checkboxes default to False"""
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

    def test_validates_list_fields(self, app):
        """Test validation of list fields"""
        with app.test_request_context(
            "/",
            method="POST",
            data=ImmutableMultiDict([
                ("name", "Test"),
                ("tags", "tag1"),
                ("tags", "tag2"),
                ("ids", "1"),
                ("ids", "2"),
            ]),
        ):
            from flask import request

            validated, errors = validate_request(SchemaWithLists, request)
            assert errors is None
            assert validated is not None
            assert validated.tags == ["tag1", "tag2"]
            assert validated.ids == [1, 2]

    def test_validates_array_bracket_notation(self, app):
        """Test validation with array bracket notation"""
        with app.test_request_context(
            "/",
            method="POST",
            data=ImmutableMultiDict([
                ("name", "Test"),
                ("tags[]", "tag1"),
                ("tags[]", "tag2"),
            ]),
        ):
            from flask import request

            validated, errors = validate_request(SchemaWithOptionalList, request)
            assert errors is None
            assert validated is not None
            assert validated.tags == ["tag1", "tag2"]

    def test_returns_errors_for_invalid_data(self, app):
        """Test that validation errors are returned for invalid data"""
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

    def test_returns_errors_for_missing_required_fields(self, app):
        """Test that errors are returned for missing required fields"""
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

    def test_validates_complex_form_with_mixed_fields(self, app):
        """Test validation of form with mixed field types"""
        with app.test_request_context(
            "/",
            method="POST",
            data=ImmutableMultiDict([
                ("name", "John"),
                ("age", "25"),
                ("active", "on"),
                ("tags[]", "tag1"),
                ("tags[]", "tag2"),
                ("scores[]", "95"),
                ("scores[]", "87"),
            ]),
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


class TestValidateDict:
    def test_validates_valid_dict(self):
        """Test validation of valid dictionary"""
        data = {"name": "John Doe", "age": 30, "active": True}
        validated, errors = validate_dict(SimpleSchema, data)
        assert errors is None
        assert validated is not None
        assert validated.name == "John Doe"
        assert validated.age == 30
        assert validated.active is True

    def test_validates_dict_with_default_values(self):
        """Test validation with default values"""
        data = {"name": "John", "age": 30}
        validated, errors = validate_dict(SimpleSchema, data)
        assert errors is None
        assert validated is not None
        assert validated.active is False

    def test_validates_dict_with_lists(self):
        """Test validation of dictionary with list fields"""
        data = {"name": "Test", "tags": ["tag1", "tag2"], "ids": [1, 2, 3]}
        validated, errors = validate_dict(SchemaWithLists, data)
        assert errors is None
        assert validated is not None
        assert validated.tags == ["tag1", "tag2"]
        assert validated.ids == [1, 2, 3]

    def test_returns_errors_for_invalid_dict(self):
        """Test that errors are returned for invalid dictionary"""
        data = {"name": "John", "age": "not_a_number"}
        validated, errors = validate_dict(SimpleSchema, data)
        assert validated is None
        assert errors is not None
        assert "age" in errors

    def test_returns_errors_for_missing_required_fields(self):
        """Test that errors are returned for missing required fields"""
        data = {"name": "John"}
        validated, errors = validate_dict(SimpleSchema, data)
        assert validated is None
        assert errors is not None
        assert "age" in errors

    def test_validates_with_field_validation_rules(self):
        """Test validation with field-level validation rules"""
        data = {"email": "test@example.com", "age": 25}
        validated, errors = validate_dict(SchemaWithValidation, data)
        assert errors is None
        assert validated is not None
        assert validated.email == "test@example.com"
        assert validated.age == 25

    def test_returns_errors_for_field_validation_failures(self):
        """Test that field validation failures return errors"""
        data = {"email": "ab", "age": 150}
        validated, errors = validate_dict(SchemaWithValidation, data)
        assert validated is None
        assert errors is not None
        assert "email" in errors or "age" in errors

    def test_validates_empty_optional_list(self):
        """Test validation with empty optional list"""
        data = {"name": "Test"}
        validated, errors = validate_dict(SchemaWithOptionalList, data)
        assert errors is None
        assert validated is not None
        assert validated.tags is None
