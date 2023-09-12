#!/usr/bin/env python3

import argparse
import datetime
import logging
import os
import tempfile
import zipfile

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

zip_file_finder = "https://external-api.faa.gov/apra/nfdc/nasr/chart"
edition_date = None

retry_strategy = Retry(total=60, backoff_factor=1.0)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)


def get_download_url(edition="current"):
    global edition_date
    params = {"edition": edition}
    headers = {"Accept": "application/json"}
    logging.info("Checking {} to find the desired zip file".format(zip_file_finder))
    r = http.get(zip_file_finder, params=params, headers=headers, timeout=10)
    edition_date = (
        datetime.datetime.strptime(r.json()["edition"][0]["editionDate"], "%m/%d/%Y")
        .date()
        .isoformat()
    )
    return r.json()["edition"][0]["product"]["url"]


def download_nasr_zip(zip_url, path=None):
    if not path:
        base_download_dir = tempfile.mkdtemp()
    else:
        base_download_dir = path

    download_dir = os.path.join(base_download_dir, edition_date)
    os.makedirs(download_dir, exist_ok=True)

    zip_name = zip_url.split("/")[-1]
    full_path = download_dir + "/" + zip_name

    logging.info("Downloading zip file {} to {}".format(zip_url, full_path))
    with open(full_path, "wb") as f:
        with http.get(zip_url, timeout=10, stream=True) as r:
            for chunk in r.iter_content(chunk_size=4096):
                f.write(chunk)

    logging.info("Download complete")
    return full_path


def extract_nasr_zip(zip_path):
    extract_dir = os.path.dirname(zip_path)
    logging.info("Extracting {} to {}".format(zip_path, extract_dir))
    with zipfile.ZipFile(zip_path, "r") as f:
        f.extractall(path=extract_dir)

    logging.info("Extraction complete")
    return extract_dir


def download_and_extract_nasr_zip(edition="current", path=None):
    if not path:
        return extract_nasr_zip(download_nasr_zip(get_download_url(edition=edition)))
    else:
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
        download_and_extract_nasr_zip(edition=args.edition, path="/tmp/faa_nasr_data")
    )
