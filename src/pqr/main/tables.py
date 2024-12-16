from __future__ import annotations

import textwrap
from datetime import datetime

from rich.console import Group
from rich.padding import Padding
from rich.text import Text

from . import ui
from .settings import PRINT_SETTINGS
from .shared import StringTransformation


def _generate_table_template_fields() -> Padding:
    style1 = "cyan"
    style2 = "green"
    accent_style1 = "yellow"

    empty_value = "-"

    table = ui.table(
        title=(
            f"[{style1}]Available template fields for generating "
            f"[{accent_style1}]image[/{accent_style1}], "
            f"[{accent_style1}]TOML[/{accent_style1}] and "
            f"[{accent_style1}]GCode[/{accent_style1}] filenames.[/{style1}]"
        ),
    )

    for header in [
        "Category",
        "Name",
        "Short Name",
        "Template String",
        "Type",
        "Unit",
        "Description",
    ]:
        table.add_column(
            header=header,
            style=style2,
        )

    category = None

    for setting in PRINT_SETTINGS.iter_settings():
        if category is None:
            category = setting.category

        if category != setting.category:
            category = setting.category
            table.add_section()

        table.add_row(
            setting.category,
            setting.name,
            setting.compact_name or empty_value,
            setting.template_string,
            setting.type.__name__,
            setting.unit or empty_value,
            setting.description.capitalize(),
        )

    return Padding(
        table,
        **ui.TABLE_PADDING,
    )


def _generate_table_template_date() -> Padding:
    style1 = "cyan"
    style2 = "green"
    accent_style1 = "yellow"
    accent_style2 = "blue"

    date = datetime.now()

    date_formats = [
        (
            "%a",  # Sun
            "Weekday as locale's abbreviated name.",
        ),
        (
            "%A",  # Sunday
            "Weekday as locale's full name.",
        ),
        (
            "%d",  # 08
            "Day of the month as a zero-padded decimal number.",
        ),
        (
            "%b",  # Sep
            "Month as locale's abbreviated name.",
        ),
        (
            "%B",  # September
            "Month as locale's full name.",
        ),
        (
            "%m",  # 09
            "Month as a zero-padded decimal number.",
        ),
        (
            "%y",  # 13
            "Year without century as a zero-padded decimal number.",
        ),
        (
            "%Y",  # 2013
            "Year with century as a decimal number.",
        ),
    ]

    table = ui.table(
        title=(
            f"[{style1}]Python [{accent_style1}]strftime[/{accent_style1}] syntax. "
            f"[dim]See [{accent_style2}]https://strftime.org/[/{accent_style2}] "
            f"for more directives.[/dim][/{style1}]"
        )
    )

    for header in [
        "Format String",
        f"Example: {date.strftime('%Y-%m-%d')}",
        "Description",
    ]:
        table.add_column(
            header=header,
            style=style2,
        )

    for date_format in date_formats:
        table.add_row(
            date_format[0],
            date.strftime(date_format[0]),
            date_format[1],
        )

    return Padding(
        table,
        **ui.TABLE_PADDING,
    )


def _generate_table_string_transformations() -> Padding:
    style1 = "cyan"
    style2 = "green"
    accent_style1 = "yellow"

    table = ui.table(
        title=(
            f"[{style1}]Available filename transformations for "
            f"[{accent_style1}]image[/{accent_style1}], "
            f"[{accent_style1}]TOML[/{accent_style1}] and "
            f"[{accent_style1}]GCode[/{accent_style1}] filenames.[/{style1}]"
        ),
    )

    example_string = "Prusament PLA - Gålåxy Blåck"

    for header in [
        "Name",
        f"Example: [yellow]{example_string}[/yellow]",
        "Description",
    ]:
        table.add_column(
            header=header,
            style=style2,
        )

    for transformation in StringTransformation:
        table.add_row(
            transformation.value,
            transformation.apply(example_string),
            transformation.description,
        )

    description = textwrap.wrap(
        text=textwrap.dedent(
            """
            Transformations can be used to modify generated filenames. These
            transformations are applied after the filenames are generated but before
            the extension is added. For complex modifications, transformations can be
            chained.
            """
        ),
        width=95,
    )

    description = Text(
        "\n".join(description),
        style="cyan",
        justify="left",
    )

    group = Group(description, "\n", table)

    return Padding(
        group,
        **ui.TABLE_PADDING,
    )


TABLE_TEMPLATES_FIELDS = _generate_table_template_fields()
TABLE_TEMPLATES_DATE = _generate_table_template_date()
TABLE_STRING_TRANSFORMATIONS = _generate_table_string_transformations()
