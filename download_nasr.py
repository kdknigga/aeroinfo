#!/usr/bin/env python3

import os
import requests
import tempfile
import zipfile

zip_file_finder = "https://soa.smext.faa.gov/apra/nfdc/nasr/chart"

def get_download_url(edition="current"):
    params = {'edition': edition}
    headers = {'Accept': 'application/json'}
    r = requests.get(zip_file_finder, params=params, headers=headers, timeout=10)
    return r.json()['edition'][0]['product']['url']

def download_nasr_zip(zip_url, path=None):
    if not path:
        download_dir = tempfile.mkdtemp()
    else:
        download_dir = path
        os.mkdir(download_dir)

    zip_name = zip_url.split("/")[-1]
    full_path = download_dir + "/" + zip_name

    with open(full_path, 'wb') as f:
        with requests.get(zip_url, timeout=10, stream=True) as r:
            for chunk in r.iter_content(chunk_size=4096):
                f.write(chunk)

    return full_path

def extract_nasr_zip(zip_path):
    extract_dir = os.path.dirname(zip_path)
    with zipfile.ZipFile(zip_path, 'r') as f:
        f.extractall(path=extract_dir)

    return extract_dir

def download_and_extract_nasr_zip(edition="current", path=None):
    if not path:
        return extract_nasr_zip(download_nasr_zip(get_download_url()))
    else:
        return extract_nasr_zip(download_nasr_zip(get_download_url(), path=path))


if __name__ == "__main__":
    print(download_and_extract_nasr_zip())