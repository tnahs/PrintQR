import textwrap
from typing import ClassVar

from pygments import lexer
from pygments.lexer import RegexLexer
from pygments.token import (
    Comment,
    Error,
    Keyword,
    Name,
    Operator,
    String,
    Whitespace,
)
from rich.console import Console
from rich.syntax import Syntax


class CompactLexer(RegexLexer):
    name = "Compact"

    tokens: ClassVar = {
        "root": [
            # Comments
            (r"^\s*#\s*.*", Comment),
            #
            # Blank Headers
            (r"^\[.+\]$", Comment),
            #
            # Headers
            (r"^.+$", Keyword),
            #
            # Key-value Pairs
            (
                r"(\s+)([a-z-]+)(=)(.*)",
                lexer.bygroups(
                    Whitespace,
                    Name,
                    Operator,
                    String,
                ),
            ),
            #
            # Errors
            (r".", Error),
        ],
    }


if __name__ == "__main__":
    data = textwrap.dedent(
        """
        Galaxy Black
          fn=Prusament
          fm=PLA
        Prusa MK4S
          ns=0.4
          nt=HF ObXidian
        [slicer]
          mv=24
          lh=0.25
          nt=230
          bt=60
          pt=00:42
          pt=00:42
        2025-01-01
        Here is a note.
        # Here is a comment
    """
    )

    console = Console()

    syntax = Syntax(
        data,
        lexer=CompactLexer(),
        theme="dracula",
        background_color="default",
    )

    console.print(syntax)
