from __future__ import annotations

from typing import Any

from rich.box import HEAVY, Box
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from .shared import console


# Constants ----------------------------------------------------------------------------


INDENT = "   "

MISSING = "?"

TABLE_BORDER: Box = Box(
    "".join(
        [
            "┏━━┓\n",
            "┃  ┃\n",
            "┠──┨\n",
            "┃  ┃\n",
            "┠──┨\n",
            "┠──┨\n",
            "┃  ┃\n",
            "┗━━┛\n",
        ]
    )
)


# Table --------------------------------------------------------------------------------


TABLE_STYLE = {
    "box": TABLE_BORDER,
    "border_style": "cyan",
    "header_style": "cyan",
    "expand": False,
}

TABLE_PADDING = {
    # top, right, bottom, left
    "pad": (
        1,
        len(INDENT),
        1,
        len(INDENT),
    ),
    "expand": False,
}


def table(
    title: str,
    **kwargs,  # noqa: ANN003
) -> Table:
    # Make a local copy to avoid mutating the original.
    table_style = TABLE_STYLE.copy()

    # Overwrite panel stlye values with those in kwargs.
    table_style.update(kwargs)

    return Table(
        title=title,
        **table_style,
    )


# Panel --------------------------------------------------------------------------------


PANEL_STYLE = {
    "box": HEAVY,
    "border_style": "cyan",
    "padding": (1, 3),
    "expand": False,
}


def panel(
    renderable: Any,
    pretty: bool = False,
    **kwargs,  # noqa: ANN003
) -> Padding:
    if pretty is True:
        renderable = Pretty(renderable, expand_all=True)

    # Make a local copy to avoid mutating the original.
    panel_style = PANEL_STYLE.copy()

    # Overwrite panel stlye values with those in kwargs.
    panel_style.update(kwargs)

    panel = Panel(
        renderable=renderable,
        **panel_style,  # pyright: ignore [reportArgumentType]
    )

    return Padding(
        panel,
        # top, right, bottom, left
        pad=(
            1,
            len(INDENT),
            1,
            len(INDENT),
        ),
        expand=False,
    )


def print_panel(
    renderable: Any,
    pretty: bool = False,
    **kwargs,  # noqa: ANN003
) -> None:
    console.print(
        panel(
            renderable,
            pretty,
            **kwargs,
        )
    )
