from typing import Any, Dict, Optional, Tuple, Type, TypeVar, Union, cast, get_args, get_origin

from flask import Request
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def _get_list_fields(schema: Type[BaseModel]) -> set[str]:
    """Extract field names that are list types from schema."""
    list_fields: set[str] = set()
    if not hasattr(schema, "model_fields"):
        return list_fields

    for field_name, field_info in schema.model_fields.items():
        annotation = field_info.annotation
        origin = get_origin(annotation)

        if origin is Union:
            for arg in get_args(annotation):
                if get_origin(arg) is list:
                    list_fields.add(field_name)
                    break
        elif origin is list:
            list_fields.add(field_name)

    return list_fields


def _process_form_value(key: str, values: list[str], list_fields: set[str]) -> Tuple[str, Any]:
    """Process a single form field value."""
    clean_key = key.rstrip("[]")

    if clean_key in list_fields or len(values) > 1 or key.endswith("[]"):
        try:
            return clean_key, [int(v) for v in values if v]
        except ValueError:
            return clean_key, [v for v in values if v]
    elif values[0] == "on":
        return key, True
    else:
        return key, values[0]


def _set_default_booleans(schema: Type[BaseModel], data: Dict[str, Any]) -> None:
    """Set missing boolean fields to False."""
    if not hasattr(schema, "model_fields"):
        return

    for field_name, field_info in schema.model_fields.items():
        if field_info.annotation == bool and field_name not in data:
            data[field_name] = False


def _parse_validation_errors(e: ValidationError) -> Dict[str, Any]:
    """Parse Pydantic validation errors into a dict."""
    errors: Dict[str, Any] = {}
    for error in e.errors():
        field = str(error["loc"][0]) if error["loc"] else "general"
        errors[field] = error["msg"]
    return errors


def validate_request(schema: Type[T], request: Request) -> Tuple[Optional[T], Optional[Dict[str, Any]]]:
    """
    Validate Flask request data against a Pydantic schema.

    Args:
        schema: Pydantic model class to validate against
        request: Flask request object

    Returns:
        Tuple of (validated_data, errors) where errors is a dict of field: error_message
    """
    try:
        data: Dict[str, Any] = {}
        list_fields = _get_list_fields(schema)

        for key in request.form.keys():
            values = request.form.getlist(key)
            field_key, field_value = _process_form_value(key, values, list_fields)
            data[field_key] = field_value

        _set_default_booleans(schema, data)

        validated = schema(**data)
        return cast(T, validated), None
    except ValidationError as e:
        return None, _parse_validation_errors(e)


def validate_dict(schema: Type[T], data: Dict[str, Any]) -> Tuple[Optional[T], Optional[Dict[str, Any]]]:
    """
    Validate a dictionary against a Pydantic schema.

    Args:
        schema: Pydantic model class to validate against
        data: Dictionary to validate

    Returns:
        Tuple of (validated_data, errors) where errors is a dict of field: error_message
    """
    try:
        validated = schema(**data)
        return cast(T, validated), None
    except ValidationError as e:
        return None, _parse_validation_errors(e)
