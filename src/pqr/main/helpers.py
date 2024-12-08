from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import tomllib
import yaml

from .shared import ConfigFormat


def edit_file(path: Path, fallback_editor: str = "vim") -> None:
    editor = os.environ.get("EDITOR", fallback_editor)
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
