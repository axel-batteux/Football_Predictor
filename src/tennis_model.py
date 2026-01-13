import pandas as pd
import numpy as np
import os

class AdvancedTennisPredictor:
    def __init__(self):
        self.ratings = {}
        self.history = [] # List of dicts: {winner, loser, surface, score, date}
        self.k_factor_surface = 32
        self.k_factor_overall = 16
        
    def get_rating(self, player, surface):
        if player not in self.ratings:
            return 1500.0
        if surface not in ['Hard', 'Clay', 'Grass']:
            surface = 'Hard'
        
        surf = self.ratings[player].get(surface, 1500.0)
        overall = self.ratings[player].get('Overall', 1500.0)
        return (surf * 0.8) + (overall * 0.2)

    def update_ratings(self, winner, loser, surface):
        # Initialize if new
        for p in [winner, loser]:
            if p not in self.ratings:
                self.ratings[p] = {'Hard': 1500.0, 'Clay': 1500.0, 'Grass': 1500.0, 'Overall': 1500.0}
        
        if surface not in ['Hard', 'Clay', 'Grass']:
            return

        # Surface Update
        w_elo, l_elo = self.ratings[winner][surface], self.ratings[loser][surface]
        w_prob = 1 / (1 + 10 ** ((l_elo - w_elo) / 400))
        delta = self.k_factor_surface * (1 - w_prob)
        self.ratings[winner][surface] += delta
        self.ratings[loser][surface] -= delta
        
        # Overall Update
        w_ov, l_ov = self.ratings[winner]['Overall'], self.ratings[loser]['Overall']
        w_prob_ov = 1 / (1 + 10 ** ((l_ov - w_ov) / 400))
        delta_ov = self.k_factor_overall * (1 - w_prob_ov)
        self.ratings[winner]['Overall'] += delta_ov
        self.ratings[loser]['Overall'] -= delta_ov

    def train_from_csv(self, file_paths):
        print("=== Training Advanced Tennis Model ===")
        for path in file_paths:
            if not os.path.exists(path):
                continue
            try:
                df = pd.read_csv(path, encoding='latin1')
                # Standardize columns
                df.columns = [c.lower() for c in df.columns]
                
                # Check required columns
                required = ['winner_name', 'loser_name', 'surface']
                if not all(col in df.columns for col in required):
                    continue
                
                # Sort by date if possible
                if 'tourney_date' in df.columns:
                    df = df.sort_values('tourney_date')
                
                for _, row in df.iterrows():
                    w, l, s = row['winner_name'], row['loser_name'], row['surface']
                    score = row.get('score', 'N/A')
                    date = row.get('tourney_date', 'N/A')
                    
                    self.update_ratings(w, l, s)
                    self.history.append({
                        'winner': w, 'loser': l, 'surface': s, 'score': score, 'date': date
                    })
            except Exception as e:
                print(f"Error processing {path}: {e}")
        print(f"Training complete. Processed {len(self.history)} matches.")

    def get_all_players(self):
        """Returns sorted list of all known players for Autocomplete."""
        return sorted(list(self.ratings.keys()))

    def get_head_to_head(self, p1, p2):
        """Returns H2H stats between p1 and p2."""
        h2h = {'p1_wins': 0, 'p2_wins': 0, 'matches': []}
        for m in self.history:
            if (m['winner'] == p1 and m['loser'] == p2):
                h2h['p1_wins'] += 1
                h2h['matches'].append(m)
            elif (m['winner'] == p2 and m['loser'] == p1):
                h2h['p2_wins'] += 1
                h2h['matches'].append(m)
        return h2h

    def predict_match(self, p1, p2, surface, best_of=3):
        elo1 = self.get_rating(p1, surface)
        elo2 = self.get_rating(p2, surface)
        
        # Win Probability (Log5)
        prob1 = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
        prob2 = 1 - prob1
        
        # Score Simulation
        scores = self.simulate_set_scores(prob1, best_of)
        
        # H2H
        h2h = self.get_head_to_head(p1, p2)
        
        # Betting Tip
        tip = self.generate_tip(prob1, p1, p2, scores)

        return {
            'player1': p1, 'player2': p2, 'surface': surface,
            'elo1': round(elo1), 'elo2': round(elo2),
            'win_prob1': round(prob1 * 100, 1),
            'win_prob2': round(prob2 * 100, 1),
            'history': h2h,
            'set_scores': scores,
            'format': f"Best of {best_of}",
            'tip': tip
        }

    def simulate_set_scores(self, p1_win_prob, best_of=3):
        """
        Estimates probabilities of specific set scores (2-0, 2-1 vs 0-2, 1-2).
        Heuristic approach: Stronger favorites are more likely to win in straight sets.
        """
        p = p1_win_prob
        q = 1 - p
        
        scores = []
        
        if best_of == 3:
            # P(2-0) approx p^2 (simplified)
            # P(2-1) approx 2 * p^2 * q
            # Normalize to match match_win_prob sum
            
            # Raw weights based on win prob
            if p > 0.5:
                prob_2_0 = p * 0.70 # Heavy bias to straight sets if strong fav
                prob_2_1 = p * 0.30
                prob_0_2 = q * 0.60
                prob_1_2 = q * 0.40
            else:
                prob_0_2 = q * 0.70
                prob_1_2 = q * 0.30
                prob_2_0 = p * 0.60
                prob_2_1 = p * 0.40
                
            scores = [
                {'score': '2-0', 'prob': round(prob_2_0 * 100, 1)},
                {'score': '2-1', 'prob': round(prob_2_1 * 100, 1)},
                {'score': '0-2', 'prob': round(prob_0_2 * 100, 1)},
                {'score': '1-2', 'prob': round(prob_1_2 * 100, 1)}
            ]
            
        elif best_of == 5:
            # Best of 5 logic
            scores = [
                {'score': '3-0', 'prob': round(p * 0.50 * 100, 1)},
                {'score': '3-1', 'prob': round(p * 0.35 * 100, 1)},
                {'score': '3-2', 'prob': round(p * 0.15 * 100, 1)},
                {'score': '0-3', 'prob': round(q * 0.50 * 100, 1)},
                {'score': '1-3', 'prob': round(q * 0.35 * 100, 1)},
                {'score': '2-3', 'prob': round(q * 0.15 * 100, 1)}
            ]
            
        # Sort by probability high to low
        scores.sort(key=lambda x: x['prob'], reverse=True)
        return scores

    def generate_tip(self, p1_prob, p1, p2, scores):
        top_score = scores[0]
        
        if p1_prob > 0.85:
            return f"💎 **Banker**: Victoire {p1} (Très Sûr). Score probable: {top_score['score']}."
        elif p1_prob > 0.65:
            return f"✅ **Conseil**: Victoire {p1}. Value sur {top_score['score']}."
        elif p1_prob < 0.15:
            return f"💎 **Banker**: Victoire {p2} (Très Sûr)."
        elif p1_prob < 0.35:
            return f"✅ **Conseil**: Victoire {p2}."
        else:
            return "⚠️ **Match Risqué**: Probabilités proches (50/50). Privilégiez 'Plus de sets' ou 'Over Games'."
