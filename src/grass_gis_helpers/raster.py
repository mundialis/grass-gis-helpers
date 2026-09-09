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
# SPDX-FileCopyrightText: 2024 Anika Weinmann, Julia Haas
# SPDX-FileCopyrightText: 2024 mundialis GmbH & Co. KG and the GRASS
#                         Development Team
# SPDX-License-Identifier: GPL-3.0-or-later
#
############################################################################


import grass.script as grass


def adjust_raster_resolution(
    raster_name,
    output,
    res,
    interp_method="bicubic",
    type=None,
):
    """Resample or inpolate raster to given resolution. It is important that
    the region already has the right resolution.

    Args:
        raster_name (str): The name of the raster map which should be
                           resampled/interpolated
        output (str): The name for the resampled/interpolated raster map
        res (float): The resolution to which the raster should be resampled.
        interp_method (str): Interpolation method for resampling.
                             Defaults to "bicubic".
        type (str, optional): Raster type. If type="CELL" the rasampled raster
                              values will be rounded to integer values.
                              Defaults to None.

    """
    res_rast = float(
        grass.parse_command("r.info", map=raster_name, flags="g")["nsres"],
    )
    resamp_out = output
    if type == "CELL" and res_rast != res:
        resamp_out = f"{output}_tmp"
    if res_rast > res:
        grass.run_command(
            "r.resamp.interp",
            input=raster_name,
            method=interp_method,
            output=resamp_out,
            nprocs=1,
            overwrite=True,
            quiet=True,
        )
    elif res_rast < res:
        grass.run_command(
            "r.resamp.stats",
            input=raster_name,
            output=resamp_out,
            method="median",
            quiet=True,
            overwrite=True,
        )
    else:
        vrt_to_raster(raster_name, output)
    if resamp_out != output:
        grass.run_command(
            "r.mapcalc",
            expression=f"{output} = round({resamp_out})",
            overwrite=True,
            quiet=True,
        )
        grass.run_command(
            "g.remove",
            type="raster",
            name=resamp_out,
            flags="f",
            quiet=True,
        )


def create_vrt(input_raster_list, output, copy_raster_maps=True):
    """Create a VRT raster map out of input list, or renaming if only one
    raster is inside the list. If the input raster maps are inside other
    mapsets they will be copied to the current mapset before the VRT will be
    created.

    Args:
        input_raster_list (list): List with input raster maps
        output (str): Name of the output (vrt) raster map
        copy_raster_maps (boolean): Flag if raster maps from different mapsets
                                    should be copied (Default: True)

    """
    # copy raster maps to current mapset
    for rast in input_raster_list:
        if "@" in rast and copy_raster_maps:
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


def vrt_to_raster(vrt_input, raster_output):
    """Computing raster map from VRT.

    Args:
        vrt_input (str): Input VRT
        raster_output (str): Created output raster map

    """
    grass.run_command(
        "g.region",
        raster=vrt_input,
    )
    grass.run_command(
        "r.mapcalc",
        expression=f"{raster_output} = {vrt_input}",
        quiet=True,
    )
