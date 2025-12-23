from src.model import Ligue1Predictor
from src.tournament_sim import SQUAD_BOOSTS, HOST_COUNTRY

def simulate_final():
    print("--- SIMULATION DE LA FINALE : MAROC vs SÉNÉGAL ---")
    
    try:
        predictor = Ligue1Predictor(data_file="data/AFCON.csv")
    except Exception as e:
        print(f"Erreur: {e}")
        return

    home_team = "Morocco"
    away_team = "Senegal"
    
    # Prepare modifiers manually to be sure
    modifiers = {}
    
    # Team 1: Morocco (Host + Tier 1)
    mods_home = {'attack': 1.0, 'defense': 1.0}
    boost_home = SQUAD_BOOSTS.get(home_team, 1.0)
    mods_home['attack'] *= boost_home
    mods_home['defense'] *= (1.0 - (boost_home - 1.0))
    # Host Boost
    if home_team == HOST_COUNTRY:
        mods_home['attack'] *= 1.15
    modifiers[home_team] = mods_home

    # Team 2: Senegal (Tier 1)
    mods_away = {'attack': 1.0, 'defense': 1.0}
    boost_away = SQUAD_BOOSTS.get(away_team, 1.0)
    mods_away['attack'] *= boost_away
    mods_away['defense'] *= (1.0 - (boost_away - 1.0))
    modifiers[away_team] = mods_away

    print(f"\nParamètres :")
    print(f"- {home_team} : Bonus Hôte (+15%) + Squad Tier 1 (+15%)")
    print(f"- {away_team} : Squad Tier 1 (+15%)")
    
    # Predict with neutral_venue=True (It's a final) BUT modifiers handle the host advantage
    results = predictor.predict_match(home_team, away_team, neutral_venue=True, modifiers=modifiers)
    
    if "error" in results:
        print(f"Erreur : {results['error']}")
    else:
        print("\n=== RÉSULTATS DU MATCH ===")
        print(f"Probabilité Victoire {home_team} : {results['win_prob']}%")
        print(f"Probabilité Match Nul (Prolongations) : {results['draw_prob']}%")
        print(f"Probabilité Victoire {away_team} : {results['loss_prob']}%")
        print(f"Score le plus probable : {results['most_likely_score']}")
        print(f"Confiance score : {results['score_prob']}%")
        print(f"xG (Buts attendus) : {results['expected_goals_home']} - {results['expected_goals_away']}")

if __name__ == "__main__":
    simulate_final()
