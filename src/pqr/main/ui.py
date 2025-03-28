from __future__ import annotations

from typing import Any

from rich.box import HEAVY, Box
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from .shared import console


# Constants ----------------------------------------------------------------------------------------


INDENT = "   "

MISSING = "?"

TABLE_BORDER: Box = Box(
    "┏━━┓\n"
    "┃  ┃\n"
    "┠──┨\n"
    "┃  ┃\n"
    "┠──┨\n"
    "┠──┨\n"
    "┃  ┃\n"
    "┗━━┛\n"
)  # fmt: skip


# Table --------------------------------------------------------------------------------------------


TABLE_STYLE = {
    "box": TABLE_BORDER,
    "border_style": "cyan",
    "header_style": "cyan",
    "expand": False,
}

TABLE_PADDING = {
    #       t  r            b  l
    "pad": (1, len(INDENT), 0, len(INDENT)),
    "expand": False,
}


def table(title: str, **kwargs) -> Table:
    # Make a local copy to avoid mutating the original.
    table_style = TABLE_STYLE.copy()

    # Overwrite panel stlye values with those in kwargs.
    table_style.update(kwargs)

    return Table(
        title=title,
        **table_style,
    )


# Panel --------------------------------------------------------------------------------------------


#                t  r  b  l
PADDING_INNER = (1, 3, 1, 3)

#                t  r            b  l
PADDING_OUTER = (1, len(INDENT), 1, len(INDENT))


PANEL_STYLE = {
    "box": HEAVY,
    "border_style": "cyan",
    #           t  r  b  l
    "padding": PADDING_INNER,
    "expand": False,
}


def panel(
    renderable: Any,
    padding_outer: tuple[int, int, int, int] = PADDING_OUTER,
    pretty: bool = False,
    **kwargs,
) -> Panel | Padding:
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
        pad=padding_outer,
        expand=False,
    )


def print_panel(
    renderable: Any,
    padding_outer: tuple[int, int, int, int] = PADDING_OUTER,
    pretty: bool = False,
    **kwargs,
) -> None:
    console.print(
        panel(
            renderable,
            padding_outer,
            pretty,
            **kwargs,
        )
    )


# Utils --------------------------------------------------------------------------------------------


def get_char_max_width(string: str) -> int:
    """Returns the character length of the longest line in a string

    Args:
        string (str): The string to test.

    Returns:
        int: Length of the longest line.
    """
    return max(len(line) for line in string.splitlines())


def pad_lines(string: str, width: int) -> str:
    """Returns a string where each line is left-justified padded to a specific width.

    Args:
        string (str): The string to be formatted.
        width (int): The target width for each line.

    Returns:
        str: The formatted string.
    """

    return "\n".join([line.ljust(width) for line in string.splitlines()])
