#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      federal_state.py
# AUTHOR(S):   Anika Weinmann
#
# PURPOSE:     open-geodata-germany: infos and functions to federale states
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

import os
import requests
import grass.script as grass

FS_ABBREVIATION = {
    "Baden-Württemberg": "BW",
    "BW": "BW",
    "Bayern": "BY",
    "BY": "BY",
    "Berlin": "BE",
    "BE": "BE",
    "Brandenburg": "BB",
    "BB": "BB",
    "Bremen": "HB",
    "HB": "HB",
    "Hamburg": "HH",
    "HH": "HH",
    "Hessen": "HE",
    "HE": "HE",
    "Mecklenburg-Vorpommern": "MV",
    "MV": "MV",
    "Niedersachsen": "NI",
    "NI": "NI",
    "Nordrhein-Westfalen": "NW",
    "NW": "NW",
    "Rheinland-Pfalz": "RP",
    "RP": "RP",
    "Saarland": "SL",
    "SL": "SL",
    "Sachsen": "SN",
    "SN": "SN",
    "Sachsen-Anhalt": "ST",
    "ST": "ST",
    "Schleswig-Holstein": "SH",
    "SH": "SH",
    "Thüringen": "TH",
    "TH": "TH",
}


def import_administrative_boundaries(output, aoi=None, level="KRS"):
    """Import administrative boundaries for AOI/region.

    Args:
        output (str): The name for the output vector map with the imported
                      administrative boundaries
        aoi (str): The name of the area of interest for which the
                   administrative boundaries should be imported; if aoi is set
                   to None the boundaries will be imported for the current
                   region
        level (str): The level of the administrative boundaries;
                     STA - Staat
                     LAN - Länder
                     RBZ - Regierungsbezirke
                     KRS - Kreise
                     VWG - Verwaltungsgemeinschaften
                     GEM - Gemeinden

    """
    # save current region and set region to AOI
    if aoi:
        reg = f"tmp_region_{grass.tempname(8)}"
        grass.run_command("g.region", save=reg)
        grass.run_command("g.region", vector=aoi, quiet=True)

    # url of administrative boundaries
    url = (
        "https://daten.gdz.bkg.bund.de/produkte/vg/vg5000_0101/"
        "aktuell/vg5000_01-01.utm32s.shape.ebenen.zip"
    )
    # file of administrative boundaries in zip
    filename = os.path.join(
        "vg5000_01-01.utm32s.shape.ebenen",
        "vg5000_ebenen_0101",
        f"VG5000_{level}.shp",
    )
    try:
        # check if URL is reachable
        response = requests.get(url)
        if response.status_code != 200:
            grass.fatal(
                "The data import of the administrative boundaries are "
                "currently not available.",
            )

        # download and import administrative boundaries
        vsi_url = f"/vsizip/vsicurl/{url}/{filename}"
        grass.run_command(
            "v.import",
            input=vsi_url,
            output=output,
            extent="region",
            quiet=True,
        )
    finally:
        if aoi:
            grass.run_command("g.region", region=reg)


def get_federal_states(federal_state, federal_state_file):
    """Get federal state and federal state file module parameters and return
    list with federal state abbreviations.

    Args:
        federal_state (str): Federal state module parameter
        federal_state_file (str): Federal state file module parameter
    Returns:
        (list): List with federal state abbreviations

    """
    if federal_state_file:
        if not os.path.isfile(federal_state_file):
            grass.fatal(
                _(
                    "Federal state file is given, but file "
                    f"<{federal_state_file}> does not exist.",
                ),
            )
        with open(federal_state_file, encoding="utf-8") as fs_file:
            fs_list_str = fs_file.read().strip()
            if fs_list_str == "":
                grass.fatal(
                    _(
                        "Federal state in <federal_state_file> is empty "
                        "string!",
                    ),
                )
    elif federal_state:
        fs_list_str = federal_state.strip()
    else:
        grass.fatal(
            _(
                "Neither <federal_state> nor <federal_state_file> are given. "
                "Please set one of the two.",
            ),
        )
    fs_list = []
    for fs in fs_list_str.split(","):
        fs = fs.strip()
        if fs not in FS_ABBREVIATION:
            grass.fatal(_(f"Non valid name of federal state: {fs}"))
        fs_list.append(FS_ABBREVIATION[fs])
    return fs_list
