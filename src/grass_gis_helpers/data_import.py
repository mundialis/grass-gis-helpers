#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      data_import.py
# AUTHOR(S):   Anika Weinmann, Julia Haas
#
# PURPOSE:     functions for the local data import
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
from subprocess import PIPE
import wget

import grass.script as grass

from .cleanup import rm_vects
from .general import communicate_grass_command
from .raster import adjust_raster_resolution, rename_raster
from .vector import patch_vectors


def download_and_import_tindex(tindex_url, output, download_dir):
    """Download and import tile index from url.

    Args:
        tindex_url (str): URL of tile index
        output (str): The output name for the tile index
        download_dir (str): The directory where the data should be downloaded

    """
    cur_dir = os.getcwd()
    zip_name = os.path.basename(tindex_url)
    tindex_gpkg = zip_name.replace(".gz", "")
    try:
        os.chdir(download_dir)
        # download data
        wget.download(tindex_url, zip_name, bar=None)

        # unzip tindex
        os.system(f"gunzip {zip_name}")

        # import data
        grass.run_command(
            "v.import",
            input=tindex_gpkg,
            output=output,
            extent="region",
            overwrite=True,
            quiet=True,
        )
    finally:
        for rm_file in [zip_name, tindex_gpkg]:
            if os.path.isfile(rm_file):
                os.remove(rm_file)
        os.chdir(cur_dir)


def get_list_of_tindex_locations(tindex, aoi=None):
    """Select the locations of the tindex which overlap with the AOI or the
    current region.

    Args:
        tindex (str): Name of the tindex vector map
        aoi (str): Name of the AOI vector map
    Returns:
        (list): List with locations which overlap with the AOI or the current
                region

    """
    tindex_clipped = f"clipped_tindex_vect_{grass.tempname(8)}"
    try:
        v_clip_kwargs = {
            "input": tindex,
            "output": tindex_clipped,
            "flags": "",
            "quiet": True,
        }
        if aoi:
            v_clip_kwargs["clip"] = aoi
            v_clip_kwargs["flags"] += "d"
        else:
            v_clip_kwargs["flags"] += "r"
        grass.run_command("v.clip", **v_clip_kwargs)
        # grass.vector_db_select(tindex_clipped, columns="location")
        tiles = [
            val[0]
            for val in grass.vector_db_select(
                tindex_clipped,
                columns="location",
            )["values"].values()
        ]
    finally:
        rm_vects([tindex_clipped])
    return tiles


def import_local_raster_data(
    aoi,
    basename,
    local_data_dir,
    native_res_flag,
    all_raster,
    rm_rasters,
    band_dict=None,
):
    """Import local raster data. Where a VRT or TIFs are given in the directory
    of "local_data_dir".

    Args:
        aoi (str): Vector map with area of interest
        basename (str): Basename for imported rasters
        local_data_dir (str): Path to local data directory with VRT or TIF
                              files inside
        native_res_flag (bool): True if native data resolution should be used
        all_raster (list/dict): Empty list/dictionary where the imported rasters
                                will be appended
        rm_rasters (list): List with rasters which should be removed
        band_dict (dict): Dictionary with band number and names, if none only
                          one band should be in the files which should be
                          imported; e.g. for DOP import band_dict = {
                              1: "red", 2: "green", 3: "blue", 4: "nir"
                          }

    Returns:
        imported_local_data (bool): True if local data imported, otherwise
                                    False

    """
    grass.message(_("Importing local raster data..."))
    imported_local_data = False
    if band_dict is None:
        band_dict = {"": ""}
    # get files (VRT if available otherwise TIF)
    raster_files = glob.glob(
        os.path.join(local_data_dir, "**", "*.vrt"),
        recursive=True,
    )
    if not raster_files:
        raster_files = glob.glob(
            os.path.join(local_data_dir, "**", "*.tif"),
            recursive=True,
        )

    # get current region
    cur_reg = grass.region()
    ns_res = cur_reg["nsres"]
    ew_res = cur_reg["ewres"]
    # import data for AOI
    # TODO parallelize local data import for multi TIFs/VRTs
    for i, raster_file in enumerate(raster_files):
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
        if err_m2 in r_import[1].decode():
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
                adjust_raster_resolution(band_name_old, band_name_new, ns_res)
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


def get_xyz_file_infos(xyz_file, separator="space"):
    """Get the infos of a XYZ file to resolution, bounding box and pixelcenter.

    Args:
        xyz_file (str): XYZ file path to import
        separator (str): Separator of XYZ file; default is "space"
    Returns:
        res (float): Resolution of the XYZ file
        xyz_reg (dict): Dictionary with region of the XYZ file
        shift_needed (bool): Boolean if the XYZ file hat to be shifted

    """
    gdalinfo_cmd = ["gdalinfo", xyz_file]
    process = grass.Popen(gdalinfo_cmd, stdout=PIPE, stderr=PIPE)
    stdout = process.communicate()[0].decode("utf-8").strip()
    # output vom ogrinfo:
    # z.B.: Pixel Size = (1.000000000000000,1.000000000000000)
    res = float(stdout.split("Pixel Size = (")[1].split(",")[0])
    # get bbox
    bbox_x1 = float(
        stdout.split("Upper Left")[1].replace("(", "").split(",")[0].strip(),
    )
    bbox_x2 = float(
        stdout.split("Upper Right")[1].replace("(", "").split(",")[0].strip(),
    )
    bbox_y1 = float(
        stdout.split("Upper Left")[1].split(",")[1].split(")")[0].strip(),
    )
    bbox_y2 = float(
        stdout.split("Lower Left")[1].split(",")[1].split(")")[0].strip(),
    )
    # check if shift is needed
    # The shift is only needed if the bbox does not contain the pixel centers
    # (in the bbox the half of the resolution could be seen)
    shift_needed = True
    half_res = res / 2.0
    if (
        bbox_x1 % res != half_res
        and bbox_x2 % res != half_res
        and bbox_y1 % res != half_res
        and bbox_y2 % res != half_res
    ):
        shift_needed = False
    # get region to xyz file
    xyz_reg_str = grass.read_command(
        "r.in.xyz",
        output="dummy",
        input=xyz_file,
        flags="sg",
        separator=separator,
    )
    xyz_reg = {
        item.split("=")[0]: float(item.split("=")[1])
        for item in xyz_reg_str.strip().split(" ")
    }
    xyz_reg["n"] += half_res
    xyz_reg["s"] -= half_res
    xyz_reg["w"] -= half_res
    xyz_reg["e"] += half_res
    return res, xyz_reg, shift_needed


def import_single_local_xyz_file(
    xyz_file,
    output,
    use_cur_reg=False,
    separator="space",
):
    """Import single XYZ file.

    Args:
        xyz_file (str): XYZ file path to import
        output (str): Output raster file name
        use_cur_reg (bool): If True the XYZ file will only be imported if it
                            overlaps with the current region, otherwise it
                            will not be imported
        separator (str): Separator of XYZ file; default is "space"
    Returns:
        output (str): If the output is imported, otherwise return None

    """
    res, xyz_reg, shift_needed = get_xyz_file_infos(
        xyz_file,
        separator=separator,
    )
    # check if aoi overlaps
    if use_cur_reg:
        cur_reg = grass.region()
        if (
            cur_reg["e"] < xyz_reg["w"]
            or xyz_reg["e"] < cur_reg["w"]
            or cur_reg["n"] < xyz_reg["s"]
            or xyz_reg["n"] < cur_reg["s"]
        ):
            return None
    # set region
    grass.run_command(
        "g.region",
        n=xyz_reg["n"],
        s=xyz_reg["s"],
        w=xyz_reg["w"],
        e=xyz_reg["e"],
        res=res,
    )
    if use_cur_reg:
        while (cur_reg["n"] + res) < xyz_reg["n"]:
            grass.run_command("g.region", n=f"n-{res}")
            xyz_reg["n"] -= res
        while (cur_reg["s"] - res) > xyz_reg["s"]:
            grass.run_command("g.region", s=f"s+{res}")
            xyz_reg["s"] += res
        while (cur_reg["e"] + res) < xyz_reg["e"]:
            grass.run_command("g.region", e=f"e-{res}")
            xyz_reg["e"] -= res
        while (cur_reg["w"] - res) > xyz_reg["w"]:
            grass.run_command("g.region", w=f"w+{res}")
            xyz_reg["w"] += res
    # import data
    grass.run_command(
        "r.in.xyz",
        input=xyz_file,
        output=output,
        method="mean",
        separator=separator,
        quiet=True,
        overwrite=True,
    )
    # shift data if needed
    if shift_needed:
        grass.run_command(
            "g.region",
            n=f"n+{res / 2.}",
            s=f"s+{res / 2.}",
            w=f"w+{res / 2.}",
            e=f"e+{res / 2.}",
            res=res,
        )
        grass.run_command("r.region", map=output, flags="c")
    return output


def import_local_xyz_files(
    aoi,
    basename,
    local_data_dir,
    all_raster,
):
    """Import local XYZ raster data.  XYZ files which are inside the
    directory of "local_data_dir" will be imported for the AOI.

    Args:
        aoi (str): Vector map with area of interest
        basename (str): Basename for imported rasters
        local_data_dir (str): Path to local data directory with XYZ files
        all_raster (list/dict): empty list/dictionary where the imported rasters
                                will be appended
    Returns:
        imported_local_data (bool): True if local data imported, otherwise False

    """
    grass.message(_("Importing local XYZ data..."))
    imported_local_data = False

    # get XYZ files
    xyz_files = glob.glob(
        os.path.join(local_data_dir, "**", "*.xyz"),
        recursive=True,
    )

    # import data for AOI
    # TODO parallelize local data import
    # get current region
    cur_reg = grass.region()
    ns_res = cur_reg["nsres"]
    ew_res = cur_reg["ewres"]
    for i, xyz_file in enumerate(xyz_files):
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
        name = import_single_local_xyz_file(xyz_file, name, True)
        if name:
            all_raster.append(name)
            grass.message(
                _(f"XYZ file <{os.path.basename(xyz_file)}> imported."),
            )
    # check if raster were imported
    if len(all_raster) > 0:
        imported_local_data = True
    return imported_local_data


def import_local_vector_data(aoi_map, local_data_dir, rm_vectors, output):
    """Import vector data from local file path.

    Args:
        aoi_map (str): Name of vector map defining AOI
        local_data_dir (str): Path to local data
        rm_vectors (list): List with vectors that should be removed
        output (str): Output map

    Returns:
        imported_local_data (bool): True if local data imported, otherwise False

    """
    imported_local_data = False

    # get files (GPKG or SHP)
    files = glob.glob(
        os.path.join(local_data_dir, "**", "*.gpkg"),
        recursive=True,
    )
    shp_files = glob.glob(
        os.path.join(local_data_dir, "**", "*.shp"),
        recursive=True,
    )
    files.extend(shp_files)

    # import data for AOI
    imported_list = []
    for i, file in enumerate(files):
        if aoi_map:
            grass.run_command(
                "g.region",
                vector=aoi_map,
                quiet=True,
            )
        grass.run_command(
            "v.import",
            input=file,
            output=f"{output}_{i}",
            extent="region",
            quiet=True,
        )
        imported_list.append(f"{output}_{i}")

    # patch outputs
    patch_vectors(imported_list, output, rm_vectors)

    # check if result has at least one feature
    map_info = grass.parse_command(
        "v.info",
        map=output,
        flags="gt",
    )
    if int(map_info["centroids"]) > 0:
        imported_local_data = True

    return imported_local_data
