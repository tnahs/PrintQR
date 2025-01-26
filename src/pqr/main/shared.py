from __future__ import annotations

import re
import unicodedata
from enum import StrEnum
from importlib import metadata, resources
from pathlib import Path
from typing import TYPE_CHECKING, Any

import qrcode.constants
from rich.console import Console

from .lexer import CompactLexer


# Console ----------------------------------------------------------------------------
if TYPE_CHECKING:
    from pygments.lexer import Lexer




console = Console()


# Constants ----------------------------------------------------------------------------


class App:
    NAME = "pqr"
    NAME_FULL = "PrintQR"

    VERSION = metadata.version(NAME)
    LINK_REPOSITORY = f"https://github.com/tnahs/{NAME_FULL}"
    LINK_DOCUMENTATION = f"https://tnahs.github.io/{NAME_FULL}"

    PATH_ROOT = Path(resources.files(NAME))  # pyright: ignore [reportArgumentType]
    PATH_DATA = PATH_ROOT / "data"
    PATH_USER_DATA = Path.home() / f".{NAME}"

    PATH_RESOURCES = PATH_ROOT / "resources"
    PATH_FONTS = PATH_RESOURCES / "fonts"
    PATH_FONT_CAPTION = PATH_FONTS / "better-vcr.ttf"

    NAME_CONFIG_FILE = "pqr.toml"
    NAME_HISTORY_FILE = "history.toml"
    NAME_PRINT_SETTINGS_FILE = "print-settings.toml"

    DEFAULT_EDITOR = "vi"


QR_CODE_VERSION_MIN = 1
QR_CODE_VERSION_MAX = 40


# Types --------------------------------------------------------------------------------


# Not a great solution, but it keeps the type checker happy.
Kwargs = Any


# Enums --------------------------------------------------------------------------------


class Key:
    DATE = "date"
    FIT = "fit"


class ConfigFormat(StrEnum):
    TOML = ".toml"
    YAML = ".yaml"
    JSON = ".json"


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


class Unit(StrEnum):
    FLOW = "mm³/s"
    LENGTH = "mm"
    TEMPERATURE = "°C"


class Encoding(StrEnum):
    TOML = "toml"
    COMPACT = "compact"

    @property
    def lexer(self) -> str | Lexer:
        match self:
            case Encoding.TOML:
                return "toml"
            case _:
                return CompactLexer()


class Delimeter(StrEnum):
    SNAKE = "_"
    KEBAB = "-"


class StringTransformation(StrEnum):
    TO_ASCII = "to-ascii"
    TO_LOWERCASE = "to-lowercase"
    REMOVE_SPACES = "remove-spaces"
    SPACES_TO_DASHES = "spaces-to-dashes"
    SPACES_TO_UNDERSCORES = "spaces-to-underscores"

    @classmethod
    def choices(cls) -> list[str]:
        return [variant.value for variant in cls]

    @property
    def description(self) -> str:
        match self:
            case StringTransformation.TO_ASCII:
                return "Convert all text to ASCII. "
            case StringTransformation.TO_LOWERCASE:
                return "Lowercase all text. "
            case StringTransformation.REMOVE_SPACES:
                return "Remove all spaces. "
            case StringTransformation.SPACES_TO_DASHES:
                return "Replace all spaces with dashes. "
            case StringTransformation.SPACES_TO_UNDERSCORES:
                return "Replace all spaces with underscores. "
            case _:
                raise ValueError(f"Missing description for: {self}")

    def apply(self, string: str) -> str:
        match self:
            case StringTransformation.TO_ASCII:
                return (
                    unicodedata.normalize("NFKD", string)
                    .encode("ascii", "ignore")
                    .decode("ascii")
                )
            case StringTransformation.TO_LOWERCASE:
                return string.lower()
            case StringTransformation.REMOVE_SPACES:
                return string.replace(" ", "")
            case StringTransformation.SPACES_TO_DASHES:
                return re.sub(r"[\s-]+", "-", string)
            case StringTransformation.SPACES_TO_UNDERSCORES:
                return re.sub(r"[\s_]+", "_", string)
            case _:
                raise ValueError(f"Missing implementation for: {self}")


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
