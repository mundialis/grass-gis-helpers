#!/usr/bin/env python3

############################################################################
#
# MODULE:       lib with parallel related helper functions for GRASS GIS
#
# AUTHOR(S):    Anika Weinmann and Lina Krisztian
#
# PURPOSE:      lib with parallel related helper functions for GRASS GIS
#
# COPYRIGHT:	(C) 2023 by mundialis and the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

import grass.script as grass
from grass.pygrass.modules import Module, ParallelModuleQueue

from .mapset import verify_mapsets


def check_parallel_errors(queue):
    """Check a parallel queue for errors in the worker modules by parsing
    the stderr output for errors. A GRASS fatal will be thrown in this case.
    To be used as except in a try/except block around a parallel GRASS
    processing queue.
    """
    for proc_num in range(queue.get_num_run_procs()):
        proc = queue.get(proc_num)
        if proc.returncode != 0:
            # save all stderr to a variable and pass it to a GRASS
            # exception
            errmsg = proc.outputs["stderr"].value.strip()
            grass.fatal(
                _(f"\nERROR processing <{proc.get_bash()}>: {errmsg}"),
            )


def check_parallel_warnings(queue):
    """Check a parallel queue for warnings in the worker modules by parsing
    the stderr output for warnings. A GRASS warning will be issued in this case.
    To be used after a successfully run processing queue.
    """
    for mod in queue.get_finished_modules():
        stderr = mod.outputs["stderr"].value.strip()
        if "WARN" in stderr:
            grass.warning(
                _(f"\nWARNING processing <{mod.get_bash()}>: {stderr}"),
            )


def run_module_parallel(
    module,
    module_kwargs,
    tile_list,
    nprocs,
    uid,
    parallel=True,
):
    """Running a module in parallel on a grid."""
    # save current mapset
    start_cur_mapset = grass.gisenv()["MAPSET"]

    queue = ParallelModuleQueue(nprocs=nprocs)
    mapset_names = []
    try:
        for num, tile in enumerate(tile_list):
            grass.message(_(f"Running {module} for tile {num} ..."))
            # create a unique mapset and vector subset name
            sid = f"{num}_{uid}"

            # Module
            new_mapset = f"tmp_{module.replace('.', '_')}_{sid}"
            mapset_names.append(new_mapset)
            module_kwargs["new_mapset"] = new_mapset
            module_kwargs["area"] = tile
            # memory=use_memory,
            if parallel:
                mod = Module(module, **module_kwargs, run_=False)
                # catch all GRASS outputs to stdout and stderr
                mod.stdout_ = grass.PIPE
                mod.stderr_ = grass.PIPE
                queue.put(mod)
            else:
                grass.run_command(module, **module_kwargs)
        # if parallel:
        queue.wait()
    except Exception:
        for proc_num in range(queue.get_num_run_procs()):
            proc = queue.get(proc_num)
            if proc.returncode != 0:
                # save all stderr to a variable and pass it to a GRASS
                # exception
                errmsg = proc.outputs["stderr"].value.strip()
                grass.fatal(
                    _(f"\nERROR by processing <{proc.get_bash()}>: {errmsg}"),
                )
    # print all logs of successfully run modules ordered by module as GRASS
    # message
    for proc in queue.get_finished_modules():
        msg = proc.outputs["stderr"].value.strip()
        grass.message(_(f"\nLog of {proc.get_bash()}:"))
        for msg_part in msg.split("\n"):
            if len(msg_part) > 0:
                grass.message(msg_part)

    # verify that switching the mapset worked
    location_path = verify_mapsets(start_cur_mapset)
    return mapset_names, location_path


def patching_vector_results(mapsets, output):
    """Patching vector results of different mapsets into one together."""
    grass.message(_(f"Patching vector {output} subsets ..."))
    if len(mapsets) > 1:
        subset_mapset = [f"{output}@{m}" for m in mapsets]
        grass.run_command(
            "v.patch",
            input=subset_mapset,
            output=output,
            flags="e",
            overwrite=True,
            quiet=True,
        )
    else:
        grass.run_command(
            "g.copy",
            vector=f"{output}@{mapsets[0]},{output}",
            overwrite=True,
        )


def patching_raster_results(mapsets, output):
    """Patching raster results of different mapsets into one together."""
    grass.message(_(f"Patching raster {output} subsets ..."))
    if len(mapsets) > 1:
        subset_mapset = [f"{output}@{m}" for m in mapsets]
        grass.run_command(
            "r.patch",
            input=subset_mapset,
            output=output,
            overwrite=True,
            quiet=True,
        )
    else:
        grass.run_command(
            "g.copy",
            raster=f"{output}@{mapsets[0]},{output}",
            overwrite=True,
        )
