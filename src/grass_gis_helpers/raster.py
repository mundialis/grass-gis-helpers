#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      raster.py
# AUTHOR(S):   Anika Weinmann, Julia Haas
#
# PURPOSE:     functions for general raster processing
# COPYRIGHT:   (C) 2024 by mundialis GmbH & Co. KG and the GRASS
#              Development Team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
############################################################################


import grass.script as grass


def adjust_raster_resolution(raster_name, output, res):
    """Resample or inpolate raster to given resolution. It is important that
    the region already has the right resolution.

    Args:
        raster_name (str): The name of the raster map which should be
                           resampled/interpolated
        output (str): The name for the resampled/interpolated raster map
        res (float): The resolution to which the raster should be resampled.

    """
    res_rast = float(
        grass.parse_command("r.info", map=raster_name, flags="g")["nsres"],
    )
    if res_rast > res:
        grass.run_command(
            "r.resamp.interp",
            input=raster_name,
            output=output,
            overwrite=True,
            quiet=True,
        )
    elif res_rast < res:
        grass.run_command(
            "r.resamp.stats",
            input=raster_name,
            output=output,
            method="median",
            quiet=True,
            overwrite=True,
        )
    else:
        rename_raster(raster_name, output)


def create_vrt(input_raster_list, output):
    """Create a VRT raster map out of input list, or renaming if only one
    raster is inside the list. If the input raster maps are inside other
    mapsets they will be copied to the current mapset before the VRT will be
    created.

    Args:
        input_raster_list (list): List with input raster maps
        output (str): Name of the output (vrt) raster map

    """
    # copy raster maps to current mapset
    for rast in input_raster_list:
        if "@" in rast:
            rast_wo_mapsetname = rast.split("@")[0]
            grass.run_command(
                "g.copy",
                raster=f"{rast},{rast_wo_mapsetname}",
            )
    input_raster_list = [val.split("@")[0] for val in input_raster_list]
    # buildvrt if required + renaming to output name
    if len(input_raster_list) > 1:
        grass.run_command("g.region", raster=input_raster_list)
        grass.run_command(
            "r.buildvrt",
            input=input_raster_list,
            output=output,
            quiet=True,
            overwrite=True,
        )
    else:
        grass.run_command(
            "g.rename",
            raster=f"{input_raster_list[0]},{output}",
            quiet=True,
            overwrite=True,
        )


def rename_raster(band_name_old, band_name_new):
    """Rename raster map.

    Args:
        band_name_old (str): Raster map name to rename
        band_name_new (str): The new name for the raster map

    """
    grass.run_command(
        "g.rename",
        raster=f"{band_name_old},{band_name_new}",
        quiet=True,
        overwrite=True,
    )
