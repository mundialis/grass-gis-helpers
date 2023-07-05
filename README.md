# mundialis GRASS GIS helper library

This library includes functions which [mundialis](https://www.mundialis.de/)
uses in different GRASS GIS addons.

## DEV setup

```
pip3 install -e .

```

```python3
from grass_gis_helpers import general
general.set_nprocs(2)
```


## Generating distribution archives
```
python3 -m pip install --upgrade build
python3 -m build
```
