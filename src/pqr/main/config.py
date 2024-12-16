from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import (
    AliasGenerator,
    BaseModel,
    ConfigDict,
    ValidationError,
    conint,
    field_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError

from . import helpers
from .errors import ConfigReadError, ConfigValidationError
from .settings import PRINT_SETTINGS, SerializedSettings, Setting
from .shared import (
    QR_CODE_VERSION_MAX,
    QR_CODE_VERSION_MIN,
    App,
    Encoding,
    ErrorCorrection,
    ImageFormat,
    Key,
    StringTransformation,
)


QrCodeVersion = (
    conint(
        ge=QR_CODE_VERSION_MIN,
        le=QR_CODE_VERSION_MAX,
    )
    | Literal[Key.FIT]
)


class BaseConfig(BaseModel):
    # Accept both `field-name` and `field_name` as valid keys.
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=helpers.snake_to_kebab,
            serialization_alias=helpers.kebab_to_snake,
        )
    )


class Options(BaseConfig):
    encoding: Encoding
    with_units: bool
    add_caption: bool
    add_date: bool


class Template(BaseConfig):
    filename: str
    filename_transformations: list[StringTransformation]
    caption_line_one: str
    caption_line_two: str
    date: str


class Caption(BaseConfig):
    font_size_max: int
    padding_top: int
    padding_bottom: int
    line_spacing: int


class QRCode(BaseConfig):
    format: ImageFormat
    version: QrCodeVersion  # pyright: ignore [reportInvalidTypeForm]
    module_size: int
    border: int
    error_correction: ErrorCorrection


class Slicer(BaseConfig):
    executable: str


class Config(BaseConfig):
    options: Options
    template: Template
    caption: Caption
    qr_code: QRCode
    slicer: Slicer
    print_settings: dict

    @classmethod
    @field_validator("print_settings")
    def validate_print_settings(cls, data: SerializedSettings) -> dict:
        errors: list[InitErrorDetails] = []

        for category, settings in data.items():
            for setting_name, setting_value in settings.items():
                path = Setting.build_fully_qualified_path(
                    category,
                    setting_name,
                )

                setting = PRINT_SETTINGS.get(path)

                if setting is None:
                    errors.append(
                        InitErrorDetails(
                            type=PydanticCustomError(
                                "invalid_key",
                                "Invalid key [green]'{setting_name}'[/green].",  # noqa: RUF027
                                {
                                    "setting_name": setting_name,
                                },
                            ),
                            loc=(category,),
                            input=setting_name,
                        )
                    )
                    continue

                if not isinstance(setting_value, setting.type):
                    errors.append(
                        InitErrorDetails(
                            type=PydanticCustomError(
                                "type_error",
                                "Input should be a valid {setting_value_type}, unable to interpret input.",
                                {
                                    "setting_value_type": setting.type.__name__,
                                },
                            ),
                            loc=(f"{category}.{setting_name}",),
                            input=setting_value,
                        )
                    )

            if errors:
                raise ValidationError.from_exception_data(
                    title=cls.__name__,
                    line_errors=errors,
                )

        return data


class ConfigManager:
    DEFAULT_LOCATION = App.PATH_DATA / App.NAME_CONFIG_FILE
    OVERRIDE_LOCATIONS = (
        App.PATH_USER_DATA / App.NAME_CONFIG_FILE,
        Path.cwd() / App.NAME_CONFIG_FILE,
    )

    __debug: bool = False
    __inner: Config

    @property
    def cfg(self) -> Config:
        return self._inner

    @property
    def debug(self) -> bool:
        return self.__debug

    @debug.setter
    def debug(self, value: bool) -> None:
        self.__debug = value

    def load(self, user: bool = False) -> None:
        filepaths = [self.DEFAULT_LOCATION]

        if user is True:
            filepaths.extend(self.get_config_file_override_paths())

        config = {}

        for filepath in filepaths:
            data = read_serialized_data(filepath)
            config = helpers.merge_dicts(config, data)

            try:
                self.__inner = Config(**config)
            except ValidationError as error:
                raise ConfigValidationError(error, filepath) from error

        PRINT_SETTINGS.update(data=self.__inner.print_settings)

    def get_config_file_override_paths(self) -> list[Path]:
        paths = []

        for location in self.OVERRIDE_LOCATIONS:
            if location.exists():
                paths.append(location)

        return paths

    @property
    def _inner(self) -> Config:
        if not self.__inner:
            self.load()

        return self.__inner


# TODO: This and `helpers.read_serialized_data` should maybe go somewhere else?
def read_serialized_data(path: Path) -> dict:
    try:
        return helpers.read_serialized_data(path)
    except Exception as error:
        raise ConfigReadError(error, path) from error


CONFIG = ConfigManager()
