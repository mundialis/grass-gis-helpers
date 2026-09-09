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
# SPDX-FileCopyrightText: 2024 Anika Weinmann, Julia Haas
# SPDX-FileCopyrightText: 2024 mundialis GmbH & Co. KG and the GRASS
#                         Development Team
# SPDX-License-Identifier: GPL-3.0-or-later
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
