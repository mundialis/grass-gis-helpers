# mundialis GRASS GIS helper library

This library provides functions which can be used for developing GRASS GIS addons and which are used by [mundialis](https://www.mundialis.de/).

## Installation

```bash
pip install grass-gis-helpers
```

## Small example

```python3
from grass_gis_helpers import general
general.set_nprocs(2)
```

## DEV setup

```bash
pip3 install -e .

```
