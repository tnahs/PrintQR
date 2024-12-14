from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime
from typing import Annotated, Any, Self

import tomli_w
from pydantic import (
    AliasGenerator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    field_serializer,
    model_validator,
)

from . import helpers
from .errors import InternalError
from .shared import App, Category, Delimeter, Encoding, Key, Unit


def _preprocess_type(value: str) -> type[Any]:
    try:
        return eval(value)
    except NameError:
        raise InternalError(f"Value '{value}' not a valid Python type.")  # noqa: B904


def _preprocess_none_type(value: str) -> str | None:
    if not value:
        return None

    return value


class Setting(BaseModel):
    # The setting's name
    name: str

    # The setting's category.
    category: Category

    # The setting's interal type.
    type: Annotated[
        type[Any],
        BeforeValidator(_preprocess_type),
    ]

    # A two-letter abbreviateion of the setting's name.
    compact_name: Annotated[
        str | None,
        BeforeValidator(_preprocess_none_type),
    ] = None

    # The setting's value. Any falsy types will be converted to `None`.
    value: Annotated[
        Any,
        BeforeValidator(_preprocess_none_type),
    ] = None

    # The setting's unit.
    unit: Annotated[
        Unit | None,
        BeforeValidator(_preprocess_none_type),
    ] = None

    # The setting's description.
    description: str = ""

    # Allow reading `field-name` and `field_name` as identical.
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=helpers.snake_to_kebab,
        )
    )

    def update(self, value: Any) -> None:
        self.value = value if value else None

    def clear(self) -> None:
        match self.type:
            case t if t is str:
                self.value = ""
            case t if t is int:
                self.value = 0
            case t if t is float:
                self.value = 0.0
            case _:
                raise TypeError(f"Unsupported type: {self.type}")

    @property
    def path(self) -> str:
        return self.build_fully_qualified_path(self.category, self.name)

    @property
    def path_normalized(self) -> str:
        return helpers.kebab_to_snake(self.path)

    @property
    def format_string(self) -> str:
        return f"{{{self.path}}}"

    @property
    def format_string_with_unit(self) -> str:
        return f"{{{self.path}}}{self.unit.value}" if self.unit else f"{{{self.path}}}"

    @property
    def value_with_unit(self) -> str:
        return f"{self.value}{self.unit.value}" if self.unit else self.value

    def description_formatted(
        self, titlecase: bool = True, add_unit: bool = True, style_unit: str = "blue"
    ) -> str:
        description = (
            self.description.title() if titlecase is True else self.description
        )

        if add_unit is False or self.unit is None:
            return description

        return f"{description} in [{style_unit}]{self.unit.value}[/{style_unit}]"

    @staticmethod
    def build_fully_qualified_path(
        category: Category | str, name: str, delimeter: Delimeter = Delimeter.KEBAB
    ) -> str:
        if isinstance(category, Category):
            category = category.value

        match delimeter:
            case Delimeter.KEBAB:
                category = helpers.snake_to_kebab(category)
                name = helpers.snake_to_kebab(name)
            case Delimeter.SNAKE:
                category = helpers.kebab_to_snake(category)
                name = helpers.kebab_to_snake(name)

        return f"{category}{delimeter.value}{name}"

    @staticmethod
    def deconstruct_fully_qualified_path(
        path: str, delimeter: Delimeter = Delimeter.KEBAB
    ) -> tuple[Category, str]:
        match delimeter:
            case Delimeter.KEBAB:
                path = helpers.snake_to_kebab(path)
            case Delimeter.SNAKE:
                path = helpers.kebab_to_snake(path)

        for category in Category:
            category_prefix = f"{category.value}{delimeter.value}"

            if path.startswith(category_prefix):
                return (
                    category,
                    path.split(category_prefix)[-1],
                )

        raise InternalError(f"Unable to deconstruct invalid path '{path}'.")

    @model_validator(mode="after")
    def _validate_value_type(self) -> Self:
        if self.value is None:
            return self

        if not isinstance(self.value, self.type):
            raise ValueError(
                f"Value '{self.value}' must be of type '{self.type.__name__}.'"
            )

        return self

    @staticmethod
    @field_serializer("type")
    def _serialize_type(obj: type[Any]) -> str:
        return obj.__name__


Settings = dict[str, Setting]
SettingsDict = dict[str, dict[str, Setting]]

SerializedSettings = dict[str, dict[str, Any]]
SerializedSettingValues = dict[str, Any]


class PrintSettings:
    DEFAULT_LOCATION = App.PATH_DATA / App.NAME_PRINT_SETTINGS_TOML

    __inner: dict[str, Setting] = {}  # noqa: RUF012
    __date: Setting

    def load(self) -> None:
        self._load()

    def get(self, path: str) -> Setting | None:
        return self._inner.get(path, None)

    def clear(self) -> None:
        for setting in self.iter_settings():
            setting.clear()

    def iter_settings(self) -> Iterator[Setting]:
        yield from self._inner.values()

    def update(self, data: SerializedSettings) -> None:
        for category, settings in data.items():
            for name, value in settings.items():
                path = Setting.build_fully_qualified_path(
                    category=category,
                    name=name,
                )

                setting = self.get(path)

                if not setting:
                    # TODO: The data should be validated before it reaches this point.
                    raise InternalError(f"Unable to update invalid path '{path}'.")

                setting.update(value)

    def stamp_date(self, date_template: str) -> None:
        self.__date.update(datetime.now().strftime(date_template))

    def to_encoded_str(self, encoding: Encoding, with_units: bool) -> str:
        match encoding:
            case Encoding.COMPACT:
                return self._encode_to_str_compact(with_units)
            case _:
                return self._encode_to_str_toml(with_units, filter_empty_values=True)

    def to_format_dict(self) -> SerializedSettingValues:
        return self._to_serialized_values_dict(
            with_units=False, filter_empty_values=False
        )

    def dump(self) -> str:
        return self._encode_to_str_toml(
            with_units=False,
            filter_empty_values=False,
        )

    @property
    def _inner(self) -> Settings:
        if not self.__inner:
            self._load()

        return self.__inner

    def _load(self) -> None:
        data = helpers.read_serialized_data(
            self.DEFAULT_LOCATION,  # pyright: ignore [reportArgumentType]
        )

        # In TOML, a list of dictionaries must be defined in a dictionay of its own.
        # It doesn't matter what this dictionary is named, we just need to extract the
        # first value from it.
        data = next(iter(data.values()))

        for item in data:
            setting = Setting(**item)

            if setting.name == Key.DATE:
                self.__date = setting

            self.__inner[setting.path] = setting

    def _to_dict(self, filter_empty_values: bool = False) -> SettingsDict:
        data = defaultdict(dict)

        for setting in self.iter_settings():
            data[setting.category.value][setting.name] = setting

        if filter_empty_values is False:
            return dict(data)

        filtered = defaultdict(dict)

        for category, settings in data.items():
            settings = {  # noqa: PLW2901
                name: setting
                for name, setting in settings.items()
                # Keep settings with a non falsy value.
                if setting.value
            }

            if not settings:
                continue

            filtered[category] = settings

        return dict(filtered)

    def _to_serialized_values_dict(
        self,
        with_units: bool = False,
        filter_empty_values: bool = False,
    ) -> SerializedSettingValues:
        data = {}

        for setting in self.iter_settings():
            if not setting.value and filter_empty_values is True:
                continue

            value = setting.value_with_unit if with_units else setting.value

            # Special handling for the date. This allows the user to use either `date`
            # or `misc-date` when defining formatting strings.
            if setting.name == Key.DATE:
                data[Key.DATE] = value

            data[setting.path] = value

        return data

    def _encode_to_str_toml(
        self,
        with_units: bool = False,
        filter_empty_values: bool = False,
    ) -> str:
        data = defaultdict(dict)

        for category, settings in self._to_dict(filter_empty_values).items():
            value_property = "value_with_unit" if with_units else "value"
            data[category] = {
                name: getattr(setting, value_property)
                for name, setting in settings.items()
            }

        return tomli_w.dumps(data, indent=2)

    # We don't remove empty values for the 'compact' format as this would cause an issue
    # if the data were to be parsed back into dict/TOML or other structured data.
    def _encode_to_str_compact(self, with_units: bool = False) -> str:
        data = []

        for setting in self.iter_settings():
            if not setting.value:
                # If the setting is a category header, and it has no value, make
                # sure there's atleast a header. This allows for parsing the data
                # back into dict/TOML or other structured data.
                if setting.path in Category.paths():
                    data.append(setting.category.placeholder)

                continue

            value_format_string = (
                setting.format_string_with_unit if with_units else setting.format_string
            )

            if setting.compact_name is not None:
                format_string = f"  {setting.compact_name}={value_format_string}"
            else:
                format_string = value_format_string

            data.append(format_string)

        return "\n".join(data).format(**self.to_format_dict())


PRINT_SETTINGS = PrintSettings()
