#!/usr/bin/env python3

############################################################################
#
# MODULE:       lib with location related helper functions for GRASS GIS
#
# AUTHOR(S):    Lina Krisztian
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

import subprocess

import grass.script as grass


def get_location_size():
    """Log size of current location"""
    current_gisdbase = grass.gisenv()["GISDBASE"]
    cmd = grass.Popen(
        f"df -h {current_gisdbase}", shell=True, stdout=subprocess.PIPE
    )
    grass.message(
        _(
            "\nDisk usage of GRASS GIS database:\n",
            f"{cmd.communicate()[0].decode('utf-8').rstrip()}\n",
        )
    )
