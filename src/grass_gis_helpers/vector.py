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
from grass.script import vector_columns, vector_db

from os import getpid

from .cleanup import general_cleanup


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


def clean_vector_cat(input, output):
    """Create unique cat in attribute table (layer 1)."""
    rm_vector = list()
    try:
        pid = getpid()

        # Get vector column names (except cat column)
        vec_cols = vector_columns(input, layer=1)
        del vec_cols["cat"]

        tablename = vector_db(input)[1]["table"]
        dbkey = vector_db(input)[1]["key"]
        grass.run_command("v.db.connect", map=input, flags="d")
        out_tmp1 = f"{input}_{pid}_tmp1"
        rm_vector.append(out_tmp1)
        grass.run_command(
            "v.category",
            input=input,
            output=out_tmp1,
            option="chlayer",
            layer="1,2",
        )
        out_tmp2 = f"{input}_{pid}_tmp2"
        rm_vector.append(out_tmp2)
        grass.run_command(
            "v.category",
            input=out_tmp1,
            output=out_tmp2,
            option="del",
            layer=1,
            cat=-1,
        )
        out_tmp3 = f"{input}_{pid}_tmp3"
        rm_vector.append(out_tmp3)
        grass.run_command(
            "v.category",
            input=out_tmp2,
            output=out_tmp3,
            option="add",
            layer=1,
            cat=1,
            step=1,
        )
        grass.run_command(
            "v.db.connect",
            map=out_tmp3,
            layer=2,
            table=tablename,
            key=dbkey,
        )
        vec_cols_types = ", ".join(
            f"{col} {info['type']}" for col, info in vec_cols.items()
        )
        grass.run_command(
            "v.db.addtable",
            map=out_tmp3,
            column=f"cat INTEGER, {vec_cols_types}",
            key="cat",
            layer=1,
        )
        for col in vec_cols.keys():
            grass.run_command(
                "v.to.db",
                map=out_tmp3,
                type="centroid",
                layer=1,
                column=col,
                option="query",
                query_layer=2,
                query_col=col,
            )
        grass.run_command(
            "v.db.droptable",
            map=out_tmp3,
            layer=2,
            flags="f",
        )
        grass.run_command(
            "v.category",
            input=out_tmp3,
            output=output,
            option="del",
            layer=2,
            cat=-1,
        )
    except Exception as e:
        raise e
    finally:
        general_cleanup(rm_vectors=rm_vector)
