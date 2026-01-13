from tennis_model import TennisElo
import os

def test_model():
    model = TennisElo()
    
    # Train on available data
    files = [
        "data/tennis/atp_2024.csv",
        "data/tennis/wta_2024.csv"
    ]
    
    model.train_from_csv(files)
    
    # Check Top Players (Overall)
    print("\n=== TOP 5 PLAYERS (OVERALL) ===")
    top = model.get_top_players('Overall', 5)
    for p, r in top:
        print(f"{p}: {round(r)}")
        
    # Check Top Players (Clay)
    print("\n=== TOP 5 PLAYERS (CLAY) ===")
    top_clay = model.get_top_players('Clay', 5)
    for p, r in top_clay:
        print(f"{p}: {round(r)}")

    # Check Top Players (Hard)
    print("\n=== TOP 5 PLAYERS (HARD) ===")
    top_hard = model.get_top_players('Hard', 5)
    for p, r in top_hard:
        print(f"{p}: {round(r)}")

    # Simulate Matrix: Alcaraz vs Sinner
    p1 = "Carlos Alcaraz"
    p2 = "Jannik Sinner"
    
    print(f"\n=== SIMULATION: {p1} vs {p2} ===")
    
    # Hard Court
    res_hard = model.predict_match(p1, p2, "Hard")
    print(f"[HARD] {p1} ({res_hard['elo1']}) vs {p2} ({res_hard['elo2']}) -> Win%: {res_hard['win_prob1']}%")
    
    # Clay Court
    res_clay = model.predict_match(p1, p2, "Clay")
    print(f"[CLAY] {p1} ({res_clay['elo1']}) vs {p2} ({res_clay['elo2']}) -> Win%: {res_clay['win_prob1']}%")
    
    if res_clay['win_prob1'] > res_hard['win_prob1']:
        print("✅ SUCCESS: Surface weighting works (Alcaraz better on Clay).")
    else:
        print("⚠️ OBSERVATION: Surface weighting neutral or Sinner better on Clay in 2024 data.")

if __name__ == "__main__":
    test_model()
