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


def get_federal_states(federal_state, federal_state_file):
    """Get federale state and federal state file module parameters and return
    list with federal state abbrevations

    Args:
        federal_state (str): federal state module parameter
        federal_state_file (str): federal state file module parameter
    Returns:
        (list): list with federale state abbrevations

    """
    if federal_state_file:
        if not os.path.isfile(federal_state_file):
            grass.fatal(
                _(
                    f"Federal state file is given, but file "
                    "<{federal_state_file}> does not exists."
                )
            )
        with open(federal_state_file) as fs_file:
            fs_list_str = fs_file.read().strip()
    elif federal_state:
        fs_list_str = federal_state.strip()
    else:
        grass.fatal(
            _(
                "Neither <federal_state> nor <federal_state_file> are given. "
                "Please set one of the two."
            )
        )
    fs_list = []
    for fs in fs_list_str.split(","):
        fs = fs.strip()
        if fs not in FS_ABBREVIATION:
            grass.fatal(_(f"Non valid name of federal state: {fs}"))
        fs_list.append(FS_ABBREVIATION[fs])
    return fs_list
