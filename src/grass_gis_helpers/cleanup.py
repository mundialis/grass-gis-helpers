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
from .location import get_location_size, switch_back_original_location


def general_cleanup(
    rm_rasters=[],
    rm_vectors=[],
    rm_files=[],
    rm_dirs=[],
    rm_groups=[],
    rm_groups_w_rasters=[],
    rm_groups_wo_rasters=[],  # kept for backwards compatibility
    rm_regions=[],
    rm_strds=[],
    rm_strds_w_rasters=[],
    rm_stvds=[],
    rm_stvds_w_vectors=[],
    orig_region=None,
    rm_mask=False,
):
    """General cleanup function."""
    grass.message(_("Cleaning up..."))
    nulldev = open(os.devnull, "w", encoding="utf-8")
    kwargs = {"flags": "f", "quiet": True, "stderr": nulldev}
    rm_groups.extend(rm_groups_wo_rasters)
    for rmg in rm_groups:
        if grass.find_file(name=rmg, element="group")["file"]:
            grass.run_command("g.remove", type="group", name=rmg, **kwargs)
    for rmg_wr in rm_groups_w_rasters:
        if grass.find_file(name=rmg_wr, element="group")["file"]:
            group_rasters = grass.parse_command(
                "i.group",
                flags="lg",
                group=rmg_wr,
            )
            rm_rasters.extend(group_rasters)
            grass.run_command("g.remove", type="group", name=rmg, **kwargs)
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
        find_reg = grass.find_file(name=orig_region, element="windows")
        if find_reg.get("file"):
            grass.run_command("g.region", region=orig_region)
            grass.run_command(
                "g.remove",
                type="region",
                name=orig_region,
                **kwargs,
            )
    for rmreg in rm_regions:
        find_reg = grass.find_file(name=rmreg, element="windows")
        if find_reg.get("file"):
            grass.run_command("g.remove", type="region", name=rmreg, **kwargs)
    strds = grass.parse_command("t.list", type="strds", quiet=True)
    stvds = grass.parse_command("t.list", type="stvds", quiet=True)
    mapset = grass.gisenv()["MAPSET"]
    rm_strds_check = []
    for rm_s in rm_strds:
        if f"{rm_s}@{mapset}" in strds:
            rm_strds_check.append(rm_s)
    if len(rm_strds_check) > 0:
        grass.run_command(
            "t.remove",
            flags="rf",
            type="strds",
            input=rm_strds_check,
            quiet=True,
            stderr=nulldev,
        )
    rm_strds_w_rasters_check = []
    for rm_r_wr in rm_strds_w_rasters:
        if f"{rm_r_wr}@{mapset}" in strds:
            rm_strds_w_rasters_check.append(rm_r_wr)
    if len(rm_strds_w_rasters_check) > 0:
        grass.run_command(
            "t.remove",
            flags="fd",
            type="strds",
            input=rm_strds_w_rasters_check,
            quiet=True,
            stderr=nulldev,
        )
    rm_stvds_check = []
    for rm_v in rm_stvds:
        if f"{rm_v}@{mapset}" in stvds:
            rm_stvds_check.append(rm_v)
    if len(rm_stvds_check) > 1:
        grass.run_command(
            "t.remove",
            flags="rf",
            type="stvds",
            input=rm_stvds_check,
            quiet=True,
            stderr=nulldev,
        )
    rm_stvds_w_vectors_check = []
    for rm_v_wv in rm_stvds_w_vectors:
        if f"{rm_v_wv}@{mapset}" in stvds:
            rm_stvds_w_vectors_check.append(rm_v_wv)
    if len(rm_stvds_w_vectors_check) > 1:
        grass.run_command(
            "t.remove",
            flags="fd",
            type="stvds",
            input=rm_stvds_w_vectors_check,
            quiet=True,
            stderr=nulldev,
        )
    if rm_mask and grass.find_file(name="MASK", element="raster")["file"]:
        grass.run_command("r.mask", flags="r")

    # get location size
    get_location_size()

    # Garbage Collector: release unreferenced memory
    gc.collect()


def rm_vects(vects):
    """Function to remove clean vector maps
    Args:
        vects (list): list of vector maps which should be removed.
    """
    nuldev = open(os.devnull, "w", encoding="utf-8")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}
    for rmv in vects:
        if grass.find_file(name=rmv, element="vector")["file"]:
            grass.run_command("g.remove", type="vector", name=rmv, **kwargs)


def reset_region(region):
    """Function to set the region to the given region
    Args:
        region (str): the name of the saved region which should be set and
                      deleted.
    """
    nulldev = open(os.devnull, "w", encoding="utf-8")
    kwargs = {"flags": "f", "quiet": True, "stderr": nulldev}
    if region and grass.find_file(name=region, element="windows")["file"]:
        grass.run_command("g.region", region=region)
        grass.run_command("g.remove", type="region", name=region, **kwargs)


def cleaning_tmp_location(original_gisrc, tmp_loc, gisdbase, tmp_gisrc):
    """Cleaning up things from temporary location.

    Args:
        original_gisrc (str): The path to the original GISRC file
        tmp_loc (str): The name of the temporary location
        gisdbase (str): The GISDBASE info
        tmp_gisrc (str): The path to the temporary GISRC file

    """
    # switch back to original gisrc
    if original_gisrc:
        switch_back_original_location(original_gisrc)
    # remove temporary location
    if tmp_loc:
        grass.try_rmdir(os.path.join(gisdbase, tmp_loc))
    if tmp_gisrc:
        grass.try_remove(tmp_gisrc)
