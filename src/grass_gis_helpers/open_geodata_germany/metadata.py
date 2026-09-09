#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      metadata.py
# AUTHOR(S):   Leon Louwarts
# PURPOSE:     Utility functions for metadata collection and export in raster
#              import modules
# SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG and the
#                             GRASS Development Team
# SPDX-License-Identifier: GPL-3.0-or-later
#
############################################################################

import os
import re
import pathlib
import traceback
from datetime import datetime, timezone
from html.parser import HTMLParser

import grass.script as grass
from grass_gis_helpers.open_geodata_germany.federal_state import (
    FS_ABBREVIATION,
)


def get_urls_from_tindex(data_type="raster"):
    """Extract download URLs from tile index vector present in any mapset.

    Args:
        data_type (str): Label used in debug messages, e.g. "DOP" or
            "DEM". Does not affect the actual query.

    Returns:
        list (str): Deduplicated list of HTTPS download URLs

    """
    gisenv = grass.gisenv()
    current_mapset = gisenv["MAPSET"]

    # Search in current mapset first then in others
    mapsets = grass.read_command("g.mapsets", flags="p").strip().split()
    mapsets = [current_mapset] + [m for m in mapsets if m != current_mapset]

    urls = []
    tindex_found = None
    for mapset in mapsets:
        vectors = grass.list_grouped("vector").get(mapset, [])
        matching = [v for v in vectors if "tindex" in v.lower()]
        if matching:
            tindex_found = f"{matching[0]}@{mapset}"
            grass.debug(f"Found TINDEX: {tindex_found}")
            break

    if not tindex_found:
        grass.debug(f"No TINDEX found for {data_type}")
        return urls

    # Read attributes of TINDEX
    try:
        columns_info = grass.vector_columns(tindex_found)

        if "location" not in columns_info:
            grass.debug(
                f"'location' column not found in TINDEX {tindex_found}",
            )
            grass.debug(f"Available columns: {list(columns_info.keys())}")
            return urls

        grass.debug("Using 'location' column from TINDEX")

        # Read URLs from table
        result = grass.read_command(
            "v.db.select",
            map=tindex_found,
            columns="location",
            flags="c",
        ).strip()

        if result:
            for line in result.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # Parse URLs from location attribute
                urls_in_line = []

                # A "location" entry can contain multiple comma-separated URLs
                if "," in line:
                    parts = [p.strip() for p in line.split(",")]
                else:
                    parts = [line]

                for part in parts:
                    https_urls = re.findall(r"https://[^\s,]+", part)
                    urls_in_line.extend(https_urls)

                    urls.extend(urls_in_line)

        # Deduplicate while preserving the original order
        seen = set()
        urls = [url for url in urls if not (url in seen or seen.add(url))]

        grass.debug(f"Extracted {len(urls)} URLs from TINDEX")

    except Exception as e:
        grass.debug(f"Error reading TINDEX {tindex_found}: {e}")

        grass.debug(traceback.format_exc())

    return urls


def extract_filename_from_url(url):
    """Extract filename from a download URL.

    Args:
        url (str): Download URL.

    Returns:
        str: filename derived from the URL

    """
    # Strip query parameters before extracting the filename
    url_clean = url.split("?")[0]

    filename = os.path.basename(url_clean)

    # Extract actual raster filename from zip-packed downloads
    if ".zip" in url_clean:
        match = re.search(
            r"([^/]+\.(?:tif|tiff|jp2|xyz))(?:/|\.zip|$)",
            url_clean,
            re.IGNORECASE,
        )
        if match:
            filename = match.group(1)

    # Remove GDAl virtual filesystem prefixes that may still be attached
    return filename.replace("/vsizip/", "").replace("vsicurl/", "")


def get_federal_state_name(fs_abbr):
    """Get full name of federal state from abbreviation.

    Args:
        fs_abbr (str): Two-letter federal state abbreviation (e.g. "NW").

    Returns:
        str: Full federal state name if found, otherwise the abbreviation

    """
    for name, abbr in FS_ABBREVIATION.items():
        if abbr == fs_abbr and name != abbr:
            return name
    return fs_abbr


def get_license_and_url_from_addon(addon_name, addon_docs_root=None):
    """Parse license information and source URL from an addon HTML help file.
    The HTML file is expected to contain structured comment blocks with
    id, name, url, and source fields following a <br> tag.

    Args:
        addon_name (str): Full addon name, e.g. "r.dop.import.nw" or
            "r.idsm.import.nw". Needs to be given in main script
        addon_docs_root (str | None): Path to the docs/html directory
            Defaults to ~/.grass8/addons/docs/html.

    Returns:
        tuple [str | None]: (license_info, base_url)
            Both values are "None" when the HTML file cannot be found or
            does not contain the expected fields

    """
    try:
        if addon_docs_root is None:
            addon_docs_root = os.path.join(
                pathlib.Path("~").expanduser(),
                ".grass8",
                "addons",
                "docs",
                "html",
            )

        html_file = os.path.join(addon_docs_root, f"{addon_name}.html")

        if not pathlib.Path(html_file).exists():
            grass.debug(f"HTML file not found: {html_file}")
            return None, None

        # Read HTML file
        html_content = pathlib.Path(html_file).read_text(encoding="utf-8")

        if not html_content:
            grass.debug(f"HTML file is empty: {html_file}")
            return None, None

        license_info = None
        base_url = None

        # Search for license information
        id_match = re.search(
            r"<br>\s*id:\s*([^,\n]+)",
            html_content,
            re.IGNORECASE,
        )
        name_match = re.search(
            r"<br>\s*name:\s*([^,\n]+)",
            html_content,
            re.IGNORECASE,
        )
        url_match = re.search(
            r"<br>\s*url:\s*(https?://[^,\s\n]+)",
            html_content,
            re.IGNORECASE,
        )
        source_match = re.search(
            r"<br>\s*source:\s*(.+?)(?=\n|<h\d>)",
            html_content,
            re.DOTALL | re.IGNORECASE,
        )

        # All four fileds must be present, otherwise the license block is
        # considered incomplete/unusable
        if not all([id_match, name_match, url_match, source_match]):
            grass.debug(f"Incomplete license block in {html_file}")
            return None, None

        license_id = id_match.group(1).strip()
        license_name = name_match.group(1).strip()
        license_url = url_match.group(1).strip()
        source_html = source_match.group(1).strip()

        # Remove html tags from source info
        class MLStripper(HTMLParser):
            """Removes html tags from source info."""

            def __init__(self) -> None:
                super().__init__()
                self.strict = False
                self.convert_charrefs = True
                self.text = []

            def handle_data(self, data) -> None:
                """Callback called by HTML parser for each text node found."""
                self.text.append(data)

            def get_data(self) -> str:
                """Combines collected text parts into one string."""
                return "".join(self.text)

        s = MLStripper()
        s.feed(source_html)
        source_clean = s.get_data().strip()

        # Create formatted license information
        license_info = (
            f"{license_name} ({license_id}), "
            f"{license_url}, "
            f"Quelle: {source_clean}"
        )

        # Get base URL from source
        source_link_match = re.search(
            r'href=["\']([^"\']+)["\']',
            source_html,
        )
        if source_link_match:
            base_url = source_link_match.group(1).strip()

    except Exception as e:
        grass.warning(f"Could not extract license/URL for {addon_name}: {e}")
        return None, None
    else:
        return license_info, base_url


def collect_metadata(
    fs,
    raster_list,
    license_info=None,
    base_url=None,
    original_names=None,
    download_urls=None,
    band_suffixes=("_red", "_green", "_blue", "_nir"),
):
    """Collect metadata dictionary for downloaded rasters for federal state.

    The function determines which source files were imported using the
    following priority:

    1. original_names - explicit list of filenames (e.g. from local dir)
    2. download_urls - URLS are converted to filenames via
        :func:`extract_filename_from_url`
    3. Fallback - the raster names in raster_list are stripped of their
       band suffixes

    Args:
        fs (str): Federal state abbreviation
        raster_list (list): List of imported raster names
        license_info (str | None): Formatted license string
        base_url (str | None): Base URL of the data source
        original_names (list | None): original filenames (local import)
        download_urls (list | None): List of download URLs used
        band_suffixes (tuple): Suffixes appended to band raster names.
            Used only for the fallback file-name derivation

    Returns:
        dict: Keys: federal_state, download_date, license, base_url,
            raster_names, download_urls, count

    """
    # Priority 1: explicit local filenames take precedence, since they are
    # the most accurate source of truth (e.g. from local_data_dir import)
    if original_names and len(original_names) > 0:
        source_files = original_names
    # Priority 2: derive filenames from download URLs if no local names
    # are available
    elif download_urls and len(download_urls) > 0:
        source_files = [extract_filename_from_url(u) for u in download_urls]
    # Priority 3 (fallback): neither names nor URLs available -> derive
    # source file names from the imported raster names by stripping band
    # suffixes
    else:
        unique = set()
        for raster in raster_list:
            base = raster
            for suffix in band_suffixes:
                base = re.sub(re.escape(suffix) + r"$", "", base)
            unique.add(base)
        source_files = sorted(unique)

    return {
        "federal_state": fs,
        "download_date": datetime.now(tz=timezone.utc).strftime("%d.%m.%Y"),
        "license": license_info,
        "base_url": base_url,
        "raster_names": sorted(set(source_files)),
        "download_urls": download_urls or [],
        "count": len(source_files),
    }


def _write_licenses(f, metadata_list) -> None:
    """Write license section to markdown file."""
    f.write("## Lizenzen\n\n")
    # Multiple federal states can share the same license text; only write
    # each distinct license once
    seen_licenses = set()
    for fs_meta in metadata_list:
        fs_name = get_federal_state_name(fs_meta["federal_state"])
        lic = fs_meta["license"]
        if lic not in seen_licenses:
            seen_licenses.add(lic)
            f.write(f"**{fs_name}:** {lic}\n\n")


def _write_raster_name(f, name, data_label) -> bool:
    """Write a single raster name entry to markdown file."""
    if name.startswith("WMS"):
        # Special encoding used for WMS-based imports, e.g.
        # "WMS_RGB:<url>|LAYER:<layer>" -> parsed into key/value pairs
        parts = dict(
            item.split(":", 1) for item in name.split("|") if ":" in item
        )
        wms_url = next(
            (v for k, v in parts.items() if k.startswith("WMS")),
            "",
        )
        layer = parts.get("LAYER", "")
        f.write(f"- WMS: [{layer}]({wms_url})\n")
        return False

    if f"{data_label}-Kacheln" in name or "via WMS" in name:
        # Pre-formatted tile-count summary string (e.g. "12 DOP-Kachel(n)"),
        # written as-is instead of as a bullet point
        f.write(f"{name}\n\n")
        return True

    f.write(f"- `{name}`\n")
    return False


def _write_fs_section(f, fs_meta, fs_name, data_label) -> None:
    """Write downloaded files section for one federal state."""
    base_url = fs_meta["base_url"]
    f.write(
        f"### Folgende {data_label}s wurden aus {fs_name} "
        f"({base_url}) bezogen:\n\n",
    )

    # Preferred case: actual donwload URLs are available -> link each file
    if fs_meta.get("download_urls"):
        for url in fs_meta["download_urls"]:
            filename = extract_filename_from_url(url)
            f.write(f"- [{filename}]({url})\n")
        f.write(f"\n**Anzahl:** {fs_meta['count']}\n\n")
    else:
        # Fallback case: only raster/file names (or a tile-count summary)
        # are available
        has_tile_count_line = False
        for name in fs_meta["raster_names"]:
            if _write_raster_name(f, name, data_label):
                has_tile_count_line = True
        # Avoid a redundant "Anzahl" line if a tile-count summary was
        # already written by _write_raster_name
        if not has_tile_count_line:
            f.write(f"\n**Anzahl:** {fs_meta['count']}\n\n")
        else:
            f.write("\n")


def write_metadata_markdown(
    metadata_list,
    metadata_path,
    data_label="Raster",
    mapset=None,
):
    """Write Markdown metadata file summarising the import run.

    Args:
        metadata_list (list): One dict per federal state as returned by
            :func:`collect_metadata`
        metadata_path (str): Destination file path. A .md extension is
            appended automatically if missing. Pass an empty string or
            "None" to skip writing
        data_label (str): Human-readable label for the data type, e.g.
            "DOP" or "DEM". Used in section headings
        mapset (str | None): GRASS mapset name for the file header. Falls
            back to the current mapset when "None".

    """
    # Don't write metadata file if path not set
    if not metadata_path or metadata_path == "":
        grass.message(
            _("No metadata path specified. Skipping metadata file creation."),
        )
        return

    # Make sure path ends with ".md"
    if not metadata_path.endswith(".md"):
        metadata_path = f"{metadata_path}.md"

    # Create directory if it does not exist yet
    metadata_dir = pathlib.Path(metadata_path).parent
    if metadata_dir and not pathlib.Path(metadata_dir).exists():
        try:
            pathlib.Path(metadata_dir).mkdir(parents=True)
            grass.message(_(f"Created directory: {metadata_dir}"))
        except Exception as e:
            grass.warning(_(f"Could not create directory {metadata_dir}: {e}"))
            return

    if mapset is None:
        mapset = grass.gisenv()["MAPSET"]

    # Create markdown file
    try:
        with pathlib.Path(metadata_path).open("w", encoding="utf-8") as f:
            # Header
            f.write(f"# Metadaten der {data_label}s im Mapset {mapset}\n\n")

            if metadata_list:
                f.write(
                    "**Downloaddatum:** "
                    f"{metadata_list[0]['download_date']}\n\n",
                )

            _write_licenses(f, metadata_list)

            f.write(f"## Heruntergeladene {data_label}s\n\n")
            for fs_meta in metadata_list:
                fs_name = get_federal_state_name(fs_meta["federal_state"])
                _write_fs_section(f, fs_meta, fs_name, data_label)

            # Additional info
            today = datetime.now(tz=timezone.utc).strftime("%d.%m.%Y")
            f.write("---\n\n")
            f.write(f"*Erstellt am {today}\n")

        grass.message(_(f"Metadata file created: {metadata_path}"))

    except Exception as e:
        grass.warning(_(f"Could not write metadata file: {e}"))
