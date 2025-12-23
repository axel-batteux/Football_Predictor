import pandas as pd
import os

print("=== VÉRIFICATION DES DONNÉES ===\n")

# Check Premier League current season (2025-2026)
file = 'data/E0_2526.csv'
if os.path.exists(file):
    df = pd.read_csv(file, encoding='latin1')
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['Date'])
    
    print(f"Fichier: {file}")
    print(f"Premier match: {df['Date'].min()}")
    print(f"Dernier match disponible: {df['Date'].max()}")
    print(f"Nombre de matchs: {len(df)}")
    
    # Check matches in last 30 days
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent = df[df['Date'] >= thirty_days_ago]
    print(f"\nMatchs des 30 derniers jours: {len(recent)}")
else:
    print(f"Fichier {file} non trouvé")
