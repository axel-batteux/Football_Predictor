import os
import requests
import pandas as pd
from io import StringIO
from datetime import datetime

DATA_DIR = "data/tennis"
# Switch to Jeff Sackmann's GitHub (Reliable)
BASE_URL_ATP = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master"
BASE_URL_WTA = "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master"

YEARS = [2024, 2025] 

def download_data():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    print("=== Downloading Tennis Data (Source: Jeff Sackmann GitHub) ===")
    
    for year in YEARS:
        # URL Logic for Jeff Sackmann Repo
        # ATP: atp_matches_YYYY.csv
        # WTA: wta_matches_YYYY.csv
        
        atp_url = f"{BASE_URL_ATP}/atp_matches_{year}.csv"
        wta_url = f"{BASE_URL_WTA}/wta_matches_{year}.csv"
        
        # Download ATP
        _download_file(atp_url, f"atp_{year}.csv")
        # Download WTA
        _download_file(wta_url, f"wta_{year}.csv")

def _download_file(url, filename):
    try:
        print(f"Fetching {url}...")
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            with open(os.path.join(DATA_DIR, filename), 'wb') as f:
                f.write(r.content)
            print(f" -> Success: {filename}")
        else:
            print(f" -> Not Found (HTTP {r.status_code}): {filename}")
    except Exception as e:
        print(f" -> Error downloading {filename}: {e}")

if __name__ == "__main__":
    download_data()
