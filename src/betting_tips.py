from src.model import Ligue1Predictor
from src.tournament_sim import SQUAD_BOOSTS

def get_betting_tips(home_team, away_team):
    print(f"--- ANALYSE PARIS SPORTIFS : {home_team.upper()} vs {away_team.upper()} ---")
    
    try:
        predictor = Ligue1Predictor(data_file="data/AFCON.csv")
    except Exception as e:
        print(f"Erreur: {e}")
        return

    # Check teams
    if home_team not in predictor.team_stats.index:
        print(f"Erreur : {home_team} introuvable dans les données.")
        return
    if away_team not in predictor.team_stats.index:
        print(f"Erreur : {away_team} introuvable dans les données.")
        return

    # Prepare modifiers
    modifiers = {}
    
    # Home Team
    mods_home = {'attack': 1.0, 'defense': 1.0}
    boost_home = SQUAD_BOOSTS.get(home_team, 1.0)
    mods_home['attack'] *= boost_home
    mods_home['defense'] *= (1.0 - (boost_home - 1.0))
    modifiers[home_team] = mods_home

    # Away Team
    mods_away = {'attack': 1.0, 'defense': 1.0}
    boost_away = SQUAD_BOOSTS.get(away_team, 1.0)
    mods_away['attack'] *= boost_away
    mods_away['defense'] *= (1.0 - (boost_away - 1.0))
    modifiers[away_team] = mods_away

    # Predict (Neutral Venue for AFCON group stage match)
    res = predictor.predict_match(home_team, away_team, neutral_venue=True, modifiers=modifiers)
    
    if "error" in res:
        print(res['error'])
        return

    # --- GENERATING TIPS ---
    p_win = res['win_prob']
    p_draw = res['draw_prob']
    p_loss = res['loss_prob']
    
    print(f"\n[STAT] PROBABILITÉS DU MODÈLE")
    print(f"Victoire {home_team} (1) : {p_win}%")
    print(f"Match Nul (N)      : {p_draw}%")
    print(f"Victoire {away_team} (2) : {p_loss}%")
    print(f"xG (Buts attendus) : {res['expected_goals_home']} - {res['expected_goals_away']}")

    print(f"\n[TIP] CONSEILS PARIS (Value Bet)")
    
    # 1. Main Bet (Vainqueur)
    if p_win > 50:
        print(f"[>] Vainqueur : {home_team} (Confiance élevée)")
    elif p_win > 40:
        print(f"[>] Vainqueur : {home_team} (Risqué mais probable)")
    elif p_loss > 50:
        print(f"[>] Vainqueur : {away_team} (Confiance élevée)")
    elif p_loss > 40:
        print(f"[>] Vainqueur : {away_team} (Risqué mais probable)")
    else:
        print(f"[!] Match très indécis. Privilégiez le Nul ou Double Chance.")

    # 2. Sécurité (Double Chance)
    if p_win + p_draw > 75:
        print(f"[SECURE] Sécurité : {home_team} ou Nul (1N)")
    elif p_loss + p_draw > 75:
        print(f"[SECURE] Sécurité : Nul ou {away_team} (N2)")

    # 3. Buts (Over/Under)
    total_xg = res['expected_goals_home'] + res['expected_goals_away']
    print(f"[GOALS] Total Buts attendus : {total_xg}")
    
    if total_xg < 2.0:
        print(f"[-] Under 2.5 Buts (Match fermé attendu)")
    elif total_xg > 2.8:
        print(f"[+] Over 2.5 Buts (Match ouvert attendu)")
    else:
        print(f"[?] Pas de tendance claire sur le nombre de buts (2-3 buts probables).")

    # 4. Score Exact Fun
    print(f"[SCORE] Score Exact tentant : {res['most_likely_score']}")


if __name__ == "__main__":
    get_betting_tips("Egypt", "Zimbabwe")
