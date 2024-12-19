#!/usr/bin/env python3

############################################################################
#
# MODULE:       lib with location related helper functions for GRASS GIS
#
# AUTHOR(S):    Lina Krisztian, Anika Weinmann
#
# PURPOSE:      lib with location related helper functions for GRASS GIS
#
# COPYRIGHT:	(C) 2023 by mundialis and the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

import os
import subprocess

import grass.script as grass


def get_location_size():
    """Log size of current location."""
    current_gisdbase = grass.gisenv()["GISDBASE"]
    cmd = grass.Popen(
        f"df -h {current_gisdbase}",
        shell=True,
        stdout=subprocess.PIPE,
    )
    grass.message(
        _(
            (
                "\nDisk usage of GRASS GIS database:\n",
                f"{cmd.communicate()[0].decode('utf-8').rstrip()}\n",
            ),
        ),
    )


def create_tmp_location(epsg=4326):
    """Creation of a new temporary location.

    Args:
        epsg (int): The number of the EPSG code

    Returns:
        tmp_loc (str): The name of the temporary location
        tmp_gisrc (str): The path to the original GISRC file

    """
    current_gisdbase = grass.gisenv()["GISDBASE"]
    srcgisrc = grass.tempfile()
    tmp_loc = f"temp_epsg{epsg}_location_{os.getpid()}"
    gisrc_file = open(srcgisrc, "w", encoding="utf-8")
    gisrc_file.write("MAPSET: PERMANENT\n")
    gisrc_file.write(f"GISDBASE: {current_gisdbase}\n")
    gisrc_file.write(f"LOCATION_NAME: {tmp_loc}\n")
    gisrc_file.write("GUI: text\n")
    gisrc_file.close()

    proj_test = grass.parse_command("g.proj", flags="g")
    if "epsg" in proj_test:
        epsg_arg = {"epsg": epsg}
    else:
        epsg_arg = {"srid": f"EPSG:{epsg}"}
    # create temp location from input without import
    grass.verbose(_(f"Creating temporary location with EPSG:{epsg}..."))
    grass.run_command(
        "g.proj",
        flags="c",
        location=tmp_loc,
        quiet=True,
        **epsg_arg,
    )

    # switch to temp location
    os.environ["GISRC"] = str(srcgisrc)
    proj = grass.parse_command("g.proj", flags="g")
    if "epsg" in proj:
        new_epsg = proj["epsg"]
    else:
        new_epsg = proj["srid"].split("EPSG:")[1]
    if new_epsg != str(epsg):
        grass.fatal(_("Creation of temporary location failed!"))

    return tmp_loc, srcgisrc


def get_current_location():
    """Get infos to current location.

    Returns:
        loc (str): The name of the current location
        mapset (str): The name of the current mapset
        gisdbase (str): The current GISDBASE info
        gisrc (str): The path to the current GISRC file

    """
    # get current location, mapset, ...
    grassenv = grass.gisenv()
    loc = grassenv["LOCATION_NAME"]
    mapset = grassenv["MAPSET"]
    gisdbase = grassenv["GISDBASE"]
    gisrc = os.environ["GISRC"]
    return loc, mapset, gisdbase, gisrc


def switch_back_original_location(original_gisrc):
    """Switching back to original location after the computation in tmp
    location.

    Args:
        original_gisrc (str): The path to the original GISRC file

    """
    # switch to target location
    os.environ["GISRC"] = str(original_gisrc)
