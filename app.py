from flask import Flask, render_template, request, jsonify
from src.model import Ligue1Predictor
from src.tournament_sim import SQUAD_BOOSTS
import os

app = Flask(__name__)

# Cache des modèles pour éviter de recharger à chaque requête
MODELS = {}

COMPETITIONS = {
    'PL': {'name': 'Premier League', 'code': 'E0', 'is_file': False},
    'L1': {'name': 'Ligue 1', 'code': 'F1', 'is_file': False},
    'L2': {'name': 'Ligue 2', 'code': 'F2', 'is_file': False},
    'BUN': {'name': 'Bundesliga', 'code': 'D1', 'is_file': False},
    'SER': {'name': 'Serie A', 'code': 'I1', 'is_file': False},
    'LAL': {'name': 'La Liga', 'code': 'SP1', 'is_file': False},
    'CAN': {'name': 'CAN (AFCON)', 'code': 'AFCON.csv', 'is_file': True}
}

def get_predictor(comp_key):
    """Charge ou récupère le modèle depuis le cache."""
    if comp_key not in MODELS:
        comp = COMPETITIONS[comp_key]
        if comp['is_file']:
            MODELS[comp_key] = Ligue1Predictor(data_file=f"data/{comp['code']}")
        else:
            MODELS[comp_key] = Ligue1Predictor(league_code=comp['code'])
    return MODELS[comp_key]

@app.route('/')
def index():
    return render_template('index.html', competitions=COMPETITIONS)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        comp_key = data['competition']
        home_team = data['home_team']
        away_team = data['away_team']
        
        predictor = get_predictor(comp_key)
        
        # Check if teams exist
        teams = predictor.get_teams()
        if home_team not in teams:
            return jsonify({'error': f'{home_team} introuvable. Vérifiez l\'orthographe.'}), 400
        if away_team not in teams:
            return jsonify({'error': f'{away_team} introuvable. Vérifiez l\'orthographe.'}), 400
        
        # Prepare modifiers for AFCON
        modifiers = None
        neutral = False
        if comp_key == 'CAN':
            neutral = True
            modifiers = {}
            
            HOST_COUNTRY = 'Morocco'  # Tournament host
            
            for team in [home_team, away_team]:
                mods = {'attack': 1.0, 'defense': 1.0}
                
                # Squad quality boost
                boost = SQUAD_BOOSTS.get(team, 1.0)
                mods['attack'] *= boost
                mods['defense'] *= (1.0 - (boost - 1.0))
                
                # Host country advantage (Morocco only)
                if team == HOST_COUNTRY:
                    mods['attack'] *= 1.15  # +15% attack boost for host
                    # Defense already benefited from squad boost
                
                modifiers[team] = mods
        
        # Get prediction
        result = predictor.predict_match(home_team, away_team, neutral_venue=neutral, modifiers=modifiers)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/teams/<comp_key>')
def get_teams(comp_key):
    try:
        predictor = get_predictor(comp_key)
        teams = predictor.get_teams()
        return jsonify({'teams': teams})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=== Serveur de predictions lance ===")
    print("Ouvrez votre navigateur sur : http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
