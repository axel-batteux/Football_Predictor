from src.model import Ligue1Predictor
from src.tournament_sim import SQUAD_BOOSTS

def analyze_afcon_match(predictor, home, away):
    print(f"\n--- {home.upper()} vs {away.upper()} ---")
    
    # Check teams
    if home not in predictor.team_stats.index:
        print(f"Erreur : {home} introuvable.")
        return
    if away not in predictor.team_stats.index:
        print(f"Erreur : {away} introuvable.")
        return

    # Prepare modifiers for AFCON
    modifiers = {}
    
    for team in [home, away]:
        mods = {'attack': 1.0, 'defense': 1.0}
        boost = SQUAD_BOOSTS.get(team, 1.0)
        mods['attack'] *= boost
        mods['defense'] *= (1.0 - (boost - 1.0))
        modifiers[team] = mods
    
    # Neutral venue for AFCON group matches
    res = predictor.predict_match(home, away, neutral_venue=True, modifiers=modifiers)
    
    if "error" in res:
        print(res['error'])
        return

    p_win = res['win_prob']
    p_draw = res['draw_prob']
    p_loss = res['loss_prob']
    total_xg = res['expected_goals_home'] + res['expected_goals_away']

    print(f"[STAT] PROBAS : 1: {p_win}% | N: {p_draw}% | 2: {p_loss}%")
    print(f"xG : {res['expected_goals_home']} - {res['expected_goals_away']}")
    print(f"[SCORE] Score probable : {res['most_likely_score']}")
    
    # Tip
    if p_win > 50: 
        print(f"[TIP] Conseil : {home}")
    elif p_loss > 50: 
        print(f"[TIP] Conseil : {away}")
    else: 
        print(f"[TIP] Conseil : Match serré, Double Chance recommandée")
    
    if total_xg < 2.0: 
        print(f"[-] Under 2.5 Buts")
    elif total_xg > 2.8: 
        print(f"[+] Over 2.5 Buts")

print("=== PRÉDICTIONS CAN 2025 ===")

try:
    predictor = Ligue1Predictor(data_file="data/AFCON.csv")
    
    analyze_afcon_match(predictor, "Nigeria", "Tanzania")
    analyze_afcon_match(predictor, "Tunisia", "Uganda")
    
except Exception as e:
    print(f"Erreur : {e}")
