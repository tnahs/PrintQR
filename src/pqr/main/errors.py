from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from . import helpers, ui
from .shared import console
from .ui import INDENT


class InternalError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ConfigValidationError(Exception):
    def __init__(self, source: ValidationError, path: Path) -> None:
        super().__init__()

        self.source = source
        self.path = path


class ConfigReadError(Exception):
    def __init__(self, source: Exception, path: Path) -> None:
        super().__init__()

        self.source = source
        self.path = path


def print_config_validation_errors(exception: ConfigValidationError) -> None:
    text_user_files = helpers.format_path(exception.path)

    ui.print_panel(
        f"Error validating [green]{exception.path.name}[/green] "
        f"in [yellow]{text_user_files}[/yellow].",
    )

    for error in exception.source.errors():
        value = error.get("input")
        message = error.get("msg")
        location = ".".join([str(loc) for loc in error.get("loc")])

        if isinstance(value, str):
            value = f"'{value}'"

        if not message.endswith("."):
            message = f"{message}."

        message = [
            f"{INDENT}[red]{location}[/red]",
            f"{INDENT * 2}{message}",
        ]

        console.print("\n".join(message))


def print_config_read_error(exception: ConfigReadError) -> None:
    text_user_files = helpers.format_path(exception.path)

    ui.print_panel(
        f"Error reading [green]{exception.path.name}[/green] "
        f"in [yellow]{text_user_files}[/yellow].",
    )

    console.print(
        f"{INDENT}[red]{exception.source.__class__.__name__}[/red]: {exception.source}"
    )
