from __future__ import annotations

from enum import StrEnum
from importlib import metadata, resources
from pathlib import Path

import qrcode.constants
from rich.console import Console


# Console ----------------------------------------------------------------------------


console = Console()


# Constants ----------------------------------------------------------------------------


class App:
    NAME = "pqr"
    NAME_FULL = "PrintQR"

    VERSION = metadata.version(NAME)
    LINK_REPOSITORY = f"https://github.com/tnahs/{NAME_FULL}"
    LINK_DOCUMENTATION = f"https://tnahs.github.io/{NAME_FULL}"

    PATH_ROOT = resources.files(NAME)
    PATH_DATA = PATH_ROOT / "data"
    PATH_USER_DATA = Path.home() / f".{NAME}"

    PATH_RESOURCES = PATH_ROOT / "resources"
    PATH_FONTS = PATH_RESOURCES / "fonts"
    PATH_FONT_CAPTION = PATH_FONTS / "better-vcr.ttf"

    NAME_CONFIG_TOML = "config.toml"
    NAME_HISTORY_TOML = "history.toml"
    NAME_PRINT_SETTINGS_TOML = "print-settings.toml"

    DEFAULT_EDITOR = "vi"


QR_CODE_VERSION_MIN = 1
QR_CODE_VERSION_MAX = 40


# Enums --------------------------------------------------------------------------------


class Delimeter(StrEnum):
    SNAKE = "_"
    KEBAB = "-"


class Encoding(StrEnum):
    TOML = "toml"
    COMPACT = "compact"

    @property
    def lexer(self) -> str:
        match self:
            case Encoding.TOML:
                return "toml"
            case _:
                return "text"


class ImageFormat(StrEnum):
    PNG = "png"
    JPG = "jpg"

    def to_suffix(self) -> str:
        return f".{self.value}"


class ErrorCorrection(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    QUARTILE = "quartile"
    HIGH = "high"

    def to_const(self) -> int:
        match self:
            case self.LOW:
                return qrcode.constants.ERROR_CORRECT_L
            case self.MEDIUM:
                return qrcode.constants.ERROR_CORRECT_M
            case self.QUARTILE:
                return qrcode.constants.ERROR_CORRECT_Q
            case self.HIGH:
                return qrcode.constants.ERROR_CORRECT_H


class Unit(StrEnum):
    FLOW = "mm³/s"
    LENGTH = "mm"
    TEMPERATURE = "°C"


class Category(StrEnum):
    FILAMENT = "filament"
    PRINTER = "printer"
    SLICER = "slicer"
    MISC = "misc"

    # TODO: This might not be the best place for either of the follwing methods.

    @classmethod
    def paths(cls) -> list[str]:
        return [f"{variant.value}-name" for variant in cls]

    @property
    def placeholder(self) -> str:
        return f"[{self.value}]"


class ConfigFormat(StrEnum):
    TOML = ".toml"
    YAML = ".yaml"
    JSON = ".json"


class Key:
    DATE = "date"
    FIT = "fit"
