import pandas as pd
import numpy as np
import os

class TennisElo:
    def __init__(self):
        # ratings[player_name] = {'Hard': 1500, 'Clay': 1500, 'Grass': 1500, 'Overall': 1500}
        self.ratings = {}
        self.k_factor_surface = 32 # Higher impact for surface specific mastery
        self.k_factor_overall = 16 # Lower impact for general form
        
        # Keep track of match counts for reliability
        self.match_counts = {}

    def get_rating(self, player, surface):
        """Returns the Effective Elo for a player on a specific surface."""
        if player not in self.ratings:
            return 1500.0
        
        # Logic: 80% Surface, 20% Overall
        # If surface is unknown or 'Carpet' (rare), fallback to Hard or Overall
        if surface not in ['Hard', 'Clay', 'Grass']:
            surface = 'Hard'
            
        surf_rating = self.ratings[player].get(surface, 1500.0)
        overall_rating = self.ratings[player].get('Overall', 1500.0)
        
        # User Requirement: "Prends bien en compte les surfaces" -> Heavy weighting.
        effective_elo = (surf_rating * 0.8) + (overall_rating * 0.2)
        return effective_elo

    def update_ratings(self, winner, loser, surface):
        if winner not in self.ratings:
            self.ratings[winner] = {'Hard': 1500.0, 'Clay': 1500.0, 'Grass': 1500.0, 'Overall': 1500.0}
        if loser not in self.ratings:
            self.ratings[loser] = {'Hard': 1500.0, 'Clay': 1500.0, 'Grass': 1500.0, 'Overall': 1500.0}
            
        if surface not in ['Hard', 'Clay', 'Grass']:
            return # Skip unsupported surfaces (Carpet, etc)

        # 1. Update Surface Specific Elo
        w_surf_elo = self.ratings[winner][surface]
        l_surf_elo = self.ratings[loser][surface]
        
        w_prob = 1 / (1 + 10 ** ((l_surf_elo - w_surf_elo) / 400))
        
        # Calculate Delta
        delta_surf = self.k_factor_surface * (1 - w_prob)
        
        self.ratings[winner][surface] += delta_surf
        self.ratings[loser][surface] -= delta_surf
        
        # 2. Update Overall Elo
        w_overall = self.ratings[winner]['Overall']
        l_overall = self.ratings[loser]['Overall']
        
        w_prob_overall = 1 / (1 + 10 ** ((l_overall - w_overall) / 400))
        delta_overall = self.k_factor_overall * (1 - w_prob_overall)
        
        self.ratings[winner]['Overall'] += delta_overall
        self.ratings[loser]['Overall'] -= delta_overall

    def train_from_csv(self, file_paths):
        print("=== Training Tennis Elo Model ===")
        for path in file_paths:
            if not os.path.exists(path):
                print(f"[WARNING] File not found: {path}")
                continue
                
            print(f"Processing {path}...")
            try:
                df = pd.read_csv(path, encoding='latin1') # Tennis-data often Latin1
                # Check required columns
                required = ['winner_name', 'loser_name', 'surface']
                if not all(col in df.columns for col in required):
                    print(f"Skipping {path}: Missing columns.")
                    continue
                
                # Sort by date if possible (tourney_date)
                if 'tourney_date' in df.columns:
                    df = df.sort_values('tourney_date')
                
                for _, row in df.iterrows():
                    self.update_ratings(row['winner_name'], row['loser_name'], row['surface'])
                    
            except Exception as e:
                print(f"Error reading {path}: {e}")
        
        print("Training complete.")

    def predict_match(self, p1, p2, surface):
        elo1 = self.get_rating(p1, surface)
        elo2 = self.get_rating(p2, surface)
        
        prob1 = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
        prob2 = 1 - prob1
        
        return {
            'player1': p1,
            'player2': p2,
            'surface': surface,
            'elo1': round(elo1),
            'elo2': round(elo2),
            'win_prob1': round(prob1 * 100, 1),
            'win_prob2': round(prob2 * 100, 1)
        }

    def get_top_players(self, surface='Overall', n=10):
        # Sort players by rating on specific surface
        # We need to construct the result list manually to include the effective rating
        players_with_ratings = []
        for player in self.ratings:
            effective_rating = self.get_rating(player, surface)
            players_with_ratings.append((player, effective_rating))
            
        sorted_players = sorted(
            players_with_ratings,
            key=lambda x: x[1], 
            reverse=True
        )
        return sorted_players[:n]
