"""
Pipeline Step 1: Fetch and Extract Raw Cricsheet Match Data (IPL & T20Is)
Downloads the official Cricsheet JSON archives and extracts them into data/raw/.
"""

import os
import io
import zipfile
import urllib.request
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

DATASETS = {
    "ipl": {
        "url": "https://cricsheet.org/downloads/ipl_json.zip",
        "extract_to": os.path.join(RAW_DIR, "ipl_json")
    },
    "t20s": {
        "url": "https://cricsheet.org/downloads/t20s_json.zip",
        "extract_to": os.path.join(RAW_DIR, "t20s_json")
    }
}

def download_and_extract(name: str, info: dict, force: bool = False):
    extract_path = info["extract_to"]
    url = info["url"]
    
    if os.path.exists(extract_path) and len(os.listdir(extract_path)) > 10 and not force:
        match_count = len([f for f in os.listdir(extract_path) if f.endswith(".json")])
        logging.info(f"'{name}' dataset already exists at {extract_path} with {match_count} JSON matches. Skipping download.")
        return match_count

    os.makedirs(extract_path, exist_ok=True)
    logging.info(f"Downloading {name} dataset from {url}...")
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CricketResearchBenchmark/1.0"}
    req = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(req, timeout=120) as resp:
        content = resp.read()
        logging.info(f"Downloaded {len(content) / (1024 * 1024):.2f} MB. Extracting archive...")
        
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            z.extractall(extract_path)
            
    match_count = len([f for f in os.listdir(extract_path) if f.endswith(".json")])
    logging.info(f"Successfully extracted {match_count} JSON matches for '{name}'.")
    return match_count

def main(force: bool = False):
    logging.info("Starting Cricsheet raw data acquisition...")
    total_matches = 0
    for name, info in DATASETS.items():
        count = download_and_extract(name, info, force=force)
        total_matches += count
    logging.info(f"All raw data ready! Total raw matches: {total_matches}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Cricsheet raw datasets")
    parser.add_argument("--force", action="store_true", help="Force re-download")
    args = parser.parse_args()
    main(force=args.force)
