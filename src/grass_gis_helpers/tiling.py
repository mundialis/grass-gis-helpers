#!/usr/bin/env python3

############################################################################
#
# MODULE:       lib with tiling related helper functions for GRASS GIS
#
# AUTHOR(S):    Anika Weinmann and Lina Krisztian
#
# PURPOSE:      lib with tiling related helper functions for GRASS GIS
#
# COPYRIGHT:	(C) 2023 by mundialis and the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

import grass.script as grass

from .cleanup import rm_vects, reset_region


def create_grid(tile_size, grid_prefix, sid, area=None):
    """Create a grid for parallelization
    Args:
        tile_size (float): the size for the tiles in map units
        grid_prefix (str): the prefix name for the output grid
        area (str): the name of area for which to create the grid tiles
        sid (str): unique identifier
    Return:
        grid_prefix (list): list with the names of the created vector map tiles
        number_tiles (int): Number of created tiles.
    """
    # save region
    orig_region = f"grid_region_{sid}"
    grass.run_command("g.region", save=orig_region, quiet=True)

    if area:
        # set region to area
        grass.run_command("g.region", vector=area, quiet=True)

    # check if region is smaller than tile size
    region = grass.region()
    dist_ns = abs(region["n"] - region["s"])
    dist_ew = abs(region["w"] - region["e"])

    grass.message(_("Creating tiles..."))
    grid = f"tmp_grid_{sid}"
    if dist_ns <= float(tile_size) and dist_ew <= float(tile_size):
        grass.run_command("v.in.region", output=grid, quiet=True)
        grass.run_command(
            "v.db.addtable",
            map=grid,
            columns="cat int",
            quiet=True,
        )
    else:
        # set region with tile_size
        grass.run_command("g.region", res=tile_size, flags="a", quiet=True)

        # create grid
        grass.run_command(
            "v.mkgrid",
            map=grid,
            box=f"{tile_size},{tile_size}",
            quiet=True,
        )
    # reset region
    reset_region(orig_region)

    grid_name = f"tmp_grid_area_{sid}"
    if area:
        grass.run_command(
            "v.select",
            ainput=grid,
            binput=area,
            output=grid_name,
            operator="overlap",
            quiet=True,
        )
        if grass.find_file(name=grid_name, element="vector")["file"] == "":
            grass.fatal(
                _(
                    f"The set region is not overlapping with {area}. "
                    f"Please define another region.",
                ),
            )
    else:
        grid_name = grid

    # create list of tiles
    tiles_num_list = list(
        grass.parse_command(
            "v.db.select",
            map=grid_name,
            columns="cat",
            flags="c",
            quiet=True,
        ).keys(),
    )

    number_tiles = len(tiles_num_list)
    grass.message(_(f"Number of tiles is: {number_tiles}"))
    tiles_list = []
    for tile in tiles_num_list:
        tile_area = f"{grid_prefix}_{tile}"
        grass.run_command(
            "v.extract",
            input=grid_name,
            where=f"cat == {tile}",
            output=tile_area,
            quiet=True,
            overwrite=True,
        )
        tiles_list.append(tile_area)

    # cleanup
    rm_vects([grid, grid_name])

    return tiles_list
