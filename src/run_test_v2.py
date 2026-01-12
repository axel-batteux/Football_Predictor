import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model import Ligue1Predictor
import pandas as pd

def test_model():
    print("=== TEST FOOTBALL PREDICTOR 2.0 ===")
    
    # 1. Load Model (Premier League by default)
    print("\n[1] Loading Model and Data...")
    try:
        predictor = Ligue1Predictor(league_code='E0') # Premier League
        print(f"OK Data Loaded: {len(predictor.df)} matches found.")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # 2. Check Data Columns
    print("\n[2] Checking Data Engineering...")
    required_cols = ['HST', 'AST', 'Estimated_xG_Home', 'Estimated_xG_Away', 'Weight']
    missing = [c for c in required_cols if c not in predictor.df.columns]
    
    if not missing:
        print("OK All new columns present (HST, AST, Estimated_xG, Weight).")
        print(predictor.df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'Estimated_xG_Home', 'Weight']].tail(3))
    else:
        print(f"Missing columns: {missing}")
        
    # 3. Test Prediction
    print("\n[3] Testing Prediction (Man City vs Liverpool)...")
    try:
        # Predict Man City (Home) vs Liverpool (Away)
        result = predictor.predict_match('Man City', 'Liverpool')
        if "error" in result:
            print(f"Prediction Error: {result['error']}")
        else:
            print(f"Prediction Successful:")
            print(f"   - Match: {result['home_team']} vs {result['away_team']}")
            print(f"   - Win Prob: {result['win_prob']}%")
            print(f"   - Draw Prob: {result['draw_prob']}% (Should be higher due to Dixon-Coles)")
            print(f"   - Loss Prob: {result['loss_prob']}%")
            print(f"   - Most Likely: {result['most_likely_score']} ({result['score_prob']}%)")
            print(f"   - xG: {result['expected_goals_home']} - {result['expected_goals_away']}")
            
    except Exception as e:
        print(f"Prediction Exception: {e}")

    # 4. Test Elo with Shots
    print("\n[4] Checking Elo System...")
    try:
        # Check if ratings exist
        top_teams = sorted(predictor.elo_system.ratings.items(), key=lambda x: x[1], reverse=True)[:5]
        print("Top 5 Elo Teams:")
        for team, rating in top_teams:
            print(f"   - {team}: {rating:.0f}")
            
    except Exception as e:
        print(f"Elo Error: {e}")

if __name__ == "__main__":
    test_model()
