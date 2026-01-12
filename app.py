from flask import Flask, render_template, request, jsonify
from src.model import Ligue1Predictor
from src.tournament_sim import SQUAD_BOOSTS
import os

app = Flask(__name__)

# Cache des modèles pour éviter de recharger à chaque requête
MODELS = {}

COMPETITIONS = {
    'PL': {'name': 'Premier League', 'code': 'E0', 'is_file': False},
    'CHA': {'name': 'Championship (ENG D2)', 'code': 'E1', 'is_file': False},
    'LG1': {'name': 'League 1 (ENG D3)', 'code': 'E2', 'is_file': False},
    'LG2': {'name': 'League 2 (ENG D4)', 'code': 'E3', 'is_file': False},
    'L1': {'name': 'Ligue 1', 'code': 'F1', 'is_file': False},
    'L2': {'name': 'Ligue 2', 'code': 'F2', 'is_file': False},
    'BUN': {'name': 'Bundesliga', 'code': 'D1', 'is_file': False},
    'BU2': {'name': 'Bundesliga 2 (GER D2)', 'code': 'D2', 'is_file': False},
    'SER': {'name': 'Serie A', 'code': 'I1', 'is_file': False},
    'SE2': {'name': 'Serie B (ITA D2)', 'code': 'I2', 'is_file': False},
    'LAL': {'name': 'La Liga', 'code': 'SP1', 'is_file': False},
    'LA2': {'name': 'La Liga 2 (ESP D2)', 'code': 'SP2', 'is_file': False},
    'ERE': {'name': 'Eredivisie (NED)', 'code': 'N1', 'is_file': False},
    'POR': {'name': 'Liga NOS (POR)', 'code': 'P1', 'is_file': False},
    'JUP': {'name': 'Jupiler Pro (BEL)', 'code': 'B1', 'is_file': False},
    'TUR': {'name': 'Super Lig (TUR)', 'code': 'T1', 'is_file': False},
    'GRE': {'name': 'Super League (GRE)', 'code': 'G1', 'is_file': False},
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
                    mods['attack'] *= 1.20  # +20% attack boost for host (Home Crowd)
                    mods['defense'] *= 0.90 # -10% goals conceded (Defensive Boost)
                
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

@app.route('/update', methods=['GET', 'POST'])
def trigger_update():
    """Endpoint to trigger a manual data update."""
    try:
        import auto_update
        print("[INFO] Manual update triggered via web...")
        exit_code = auto_update.main()
        
        # Clear model cache to force reload
        MODELS.clear()
        
        if exit_code == 0:
            return jsonify({'status': 'success', 'message': 'Data updated successfully.'})
        else:
            return jsonify({'status': 'error', 'message': 'Update failed.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === AUTO UPDATE ON STARTUP (Background Thread) ===
def start_background_update():
    """Runs data update in background to not block Gunicorn startup."""
    try:
        import auto_update
        import time
        
        print("[INFO] Checking data freshness (Background)...")
        # Simple check: if main file is older than 24h or missing
        should_update = False
        data_dir = "data"
        proxy_file = os.path.join(data_dir, "E0_2526.csv") 
        
        if not os.path.exists(data_dir) or not os.path.exists(proxy_file):
            should_update = True
        elif time.time() - os.path.getmtime(proxy_file) > 86400: # 24h
            should_update = True
            
        if should_update:
            print("[INFO] Data is old or missing. Updating in background...")
            auto_update.main()
            # Clear cache after update
            MODELS.clear()
            print("[INFO] Background update complete & Cache cleared.")
        else:
            print("[INFO] Data is up to date.")
            
    except Exception as e:
        print(f"[WARNING] Background update failed: {e}")

# Start the background thread immediately on import
import threading
update_thread = threading.Thread(target=start_background_update)
update_thread.daemon = True # Daemonize thread
update_thread.start()

if __name__ == '__main__':
    print("=== Football Predictor Web App ===")
    print("Ouvrez votre navigateur sur : http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
