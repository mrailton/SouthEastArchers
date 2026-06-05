from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import Request
from markupsafe import Markup, escape
from pydantic import BaseModel, ValidationError

from app.templating import flash
from app.utils.formdata import MultiDict


def multidict_to_dict(raw: MultiDict | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(raw, MultiDict):
        data: dict[str, Any] = {}
        for key in raw.keys():
            values = raw.getlist(key)
            data[key] = values if len(values) > 1 else (values[0] if values else "")
        return data
    return dict(raw)


def single_field_errors(errors: dict[str, list[str]]) -> dict[str, str]:
    return {field: messages[0] for field, messages in errors.items() if messages}


def flash_field_errors(request: Request, errors: dict[str, list[str]]) -> None:
    for message in single_field_errors(errors).values():
        flash(request, "error", message)


def pydantic_errors(exc: ValidationError) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    for error in exc.errors():
        loc = error.get("loc", ())
        field_name = ".".join(str(part) for part in loc) if loc else "form"
        errors.setdefault(field_name, []).append(str(error.get("msg", "Invalid value")))
    return errors


def parse_form[FormModelT: BaseModel](
    model_cls: type[FormModelT],
    raw: MultiDict | Mapping[str, Any],
) -> tuple[FormModelT | None, dict[str, list[str]], dict[str, Any]]:
    data = multidict_to_dict(raw)
    try:
        model = model_cls.model_validate(data)
        return model, {}, model.model_dump()
    except ValidationError as exc:
        return None, pydantic_errors(exc), data


@dataclass
class FieldView:
    data: Any = None
    choices: list[tuple[Any, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    description: str = ""
    name: str = ""
    input_type: str = "text"

    def __call__(self, **attrs: Any) -> Markup:
        attr_str = " ".join(f'{escape(k)}="{escape(v)}"' for k, v in attrs.items())
        if self.input_type == "checkbox":
            checked = " checked" if self.data else ""
            return Markup(f'<input type="checkbox" name="{escape(self.name)}" id="{escape(self.name)}"{checked} {attr_str}>')
        if self.input_type == "textarea":
            return Markup(f'<textarea name="{escape(self.name)}" id="{escape(self.name)}" {attr_str}>{escape(self.data or "")}</textarea>')
        value = "" if self.data is None else escape(self.data)
        return Markup(f'<input type="{escape(self.input_type)}" name="{escape(self.name)}" id="{escape(self.name)}" value="{value}" {attr_str}>')


class FormView:
    def __init__(
        self,
        *,
        values: dict[str, Any] | None = None,
        errors: dict[str, list[str]] | None = None,
        choices: dict[str, list[tuple[Any, str]]] | None = None,
        descriptions: dict[str, str] | None = None,
        field_types: dict[str, str] | None = None,
    ) -> None:
        self._values = values or {}
        self.errors = errors or {}
        self._choices = choices or {}
        self._descriptions = descriptions or {}
        self._field_types = field_types or {}

    def __getattr__(self, name: str) -> FieldView:
        if name == "errors":
            raise AttributeError(name)
        return FieldView(
            data=self._values.get(name),
            choices=self._choices.get(name, []),
            errors=self.errors.get(name, []),
            description=self._descriptions.get(name, ""),
            name=name,
            input_type=self._field_types.get(name, "text"),
        )


def coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return False
    return str(value).lower() in ("on", "true", "1", "yes")


def coerce_int_list(value: Any) -> list[int]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [int(v) for v in value if str(v).strip()]
    return [int(value)]


def coerce_optional_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def coerce_optional_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
