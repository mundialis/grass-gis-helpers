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
import subprocess
import psutil

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


def communicate_grass_command(*args, **kwargs):
    """Return stdout and stderr from executed GRASS command"""
    kwargs["stdout"] = grass.PIPE
    kwargs["stderr"] = grass.PIPE
    grass_ps = grass.start_command(*args, **kwargs)
    return grass_ps.communicate()


def check_grass_version(comp_version=(8, 0, 0)):
    """Returns boolean, if current GRASS version is >= some compare version"""
    cur_version = tuple(
        [
            int(x.replace("dev", "")) if x != "dev" else 0
            for x in grass.version()["version"].split(".")
        ]
    )
    return cur_version >= comp_version


def log_memory(grassenv=None):
    """Log memory usage"""
    if not grassenv:
        grassenv = grass.gisenv()
    cmd = grass.Popen(
        f"df -h {grassenv['GISDBASE']}", shell=True, stdout=subprocess.PIPE
    )
    grass.message(
        _(
            (
                "\nDisk usage of GRASS GIS database:\n",
                f"{cmd.communicate()[0].decode('utf-8').rstrip()}\n",
            ),
        )
    )

    grass.message(_(f"\nmemory: \n{str(psutil.virtual_memory())}"))
    grass.message(_(f"\nswap memory: \n{str(psutil.swap_memory())}"))
    # ulimit -a
    cmd = grass.Popen("ulimit -a", shell=True, stdout=subprocess.PIPE)
    grass.message(
        _(f"\nulimit -a: \n{cmd.communicate()[0].decode('utf-8').rstrip()}")
    )


def free_ram(unit, percent=100):
    """The function gives the amount of the percentages of the available
    RAM memory and free swap space.
    Args:
        unit(string): 'GB' or 'MB'
        percent(int): number of percent which shoud be used of the available
                      RAM memory and free swap space
                      default 100%
    Returns:
        memory_MB_percent/memory_GB_percent(int): percent of the the available
                                                  memory and free swap in MB or
                                                  GB

    """
    # use psutil cause of alpine busybox free version for RAM/SWAP usage
    mem_available = psutil.virtual_memory().available
    swap_free = psutil.swap_memory().free
    memory_gb = (mem_available + swap_free) / 1024.0**3
    memory_mb = (mem_available + swap_free) / 1024.0**2

    if unit == "MB":
        memory_mb_percent = memory_mb * percent / 100.0
        return int(round(memory_mb_percent))
    elif unit == "GB":
        memory_gb_percent = memory_gb * percent / 100.0
        return int(round(memory_gb_percent))
    else:
        grass.fatal(f"Memory unit {unit} not supported")
