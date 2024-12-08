# TODO

## Improvements

- What's the best way to handle image text fitting?
- Allow the user to edit the raw data before generation.
- Do we want to output with or without the units? e.g. `230` vs `230°C`.
  - Most, if not all, the units are common/standardized across slicers.
  - Maybe make this configurable?
- If the user asks for a value in a filename/caption template but does not
  provide the value, then replace it with `?`.
- Can we allow the user to use a specific QR Code version?
  - It should display a warning if the data will not fit.
- Add a command to drop an `encoded` template in the current directory.
- Add a command to drop the default `config.toml` into the current directory.
- Add `--dump` to also dump a `TOML` file in the output directory.
  - Right now it is automatically done for every run.
- Look into different pixel fonts.
- Change the color if the default value in `ask` depending on if it's coming from:
  - the directory's config
  - the user's config
  - the app's config
- Add `confirm-all` flag to say yes to any confirmations.
  - This would just skip the revise pass.
- Format `print-time`, so it parses out `hh:mm` or `##h##m`
  - This would require us to define a new field in `print-settings.toml` called `format`

## Chores

- Make sure all relevant config options are available in the right places.
- Square away the usage of `-` and `_` / `name` and `path`.
  - `name_internal` - uses `_`
  - `name_external` - uses `-`
  - `name` is key name for nested dict.
  - `path` is key name for flat fict.
- Add tests.
- Document code.
- Add user documentation.
- Layout/UI pass.
- Improve how `Config` is accessed through `ConfigManager`.
- Unify styling.

## Rich

- Customize `typer` help text.

  ```python
  Panel__init___ = Panel.__init__


  def Panel__init__patched(self, *args, box=None, border_style=None, **kwargs):
      Panel__init___(self, *args, box=SQUARE, border_style="red", **kwargs)

  setattr(rich_utils.Panel, "__init__", Panel__init__patched)

  Panel.__init__ = __init__patched
  ```

- Why does a padded console cause `ask` to print extra lines?

  ```python
  class PaddedConsole(Console):
      def __init__(self, padding=(0, 5), **kwargs):
          super().__init__(**kwargs)

          self.padding = padding

      def print(self, *objects, padding=None, **kwargs):
          padding = padding or self.padding

          if not objects:
              super().print(*objects, **kwargs)
              return

          objects = Padding(*objects, pad=padding, expand=False)

          super().print(objects, **kwargs)
  ```