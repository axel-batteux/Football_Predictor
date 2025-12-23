from src.model import Ligue1Predictor
import pandas as pd

def predict_competition_winner():
    print("Chargement du modèle AFCON...")
    try:
        predictor = Ligue1Predictor(data_file="data/AFCON.csv")
    except Exception as e:
        print(f"Erreur: {e}")
        return

    print("Analyse des forces en présence...\n")
    
    # We can access the trained stats from the predictor
    stats = predictor.team_stats.copy()
    
    # We will create a "Power Score"
    # A simple metric: Attack Strength - Defense Strength (lower defense is better, so we invert logic or just subtract?)
    # Attack > 1 is good (scores more than avg). Defense < 1 is good (concedes less than avg).
    # Simple Score = Attack Strength + (2 - Defense Strength) 
    # (Assuming defense oscillates around 1. If Defense is 0.5 (good), score adds 1.5. If Defense is 1.5 (bad), score adds 0.5)
    
    # We need to average Home and Away stats because in a tournament, venues are neutral (mostly), 
    # but our model distinguishes Home/Away. 
    # For a tournament hosted in Morocco, Morocco is Home, others are Away/Neutral.
    # But for a general "Power Ranking", let's average Home and Away perf.
    
    stats['OverallAttack'] = (stats['HomeAttackStrength'] + stats['AwayAttackStrength']) / 2
    stats['OverallDefense'] = (stats['HomeDefenseStrength'] + stats['AwayDefenseStrength']) / 2
    
    # Higher Score = Better
    # We want High Attack and Low Defense.
    # Score = OverallAttack / OverallDefense
    stats['PowerScore'] = stats['OverallAttack'] / stats['OverallDefense']
    
    # Sort by Power Score
    ranked_teams = stats.sort_values(by='PowerScore', ascending=False)
    
    print("--- CLASSEMENT DES FAVORIS (Selon le modèle) ---")
    print(f"{'Rang':<5} {'Équipe':<20} {'Score Puissance':<15} {'Attaque':<10} {'Défense (Bas=Bon)':<10}")
    print("-" * 70)
    
    for i, (team, row) in enumerate(ranked_teams.head(10).iterrows(), 1):
        print(f"{i:<5} {team:<20} {row['PowerScore']:.3f}           {row['OverallAttack']:.3f}      {row['OverallDefense']:.3f}")
        
    print("\nNote: Le 'Score Puissance' compare l'efficacité offensive par rapport à la solidité défensive.")
    print("Le Maroc (Pays hôte) a un avantage supplémentaire non compté ici s'ils jouent à domicile.")

if __name__ == "__main__":
    predict_competition_winner()
