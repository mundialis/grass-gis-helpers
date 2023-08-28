#!/usr/bin/env python3

############################################################################
#
# MODULE:       lib with validation related helper functions for GRASS GIS
#
# AUTHOR(S):    Lina Krisztian
#
# PURPOSE:      lib with validation related helper functions for GRASS GIS
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


def check_valid_rasterdata(input):
    # check if input is not broken
    gdalinfo_cmd = ["gdalinfo", "-mm", input]
    p_gdalinfo = subprocess.Popen(
        gdalinfo_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    gdalinfo_err = p_gdalinfo.communicate()[1]
    if gdalinfo_err.decode("utf-8") != "":
        grass.fatal(_(f"<{input}> is a broken file"))
