from __future__ import annotations

from io import StringIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from qrcode.main import QRCode

from . import ui
from .config import CONFIG
from .settings import PrintSettings
from .shared import App, Encoding


def generate_and_save_qr_code(  # noqa: PLR0913, PLR0917
    print_settings: PrintSettings,
    add_caption: bool,
    with_units: bool,
    encoding: Encoding,
    output_directory: Path,
    filename_template: str,
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

    print_settings_dict = print_settings.to_format_dict()

    if add_caption:
        caption_line_one = caption_templates[0].format(**print_settings_dict)
        caption_line_two = caption_templates[1].format(**print_settings_dict)

        image = _add_caption_to_image(
            image=image,
            image_width=CONFIG.cfg.qr_code.max_width,
            image_height=CONFIG.cfg.qr_code.max_height,
            caption_line_one=caption_line_one,
            caption_line_two=caption_line_two,
        )

    filename_formatted = filename_template.format(**print_settings_dict)

    image_path = f"{filename_formatted}{CONFIG.cfg.qr_code.format.to_suffix()}"
    image_path = output_directory / image_path
    image.save(image_path)
    image.close()

    # Save a copy of the QR Code data in the output directory.
    config_path = f"{filename_formatted}.toml"
    config_path = output_directory / config_path
    config_path.write_text(print_settings.dump())

    # Save a copy of the QR Code data in the user data directory.
    history_path = App.PATH_USER_DATA / App.NAME_HISTORY_TOML
    history_path.write_text(print_settings.dump())

    ui.print_panel(
        f"QR Code and TOML config saved to [cyan]{image_path.parent}[/cyan]",
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
    image_width: int,
    image_height: int,
    caption_line_one: str,
    caption_line_two: str,
) -> Image.Image:
    font = ImageFont.truetype(
        font=str(App.PATH_FONT_CAPTION),
        size=CONFIG.cfg.qr_code.caption_size,
    )

    # Returns: (left, top, right, bottom)
    caption_bbox_line_one = font.getbbox(caption_line_one)
    caption_bbox_line_two = font.getbbox(caption_line_two)

    caption_bbox_line_one_width = int(
        caption_bbox_line_one[2] - caption_bbox_line_one[0]
    )
    caption_bbox_line_two_width = int(
        caption_bbox_line_two[2] - caption_bbox_line_two[0]
    )

    caption_bbox_line_one_height = int(
        caption_bbox_line_one[3] - caption_bbox_line_one[1]
    )
    caption_bbox_line_two_height = int(
        caption_bbox_line_two[3] - caption_bbox_line_two[1]
    )

    caption_bbox_width = max(
        caption_bbox_line_one_width,
        caption_bbox_line_two_width,
    )

    border_thickness = CONFIG.cfg.qr_code.border * CONFIG.cfg.qr_code.module_size

    caption_bbox_height = (
        CONFIG.cfg.qr_code.caption_padding_top
        + caption_bbox_line_one_height
        + CONFIG.cfg.qr_code.caption_line_spacing
        + caption_bbox_line_two_height
        + CONFIG.cfg.qr_code.caption_padding_bottom
    )

    image_width = max(
        image_width,
        image.width,
        caption_bbox_width + border_thickness,
    )

    image_height = max(
        image_height,
        image.height + caption_bbox_height + border_thickness,
    )

    image_with_caption = Image.new(
        "1",
        (image_width, image_height),
        "white",
    )

    # Create a new drawing context.
    image_draw = ImageDraw.Draw(image_with_caption)

    # Start drawing.
    y_draw_pos = 0
    image_with_caption.paste(
        image,
        (
            (image_width - image.width) // 2,
            y_draw_pos,
        ),
    )

    # Draw first line of text.
    y_draw_pos += (
        image.height
        + CONFIG.cfg.qr_code.caption_padding_top
        + caption_bbox_line_one_height
    )
    image_draw.text(
        (
            image_width / 2,
            y_draw_pos,
        ),
        caption_line_one,
        anchor="ms",
        fill="black",
        font=font,
    )

    # Draw second line of text.
    y_draw_pos += CONFIG.cfg.qr_code.caption_line_spacing + caption_bbox_line_two_height
    image_draw.text(
        (
            image_width / 2,
            y_draw_pos,
        ),
        caption_line_two,
        anchor="ms",
        fill="black",
        font=font,
    )

    return image_with_caption
