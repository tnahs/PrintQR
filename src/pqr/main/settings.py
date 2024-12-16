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
    _value: Annotated[
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
        if isinstance(value, str):
            value = value.strip()

        if not value:
            self.clear()
            return

        self._value = value

    def clear(self) -> None:
        match self.type:
            case t if t is str:
                self._value = ""
            case t if t is int:
                self._value = 0
            case t if t is float:
                self._value = 0.0
            case _:
                raise TypeError(f"Unsupported type: {self.type}")

    @property
    def path(self) -> str:
        return self.build_fully_qualified_path(self.category, self.name)

    @property
    def path_normalized(self) -> str:
        return helpers.kebab_to_snake(self.path)

    @property
    def template_string(self) -> str:
        return f"{{{self.path}}}"

    @property
    def template_string_with_unit(self) -> str:
        return f"{{{self.path}}}{self.unit.value}" if self.unit else f"{{{self.path}}}"

    @property
    def value(self) -> Any:
        if self._value:
            return self._value

        match self.type:
            case t if t is str:
                return ""
            case t if t is int:
                return 0
            case t if t is float:
                return 0.0
            case _:
                raise TypeError(f"Unsupported type: {self.type}")

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
        if self._value is None:
            return self

        if not isinstance(self._value, self.type):
            raise ValueError(
                f"Value '{self._value}' must be of type '{self.type.__name__}.'"
            )

        return self

    @staticmethod
    @field_serializer("type")
    def _serialize_type(obj: type[Any]) -> str:
        return obj.__name__


Settings = dict[str, Setting]
SettingsDict = dict[str, dict[str, Setting]]
SerializedSettings = dict[str, dict[str, Any]]
TemplateContext = dict[str, Any]


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

    def prepare(self) -> None:
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

    @property
    def date(self) -> Setting:
        return self.__date

    @date.setter
    def date(self, value: str) -> None:
        self.__date.update(value)

    def stamp_date(self, date_template: str) -> None:
        self.__date.update(datetime.now().strftime(date_template))

    def to_encoded_str(self, encoding: Encoding, with_units: bool) -> str:
        match encoding:
            case Encoding.COMPACT:
                return self._encode_to_str_compact(with_units)
            case _:
                return self._encode_to_str_toml(with_units, filter_empty_values=True)

    def to_template_context(self) -> TemplateContext:
        data = {}

        for setting in self.iter_settings():
            # Replace any falsy values with "?".
            value = setting.value or "?"

            # Special handling for the date. This allows the user to use either `date`
            # or `misc-date` when defining template strings.
            if setting.name == Key.DATE:
                data[Key.DATE] = value

            data[setting.path] = value

        return data

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
        data = helpers.read_serialized_data(self.DEFAULT_LOCATION)

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

    def _encode_to_str_toml(
        self,
        with_units: bool = False,
        filter_empty_values: bool = False,
    ) -> str:
        data = defaultdict(dict)

        for category, settings in self._to_dict(filter_empty_values).items():
            category_settings = {}

            for name, setting in settings.items():
                category_settings[name] = (
                    setting.value_with_unit if with_units else setting.value
                )

            data[category] = category_settings

        return tomli_w.dumps(data, indent=2)

    # We don't remove empty values for the 'compact' format as this would cause an issue
    # if the data were to be parsed back into dict/TOML or other structured data.
    def _encode_to_str_compact(self, with_units: bool = False) -> str:
        template = []

        for setting in self.iter_settings():
            if not setting.value:
                # If the setting is a category header, and it has no value, make
                # sure there's atleast a header. This allows for parsing the data
                # back into dict/TOML or other structured data.
                if setting.path in Category.paths():
                    template.append(setting.category.placeholder)

                continue

            value_template = (
                setting.template_string_with_unit
                if with_units
                else setting.template_string
            )

            if setting.compact_name is not None:
                setting_template = f"  {setting.compact_name}={value_template}"
            else:
                setting_template = value_template

            template.append(setting_template)

        return "\n".join(template).format(**self.to_template_context())


PRINT_SETTINGS = PrintSettings()
