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


def get_gdalinfo_returncodes(input):
    """Return return codes from reading input file with gdalinfo."""
    gdalinfo_cmd = ["gdalinfo", "-mm", input]
    p_gdalinfo = subprocess.Popen(
        gdalinfo_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    gdalinfo_err = p_gdalinfo.communicate()[1].decode("utf-8")
    gdalinfo_returncode = p_gdalinfo.returncode
    return gdalinfo_err, gdalinfo_returncode


def check_valid_rasterdata(input, strict=True):
    """Check if input is broken and returns grass.fatal() in this case."""
    gdalinfo_err, gdalinfo_returncode = get_gdalinfo_returncodes(input)
    if strict:
        # strict check: checks if gdalinfo contains any error
        if gdalinfo_err != "":
            grass.fatal(
                _(
                    f"<{input}> contains erroneous data.\n"
                    "NOTE: Might be harmless error messages. "
                    "Data might be still readable. "
                    "For a less strict check use: "
                    "check_valid_rasterdata(<input>,strict=False).",
                ),
            )
    # less strict check: fails only if bands can't be read
    elif gdalinfo_returncode != 0 or ("TIFFReadEncodedStrip" in gdalinfo_err):
        grass.fatal(_(f"<{input}> is a broken file"))
