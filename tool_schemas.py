"""Tool schemas for the Claude API, typed with the SDK's ToolParam."""
from anthropic.types import ToolParam

get_current_datetime_schema = ToolParam(
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
)

