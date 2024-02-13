#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      import_local_data.py
# AUTHOR(S):   Anika Weinmann, Julia Haas
#
# PURPOSE:     open-geodata-germany: functions for the local data import
# COPYRIGHT:   (C) 2024 by mundialis GmbH & Co. KG and the GRASS
#              Development Team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
############################################################################

import glob
import os

import grass.script as grass

from grass_gis_helpers.general import communicate_grass_command


def adjust_raster_resolution(raster_name, output, res):
    """Resample or inpolate raster to given resolution. It is important that
    the region already has the right resolution

    Args:
        raster_name (str): The name of the raster map which should be
                           resampled/interpolated
        output (str): The name for the resampled/interpolated raster map
        res (float): The resolution to which the raster should be resampled.
    """
    res_rast = float(
        grass.parse_command("r.info", map=raster_name, flags="g")["nsres"]
    )
    if res_rast > res:
        grass.run_command(
            "r.resamp.interp",
            input=raster_name,
            output=output,
            overwrite=True,
            quiet=True,
        )
    elif res_rast < res:
        grass.run_command(
            "r.resamp.stats",
            input=raster_name,
            output=output,
            method="median",
            quiet=True,
            overwrite=True,
        )
    else:
        rename_raster(raster_name, output)


def import_local_raster_data(
        aoi,
        basename,
        local_data_dir,
        fs,
        native_res_flag,
        all_raster,
        rm_rasters,
        band_dict=None,  # e.g. band_dict = {1: "red", 2: "green", 3: "blue", 4: "nir"}
    ):
    """Import local raster data. Where a VRT or TIFs are given in the directory
    of "local_data_dir/fs".

    Args:
        aoi (str): Vector map with area of interest
        basename (str): Basename for imported rasters
        local_data_dir (str): Path to local data directory with federal state
                              subfolders
        fs (str): the abbrivation of the federal state
        native_res_flag (bool): True if native data resolution should be used
        all_raster (list/dict): empty list/dictonary where the imported rasters
                                will be appended
        band_dict (dict): TODO
    Returns:
        imported_local_data (bool): True if local data imported, otherwise False
    """
    grass.message(_("Importing local raster data..."))
    imported_local_data = False
    if band_dict is None:
        band_dict = {"": ""}
    # get files (VRT if available otherwise TIF)
    raster_files = glob.glob(
        os.path.join(local_data_dir, fs, "**", "*.vrt"),
        recursive=True,
    )
    if not raster_files:
        raster_files = glob.glob(
            os.path.join(local_data_dir, fs, "**", "*.tif"),
            recursive=True,
        )

    # import data for AOI
    # TODO parallize local data import for multi TIFs/VRTs
    for i, raster_file in enumerate(raster_files):
        # get current region
        cur_reg = grass.region()
        ns_res = cur_reg["nsres"]
        ew_res = cur_reg["ewres"]
        # set aoi if it is given with current resolution
        if aoi and aoi != "":
            grass.run_command(
                "g.region",
                vector=aoi,
                nsres=ns_res,
                ewres=ew_res,
                flags="a",
                quiet=True,
            )
            # grow region because of interpolation
            grass.run_command("g.region", grow=1, quiet=True)
        # Import data
        name = f"{basename}_{i}"
        kwargs = {
            "input": raster_file,
            "output": name,
            "extent": "region",
            "quiet": True,
            "overwrite": True,
        }
        # resolution settings: -r native resolution; otherwise from region
        if not native_res_flag:
            kwargs["resolution"] = "region"
        r_import = communicate_grass_command("r.import", **kwargs)
        err_m1 = "Input raster does not overlap current computational region."
        err_m2 = "already exists and will be overwritten"
        if err_m1 in r_import[1].decode():
            continue
        elif err_m2 in r_import[1].decode():
            pass
        elif r_import[1].decode() != "":
            grass.fatal(_(r_import[1].decode()))

        # resample / interpolate data
        for band_num, band in band_dict.items():
            band_name_old = f"{name}.{band_num}" if band_num != "" else name
            band_name_new = f"{name}.{band}" if band_num != "" else name
            rm_rasters.append(band_name_old)
            # check resolution and resample if needed
            if not native_res_flag:
                adjust_raster_resolution(
                    band_name_old, band_name_new, ns_res
                )
            else:
                rename_raster(band_name_old, band_name_new)
            if isinstance(all_raster, dict):
                all_raster[band].append(band_name_new)
            else:
                all_raster.append(band_name_new)

    # check if all bands have at least one input raster
    if isinstance(all_raster, dict):
        if all([len(val) > 0 for band, val in all_raster.items()]):
            imported_local_data = True
    elif len(all_raster) > 0:
        imported_local_data = True

    return imported_local_data


def import_local_xyz_data(
        aoi,
        basename,
        local_data_dir,
        fs,
        native_res_flag,
        all_raster,
        rm_rasters,
    ):
    """Import local XYZ raster data. Where the XYZ files which are inside the
    directory of "local_data_dir/fs", will be imported for the AOI.

    Args:
        aoi (str): Vector map with area of interest
        basename (str): Basename for imported rasters
        local_data_dir (str): Path to local data directory with federal state
                              subfolders
        fs (str): the abbrivation of the federal state
        native_res_flag (bool): True if native data resolution should be used
        all_raster (list/dict): empty list/dictonary where the imported rasters
                                will be appended
    Returns:
        imported_local_data (bool): True if local data imported, otherwise False
    """
    grass.message(_("Importing local XYZ data..."))
    imported_local_data = False

    # get files (XYZ)
    xyz_files = glob.glob(
        os.path.join(local_data_dir, fs, "**", "*.xyz"),
        recursive=True,
    )

    # import data for AOI
    # TODO parallize local data import
    for i, xyz_file in enumerate(xyz_files):
        # get current region
        cur_reg = grass.region()
        ns_res = cur_reg["nsres"]
        ew_res = cur_reg["ewres"]
        # set aoi if it is given with current resolution
        if aoi and aoi != "":
            grass.run_command(
                "g.region",
                vector=aoi,
                nsres=ns_res,
                ewres=ew_res,
                flags="a",
                quiet=True,
            )
            # grow region because of interpolation
            grass.run_command("g.region", grow=1, quiet=True)
        # TODO: Import data
        name = f"{basename}_{i}"
        kwargs = {
            "input": xyz_file,
            "output": name,
            "extent": "region",
            "quiet": True,
            "overwrite": True,
        }
        # resolution settings: -r native resolution; otherwise from region
        if not native_res_flag:
            kwargs["resolution"] = "region"
        r_import = communicate_grass_command("r.import", **kwargs)
        err_m1 = "Input raster does not overlap current computational region."
        err_m2 = "already exists and will be overwritten"
        if err_m1 in r_import[1].decode():
            continue
        elif err_m2 in r_import[1].decode():
            pass
        elif r_import[1].decode() != "":
            grass.fatal(_(r_import[1].decode()))

        for band_num, band in band_dict.items():
            band_name_old = f"{name}.{band_num}" if band_num != "" else name
            band_name_new = f"{name}.{band}" if band_num != "" else name
            rm_rasters.append(band_name_old)
            # check resolution and resample if needed
            if not native_res_flag:
                adjust_raster_resolution(
                    band_name_old, band_name_new, ns_res
                )
            else:
                rename_raster(band_name_old, band_name_new)
            if isinstance(all_raster, dict):
                all_raster[band].append(band_name_new)
            else:
                all_raster.append(band_name_new)

    # check if all bands have at least one input raster
    if isinstance(all_raster, dict):
        if all([len(val) > 0 for band, val in all_raster.items()]):
            imported_local_data = True
    elif len(all_raster) > 0:
        imported_local_data = True

    return imported_local_data


    # (data, src_res, output_name, aoi):
    # """Imports XYZ file
    # Args:
    #     data (str): the XYZ file
    #     output_name (str): the base name for the output raster
    #     src_res (float): the resolution of the data in the XYZ file
    # """
    # gs.message(f"Importing {output_name} XYZ raster data ...")
    # # set region to xyz file
    # xyz_reg_str = gs.read_command(
    #     "r.in.xyz",
    #     output="dummy",
    #     input=data,
    #     flags="sg",
    #     separator="space",
    #     overwrite=True,
    # )
    # xyz_reg = {
    #     item.split("=")[0]: float(item.split("=")[1])
    #     for item in xyz_reg_str.strip().split(" ")
    # }
    # dtm_res_h = src_res / 2.0
    # north = xyz_reg["n"] + dtm_res_h
    # south = xyz_reg["s"] - dtm_res_h
    # west = xyz_reg["w"] - dtm_res_h
    # east = xyz_reg["e"] + dtm_res_h
    # # import only study area
    # area_reg = gs.parse_command("g.region", flags="ug", vector=aoi)
    # while (north - src_res) > float(area_reg["n"]):
    #     north -= src_res
    # while (south + src_res) < float(area_reg["s"]):
    #     south += src_res
    # while (west + src_res) < float(area_reg["w"]):
    #     west += src_res
    # while (east - src_res) > float(area_reg["e"]):
    #     east -= src_res
    # if north < south:
    #     north += src_res
    #     south -= src_res
    # if east < west:
    #     east += src_res
    #     west -= src_res
    # gs.run_command("g.region", n=north, s=south, w=west, e=east, res=src_res)
    # gs.run_command(
    #     "r.in.xyz",
    #     input=data,
    #     output=output_name,
    #     method="mean",
    #     separator="space",
    #     quiet=True,
    #     overwrite=True,
    # )
    # gs.run_command(
    #     "g.region",
    #     n=f"n+{dtm_res_h}",
    #     s=f"s+{dtm_res_h}",
    #     w=f"w+{dtm_res_h}",
    #     e=f"e+{dtm_res_h}",
    #     res=src_res,
    # )
    # gs.run_command("r.region", map=output_name, flags="c")
    # gs.message(_(f"The XYZ raster map <{output_name}> is imported."))


def rename_raster(band_name_old, band_name_new):
    """Rename raster map

    Args:
        band_name_old (str): Raster map name to rename
        band_name_new (str): The new name for the raster map
    """
    grass.run_command(
        "g.rename",
        raster=f"{band_name_old},{band_name_new}",
        quiet=True,
        overwrite=True,
    )