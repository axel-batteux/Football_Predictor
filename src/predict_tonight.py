from src.model import Ligue1Predictor
from src.tournament_sim import SQUAD_BOOSTS

def analyze_match(predictor, home, away):
    print(f"\n--- {home.upper()} vs {away.upper()} ---")
    
    # Check teams
    if home not in predictor.team_stats.index:
        print(f"Erreur : {home} introuvable.")
        return
    if away not in predictor.team_stats.index:
        print(f"Erreur : {away} introuvable.")
        return

    # Standard league match (Home vs Away applies, no neutral venue)
    # No special modifiers unless we want to manually boost squads, but for leagues the data is usually enough
    res = predictor.predict_match(home, away)
    
    if "error" in res:
        print(res['error'])
        return

    p_win = res['win_prob']
    p_draw = res['draw_prob']
    p_loss = res['loss_prob']
    total_xg = res['expected_goals_home'] + res['expected_goals_away']

    print(f"[STAT] PROBAS : 1: {p_win}% | N: {p_draw}% | 2: {p_loss}%")
    print(f"xG : {res['expected_goals_home']} - {res['expected_goals_away']}")
    print(f"[SCORE] Score : {res['most_likely_score']}")
    
    # Simple Tip
    if p_win > 50: print(f"[TIP] Conseil : {home}")
    elif p_loss > 50: print(f"[TIP] Conseil : {away}")
    else: print(f"[TIP] Conseil : Nul ou Double Chance")
    
    if total_xg < 2.0: print(f"[-] Under 2.5 Buts")
    elif total_xg > 3.0: print(f"[+] Over 2.5 Buts")

def predict_tonight():
    # 1. Premier League Check
    print("\n>>> PREMIER LEAGUE <<<")
    try:
        # Load Premier League Data (E0)
        pred_pl = Ligue1Predictor(league_code="E0")
        analyze_match(pred_pl, "Fulham", "Nott'm Forest") # Check naming convention
    except Exception as e:
        print(f"Error PL: {e}")

    # 2. La Liga Check
    print("\n>>> LA LIGA <<<")
    try:
        # Load La Liga Data (SP1)
        pred_liga = Ligue1Predictor(league_code="SP1")
        analyze_match(pred_liga, "Ath Bilbao", "Espanol") # Check naming convention
    except Exception as e:
        print(f"Error Liga: {e}")

if __name__ == "__main__":
    predict_tonight()
