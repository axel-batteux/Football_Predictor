import random
from src.model import Ligue1Predictor
import collections

# --- CONFIGURATION DU TOURNOI ---
HOST_COUNTRY = "Morocco"

# Estimation "Manuelle" du boost "Qualité d'effectif" (Basé sur la valeur marchande théorique)
# 1.15 = Top Tier (World Class players)
# 1.10 = High Tier
# 1.05 = Mid Tier
# 1.00 = Base
SQUAD_BOOSTS = {
    # Tier 1
    "Morocco": 1.15, "Senegal": 1.15, "Nigeria": 1.15, "Ivory Coast": 1.15, "Egypt": 1.12,
    # Tier 2
    "Algeria": 1.10, "Cameroon": 1.10, "Mali": 1.10, "Ghana": 1.10, "Tunisia": 1.08,
    # Tier 3 (Outsiders)
    "South Africa": 1.05, "DR Congo": 1.05, "Burkina Faso": 1.05, "Guinea": 1.05
}

# 24 Équipes qualifiées (Liste approximative des habitués + qualifiés probables)
# Nous devons nous assurer que ces noms correspondent au CSV (anglais)
QUALIFIED_TEAMS = [
    "Ivory Coast", "Nigeria", "Equatorial Guinea", "Guinea-Bissau", # Group A (Ex 2023)
    "Egypt", "Ghana", "Cape Verde", "Mozambique", # Group B
    "Senegal", "Cameroon", "Guinea", "Gambia", # Group C
    "Algeria", "Burkina Faso", "Mauritania", "Angola", # Group D
    "Tunisia", "Mali", "South Africa", "Namibia", # Group E
    "Morocco", "DR Congo", "Zambia", "Tanzania" # Group F
]

def simulate_tournament(predictor, n_simulations=100):
    winners = []
    
    # Pre-calculate modifiers
    modifiers = {}
    for team in QUALIFIED_TEAMS:
        mods = {'attack': 1.0, 'defense': 1.0}
        
        # Squad Boost
        boost = SQUAD_BOOSTS.get(team, 1.0)
        mods['attack'] *= boost
        # Good squad also defends better (Defense factor < 1 is good)
        mods['defense'] *= (1.0 - (boost - 1.0)) 
        
        # Host Boost
        if team == HOST_COUNTRY:
            mods['attack'] *= 1.15 # Strong Home Advantage
        
        modifiers[team] = mods

    print(f"Simulation de {n_simulations} tournois...")

    for sim in range(n_simulations):
        # 1. PHASE DE POULES (Simplifiée: On prend les 16 meilleurs au Power Ranking global pour aller vite ?)
        # Non, faisons une vraie simu de groupes aléatoires si on veut être fun
        # Pour l'instant : On simule des matchs Knockout directs pour simplifier ou des poules ?
        # Allons sur une "Phase Finale" simulée : 16 équipes (les 16 meilleures du ranking)
        
        # Get top 16 weighted by modifiers to simulate Group Stage exit
        # We assume top teams qualify
        # Let's verify existing teams
        available_teams = [t for t in QUALIFIED_TEAMS if t in predictor.team_stats.index]
        
        if len(available_teams) < 16:
            print("Erreur: Pas assez d'équipes trouvées dans le CSV historique.")
            return

        # Shuffle and pick 16 for Round of 16
        knockout_teams = available_teams[:16] # Just taking first 16 is arbitrary, let's randomize
        random.shuffle(available_teams)
        knockout_teams = available_teams[:16]

        winner = play_knockout_phase(predictor, knockout_teams, modifiers)
        winners.append(winner)

    return collections.Counter(winners)

def play_match(predictor, team1, team2, modifiers):
    # Determine Host context
    # If one team is host, it's NOT a neutral venue for them technically, 
    # but our neutral=True logic averages stats.
    # The 'modifiers' handle the boost.
    res = predictor.predict_match(team1, team2, neutral_venue=True, modifiers=modifiers)
    
    # Simulate outcome based on probabilities
    rand = random.uniform(0, 100)
    if rand < res['win_prob']:
        return team1
    elif rand < res['win_prob'] + res['draw_prob']:
        # Draw -> Penalty Shootout (50/50 coin flip for simplicity or based on tier)
        return team1 if random.random() > 0.5 else team2
    else:
        return team2

def play_knockout_phase(predictor, teams, modifiers):
    current_round = teams
    while len(current_round) > 1:
        next_round = []
        for i in range(0, len(current_round), 2):
            t1 = current_round[i]
            t2 = current_round[i+1]
            winner = play_match(predictor, t1, t2, modifiers)
            next_round.append(winner)
        current_round = next_round
    return current_round[0]

if __name__ == "__main__":
    try:
        predictor = Ligue1Predictor(data_file="data/AFCON.csv")
        results = simulate_tournament(predictor, n_simulations=500)
        
        print("\n=== RÉSULTATS DE LA SIMULATION (500 Tournois) ===")
        print(f"Paramètres : Hôte={HOST_COUNTRY} (Boost +15%), Bonus Effectif Actif")
        
        sorted_res = results.most_common(10)
        for i, (team, wins) in enumerate(sorted_res, 1):
            print(f"{i}. {team} : {wins/5}% de victoires ({wins} titres)")
            
    except Exception as e:
        print(f"Erreur : {e}")
