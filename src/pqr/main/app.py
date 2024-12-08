from __future__ import annotations

import shutil
import sys
from datetime import datetime

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
from .shared import App, Encoding, Key, console
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


def create_user_config(force: bool = False) -> None:
    style1 = "cyan"
    style2 = "yellow"

    text_user_files = helpers.format_path(App.PATH_USER_DATA)
    text_user_files = f"[{style2}]{text_user_files}[/{style2}]"

    ui.print_panel(
        f"[{style1}]Initializing user config file in {text_user_files}...[/{style1}]",
    )

    if not App.PATH_USER_DATA.exists():
        console.print(f"{INDENT}Created directory {text_user_files}.")

        App.PATH_USER_DATA.mkdir(parents=True)

    source = ConfigManager.DEFAULT_LOCATION
    destination = App.PATH_USER_DATA / source.name

    text_destination = f"[{style2}]{destination.name}[/{style2}]"

    if destination.exists() and not force:
        console.print(
            f"{INDENT}[red]Warning:[/red] File {text_destination} exists. Skipping!"
        )

        return

    shutil.copy(
        source,  # pyright: ignore [reportArgumentType, reportCallIssue]
        destination,
    )

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

    # ----------------------------------------------------------------------------------

    destination.write_text(
        "".join(
            [
                f"{comment_prefix}{helpers.format_path(destination)}",
                f"\n{comment_prefix}",
                f"\n{panel_config_header}",
                "\n",
                "\n",
                "\n",
                "\n",
                f"{destination.read_text().strip()}",
            ]
        )
    )

    console.print(f"{INDENT}Created file {text_destination}.")


def is_user_config_setup() -> bool:
    required_items = [
        App.PATH_USER_DATA,
        App.PATH_USER_DATA / App.NAME_CONFIG_TOML,
    ]

    # We need to initialize the application before editing the files.
    return all(item.exists() for item in required_items)


def print_auto_filling_note() -> None:
    config_filepath = helpers.format_path(CONFIG.filepath)
    ui.print_panel(
        f"[cyan]Default print settings taken from:[/cyan] [blue]{config_filepath}[/blue]\n"
        f"[dim]Use [cyan]--ignore-defaults[/cyan] to ignore default print settings [/dim]\n"
        f"[dim]or run [cyan]{App.NAME} edit[/cyan] to edit default print settings.[/dim]",
    )


def prompt_date(date_template: str, date: str | None = None) -> str:
    # Initially we need to get the date template string from the user...
    if date is None:
        date = Prompt.ask(
            prompt=f"{INDENT * 2}Date template string",
            default=date_template,
        )
        date = datetime.now().strftime(date)

    else:
        # ...on a revising pass, we allow the user to edit the formatted date.
        date = Prompt.ask(
            prompt=f"{INDENT * 2}Current date",
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
                f"{new_line}{INDENT}[magenta]{category.capitalize()} Settings[/magenta]"
            )

            first_line = False

        # Special handling for the date.
        if setting.name == Key.DATE:
            if add_date is True:
                setting.value = prompt_date(
                    date_template=date_template,
                    date=setting.value,
                )

            continue

        match setting.type:
            case i if i is int:
                prompt = IntPrompt
            case f if f is float:
                prompt = FloatPrompt
            case _:
                prompt = Prompt

        prompt_text = f"{INDENT * 2}{setting.description_formatted()}"
        default = setting.value if (revising_pass or ignore_defaults is False) else None

        reply = prompt.ask(prompt_text, default=default)

        if isinstance(reply, str):
            reply = reply.strip()

        setting.update(reply)

    return print_settings


def revise_print_settings(  # noqa: PLR0913, PLR0917
    print_settings: PrintSettings,
    ignore_defaults: bool,
    encoding: Encoding,
    add_date: bool,
    date_template: str,
    filename_template: str,
    caption_templates: tuple[str, str],
) -> PrintSettings:
    color_style = "cyan"

    while True:
        qr_code_data = print_settings.to_encoded_str(encoding)

        qr_code = qr.generate_qr_code(
            qr_code_data,
            module_size=CONFIG.cfg.qr_code.module_size,
            border=CONFIG.cfg.qr_code.border,
            error_correction=CONFIG.cfg.qr_code.error_correction.to_const(),
        )

        qr_code.make()

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
            padding=(2, 6),
        )

        # Panel/Table: QR Code ASCII preview -------------------------------------------

        filename = filename_template.format(**print_settings.to_format_dict())
        filename = f"filename:[yellow]{filename}{CONFIG.cfg.qr_code.format.to_suffix()}[/yellow]"

        caption = "\n".join(caption_templates).format(**print_settings.to_format_dict())

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
            # top, right, bottom, left
            padding=(
                2,
                6,
                1,
                6,
            ),
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
            f"{INDENT}[magenta]Continue [Cc] or Revise [Rr][/magenta]",
            choices=["C", "R"],
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
        else:
            break

    return print_settings