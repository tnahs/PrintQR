from __future__ import annotations

from pathlib import Path

from pydantic import (
    AliasGenerator,
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError

from . import helpers
from .errors import ConfigReadError, ConfigValidationError
from .settings import PRINT_SETTINGS, SerializedSettings, Setting
from .shared import App, Encoding, ErrorCorrection, ImageFormat


class BaseConfig(BaseModel):
    # Allow reading `field-name` and `field_name` as identical.
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=helpers.snake_to_kebab,
            serialization_alias=helpers.kebab_to_snake,
        )
    )


class Options(BaseConfig):
    add_caption: bool
    add_date: bool
    encoding: Encoding


class Template(BaseConfig):
    filename: str
    caption_line_one: str
    caption_line_two: str
    date: str


class Slicer(BaseConfig):
    executable: str


class QRCode(BaseConfig):
    format: ImageFormat
    max_width: int
    max_height: int
    module_size: int
    border: int
    error_correction: ErrorCorrection
    caption_size: int
    caption_padding_top: int
    caption_padding_bottom: int
    caption_line_spacing: int


class Config(BaseConfig):
    options: Options
    template: Template
    slicer: Slicer
    qr_code: QRCode
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
    DEFAULT_LOCATION = App.PATH_DATA / App.NAME_CONFIG_TOML
    LOCATIONS = (
        Path.cwd() / App.NAME_CONFIG_TOML,
        App.PATH_USER_DATA / App.NAME_CONFIG_TOML,
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

    @property
    def filepath(self) -> Path:
        return self._get_config_toml()

    def load(self, user: bool = False) -> None:
        config = helpers.read_serialized_data(
            self.DEFAULT_LOCATION  # pyright: ignore [reportArgumentType]
        )

        if user is True:
            config_user = read_serialized_data(self.filepath)
            # TODO: Check if we lose key:value pairs during update.
            config.update(config_user)

        try:
            self.__inner = Config(**config)
        except ValidationError as error:
            raise ConfigValidationError(error, self.filepath) from error

        PRINT_SETTINGS.update(data=self.__inner.print_settings)

    @property
    def _inner(self) -> Config:
        if not self.__inner:
            self.load()

        return self.__inner

    @classmethod
    def _get_config_toml(cls) -> Path:
        path = cls.DEFAULT_LOCATION

        for location in cls.LOCATIONS:
            if location.exists():
                path = location
                break

        return path  # pyright: ignore [reportReturnType]


# TODO: This and `helpers.read_serialized_data` should maybe go somewhere else?
def read_serialized_data(path: Path) -> dict:
    try:
        return helpers.read_serialized_data(path)
    except Exception as error:
        raise ConfigReadError(error, path) from error


CONFIG = ConfigManager()
