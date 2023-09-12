#!/usr/bin/env python3

############################################################################
#
# MODULE:       lib with cleanup related helper functions for GRASS GIS
#
# AUTHOR(S):    Anika Weinmann
#
# PURPOSE:      lib with cleanup related helper functions for GRASS GIS
#
# COPYRIGHT:	(C) 2023 by mundialis and the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

import os
import shutil
import gc

import grass.script as grass
from .location import get_location_size


def general_cleanup(
    rm_rasters=[],
    rm_vectors=[],
    rm_files=[],
    rm_dirs=[],
    rm_groups=[],
    rm_groups_wo_rasters=[],
    rm_regions=[],
    rm_strds=[],
    orig_region=None,
    rm_mask=False,
):
    """General cleanup function"""

    grass.message(_("Cleaning up..."))
    nulldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nulldev}
    for rmg in rm_groups:
        if grass.find_file(name=rmg, element="group")["file"]:
            group_rasters = grass.parse_command(
                "i.group", flags="lg", group=rmg
            )
            rm_rasters.extend(group_rasters)
            grass.run_command("g.remove", type="group", name=rmg, **kwargs)
    for rmg_wor in rm_groups_wo_rasters:
        if grass.find_file(name=rmg_wor, element="group")["file"]:
            grass.run_command("g.remove", type="group", name=rmg_wor, **kwargs)
    for rmrast in rm_rasters:
        if grass.find_file(name=rmrast, element="raster")["file"]:
            grass.run_command("g.remove", type="raster", name=rmrast, **kwargs)
    for rmvect in rm_vectors:
        if grass.find_file(name=rmvect, element="vector")["file"]:
            grass.run_command("g.remove", type="vector", name=rmvect, **kwargs)
    for rmfile in rm_files:
        if os.path.isfile(rmfile):
            os.remove(rmfile)
    for rmdir in rm_dirs:
        if os.path.isdir(rmdir):
            shutil.rmtree(rmdir)
    if orig_region is not None:
        if grass.find_file(name=orig_region, element="windows")["file"]:
            grass.run_command("g.region", region=orig_region)
            grass.run_command(
                "g.remove", type="region", name=orig_region, **kwargs
            )
    for rmreg in rm_regions:
        if grass.find_file(name=rmreg, element="windows")["file"]:
            grass.run_command("g.remove", type="region", name=rmreg, **kwargs)
    strds = grass.parse_command("t.list", type="strds")
    mapset = grass.gisenv()["MAPSET"]
    for rm_s in rm_strds:
        if f"{rm_s}@{mapset}" in strds:
            grass.run_command(
                "t.remove",
                flags="rf",
                type="strds",
                input=rm_s,
                quiet=True,
                stderr=nulldev,
            )
    if rm_mask:
        if grass.find_file(name="MASK", element="raster")["file"]:
            grass.run_command("r.mask", flags="r")

    # get location size
    get_location_size()

    # Garbage Collector: release unreferenced memory
    gc.collect()


def rm_vects(vects):
    """Function to remove clean vector maps
    Args:
        vects (list): list of vector maps which should be removed"""
    nuldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}
    for rmv in vects:
        if grass.find_file(name=rmv, element="vector")["file"]:
            grass.run_command("g.remove", type="vector", name=rmv, **kwargs)


def reset_region(region):
    """Function to set the region to the given region
    Args:
        region (str): the name of the saved region which should be set and
                      deleted
    """
    nulldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nulldev}
    if region:
        if grass.find_file(name=region, element="windows")["file"]:
            grass.run_command("g.region", region=region)
            grass.run_command("g.remove", type="region", name=region, **kwargs)
