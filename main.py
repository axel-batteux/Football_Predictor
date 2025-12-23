from src.model import Ligue1Predictor
import difflib

def get_closest_match(team_name, all_teams):
    matches = difflib.get_close_matches(team_name, all_teams, n=1, cutoff=0.6)
    return matches[0] if matches else None

def main():
    print("--- PRÉDICTION DE MATCHS DE FOOTBALL ---")
    print("1. Premier League (Angleterre)")
    print("2. Ligue 1 (France)")
    print("3. Bundesliga (Allemagne)")
    print("4. Serie A (Italie)")
    print("5. La Liga (Espagne)")
    print("6. Ligue 2 (France)")
    print("7. Coupe d'Afrique des Nations (AFCON)")
    choice = input("Choisissez une compétition (1-7) : ").strip()

    data_file = None
    league_code = "E0" # Default
    competition_name = "Premier League"

    # Map choices to (Code, Name, IsFile)
    # IsFile True means we use 'data_file', False means we use 'league_code'
    leagues_map = {
        '1': ('E0', 'Premier League', False),
        '2': ('F1', 'Ligue 1', False),
        '3': ('D1', 'Bundesliga', False),
        '4': ('I1', 'Serie A', False),
        '5': ('SP1', 'La Liga', False),
        '6': ('F2', 'Ligue 2', False),
        '7': ('AFCON', 'Coupe d\'Afrique des Nations', True)
    }

    if choice in leagues_map:
        code, name, is_file = leagues_map[choice]
        competition_name = name
        if is_file:
            data_file = f"data/{code}.csv"
        else:
            league_code = code
    else:
        print("Choix invalide, chargement de la Premier League par défaut.")

    print(f"\nInitialisation du modèle pour : {competition_name}...")
    try:
        predictor = Ligue1Predictor(data_file=data_file, league_code=league_code)
    except Exception as e:
        print(f"Erreur lors de l'initialisation : {e}")
        return

    all_teams = predictor.get_teams()
    print(f"\nDonnées chargées pour {len(all_teams)} équipes.")

    # Show example teams based on selection
    examples = {
        '1': "Man City, Arsenal, Liverpool, Chelsea",
        '2': "PSG, Marseille, Lyon, Lens",
        '3': "Bayern Munich, Dortmund, Leverkusen",
        '4': "Inter, Milan, Juventus, Napoli",
        '5': "Real Madrid, Barcelona, Atletico",
        '6': "Bordeaux, Metz, Paris FC",
        '7': "Morocco, Senegal, Egypt"
    }
    print(f"Exemple d'équipes : {examples.get(choice, '...')}")
    print("\n")

    while True:
        print("-" * 50)
        home_input = input("Entrez l'équipe à Domicile (ou 'q' pour quitter) : ").strip()
        if home_input.lower() == 'q':
            break
        
        home_team = get_closest_match(home_input, all_teams)
        if not home_team:
            print(f"Équipe '{home_input}' introuvable. Essayez encore.")
            continue
        print(f" -> Équipe sélectionnée : {home_team}")

        away_input = input("Entrez l'équipe à l'Extérieur : ").strip()
        away_team = get_closest_match(away_input, all_teams)
        if not away_team:
            print(f"Équipe '{away_input}' introuvable. Essayez encore.")
            continue
        print(f" -> Équipe sélectionnée : {away_team}")

        if home_team == away_team:
            print("Une équipe ne peut pas jouer contre elle-même !")
            continue

        print(f"\nCalcul de la prédiction pour {home_team} vs {away_team}...")
        results = predictor.predict_match(home_team, away_team)

        if "error" in results:
            print(f"Erreur : {results['error']}")
        else:
            print("\n--- RÉSULTATS DE LA PRÉDICTION ---")
            print(f"Probabilité Victoire {home_team} : {results['win_prob']}%")
            print(f"Probabilité Match Nul : {results['draw_prob']}%")
            print(f"Probabilité Victoire {away_team} : {results['loss_prob']}%")
            print(f"Score le plus probable : {results['most_likely_score']} (Confiance: {results['score_prob']}%)")
            print(f"Buts attendus (xG) : {results['expected_goals_home']} - {results['expected_goals_away']}")

if __name__ == "__main__":
    main()
