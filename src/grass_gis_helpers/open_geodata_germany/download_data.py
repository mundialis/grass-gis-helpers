#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      download_data.py
# AUTHOR(S):   Anika Weinmann
#
# PURPOSE:     open-geodata-germany: functions for the download
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


def check_download_dir(download_dir):
    """Checks if download directory is set. If yes check if folder exists or
    creating it. If not set a temporary directory

    Args:
        download_dir (str): download directory module parameter
    Returns:
        (str): Path to download directory
    """
    if not download_dir:
        download_dir = grass.tempdir()
    else:
        if not os.path.isdir(download_dir):
            grass.message(
                _(
                    f"Download folder {download_dir} does not exist and will "
                    "be created."
                )
            )
            os.makedirs(download_dir)
    grass.message(f"Download directory: {download_dir}")
    return download_dir
