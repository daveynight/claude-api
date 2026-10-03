"""Tool schemas for the Claude API, typed with the SDK's ToolParam."""
from copy import deepcopy

from anthropic.types import ToolParam

__all__ = ["get_schemas"]

_REGISTRY: dict[str, ToolParam] = {}


def _register(schema: ToolParam) -> ToolParam:
    _REGISTRY[schema["name"]] = schema
    return schema


get_current_datetime_schema = _register(ToolParam(
    name="get_current_datetime",
    description=(
        "Returns the current date and time from the system clock. Use this whenever "
        "the user asks about the current date, time, day of week, or anything that "
        "depends on 'now' (e.g. how many days until a deadline). Claude cannot know "
        "the current date without this tool. Takes an optional strftime format "
        "string; with no arguments it returns 'YYYY-MM-DD HH:MM:SS'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "date_format": {
                "type": "string",
                "description": (
                    "A Python strftime format string controlling the output, e.g. "
                    "'%Y-%m-%d' for just the date or '%H:%M' for just the time. "
                    "Must not be empty. Defaults to '%Y-%m-%d %H:%M:%S'."
                ),
                "default": "%Y-%m-%d %H:%M:%S",
            }
        },
        "required": [],
    },
))

add_duration_to_datetime_schema = _register(ToolParam(
    name="add_duration_to_datetime",
    description= "Adds a duration to a datetime and returns the new datetime in ISO 8601 format.",
    input_schema={
        "type": "object",
        "properties": {
            "datetime_str": {"type": "string", "description": "Starting datetime, ISO 8601, e.g. 2026-10-03T14:30:00"},
            "duration": {"type": "number", "description": "How much to add. Negative values subtract."},
            "unit": {"type": "string", "enum": ["seconds", "minutes", "hours", "days", "weeks"]},
        },
        "required": ["datetime_str", "duration"],
    },
))

set_reminder_schema = _register(ToolParam(
    name= "set_reminder",
    description="Sets a reminder for the user at a specific time. Use add_duration_to_datetime first if the user gave a relative time like 'in 3 days'.",
    input_schema={
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "What to remind the user about."},
            "timestamp": {"type": "string", "description": "When to fire the reminder, ISO 8601."},
        },
        "required": ["content", "timestamp"],
    },
))


def get_schemas(names: list[str] | None = None) -> list[ToolParam]:
    """All schemas, or just the named ones, in the order requested."""
    names = list(_REGISTRY) if names is None else names
    return deepcopy([_REGISTRY[n] for n in names])
