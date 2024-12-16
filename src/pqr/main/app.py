from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from rich.box import HEAVY
from rich.columns import Columns
from rich.panel import Panel
from rich.prompt import FloatPrompt, IntPrompt, Prompt
from rich.syntax import Syntax
from rich.table import Table

from . import errors, helpers, qr, ui
from .config import CONFIG, ConfigManager
from .errors import ConfigReadError, ConfigValidationError
from .settings import PrintSettings
from .shared import App, Encoding, Key, StringTransformation, console
from .ui import INDENT


def load_config(user: bool) -> None:
    try:
        CONFIG.load(user)
    except ConfigValidationError as error:
        errors.print_config_validation_errors(error)
        sys.exit(-1)
    except ConfigReadError as error:
        errors.print_config_read_error(error)
        sys.exit(-1)


def save_print_settings_file(
    destination: Path,
    print_settings: PrintSettings,
    force: bool = False,
) -> None:
    style1 = "cyan"
    style2 = "yellow"

    destination = destination.resolve()

    text_destination = f"[{style2}]{helpers.format_path(destination)}[/{style2}]"
    text_filename = f"[{style2}]{destination.name}[/{style2}]"

    ui.print_panel(
        f"[{style1}]Creating {text_filename} in {text_destination}...[/{style1}]",
        #              t  r            b  l
        padding_outer=(1, len(INDENT), 0, len(INDENT)),
    )

    if destination.exists() and force is False:
        console.print(
            f"{INDENT * 2}[red]Warning:[/red] File {text_filename} exists. Skipping!"
        )
        return

    destination.write_text(print_settings.dump())


def save_config_file(
    destination: Path | None = None,
    create_destination: bool = True,
    force: bool = False,
) -> None:
    style1 = "cyan"
    style2 = "yellow"

    source = ConfigManager.DEFAULT_LOCATION

    destination = destination or App.PATH_USER_DATA
    destination = destination.resolve()

    config_file = destination / source.name

    text_destination = f"[{style2}]{helpers.format_path(destination)}[/{style2}]"

    ui.print_panel(
        f"[{style1}]Initializing user config file in {text_destination}...[/{style1}]",
        #              t  r            b  l
        padding_outer=(1, len(INDENT), 0, len(INDENT)),
    )

    helpers.copy_file(source, destination, create_destination, force)

    # Build Config Header --------------------------------------------------------------

    width = 100
    comment_prefix = "# "

    panel_config_header = Panel(
        "\n".join(
            [
                App.NAME_FULL,
                f"  Repo: {App.LINK_REPOSITORY}",
                f"  Docs: {App.LINK_DOCUMENTATION}",
            ]
        ),
        width=width - len(comment_prefix),
        padding=(1, 3),
        box=HEAVY,
    )

    # Capture the rendered output
    with console.capture() as capture:
        console.print(panel_config_header)

    panel_config_header = capture.get()
    panel_config_header = "\n".join(
        [f"{comment_prefix}{line}" for line in panel_config_header.splitlines()]
    )

    config_file.write_text(
        "".join(
            [
                f"{comment_prefix}{helpers.format_path(config_file)}",
                f"\n{comment_prefix}",
                f"\n{panel_config_header}",
                "\n",
                "\n",
                "\n",
                "\n",
                f"{config_file.read_text().strip()}",
            ]
        )
    )


def is_user_config_setup() -> bool:
    required_items = [
        App.PATH_USER_DATA,
        App.PATH_USER_DATA / App.NAME_CONFIG_FILE,
    ]

    # We need to initialize the application before editing the files.
    return all(item.exists() for item in required_items)


def print_auto_filling_note() -> None:
    config_filepaths = "\n  ".join(
        [
            helpers.format_path(filepath)
            for filepath in CONFIG.get_config_file_override_paths()
        ]
    )

    ui.print_panel(
        f"[cyan]Default print settings taken from:[/cyan]\n"
        f"[blue]  {config_filepaths}[/blue]\n"
        f"\n"
        f"[dim]Use [cyan]--ignore-defaults[/cyan] to ignore default print settings "
        f"or run [cyan]{App.NAME} edit[/cyan] to edit them.[/dim]",
    )


def prompt_date(date_template: str, date: str | None = None) -> str:
    # Initially we need to get the date template string from the user...
    if date is None:
        date = Prompt.ask(
            prompt=f"{INDENT * 3}Date template string",
            default=date_template,
        )
        date = datetime.now().strftime(date)

    else:
        # ...on a revising pass, we allow the user to edit the formatted date.
        date = Prompt.ask(
            prompt=f"{INDENT * 3}Current date",
            default=date,
        )

    return date


def prompt_print_settings(
    print_settings: PrintSettings,
    ignore_defaults: bool,
    add_date: bool,
    date_template: str,
    revising_pass: bool = False,
) -> PrintSettings:
    category = None
    first_line = True

    for setting in print_settings.iter_settings():
        if category != setting.category:
            category = setting.category

            new_line = "" if first_line is True else "\n"

            console.print(
                f"{new_line}{INDENT * 2}[magenta]{category.capitalize()} Settings[/magenta]"
            )

            first_line = False

        # Special handling for the date.
        if setting.name == Key.DATE:
            if add_date is True:
                print_settings.date = prompt_date(
                    date_template,
                    print_settings.date.value or None,  # pyright: ignore [reportArgumentType]
                )

            continue

        match setting.type:
            case i if i is int:
                prompt = IntPrompt
            case f if f is float:
                prompt = FloatPrompt
            case _:
                prompt = Prompt

        prompt_text = f"{INDENT * 3}{setting.description_formatted()}"

        match (revising_pass, ignore_defaults):
            case (True, False):
                default = setting.value or None
            case _:
                default = None

        reply = prompt.ask(prompt_text, default=default)

        setting.update(reply)

    return print_settings


def revise_print_settings(  # noqa: PLR0913, PLR0914, PLR0917
    print_settings: PrintSettings,
    ignore_defaults: bool,
    encoding: Encoding,
    with_units: bool,
    add_date: bool,
    date_template: str,
    filename_template: str,
    filename_transformations: list[StringTransformation],
    caption_templates: tuple[str, str],
) -> PrintSettings:
    color_style = "cyan"

    while True:
        qr_code_data = print_settings.to_encoded_str(encoding, with_units)

        qr_code = qr.generate_qr_code(
            qr_code_data,
            version=CONFIG.cfg.qr_code.version,
            error_correction=CONFIG.cfg.qr_code.error_correction.to_const(),
            module_size=CONFIG.cfg.qr_code.module_size,
            border=CONFIG.cfg.qr_code.border,
        )

        # Panel: QR Code data ----------------------------------------------------------

        qr_code_data_stats = " ".join(
            [
                f"mode:[yellow]{CONFIG.cfg.options.encoding.value}[/yellow]",
                f"bytes:[yellow]{len(qr_code_data)}[/yellow]",
            ]
        )

        # HACK: This ensures the minimum width of the panel is 25. Otherwise the title
        # or subtitle of the panel could be truncated.
        qr_code_data = f"{qr_code_data}\n{' ' * 25}"

        syntax_qr_code_data = Syntax(
            code=qr_code_data,
            lexer=encoding.lexer,
            theme="dracula",
            background_color="default",
        )

        # TODO: Can we set a minimum width on this?
        panel_qr_code_data = ui.panel(
            syntax_qr_code_data,
            title="Encoded Data",
            subtitle=qr_code_data_stats,
            #              t  r  b  l
            padding_outer=(1, 0, 1, 1),
        )

        # Panel/Table: QR Code ASCII preview -------------------------------------------

        template_context = print_settings.to_template_context()

        basename = helpers.generate_basename(
            template=filename_template,
            template_context=template_context,
            string_transformations=filename_transformations,
        )

        filename = f"filename:[yellow]{basename}{CONFIG.cfg.qr_code.format.to_suffix()}[/yellow]"

        caption = "\n".join(caption_templates).format(**template_context)

        qr_code_stats = " ".join(
            [
                f"version:[yellow]{qr_code.version}[/yellow]",
                f"modules:[yellow]{qr_code.modules_count}x{qr_code.modules_count}[/yellow]",
            ]
        )

        qr_code_ascii = qr.to_ascii(qr_code)

        table_qr_code = Table.grid(pad_edge=True, padding=1)
        table_qr_code.add_column(justify="center")
        table_qr_code.add_row(qr_code_ascii)
        table_qr_code.add_row(caption)

        panel_qr_code = ui.panel(
            table_qr_code,
            title=filename,
            subtitle=qr_code_stats,
            #        t  r  b  l
            padding=(2, 6, 0, 6),
            #              t  r  b  l
            padding_outer=(1, 1, 1, len(INDENT)),
        )

        # ------------------------------------------------------------------------------

        if CONFIG.debug is False:
            console.clear()
            console.print()

        console.print(
            Columns(
                [
                    panel_qr_code,
                    panel_qr_code_data,
                ],
                padding=0,
            ),
        )

        # ------------------------------------------------------------------------------

        reply = Prompt.ask(
            f"{INDENT * 2}[magenta]Generate [Gg] / Revise [Rr] / Abort [Aa][/magenta]",
            choices=["G", "R", "A"],
            show_choices=False,
            case_sensitive=False,
        )

        if reply == "R":
            if CONFIG.debug is False:
                console.clear()
                console.print()

            ui.print_panel(
                f"[{color_style}]Revising QR Code data.[/{color_style}] "
                f"[dim]Fields have been auto-filled from initial pass.[/dim]",
            )

            print_settings = prompt_print_settings(
                print_settings=print_settings,
                add_date=add_date,
                date_template=date_template,
                ignore_defaults=ignore_defaults,
                revising_pass=True,
            )
        elif reply == "A":
            sys.exit(-1)
        else:
            break

    return print_settings
