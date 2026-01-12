import pandas as pd
import numpy as np
from pathlib import Path

class EloRatingSystem:
    """Elo rating system for football teams."""
    
    def __init__(self, base_rating=1500, k_factor=32):
        """
        Initialize Elo system.
        
        Args:
            base_rating: Starting Elo for all teams
            k_factor: Maximum points change per match
        """
        self.base_rating = base_rating
        self.k_factor = k_factor
        self.ratings = {}
        
    def get_rating(self, team):
        """Get current Elo rating for a team."""
        if team not in self.ratings:
            self.ratings[team] = self.base_rating
        return self.ratings[team]
    
    def expected_score(self, rating_a, rating_b):
        """Calculate expected score for team A vs team B."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def update_ratings(self, home_team, away_team, home_goals, away_goals, match_type='tournament', home_shots_ot=None, away_shots_ot=None):
        """
        Update Elo ratings based on match result.
        
        Args:
            home_team: Name of home team
            away_team: Name of away team
            home_goals: Goals scored by home team
            away_goals: Goals scored by away team
            away_goals: Goals scored by away team
            match_type: 'tournament', 'qualifier', or 'friendly'
            home_shots_ot: (Optional) Home shots on target
            away_shots_ot: (Optional) Away shots on target
        """
        # Get current ratings
        home_rating = self.get_rating(home_team)
        away_rating = self.get_rating(away_team)
        
        # Calculate expected scores
        home_expected = self.expected_score(home_rating, away_rating)
        away_expected = 1 - home_expected
        
        # Actual score (1 for win, 0.5 for draw, 0 for loss)
        if home_goals > away_goals:
            home_actual = 1.0
            away_actual = 0.0
        elif home_goals < away_goals:
            home_actual = 0.0
            away_actual = 1.0
        else:
            home_actual = 0.5
            away_actual = 0.5
        
        # K-factor based on match importance
        k = self.k_factor
        if match_type == 'tournament':
            k *= 1.5  # Tournaments more important
        elif match_type == 'friendly':
            k *= 0.5  # Friendlies less important
        
        # === 1. GOAL DIFFERENCE MULTIPLIER ===
        # (Bigger wins = bigger rating change)
        goal_diff = abs(home_goals - away_goals)
        goal_multiplier = 1.0 + goal_diff * 0.1  # +10% per goal difference
        goal_multiplier = min(goal_multiplier, 2.0)  # Cap at 2x
        
        # === 2. DOMINATION MULTIPLIER (xG / Shots Logic) ===
        # If we have shot data, adjust K based on fairness of result
        domination_multiplier = 1.0
        
        if home_shots_ot is not None and away_shots_ot is not None:
            # Avoid division by zero
            total_shots = home_shots_ot + away_shots_ot
            if total_shots > 5:
                home_domination = home_shots_ot / total_shots
                
                # Case A: Lucky Win (Won but dominated in shots)
                # e.g. Home wins but had < 40% of shots
                if home_actual == 1.0 and home_domination < 0.4:
                    domination_multiplier = 0.7  # "Lucky win" - earn fewer points
                elif away_actual == 1.0 and home_domination > 0.6:
                    domination_multiplier = 0.7  # "Lucky win" for away
                    
                # Case B: Dominant Win (Won and dominated shots)
                # e.g. Home wins and had > 70% of shots
                elif home_actual == 1.0 and home_domination > 0.7:
                    domination_multiplier = 1.2  # "Convincing win" - earn more points
                elif away_actual == 1.0 and home_domination < 0.3:
                    domination_multiplier = 1.2
        
        # Apply multipliers
        k *= goal_multiplier * domination_multiplier
        
        # Update ratings
        self.ratings[home_team] = home_rating + k * (home_actual - home_expected)
        self.ratings[away_team] = away_rating + k * (away_actual - away_expected)
    
    def process_historical_data(self, df):
        """
        Process historical match data to build Elo ratings.
        
        Args:
            df: DataFrame with columns: Date, HomeTeam, AwayTeam, FTHG, FTAG, (optional: MatchType)
        """
        # Sort by date to process chronologically
        df = df.copy()
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.sort_values('Date')
        
        # Detect match type if not provided
        if 'MatchType' not in df.columns:
            df['MatchType'] = 'tournament'  # Default assumption
        
        for _, row in df.iterrows():
            home_team = row['HomeTeam']
            away_team = row['AwayTeam']
            home_goals = row['FTHG']
            away_goals = row['FTAG']
            match_type = row.get('MatchType', 'tournament')
            
            # Extract shots if available (handle NaN with 0 or None)
            home_shots_ot = row.get('HST', None)
            away_shots_ot = row.get('AST', None)
            
            # Ensure valid numbers
            if pd.isna(home_shots_ot): home_shots_ot = None
            if pd.isna(away_shots_ot): away_shots_ot = None
            
            self.update_ratings(home_team, away_team, home_goals, away_goals, match_type, home_shots_ot, away_shots_ot)
    
    def get_all_ratings(self):
        """Return all current Elo ratings as a dict."""
        return self.ratings.copy()
    
    def get_rating_difference(self, team_a, team_b):
        """Get the Elo difference between two teams."""
        return self.get_rating(team_a) - self.get_rating(team_b)
    
    def get_top_teams(self, n=10):
        """Get top N teams by Elo rating."""
        sorted_ratings = sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)
        return sorted_ratings[:n]


def build_elo_ratings(data_file):
    """
    Build Elo ratings from a historical data file.
    
    Args:
        data_file: Path to CSV file with match data
        
    Returns:
        EloRatingSystem instance with computed ratings
    """
    df = pd.read_csv(data_file)
    elo = EloRatingSystem()
    elo.process_historical_data(df)
    return elo


if __name__ == '__main__':
    # Test with AFCON data
    print("=== Building Elo Ratings for AFCON ===\n")
    elo = build_elo_ratings('data/AFCON.csv')
    
    print("Top 10 Teams by Elo Rating:")
    for i, (team, rating) in enumerate(elo.get_top_teams(10), 1):
        print(f"{i}. {team}: {rating:.0f}")
    
    print("\n=== Sample Elo Differences ===")
    print(f"Morocco vs Comoros: {elo.get_rating_difference('Morocco', 'Comoros'):.0f}")
    print(f"Senegal vs Botswana: {elo.get_rating_difference('Senegal', 'Botswana'):.0f}")
    print(f"Nigeria vs Tanzania: {elo.get_rating_difference('Nigeria', 'Tanzania'):.0f}")
