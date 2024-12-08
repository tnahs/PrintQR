from __future__ import annotations

import inspect
import sys
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from inspect import Parameter, Signature
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated

from typer import Argument, BadParameter, Exit, Option, Typer

from . import app, errors, helpers, qr, ui
from .config import CONFIG, read_serialized_data
from .errors import ConfigReadError
from .settings import PRINT_SETTINGS, Setting
from .shared import App, Delimeter, Encoding, Key, console
from .tables import TABLE_TEMPLATES_DATE, TABLE_TEMPLATES_FIELDS


cli = Typer(
    add_completion=False,
    no_args_is_help=True,
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
    rich_markup_mode="rich",
    help="Generate QR Codes for 3d prints",
)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"{App.NAME_FULL} [green]v{App.VERSION}[/green]")
        raise Exit()


@cli.callback()
def main_cli(
    _: Annotated[
        bool,
        Option(
            "-v",
            "--version",
            help="Print version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
    debug: Annotated[
        bool,
        Option(
            "-d",
            "--debug",
            help="Print debug info.",
        ),
    ] = False,
) -> None:
    CONFIG.debug = debug


# Validation ---------------------------------------------------------------------------


def validate_template_string(value: str | list[str] | None) -> str | list[str] | None:
    if value is None:
        return value

    strings = [value] if isinstance(value, str) else value

    for string in strings:
        try:
            string.format(**PRINT_SETTINGS.to_format_dict())
        except Exception as error:
            raise BadParameter(string) from error

    return value


def validate_date_template(value: str | None) -> str | None:
    if value is None:
        return None

    try:
        datetime.now().strftime(value)
    except Exception as error:
        raise BadParameter(value) from error

    return value


# Shared Args --------------------------------------------------------------------------


arg_output_directory = Option(
    "-o",
    "--output",
    help="File output directory.",
    show_default=False,
)

arg_ignore_defaults = Option(
    "-d",
    "--ignore-defaults",
    help=f"Ignore default print settings in [green]{App.NAME_CONFIG_TOML}[/green].",
    show_default=False,
)

arg_encoding = Option(
    "-e",
    "--encoding",
    help="Encoding method used for the QR Code's data.",
    show_default=False,
)

arg_add_caption = Option(
    "--add-caption/--no-caption",
    help="Add a two-line caption to the QR Code.",
    show_default=False,
)

arg_add_date = Option(
    "--add-date/--no-date",
    help="Add the current date into the QR Code's data.",
    show_default=False,
)

arg_date_template = Option(
    "--date-template",
    help="Template used to generate the date. Uses strftime [yellow]strftime[/yellow].",
    show_default=False,
    callback=validate_date_template,
)

arg_filename_template = Option(
    "--filename-template",
    help="Template used to generate image, TOML and GCode filenames.",
    show_default=False,
    callback=validate_template_string,
)

arg_caption_templates = Option(
    "--caption-template",
    min=2,
    max=2,
    help="Templates used to generate the caption. As: [yellow]'{line-one} {line-two}'[/yellow]",
    show_default=False,
    callback=validate_template_string,
)


# NOTE: Until theres a better way to share command level args this is the simplest way
# we can process shared args between different commands.
#
# TODO: It might be a better idea to set the `CONFIG` value so we don't have to keep
# passing around the variables. As we add more options the list of parameters will
# expand and it would be much better it either pass a `Config` object ot just access
# the global CONFIG.
def process_shared_args(  # noqa: PLR0913, PLR0917
    output_directory: Path,
    ignore_defaults: bool,
    encoding: Encoding | None,
    add_caption: bool | None,
    add_date: bool | None,
    date_template: str | None,
    filename_template: str | None,
    caption_templates: tuple[str, str] | None,
) -> SimpleNamespace:
    if not app.is_user_config_setup():
        app.create_user_config()

    if CONFIG.debug is False:
        console.clear()
        console.print()

    output_directory = output_directory.resolve()

    if ignore_defaults is False:
        app.load_config(user=True)
        app.print_auto_filling_note()

    encoding = encoding or CONFIG.cfg.options.encoding
    add_caption = (
        add_caption if add_caption is not None else CONFIG.cfg.options.add_caption
    )
    add_date = add_date if add_date is not None else CONFIG.cfg.options.add_date
    date_template = date_template or CONFIG.cfg.template.date
    filename_template = filename_template or CONFIG.cfg.template.filename
    caption_templates = caption_templates or (
        CONFIG.cfg.template.caption_line_one,
        CONFIG.cfg.template.caption_line_two,
    )

    namespace = SimpleNamespace(
        output_directory=output_directory,
        ignore_defaults=ignore_defaults,
        encoding=encoding,
        add_caption=add_caption,
        add_date=add_date,
        date_template=date_template,
        filename_template=filename_template,
        caption_templates=caption_templates,
    )

    if CONFIG.debug:
        ui.print_panel(
            namespace.__dict__,
            pretty=True,
            title="Shared Command Args",
            border_style="red",
        )

    return namespace


# Command: prompts ---------------------------------------------------------------------


@cli.command(
    name="prompts",
    no_args_is_help=True,
    short_help="...from commandline [green]prompts[/green].",
    rich_help_panel="Generate",
)
def run_command_generate_from_prompts(  # noqa: PLR0913, PLR0917
    output_directory: Annotated[
        Path,
        arg_output_directory,
    ],
    ignore_defaults: Annotated[
        bool,
        arg_ignore_defaults,
    ] = False,
    encoding: Annotated[
        Encoding | None,
        arg_encoding,
    ] = None,
    add_caption: Annotated[
        bool | None,
        arg_add_caption,
    ] = None,
    add_date: Annotated[
        bool | None,
        arg_add_date,
    ] = None,
    date_template: Annotated[
        str | None,
        arg_date_template,
    ] = None,
    filename_template: Annotated[
        str | None,
        arg_filename_template,
    ] = None,
    caption_templates: Annotated[
        tuple[str, str] | None,
        arg_caption_templates,
    ] = None,
) -> None:
    """Generate a QR Code from commandline [green]prompts[/green]."""

    args = process_shared_args(
        output_directory,
        ignore_defaults,
        encoding,
        add_caption,
        add_date,
        date_template,
        filename_template,
        caption_templates,
    )

    print_settings = app.prompt_print_settings(
        PRINT_SETTINGS,
        args.ignore_defaults,
        args.add_date,
        args.date_template,
    )

    print_settings = app.revise_print_settings(
        print_settings,
        args.ignore_defaults,
        args.encoding,
        args.add_date,
        args.date_template,
        args.filename_template,
        args.caption_templates,
    )

    qr.generate_and_save_qr_code(
        print_settings,
        args.add_caption,
        args.encoding,
        args.output_directory,
        args.filename_template,
        args.caption_templates,
    )


# Command: args ------------------------------------------------------------------------


def run_command_generate_from_args(  # noqa: PLR0913, PLR0917
    output_directory: Annotated[
        Path,
        arg_output_directory,
    ],
    ignore_defaults: Annotated[
        bool,
        arg_ignore_defaults,
    ] = False,
    encoding: Annotated[
        Encoding | None,
        arg_encoding,
    ] = None,
    add_caption: Annotated[
        bool | None,
        arg_add_caption,
    ] = None,
    add_date: Annotated[
        bool | None,
        arg_add_date,
    ] = None,
    date_template: Annotated[
        str | None,
        arg_date_template,
    ] = None,
    filename_template: Annotated[
        str | None,
        arg_filename_template,
    ] = None,
    caption_templates: Annotated[
        tuple[str, str] | None,
        arg_caption_templates,
    ] = None,
    **print_settings,  # noqa: ANN003
) -> None:
    """Generate a QR Code from commandline [green]args[/green]."""

    args = process_shared_args(
        output_directory,
        ignore_defaults,
        encoding,
        add_caption,
        add_date,
        date_template,
        filename_template,
        caption_templates,
    )

    # Convert the flattened dictionary into a nested one for updaing `PRINT_SETTINGS`.
    data = defaultdict(dict)
    for path, value in print_settings.items():
        # This can throw an error but it should never happen as we're just reversing
        # what's done in the wrapper function below. If it errors out it's a bug.
        category, name = Setting.deconstruct_fully_qualified_path(
            path, delimeter=Delimeter.SNAKE
        )

        data[category][name] = value

    # TODO: We need to run validation before this data is used for updating.
    PRINT_SETTINGS.update(data)

    if add_date is True:
        PRINT_SETTINGS.stamp_date(args.date_template)

    print_settings = app.revise_print_settings(
        PRINT_SETTINGS,
        args.ignore_defaults,
        args.encoding,
        args.add_date,
        args.date_template,
        args.filename_template,
        args.caption_templates,
    )

    qr.generate_and_save_qr_code(
        print_settings,
        args.add_caption,
        args.encoding,
        args.output_directory,
        args.filename_template,
        args.caption_templates,
    )


def _wrapper_run_command_generate_from_args() -> Callable:
    # Get original parameters.

    #   `eval_str` controls whether or not values of type `str` are replaced with the
    #   result of calling eval() on those values.
    #
    # https://docs.python.org/3/library/inspect.html#inspect.get_annotations
    # https://docs.python.org/3/library/inspect.html#inspect.signature
    original_parameters = inspect.signature(
        run_command_generate_from_args,
        eval_str=True,
    )

    original_parameters = dict(original_parameters.parameters.items())

    # This entry is deleted as we'll be building these args in the loop below.
    del original_parameters["print_settings"]

    original_parameters = list(original_parameters.values())

    # Compile print settings.
    print_settings = []

    # Build a list of parameters to inject into the generate from args function.
    for setting in PRINT_SETTINGS.iter_settings():
        # Special handling for the date. Ignore!
        if setting.name == Key.DATE:
            continue

        parameter = Parameter(
            name=setting.path_normalized,
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Annotated[
                setting.type,
                Option(
                    help=setting.description_formatted(),
                    rich_help_panel="Print Settings",
                    show_default=False,
                ),
            ],
            default=setting.value or None,
        )

        print_settings.append(parameter)

    parameters = original_parameters + print_settings

    run_command_generate_from_args.__signature__ = Signature(parameters)  # type: ignore

    return run_command_generate_from_args


cli.command(
    name="args",
    no_args_is_help=True,
    short_help="...from commandline [green]args[/green].",
    rich_help_panel="Generate",
)(_wrapper_run_command_generate_from_args())


# Command: config ----------------------------------------------------------------------


@cli.command(
    name="encoded",
    no_args_is_help=True,
    short_help="...from [green]TOML encoded[/green] data.",
    rich_help_panel="Generate",
)
def run_command_generate_from_encoded(  # noqa: PLR0913, PLR0917
    path: Annotated[
        Path,
        Option(
            "-i",
            "--input",
            help="Path to a file with [green]TOML encoded[/green] data.",
            show_default=False,
        ),
    ],
    output_directory: Annotated[
        Path,
        arg_output_directory,
    ],
    ignore_defaults: Annotated[
        bool,
        arg_ignore_defaults,
    ] = False,
    encoding: Annotated[
        Encoding | None,
        arg_encoding,
    ] = None,
    add_caption: Annotated[
        bool | None,
        arg_add_caption,
    ] = None,
    add_date: Annotated[
        bool | None,
        arg_add_date,
    ] = None,
    date_template: Annotated[
        str | None,
        arg_date_template,
    ] = None,
    filename_template: Annotated[
        str | None,
        arg_filename_template,
    ] = None,
    caption_templates: Annotated[
        tuple[str, str] | None,
        arg_caption_templates,
    ] = None,
) -> None:
    """Generate a QR Code from [green]TOML encoded[/green] data."""

    args = process_shared_args(
        output_directory,
        ignore_defaults,
        encoding,
        add_caption,
        add_date,
        date_template,
        filename_template,
        caption_templates,
    )

    try:
        data = read_serialized_data(path)
    except ConfigReadError as error:
        errors.print_config_read_error(error)
        sys.exit(-1)

    app.load_config(user=True)

    # TODO: We need to run validation before this data is used for updating.
    PRINT_SETTINGS.update(data)

    if add_date is True:
        PRINT_SETTINGS.stamp_date(args.date_template)

    print_settings = app.revise_print_settings(
        PRINT_SETTINGS,
        args.ignore_defaults,
        args.encoding,
        args.add_date,
        args.date_template,
        args.filename_template,
        args.caption_templates,
    )

    qr.generate_and_save_qr_code(
        print_settings,
        args.add_caption,
        args.encoding,
        args.output_directory,
        args.filename_template,
        args.caption_templates,
    )


# Command: init ------------------------------------------------------------------------


@cli.command(
    name="init",
    short_help="Create user config file.",
    rich_help_panel="Application",
)
def run_command_init(
    force: Annotated[
        bool,
        Option(
            "--force",
            help="Overwrite existing file.",
        ),
    ] = False,
) -> None:
    """Create user config file."""

    app.create_user_config(force)


# Command: print -----------------------------------------------------------------------


class ChoiceReferenceTable(StrEnum):
    DATE = "date"
    FIELDS = "fields"


@cli.command(
    name="info",
    no_args_is_help=True,
    short_help="Print reference tables.",
    rich_help_panel="Other",
)
def run_command_info(
    table: Annotated[
        ChoiceReferenceTable,
        Argument(
            help="Select reference table to print.",
            show_default=False,
        ),
    ],
) -> None:
    """Print reference tables."""

    app.load_config(user=True)

    match table:
        case ChoiceReferenceTable.DATE:
            console.print(TABLE_TEMPLATES_DATE)
        case ChoiceReferenceTable.FIELDS:
            console.print(TABLE_TEMPLATES_FIELDS)


# Command: edit ------------------------------------------------------------------------


@cli.command(
    name="edit",
    short_help="Edit user config file.",
    rich_help_panel="Application",
)
def edit() -> None:
    """Edit user config file."""

    if not app.is_user_config_setup():
        app.create_user_config()

    helpers.edit_file(App.PATH_USER_DATA / App.NAME_CONFIG_TOML)
