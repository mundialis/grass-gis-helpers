#!/usr/bin/env python3

############################################################################
#
# MODULE:       lib with test related helper functions for GRASS GIS
#
# AUTHOR(S):    Anika Weinmann
#
# PURPOSE:      lib with test related helper functions for GRASS GIS
#
# COPYRIGHT:	(C) 2024 by mundialis and the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

import grass.script as grass


def get_number_of_grass_elements():
    """Get the number of grass elements like raster, vector and regions.

    Returns:
        num_rast (int): The number of raster maps in current mapset
        num_vect (int): The number of vector maps in current mapset
        num_gr (int): The number of groups in current mapset
        num_reg (int): The number of regions in current mapset
        num_mapsets (int): The number of mapsets in current location

    """
    rast_list = grass.parse_command("g.list", type="raster")
    vect_list = grass.parse_command("g.list", type="vector")
    gr_list = grass.parse_command("g.list", type="group")
    reg_list = grass.parse_command("g.list", type="region")
    mapset_list = grass.parse_command("g.mapsets", flags="l", quiet=True)
    num_rast = len(rast_list)
    num_vect = len(vect_list)
    num_gr = len(gr_list)
    num_reg = len(reg_list)
    num_mapsets = len(mapset_list)
    return num_rast, num_vect, num_gr, num_reg, num_mapsets


def check_number_of_grass_elements(
    ref_num_rast,
    ref_num_vect,
    ref_num_gr,
    ref_num_reg,
    ref_num_mapsets,
):
    """Check the number of grass elements.

    Args:
        ref_num_rast (int): The reference number of raster maps
        ref_num_vect (int): The reference number of vector maps
        ref_num_gr (int): The reference number of groups
        ref_num_reg (int): The reference number of regions
        ref_num_mapsets (int): The reference number of mapsets

    """
    n_rast, n_vect, n_gr, n_reg, n_mapsets = get_number_of_grass_elements()
    for num, ref, data_type in [
        (n_rast, ref_num_rast, "rasters"),
        (n_vect, ref_num_vect, "vectors"),
        (n_gr, ref_num_gr, "groups"),
        (n_reg, ref_num_reg, "regions"),
        (n_mapsets, ref_num_mapsets, "mapsets"),
    ]:
        assert (
            num == ref
        ), f"The number of {data_type} is {num} but should be {ref}"
