from __future__ import annotations

from .main import app, cli
from .main.settings import PRINT_SETTINGS


def main() -> None:
    PRINT_SETTINGS.load()

    app.load_config(user=False)

    cli.cli()
