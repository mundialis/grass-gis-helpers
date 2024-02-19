# mundialis GRASS GIS helper library

This library provides functions which can be used for developing GRASS GIS addons and which are used by [mundialis](https://www.mundialis.de/).

The library usage needs to be in a GRASS GIS session, so that the the module `grass` can be imported.

## Installation

```bash
pip install grass-gis-helpers
```

## Small example

Small example how the library can be used inside a GRASS GIS session:

```python3
from grass_gis_helpers import general
general.set_nprocs(2)
```

## DEV setup

pip-tools is required for DEV setup:

```bash
# only once
pip3 install pip-tools
```

then install grass-gis-helpers from the local repository:

```bash
pip3 install -e .

```
