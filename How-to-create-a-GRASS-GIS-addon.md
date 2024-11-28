# How does it work at all?

GRASS GIS is written in more than one programming language. While most
of the source code is written in C, about 30% is written in Python. A
compiler is needed to convert the C/C++ source code into executable
files ("binaries"). In contrast, Python is an interpreted language that
can only be executed with Python software.

Now, in order to create an installable binary package from a source
code package, the so-called "compilation step" is required. While the
source code consists of thousands of C and Python files (plus HTML
documentation), the included "makefiles" tell the build system to
generate binaries from the source code in the correct order, render the
manual pages, etc.

The way to install the compiler tools and Python depends on the operating
system. To make this easier, there are collected copy-paste instructions
for most operating systems in the wiki:

[Compile and install instructions](https://grasswiki.osgeo.org/wiki/Compile_and_Install)

Running GRASS GIS is effectively not much more than setting some environmental
variables that define where the GRASS GIS binaries and some auxiliary libraries
are located and where to find the spatial data. Since GRASS GIS is a modular
system, only the core libraries are needed as a minimum.

## How to create a GRASS GIS addon

A GRASS python module consists of

- Makefile
- html documentation file
- either a python script (most easy with one script as whole addon)
- or C code

### Reuse & Recycle... and refactor

- it helps if GRASS GIS source code is there to look at
- best to look at existing GRASS addons
  - [r.mapcalc.simple](https://github.com/OSGeo/grass/tree/master/scripts/r.mapcalc.simple)
  - [v.example](https://github.com/mundialis/v.example)
  - ...
- inside the GRASS GIS source code all python modules are in folder 'scripts'
- or see [https://grasswiki.osgeo.org/wiki/Category:Python](https://grasswiki.osgeo.org/wiki/Category:Python), especially [https://grasswiki.osgeo.org/wiki/GRASS_Python_Scripting_Library](https://grasswiki.osgeo.org/wiki/GRASS_Python_Scripting_Library)
- use `r.blend --script` and it will generate how it would look like as addon (like a template, not a copy of source code!) (will always create generic long version)
- use of predefinded functions `import grass.script as grass` (e.g. `grass.run_command`, `grass.message`, `grass.fatal`, `grass.warning`, `grass.read_command`)
  - See [script documentation](https://grass.osgeo.org/grass-devel/manuals/libpython/script.html) for more usage examples
  - located in `python/grass/script/`, please read to avoid to reinvent the wheel
  - TODO add docs (but better to read source code because it might be more up-to-date)
- use of [grass-gis-helpers](https://github.com/mundialis/grass-gis-helpers) library
  - also beware of copying multiple code mutiple times, if there are only small changes. Consider adding methods to [grass-gis-helpers](https://github.com/mundialis/grass-gis-helpers) library instead and reuse.
- use of [github-workflows](https://github.com/mundialis/github-workflows)
  - add linting workflow
  - add workflow to run tests
- Submitting rules:
  - [https://github.com/OSGeo/grass/blob/master/CONTRIBUTING.md](https://github.com/OSGeo/grass/blob/master/CONTRIBUTING.md)

### Structure (here `r.blend` as example)

1. shebang (first line)

1. header (author, purpose, license)

1. `# % ` comments are important (ignored by python but important for parser)

   - See [https://grass.osgeo.org/grass-devel/manuals/g.parser.html](https://grass.osgeo.org/grass-devel/manuals/g.parser.html)

   ```shell
   r.blend -c first=aspect second=elevation output=elev_shade_blend
   ```

   #### `# % module`

   - including `keyword` to make it appear in keyword searches and lists

   #### `# % options`

   - (e.g. 'input', 'output', 'first'), some are predefined (predefined or custom, predefined is more convenient but also needs more knowledge to use)
   - key is key in command line (e.g. 'first')
   - answer is default values
   - access them in main function like `options['first']`
   - there are also [standard options](%22https://grass.osgeo.org/grass-devel/manuals/parser_standard_options.html) which can be extended

   #### `# % flag`

   #### `# % rules`

   - define dependencies between options, required options and more. See official [docs](https://grass.osgeo.org/grass-devel/manuals/g.parser.html#conditional-parameters)

1. `def main():` reads in all variables (`options['first']`)

   - a main function is required

1. indefinite additional functions are possible

1. include parser at the end before calling main function:

   ```python
   if __name__ == "__main__":
       options, flags = grass.parser()
       main()
   ```

   or optionally clean temporary stuff in 'cleanup' function and call it on exit

   ```python
   if __name__ == "__main__":
       options, flags = grass.parser()
       atexit.register(cleanup)
       main()
   ```

## Best practises

- Python style guide

  - [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/%5D)
  - [GRASS Programming Style Guide](https://github.com/OSGeo/grass/blob/main/doc/development/style_guide.md)
  - Python section in [GRASS Programming Style Guide](https://github.com/OSGeo/grass/blob/main/doc/development/style_guide.md#python)

- C/C++ style guide

  - C/C++ section in [GRASS Programming Style Guide](https://github.com/OSGeo/grass/blob/main/doc/development/style_guide.md#c-and-c)

- HTML documentation (no full html please, parts are auto-generated at compile time)

  - HTML section in [GRASS Programming Style Guide](https://github.com/OSGeo/grass/blob/main/doc/development/style_guide.md#documentation)

- Message translations: to support i18n, import following module and use macro '\_' before strings. The text after will be replaced with existing lookup tables for other languages

- use existing functions: esp. from PyGRASS

  - [PyGRASS API description](https://grass.osgeo.org/grass-devel/manuals/libpython/pygrass_index.html)
  - PyGRASS paper: An Object Oriented Python Application Programming Interface (API) for GRASS: [https://www.mdpi.com/2220-9964/2/1/201/htm](https://www.mdpi.com/2220-9964/2/1/201/htm)

  ```python
  # i18N
  import gettext
  gettext.install('grassmods', os.path.join(os.getenv("GISBASE"), 'locale'))
  ```

- for this to work use message standardisation (look at locale)

### how to name it

Choose a name depending on the "family":

- start with `v.` if it is a vector module
- start with `r.` if it is a raster module
- start with `i.` if it is a imagery module
- start with `db.` if it is a database module
- try to stick to existing convention but no strickt rules
- do not use too long module names
- existing families are d, db, g, i, m, ps, r, r3, t, test and v

### mundialis / actinia specific

- How to handle dependencies (for installation within actinia)
  - use `requirements.txt` for python packages
- How can I log to actinia output? (with `grass.message`)
- GRASS GIS addons need to be installed globally (see `$HOME`)
- Which things are tricky
  - `db.login`, `db.connect -d`
  - $HOME directory might not be what you think (`/root`)
  - ...

## Steps to make the GRASS GIS addon public + open source

### General code-related steps

#### General steps

- Decide whether it should be a single addon or **multi-module / toolbox**. Example for multi-module is here: [t.sentinel](https://github.com/mundialis/t.sentinel)
- Check for **sensitive information**. If included, remove them and publish without git history (or rewrite if needed).

#### License + Copyright

- License is GPL3. If no LICENSE.md exists, create it later directly with GitHub (see section below).
- Copyright: no single person (only as author), `mundialis -> mundialis GmbH & Co. KG`
- Add license information to `*.py` file header:

```shell
# COPYRIGHT:    (C) 2021-2024 by mundialis GmbH & Co. KG and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
```

- Adjust year

#### Linting

- Add reusable linting workflow as described [here](https://github.com/mundialis/github-workflows?tab=readme-ov-file#python-linting)

  ```yaml
  name: Python Flake8, black and pylint code quality check

  on: [push]

  jobs:
    lint:
      uses: mundialis/github-workflows/.github/workflows/linting.yml@main
  ```

- Run locally. Mind that there might be differences due to version mismatches.
  To overcome this, pre-commit hooks from the same repository can be used

  ```shell
  black --check --diff --line-length 79 .
  flake8 --config=.flake8 --count --statistics --show-source .
  pylint .
  ```

- Fix lint errors which black couldn't fix or add exception to `.flake8` file

- Black does not fix GRASS GIS parameter `#%`. This can be batch changed with `sed -i 's|^#%|# %|g' foo.py`

- There may not be any linting issues left as the pipeline would fail

- The GRASS GIS project is moving to `ruff`.

#### General steps Part 2

- For GRASS GIS parameters, pay attention to label and description, so that the first word after the `:` is written in capital letters
- For GRASS GIS module description the sentence should be ended with a point. No point for parameter description or any other parameter value
- for GRASS messages like `grass.message()`, `grass.fatal()` and `grass.warning()`, use the format with underscore (in order to support [message translations](https://grasswiki.osgeo.org/wiki/GRASS_messages_translation)), e.g.: `grass.message(_("Message text"))`.
  - NOTE that underscores in `grass.debug()` messages are not desired.
  - NOTE that variables should not go into the macro, e.g. `grass.message(_("Created output group <%s>") % output)` instead of `grass.message(_("Created output group <%s>" % output))`
- There should be no space between the text and suspension points, e.g. `Reading raster map...` instead of `Reading raster map ...`

For more information on standardized messages see [here](https://trac.osgeo.org/grass/wiki/MessageStandardization).

#### Tests

- If tests exist, the header should look like in the actual module.
- If tests exist, the test workflow should be included. [See here](https://github.com/mundialis/github-workflows?tab=readme-ov-file#grass-gis-addon-tests) for instructions.

#### In the end

- Create a merge request in the old repository with your changes, so it can be reviewed there and moved to GitHub when cleanup is done

### Steps on GitHub

- Every addon gets its own GitHub repo
  - default location is at [https://github.com/mundialis](https://github.com/mundialis). If needed they can be integrated somewhere else as submodule.
- Choose "GPL3" as license
- Copy code to new repository (not via `git remote` if sensitive information are included)
- Release new addon in GitHub with 1.0.0
- Add project label if applicable (e.g. `vale`, `hermosa-earth`, `incora`)
- Add / update README.md in project repositories which use this addon.

### Cleanup

- Delete "old" code from internal repository
- Add hint to internal repository README that the addon was moved and where to find it
- Adjust README.md in actinia-assets/grass-gis-addons
- Adjust deployments which use the addon, if applicable
