from __future__ import annotations

from datetime import datetime

from rich.padding import Padding

from . import ui
from .settings import PRINT_SETTINGS


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
        "Format String",
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
            setting.format_string,
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

    formats = [
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

    for row in formats:
        table.add_row(row[0], date.strftime(row[0]), row[1])

    return Padding(
        table,
        **ui.TABLE_PADDING,
    )


TABLE_TEMPLATES_FIELDS = _generate_table_template_fields()
TABLE_TEMPLATES_DATE = _generate_table_template_date()
