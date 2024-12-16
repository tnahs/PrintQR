from __future__ import annotations

from io import StringIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from qrcode.main import QRCode

from . import helpers, ui
from .config import CONFIG
from .settings import PrintSettings
from .shared import App, Encoding, StringTransformation
from .ui import INDENT


def generate_and_save_qr_code(  # noqa: PLR0913, PLR0917
    print_settings: PrintSettings,
    add_caption: bool,
    with_units: bool,
    encoding: Encoding,
    output_directory: Path,
    filename_template: str,
    filename_transformations: list[StringTransformation],
    caption_templates: tuple[str, str],
) -> None:
    qr_code_data = print_settings.to_encoded_str(encoding, with_units)

    qr_code = generate_qr_code(
        qr_code_data,
        version=CONFIG.cfg.qr_code.version,
        error_correction=CONFIG.cfg.qr_code.error_correction.to_const(),
        module_size=CONFIG.cfg.qr_code.module_size,
        border=CONFIG.cfg.qr_code.border,
    )

    image = qr_code.make_image().get_image()

    template_context = print_settings.to_template_context()

    if add_caption:
        caption_line_one = caption_templates[0].format(**template_context)
        caption_line_two = caption_templates[1].format(**template_context)

        image = _add_caption_to_image(
            image,
            caption_line_one,
            caption_line_two,
        )

    basename = helpers.generate_basename(
        template=filename_template,
        template_context=template_context,
        string_transformations=filename_transformations,
    )

    image_path = output_directory / f"{basename}{CONFIG.cfg.qr_code.format.to_suffix()}"
    image.save(image_path)
    image.close()

    # Save a copy of the QR Code data in the output directory.
    config_path = output_directory / f"{basename}.toml"
    config_path.write_text(print_settings.dump())

    # Save a copy of the QR Code data in the user data directory.
    history_path = App.PATH_USER_DATA / App.NAME_HISTORY_TOML
    history_path.write_text(print_settings.dump())

    ui.print_panel(
        f"QR Code and TOML config saved to [cyan]{image_path.parent}[/cyan]",
        #              t  r            b  l
        padding_outer=(1, len(INDENT), 0, len(INDENT)),
    )

    with Image.open(image_path) as img:
        img.show()


def generate_qr_code(
    data: str,
    version: int | str,
    error_correction: int,
    module_size: int,
    border: int,
) -> QRCode:
    qr_code = QRCode(
        box_size=module_size,
        border=border,
        error_correction=error_correction,
    )

    qr_code.add_data(data)

    if isinstance(version, int):
        qr_code.version = version
        qr_code.make()
    else:
        qr_code.version = None
        qr_code.make(fit=True)

    return qr_code


def to_ascii(qr_code: QRCode) -> str:
    with StringIO() as output:
        qr_code.print_ascii(out=output)
        qr_code_ascii = output.getvalue()

    qr_code_ascii = qr_code_ascii.split("\n")

    # If the last contains no characters remove it.
    if not qr_code_ascii[-1].strip():
        qr_code_ascii.pop()

    return "\n".join(qr_code_ascii)


def _add_caption_to_image(
    image: Image.Image,
    caption_line_one: str,
    caption_line_two: str,
) -> Image.Image:
    border_thickness = CONFIG.cfg.qr_code.border * CONFIG.cfg.qr_code.module_size

    font_size = _get_font_size(
        image.width,
        border_thickness,
        caption_line_one,
        caption_line_two,
    )

    font = ImageFont.truetype(
        font=str(App.PATH_FONT_CAPTION),
        size=font_size,
    )

    caption_bbox_height = (
        CONFIG.cfg.caption.padding_top
        + font_size
        + CONFIG.cfg.caption.line_spacing
        + font_size
        + CONFIG.cfg.caption.padding_bottom
    )

    image_height = image.height + caption_bbox_height + border_thickness

    image_with_caption = Image.new(
        "1",
        (image.width, image_height),
        "white",
    )

    # Create a new drawing context.
    image_draw = ImageDraw.Draw(image_with_caption)

    # Start drawing.

    y_draw_pos = 0

    image_with_caption.paste(
        image,
        (0, y_draw_pos),
    )

    # Draw first line of text.

    y_draw_pos += image.height + CONFIG.cfg.caption.padding_top + font_size

    image_draw.text(
        (
            image.width // 2,
            y_draw_pos,
        ),
        caption_line_one,
        anchor="ms",
        fill="black",
        font=font,
    )

    # Draw second line of text.

    y_draw_pos += CONFIG.cfg.caption.line_spacing + font_size

    image_draw.text(
        (
            image.width // 2,
            y_draw_pos,
        ),
        caption_line_two,
        anchor="ms",
        fill="black",
        font=font,
    )

    return image_with_caption


def _get_font_size(
    image_width: int,
    border_thickness: int,
    caption_line_one: str,
    caption_line_two: str,
) -> int:
    font_size_max = CONFIG.cfg.caption.font_size_max
    font_size = font_size_max

    while True:
        font = ImageFont.truetype(
            font=str(App.PATH_FONT_CAPTION),
            size=font_size,
        )

        bbox_line_one = font.getbbox(caption_line_one)
        bbox_line_one_width = int(bbox_line_one[2] - bbox_line_one[0])

        bbox_line_two = font.getbbox(caption_line_two)
        bbox_line_two_width = int(bbox_line_two[2] - bbox_line_two[0])

        bbox_width = max(bbox_line_one_width, bbox_line_two_width)

        if bbox_width + border_thickness <= image_width:
            # Print a warning if the font size had to be reduced.
            if font_size < font_size_max:
                ui.print_panel(
                    f"The caption font size was reduced from [green]{font_size_max}[/green] "
                    f"to [red]{font_size}[/red] to fit the caption text.",
                    title="Warning",
                    border_style="red",
                    #              t  r            b  l
                    padding_outer=(1, len(INDENT), 0, len(INDENT)),
                )

            return font_size

        font_size -= 1

        if font_size < 1:
            raise ValueError("Font size became too small to fit the caption text.")
