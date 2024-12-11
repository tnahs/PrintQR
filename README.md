<div align="center">
    <img src="./images/logo-light.png#gh-light-mode-only">
    <img src="./images/logo-dark.png#gh-dark-mode-only">
</div>
<h1 align="center">PrintQR - Generate QR Codes for 3d prints</h1>

## Installation

The recommended method for installation requires [`uv`][uv]. This allows us
to easily install `PrintQR` into its own virtual environment with the correct
version of python and add it to `PATH`.

If that's not possible, a `requirements.txt` file is included for a manual
installation using `pip`.

1. Install `uv`.

   See the [uv docs][uv] for the latest instructions.

2. Clone this repo.

   ```shell
   $ git clone https://github.com/tnahs/PrintQR
   $ cd PrintQR
   ```

3. Install using `uv`.

   ```shell
   $ uv tool install .
   ```

4. Check the installation.

   ```shell
    $ pqr --version
   ```

5. Initialize `PrintQR`. This creates a `~/.pqr` directory and a `config.toml` file.

   ```shell
   $ pqr init

      ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
      ┃                                                ┃
      ┃   Initializing user config file in ~/.pqr...   ┃
      ┃                                                ┃
      ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

      Created directory ~/.pqr.
      Created file config.toml.

   $ tree ~/.pqr
   .pqr
   └── config.toml
   ```

6. That's it! Run `--help` to see available options.

   ```shell
   $ pqr --help
   ```

## Available Fields

You can access the available template fields table using:

```shell
$ pqr info fields
```

```plaintext
                       Available template fields for generating image, TOML and GCode filenames.
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category  Name                  Short Name  Format String                  Type   Unit   Description          ┃
┠───────────────────────────────────────────────────────────────────────────────────────────────────────────────┨
┃ filament  name                  -           {filament-name}                str    -      Filament name        ┃
┃ filament  brand                 fb          {filament-brand}               str    -      Filament brand       ┃
┃ filament  material              fm          {filament-material}            str    -      Filament material    ┃
┠───────────────────────────────────────────────────────────────────────────────────────────────────────────────┨
┃ printer   name                  -           {printer-name}                 str    -      Printer name         ┃
┃ printer   nozzle-size           ns          {printer-nozzle-size}          float  mm     Nozzle size          ┃
┃ printer   nozzle-type           nt          {printer-nozzle-type}          str    -      Nozzle type          ┃
┠───────────────────────────────────────────────────────────────────────────────────────────────────────────────┨
┃ slicer    name                  -           {slicer-name}                  str    -      Slicer name          ┃
┃ slicer    setting-preset        sp          {slicer-setting-preset}        str    -      Setting preset       ┃
┃ slicer    filament-preset       fp          {slicer-filament-preset}       str    -      Filament preset      ┃
┃ slicer    printer-preset        pp          {slicer-printer-preset}        str    -      Printer preset       ┃
┃ slicer    max-volumetric-speed  vs          {slicer-max-volumetric-speed}  int    mm³/s  Max volumetric speed ┃
┃ slicer    layer-height          lh          {slicer-layer-height}          float  mm     Layer height         ┃
┃ slicer    nozzle-temp           nt          {slicer-nozzle-temp}           int    °C     Nozzle temp          ┃
┃ slicer    bed-temp              bt          {slicer-bed-temp}              int    °C     Bed temp             ┃
┃ slicer    print-time            pt          {slicer-print-time}            str           Print time           ┃
┠───────────────────────────────────────────────────────────────────────────────────────────────────────────────┨
┃ misc      date                  -           {misc-date}                    str    -      Current date         ┃
┃ misc      notes                 -           {misc-notes}                   str    -      Notes                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Encoding Schemas

### As `toml`

```toml
[filament]
name = ""
brand = ""
material = ""

[printer]
name = ""
nozzle-size = 0.0
nozzle-type = ""

[slicer]
name = ""
setting-preset = ""
filament-preset = ""
printer-preset = ""
max-volumetric-speed = 0
layer-height = 0.0
nozzle-temp = 0
bed-temp = 0
print-time = ""

[misc]
date = ""
notes = ""
```

#### `toml` Example

```toml
[filament]
name = "Galaxy Black"
brand = "Prusament"
material = "PLA"

[printer]
name = "Prusa MK4S"
nozzle-size = 0.4
nozzle-type = "HF ObXidian"

[slicer]
name = "PrusaSlicer"
max-volumetric-speed = 24
layer-height = 0.25
nozzle-temp = 230
bed-temp = 60
print-time = "00:42"
```

### As `compact`

```plaintext
{filament-name}
  fb={filament-brand}
  fm={filament-material}
{printer-name}
  ns={nozzle-size}
  nt={nozzle-type}
{slicer-name}
  sp={setting-preset}
  fp={filament-preset}
  pp={printer-preset}
  mv={max-volumetric-speed}
  lh={layer-height}
  nt={nozzle-temp}
  bt={bed-temp}
  pt={print-time}
{date}
{notes}
```

#### `compact` Example

```plaintext
Galaxy Black
  fn=Prusament
  fm=PLA
Prusa MK4S
  ns=0.4
  nt=HF ObXidian
PrusaSlicer
  mv=24
  lh=0.25
  nt=230
  bt=60
  pt=00:42
```

## Adding a Field

For most cases, adding a new field is relatively easy.

1. Add the new field to [`print-settings.toml`][print-settings]
2. Add its default value to [`config.toml`][config]
3. Reinstall the application.
4. Add your default for the field in your `config.toml`.

### [`print-settings.toml`][print-settings]

All fields and their associate attributes are defined in this file. A
single field is defined as a dictionary in a list named `print-settings`. See
[`print-settings.toml`][print-settings] for more examples.

```toml
[[print-settings]]

# Must be in "kebab-case".
name = "extrusion-width"

# Must be one of:
#
#   'filament'
#   'printer'
#   'slicer'
#   'misc'S
#
category = "slicer"

# A valid Python type. This type is used when validating
# values passed into the field. The value defined here
# is passed to `eval` to retrieve the type.
#
# The most common values would be:
#
#   'str'
#   'int'
#   'float'
#
type = "float"

# This is a two-character abbreviation of the field name.
compact-name = "ew"

# The unit of measurement. For display purposes only.
unit = ""

# The field's description.
description = "filament preset"
```

### [`config.toml`][config]

The field's default value is defined in this file within the `print-settings`
dictionary.

When the application starts, this file is copied to the user's config directory
(`~./pqr`) if it doesn't already exist there. It's important to add the
default value to the application's [`config.toml`][config] and not just your
own. The application's [`config.toml`][config] acts as a fallback for any values
not defined in the user's `config.toml`.

[config]: ./src/pqr/data/config.toml
[print-settings]: ./src/pqr/data/print-settings.toml
[uv]: https://docs.astral.sh/uv/
