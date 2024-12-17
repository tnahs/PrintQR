# TODO

## Features/Improvements

### v0.1.0

- Remove `date` from file output from `init template`.
- Add `--dump-toml/--no-dump-toml` to toggle dumping a `TOML` file.
  - Add to `config.toml` too.
- Add `--confirm-all` flag to say yes to any confirmations.
  - This would just skip the revise pass.
- Support category-less names for non-ambiguous fields.
  - `slicer-nozzle-temp` CAN be shortened to `nozzle-temp`.
  - `filament-name` CANNOT be shortened to `name`.

### v0.2.0

- Generate QR Code from `3mf` file.
  - Add `--generate-gcode` to also slice and generate the GCode file.
- Format `print-time`, so it parses out `hh:mm` or `##h##m`
  - This would require:
    - Implement `list` as a `Setting.type`
    - Define a new field in `print-settings.toml` called `format`
- Allow the user to edit the raw data before generation.
- User-defined fonts.

## Chores

- When saving the dumped QR Code data, prepend a comment block with:
  - 'Generated with PrintQR on YY-MM-DD'
  - 'Run `pqr template [this file]` to revise these settings.'
  - The encoding.
  - A link to the repo.
- Revisit `Setting._value`.
  - Do we still need to convert all internal values to `None`?
- Replace lists of arg parameters with an `InputArgs` object.
  - We can move the contents of `process_shared_args` into the `__init__`.
- Add help text that all `Options` fallback to `config.toml`
- Sort out default `Padding` - `padding_outer`
- Make sure all relevant config options are available in the right places.
- Square away the usage of `-` and `_` / `name` and `path`.
  - `name_internal` - uses `_`
  - `name_external` - uses `-`
  - `name` is key name for nested dict.
  - `path` is key name for flat dict.
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
