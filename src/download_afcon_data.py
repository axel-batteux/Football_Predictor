import pandas as pd
import requests
import io
import os
from datetime import datetime

def download_afcon_data():
    url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
    data_dir = "data"
    output_file = os.path.join(data_dir, "AFCON.csv")

    print(f"Downloading international data from {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.content.decode('utf-8')
        
        df = pd.read_csv(io.StringIO(content))
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter for AFCON tournaments and recent years
        # We include qualifiers and the main tournament
        # Let's take data from 2018 onwards to be relevant but have enough sample size
        relevant_tournaments = ["African Cup of Nations", "African Cup of Nations qualification"]
        start_date = "2018-01-01"
        
        mask = (df['tournament'].isin(relevant_tournaments)) & (df['date'] >= start_date)
        afcon_df = df[mask].copy()
        
        # Renaissance relevant columns for our model
        # Our model expects: Date, HomeTeam, AwayTeam, FTHG, FTAG
        afcon_df = afcon_df.rename(columns={
            'date': 'Date',
            'home_team': 'HomeTeam',
            'away_team': 'AwayTeam',
            'home_score': 'FTHG',
            'away_score': 'FTAG'
        })
        
        # Clean up
        afcon_df = afcon_df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']]
        
        print(f"Filtered {len(afcon_df)} AFCON matches since {start_date}.")
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        afcon_df.to_csv(output_file, index=False)
        print(f"Saved to {output_file}")
        
    except Exception as e:
        print(f"Error processing AFCON data: {e}")

if __name__ == "__main__":
    download_afcon_data()
