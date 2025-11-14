#!/usr/bin/env python3
"""
Utilities to download and extract FAA NASR zip files.

This module provides small helpers used by scripts/tests to fetch the NASR
edition zip and extract it locally.
"""

import argparse
import datetime
import logging
import tempfile
import zipfile
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

zip_file_finder = "https://external-api.faa.gov/apra/nfdc/nasr/chart"

edition_date: str | None = None

logger = logging.getLogger(__name__)

retry_strategy = Retry(total=60, backoff_factor=1.0)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)


def get_download_url(edition: str = "current") -> str:
    """Return the download URL for the requested NASR edition and set global edition_date."""
    global edition_date
    params = {"edition": edition}
    headers = {"Accept": "application/json"}
    logger.info("Checking %s to find the desired zip file", zip_file_finder)
    r = http.get(zip_file_finder, params=params, headers=headers, timeout=10)
    edition_date = (
        datetime.datetime.strptime(r.json()["edition"][0]["editionDate"], "%m/%d/%Y")
        .date()
        .isoformat()
    )
    return r.json()["edition"][0]["product"]["url"]


def download_nasr_zip(zip_url: str, path: str | None = None) -> str:
    """
    Download the NASR zip file and return the local path to the file.

    If ``path`` is omitted a temporary directory is used.
    """
    base_download_dir = Path(path) if path else Path(tempfile.mkdtemp())

    if edition_date is None:
        msg = "edition_date must be set by get_download_url"
        raise RuntimeError(msg)
    download_dir = base_download_dir / edition_date
    download_dir.mkdir(parents=True, exist_ok=True)

    zip_name = zip_url.split("/")[-1]
    full_path = download_dir / zip_name

    logger.info("Downloading zip file %s to %s", zip_url, str(full_path))
    with full_path.open("wb") as f, http.get(zip_url, timeout=10, stream=True) as r:
        f.writelines(r.iter_content(chunk_size=4096))

    logger.info("Download complete")
    return str(full_path)


def extract_nasr_zip(zip_path: str) -> str:
    """Extract the given zip file and return the extraction directory."""
    extract_dir = str(Path(zip_path).parent)
    logger.info("Extracting %s to %s", zip_path, extract_dir)
    with zipfile.ZipFile(zip_path, "r") as f:
        f.extractall(path=extract_dir)

    logger.info("Extraction complete")
    return extract_dir


def download_and_extract_nasr_zip(
    edition: str = "current", path: str | None = None
) -> str:
    """Download and extract the NASR zip for ``edition`` and return the extraction directory."""
    if not path:
        return extract_nasr_zip(download_nasr_zip(get_download_url(edition=edition)))
    return extract_nasr_zip(
        download_nasr_zip(get_download_url(edition=edition), path=path)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--edition", help="current or next", default="current")
    parser.add_argument(
        "-l",
        "--log-level",
        help="how much logging do you want?",
        choices=["debug", "info", "warning", "error", "critical"],
        default="warning",
    )
    args = parser.parse_args()
    log_level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    logging.basicConfig(level=log_level_map[args.log_level])
    print(
        download_and_extract_nasr_zip(
            edition=args.edition,
            path=str(Path(tempfile.gettempdir()) / "faa_nasr_data"),
        )
    )
