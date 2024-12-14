from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import tomllib
import yaml

from .shared import App, ConfigFormat, console
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


def format_path(path: Path) -> str:
    home = str(Path.home())
    return str(path).replace(home, "~")


def kebab_to_snake(string: str) -> str:
    return string.replace("-", "_")


def snake_to_kebab(string: str) -> str:
    return string.replace("_", "-")
