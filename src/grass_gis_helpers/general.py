#!/usr/bin/env python3

############################################################################
#
# MODULE:       lib with general related helper functions for GRASS GIS
#
# AUTHOR(S):    Anika Weinmann
#
# PURPOSE:      lib with general related helper functions for GRASS GIS
#
# COPYRIGHT:	(C) 2023 by mundialis and the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

import multiprocessing as mp

import grass.script as grass


def set_nprocs(nprocs):
    """Set nprocs to value if it is -2, otherwise check value"""
    if isinstance(nprocs, str):
        nprocs = int(nprocs)
    if nprocs == -2:
        return mp.cpu_count() - 1 if mp.cpu_count() > 1 else 1
    else:
        nprocs_real = mp.cpu_count()
        if nprocs > nprocs_real:
            grass.warning(
                f"Using {nprocs} parallel processes but only "
                f"{nprocs_real} CPUs available."
            )
        return nprocs
