#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      vector.py
# AUTHOR(S):   Anika Weinmann, Julia Haas
#
# PURPOSE:     functions for general vector processing
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

import grass.script as grass


def patch_vectors(vector_list, output, rm_vectors=None):
    """Patch vector data from a list.

    Args:
        vector_list (list): List with vectors to patch
        output (str): Output map
        rm_vectors (list): List with vectors that should be removed

    """
    # patch several vectors (e.g. from parallel imports)
    if len(vector_list) > 1:
        grass.run_command(
            "v.patch",
            input=vector_list,
            output=output,
            flags="e",
            quiet=True,
        )
        if rm_vectors is not None:
            rm_vectors.extend(vector_list)
    else:
        grass.run_command(
            "g.rename",
            vector=f"{vector_list[0]},{output}",
            quiet=True,
        )
