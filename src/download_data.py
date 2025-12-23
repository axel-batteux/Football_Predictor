import os
import requests

def download_data():
    base_url = "https://www.football-data.co.uk/mmz4281/{}/{}.csv"
    # Saisons: 2526 = 2025/2026 (actuelle), puis historique
    seasons = ["2526", "2425", "2324", "2223"]
    
    leagues = {
        "E0": "Premier League",
        "D1": "Bundesliga",
        "I1": "Serie A",
        "SP1": "La Liga",
        "F1": "Ligue 1",
        "F2": "Ligue 2"
    }

    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    for code, name in leagues.items():
        print(f"\nDownloading data for {name} ({code})...")
        for season in seasons:
            url = base_url.format(season, code)
            filename = os.path.join(data_dir, f"{code}_{season}.csv")
            
            try:
                response = requests.get(url)
                response.raise_for_status()
                
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f" -> {season}: Done.")
            except requests.exceptions.RequestException as e:
                print(f" -> {season}: Failed ({e})")

if __name__ == "__main__":
    download_data()
