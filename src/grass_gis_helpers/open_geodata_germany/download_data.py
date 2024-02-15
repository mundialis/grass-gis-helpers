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

from multiprocessing.pool import ThreadPool
import os
import requests
from zipfile import ZipFile

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


def url_response(url):
    """URL response function which is used by download_data_using_threadpool

    Arsg:
        url (str): data download url
    Return:
        url (str): Return the url for printing
    """
    filename = os.path.basename(url)
    response = requests.get(url, stream=True)
    with open(str(filename), "wb") as f:
        for chunk in response:
            f.write(chunk)
    return url


def download_data_using_threadpool(urls, download_dir, nprocs):
    """Download data from urls via ThreadPool

    Args:
        urls (list): List with data download urls
        download_dir (str): Path to directory where the data should be
                            downloaded
        nprocs (int): The number of worker threads to use; If processes is None
                      then the number returned by os.cpu_count() is used.
    """
    cur_dir = os.getcwd()
    try:
        os.chdir(download_dir)
        pool = ThreadPool(nprocs)
        results = pool.imap_unordered(url_response, urls)
        grass.message(_("Downloading data of url:"))
        for result in results:
            print(result)
    finally:
        os.chdir(cur_dir)


def extract_compressed_files(file_names, download_dir):
    """Extract compressed files to download directory.
    Args:
        file_names (list): List with compressed e.g. zip file names which
                           are stored in the download_dir
        download_dir (str): Path to directory where the data should be
                            downloaded
    """
    for file_name in file_names:
        file = os.path.join(download_dir, file_name)
        with ZipFile(file, "r") as zipObj:
            # Extract all the contents of zip file in current directory
            zipObj.extractall(download_dir)