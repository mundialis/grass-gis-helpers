#!/usr/bin/env python3

############################################################################
#
# MODULE:       lib with mapset related helper functions for GRASS GIS
#
# AUTHOR(S):    Anika Weinmann
#
# PURPOSE:      lib with mapset related helper functions for GRASS GIS
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

import grass.script as grass


def switch_to_new_mapset(new_mapset, new=True):
    """The function switches to a new mapset and changes the GISRC file for
    parallel processing.

    Args:
        new_mapset (string): Unique name of the new mapset
        new (boolean): Boolean if existing mapset should be used
                       or a new one created
    Returns:
        gisrc (string): The path of the old GISRC file
        newgisrc (string): The path of the new GISRC file
        old_mapset (string): The name of the old mapset

    """
    # current gisdbase, location
    env = grass.gisenv()
    gisdbase = env["GISDBASE"]
    location = env["LOCATION_NAME"]
    old_mapset = env["MAPSET"]

    if new:
        grass.verbose(_(f"New mapset {new_mapset}"))
        grass.utils.try_rmdir(os.path.join(gisdbase, location, new_mapset))
    else:
        grass.verbose(_(f"Using, not deleting mapset {new_mapset}"))
        grass.try_remove(
            os.path.join(gisdbase, location, new_mapset, ".gislock"),
        )

    gisrc = os.environ["GISRC"]
    newgisrc = f"{gisrc}_{os.getpid()}"
    grass.try_remove(newgisrc)
    shutil.copyfile(gisrc, newgisrc)
    os.environ["GISRC"] = newgisrc

    grass.verbose(f"GISRC: {os.environ['GISRC']}")
    grass.run_command("g.mapset", flags="c", mapset=new_mapset, quiet=True)

    # verify that switching of the mapset worked
    cur_mapset = grass.gisenv()["MAPSET"]
    if cur_mapset != new_mapset:
        grass.fatal(f"new mapset is {cur_mapset}, but should be {new_mapset}")
    return gisrc, newgisrc, old_mapset


def verify_mapsets(start_cur_mapset):
    """The function verifies the switches to the start_cur_mapset.

    Args:
        start_cur_mapset (string): Name of the mapset which is to verify
    Returns:
        location_path (string): The path of the location

    """
    env = grass.gisenv()
    gisdbase = env["GISDBASE"]
    location = env["LOCATION_NAME"]
    cur_mapset = env["MAPSET"]
    if cur_mapset != start_cur_mapset:
        grass.fatal(
            f"new mapset is {cur_mapset}, but should be {start_cur_mapset}",
        )
    return os.path.join(gisdbase, location)
