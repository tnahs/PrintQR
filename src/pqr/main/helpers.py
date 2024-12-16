from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import tomllib
import yaml

from .shared import App, ConfigFormat, StringTransformation, console
from .ui import INDENT


def copy_file(
    source: Path,
    destination: Path,
    create_destination: bool = False,
    force: bool = False,
) -> None:
    """Copies a file into a directory.

    Args:
        source: Path to source file.
        destination: Path to destination directory.
        create_destination: Create the destination if it doesn't exist.
        force: Overwrite file if it exists.

    Returns:
        None
    """

    style = "yellow"

    destination = destination.resolve() / source.name

    text_destination = f"[{style}]{format_path(destination.parent)}[/{style}]"
    text_filename = f"[{style}]{destination.name}[/{style}]"

    if not destination.parent.exists() and create_destination is True:
        console.print(
            f"{INDENT * 2}Created directory {text_destination}.",
        )
        destination.parent.mkdir(parents=True)

    if destination.exists() and force is False:
        console.print(
            f"{INDENT * 2}[red]Warning:[/red] File {text_filename} exists. Skipping!"
        )
        return

    shutil.copy(source, destination)

    console.print(f"{INDENT * 2}Created {text_filename}.")


def edit_file(path: Path) -> None:
    """Edit a file.

    Args:
        path: Path to the file.

    Returns:
        None
    """

    editor = os.environ.get("EDITOR", App.DEFAULT_EDITOR)

    subprocess.run([editor, path], check=False)


def read_serialized_data(path: Path) -> dict:
    match path.suffix:
        case ConfigFormat.JSON:
            with path.open() as f:
                return json.load(f)
        case ConfigFormat.TOML:
            with path.open(mode="rb") as f:
                return tomllib.load(f)
        case ConfigFormat.YAML:
            with path.open() as f:
                return yaml.safe_load(f)

    raise ValueError(f"Unsupported serialized data format: '{path.name}'.")


def merge_dicts(base: dict, overrides: dict) -> dict:
    def recursive_merge(base: dict, override: dict) -> dict:
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key] = recursive_merge(base[key], value)
            else:
                base[key] = value

        return base

    return recursive_merge(base.copy(), overrides)


def generate_basename(
    template: str,
    template_context: dict,
    string_transformations: list[StringTransformation],
) -> str:
    basename = template.format(**template_context)
    basename = apply_string_transformations(basename, string_transformations)

    return basename


def apply_string_transformations(
    string: str, string_transformations: list[StringTransformation]
) -> str:
    string = str(string).strip()

    for string_transformation in string_transformations:
        string_transformation.apply(string)

    return string


def format_path(path: Path) -> str:
    """Returns a compacted string representation of the path:

        If the path is...
        1. ...the current directory, return "current directory".
        2. ...relative to the current directory, return a relative path.
        3. ...relative to the user's home directory, use '~' shorthand.
        4. Otherwise, return the absolute path.

    Args:
        path: Path to format.

    Returns:
        str: Formatted path.
    """

    cwd = Path.cwd()
    home = Path.home()

    # TODO: How wo we want to handle this case?
    if path == cwd:
        return "current directory"

    # Return if path is relative to the current directory.
    if path.is_relative_to(cwd):
        return f"./{path.relative_to(cwd)}"

    # Return if path is relative to the user's home directory
    if path.is_relative_to(home):
        return str(path).replace(str(home), "~", count=1)

    # Return absolute path as fallback.
    return str(path)


def kebab_to_snake(string: str) -> str:
    return string.replace("-", "_")


def snake_to_kebab(string: str) -> str:
    return string.replace("_", "-")
