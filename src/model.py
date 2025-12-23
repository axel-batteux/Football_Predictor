import pandas as pd
import numpy as np
from scipy.stats import poisson
import os
from src.elo import EloRatingSystem

class Ligue1Predictor:
    def __init__(self, data_dir="data", data_file=None, league_code="F1"):
        self.data_dir = data_dir
        self.data_file = data_file
        self.league_code = league_code
        self.df = self._load_data()
        self.teams = sorted(self.df['HomeTeam'].unique())
        self.avg_home_goals = 0
        self.avg_away_goals = 0
        self.team_stats = {}
        self.elo_system = None  # Will be built during training
        self._train_model()

    def _load_data(self):
        """Loads data from a specific file or all CSVs matching the league code."""
        if self.data_file:
            if os.path.exists(self.data_file):
                 try:
                    df = pd.read_csv(self.data_file, encoding='latin1')
                    return df
                 except Exception as e:
                     print(f"Error loading {self.data_file}: {e}")
                     return pd.DataFrame()
            else:
                return pd.DataFrame()

        # Default behavior: Load CSVs starting with league_code (e.g., 'E0' or 'F1')
        all_files = [
            os.path.join(self.data_dir, f) 
            for f in os.listdir(self.data_dir) 
            if f.endswith('.csv') and f.startswith(self.league_code)
        ]
        
        df_list = []
        for file in all_files:
            try:
                # football-data.co.uk sometimes has encoding issues, try latin1 if utf-8 fails
                try:
                    df = pd.read_csv(file)
                except UnicodeDecodeError:
                    df = pd.read_csv(file, encoding='latin1')
                
                # Keep only relevant columns
                if 'HomeTeam' in df.columns and 'AwayTeam' in df.columns and 'FTHG' in df.columns and 'FTAG' in df.columns:
                    df = df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']]
                    df_list.append(df)
            except Exception as e:
                print(f"Error loading {file}: {e}")
        
        full_df = pd.concat(df_list, ignore_index=True)
        # Filter out matches that haven't been played (no score)
        full_df = full_df.dropna(subset=['FTHG', 'FTAG'])
        return full_df

    def _train_model(self):
        """Calculates Attack and Defense strengths for each team with temporal weighting, Elo ratings, and recent form."""
        # Parse dates (works for both DD/MM/YYYY and YYYY-MM-DD formats)
        self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce')
        self.df = self.df.dropna(subset=['Date'])
        
        # Sort by date for Elo calculation
        self.df = self.df.sort_values('Date').reset_index(drop=True)
        
        # Build Elo ratings from historical data
        self.elo_system = EloRatingSystem()
        self.elo_system.process_historical_data(self.df)
        
        # Current date reference (use latest match in dataset)
        latest_date = self.df['Date'].max()
        
        # Calculate age of each match in days
        self.df['DaysAgo'] = (latest_date - self.df['Date']).dt.days
        
        # Enhanced temporal weighting with Last 5 matches boost
        # Step 1: Base temporal weight
        def calculate_base_weight(days_ago):
            if days_ago <= 180:  # Last 6 months
                return 3.0
            elif days_ago <= 545:  # 6-18 months
                return 2.0
            else:  # Older
                return 1.0
        
        self.df['Weight'] = self.df['DaysAgo'].apply(calculate_base_weight)
        
        # Step 2: Apply ULTRA boost to last 5 matches per team
        for team in self.teams:
            # Last 5 home matches
            home_matches = self.df[self.df['HomeTeam'] == team].tail(5)
            self.df.loc[home_matches.index, 'Weight'] *= 2.0  # 2x additional boost (reduced from 3x)
            
            # Last 5 away matches
            away_matches = self.df[self.df['AwayTeam'] == team].tail(5)
            self.df.loc[away_matches.index, 'Weight'] *= 2.0  # 2x additional boost (reduced from 3x)
        
        # Calculate weighted league averages
        total_weight = self.df['Weight'].sum()
        self.avg_home_goals = (self.df['FTHG'] * self.df['Weight']).sum() / total_weight
        self.avg_away_goals = (self.df['FTAG'] * self.df['Weight']).sum() / total_weight
        
        # Calculate weighted stats per team
        def weighted_stats(group, is_home=True):
            total_w = group['Weight'].sum()
            if total_w == 0:
                return pd.Series({'scored': 0, 'conceded': 0})
            
            if is_home:
                scored = (group['FTHG'] * group['Weight']).sum() / total_w
                conceded = (group['FTAG'] * group['Weight']).sum() / total_w
            else:
                scored = (group['FTAG'] * group['Weight']).sum() / total_w
                conceded = (group['FTHG'] * group['Weight']).sum() / total_w
            
            return pd.Series({'scored': scored, 'conceded': conceded})
        
        # Home stats with weights
        home_stats = self.df.groupby('HomeTeam').apply(
            lambda x: weighted_stats(x, is_home=True), include_groups=False
        ).rename(columns={'scored': 'AvgHomeGoalsScored', 'conceded': 'AvgHomeGoalsConceded'})
        
        # Away stats with weights
        away_stats = self.df.groupby('AwayTeam').apply(
            lambda x: weighted_stats(x, is_home=False), include_groups=False
        ).rename(columns={'scored': 'AvgAwayGoalsScored', 'conceded': 'AvgAwayGoalsConceded'})
        
        # Merge stats
        self.team_stats = pd.merge(home_stats, away_stats, left_index=True, right_index=True, how='outer')
        
        # Calculate Strength Metrics
        self.team_stats['HomeAttackStrength'] = self.team_stats['AvgHomeGoalsScored'] / self.avg_home_goals
        self.team_stats['AwayAttackStrength'] = self.team_stats['AvgAwayGoalsScored'] / self.avg_away_goals
        self.team_stats['HomeDefenseStrength'] = self.team_stats['AvgHomeGoalsConceded'] / self.avg_away_goals
        self.team_stats['AwayDefenseStrength'] = self.team_stats['AvgAwayGoalsConceded'] / self.avg_home_goals
        
        # Fill NaN with 1.0 (neutral strength)
        self.team_stats = self.team_stats.fillna(1.0)

    def predict_match(self, home_team, away_team, neutral_venue=False, modifiers=None):
        """
        Predicts match outcomes.
        neutral_venue: If True, uses average of Home/Away stats for both teams.
        modifiers: Dict like {'TeamName': {'attack': 1.1, 'defense': 0.9}}. 
                   (Attack > 1 is boost, Defense < 1 is boost).
        """
        if home_team not in self.team_stats.index or away_team not in self.team_stats.index:
            return {"error": f"Team not found."}

        # Base Stats
        h_attack = self.team_stats.loc[home_team, 'HomeAttackStrength']
        h_defense = self.team_stats.loc[home_team, 'HomeDefenseStrength']
        a_attack = self.team_stats.loc[away_team, 'AwayAttackStrength']
        a_defense = self.team_stats.loc[away_team, 'AwayDefenseStrength']

        # If neutral venue (Tournament mode), average the Home/Away stats to get a "Raw Ability"
        if neutral_venue:
            h_attack = (self.team_stats.loc[home_team, 'HomeAttackStrength'] + self.team_stats.loc[home_team, 'AwayAttackStrength']) / 2
            a_defense = (self.team_stats.loc[away_team, 'HomeDefenseStrength'] + self.team_stats.loc[away_team, 'AwayDefenseStrength']) / 2
            
            a_attack = (self.team_stats.loc[away_team, 'HomeAttackStrength'] + self.team_stats.loc[away_team, 'AwayAttackStrength']) / 2
            h_defense = (self.team_stats.loc[home_team, 'HomeDefenseStrength'] + self.team_stats.loc[home_team, 'AwayDefenseStrength']) / 2

        # Apply Modifiers (Squad Quality, Host Advantage, etc.)
        if modifiers:
            if home_team in modifiers:
                h_attack *= modifiers[home_team].get('attack', 1.0)
                h_defense *= modifiers[home_team].get('defense', 1.0)
            if away_team in modifiers:
                a_attack *= modifiers[away_team].get('attack', 1.0)
                a_defense *= modifiers[away_team].get('defense', 1.0)

        # === ELO ADJUSTMENT ===
        # Use Elo difference to modify attack/defense strengths (subtle adjustment)
        elo_diff = self.elo_system.get_rating_difference(home_team, away_team)
        elo_multiplier = 1.0 + (elo_diff / 1200)  # Very subtle: 1 point per 1200 Elo
        elo_multiplier = max(0.8, min(elo_multiplier, 1.3))  # Cap between 0.8x and 1.3x
        
        # Apply Elo boost to the stronger team
        if elo_diff > 0:  # Home team is stronger
            h_attack *= elo_multiplier
            a_defense *= elo_multiplier  # Harder to score against them
        else:  # Away team is stronger
            a_attack *= (2.0 - elo_multiplier)  # Inverse for away
            h_defense *= (2.0 - elo_multiplier)

        # === HEAD-TO-HEAD ADJUSTMENT ===
        # Filter H2H matches and apply extra weight
        h2h_matches = self.df[
            ((self.df['HomeTeam'] == home_team) & (self.df['AwayTeam'] == away_team)) |
            ((self.df['HomeTeam'] == away_team) & (self.df['AwayTeam'] == home_team))
        ]
        
        if len(h2h_matches) >= 3:  # Only if we have enough H2H history
            # Calculate H2H-specific goal averages
            h2h_home_goals = h2h_matches[h2h_matches['HomeTeam'] == home_team]['FTHG'].mean()
            h2h_away_goals = h2h_matches[h2h_matches['AwayTeam'] == away_team]['FTAG'].mean()
            
            if pd.notna(h2h_home_goals) and pd.notna(h2h_away_goals):
                # Blend general stats (70%) with H2H stats (30%)
                h2h_weight = 0.3
                h_attack = h_attack * (1 - h2h_weight) + (h2h_home_goals / self.avg_home_goals) * h2h_weight
                a_attack = a_attack * (1 - h2h_weight) + (h2h_away_goals / self.avg_away_goals) * h2h_weight

        # Expected Goals (Lambda)
        # For neutral matches, we use the global average goal rate as the baseline
        avg_goals = (self.avg_home_goals + self.avg_away_goals) / 2 if neutral_venue else self.avg_home_goals
        
        home_xg = h_attack * a_defense * avg_goals
        away_xg = a_attack * h_defense * avg_goals

        # Calculate probabilties for scores 0-9
        max_goals = 10
        home_probs = [poisson.pmf(i, home_xg) for i in range(max_goals)]
        away_probs = [poisson.pmf(i, away_xg) for i in range(max_goals)]

        # Calculate Outcome Probabilities and categorize scores
        prob_home_win = 0
        prob_draw = 0
        prob_away_win = 0
        
        # Categorize scores by outcome AND keep global list
        home_win_scores = []
        draw_scores = []
        away_win_scores = []
        all_scores = []  # Global list for precision

        for h in range(max_goals):
            for a in range(max_goals):
                p = home_probs[h] * away_probs[a]
                all_scores.append(((h, a), p))
                
                if h > a:
                    prob_home_win += p
                    home_win_scores.append(((h, a), p))
                elif h == a:
                    prob_draw += p
                    draw_scores.append(((h, a), p))
                else:
                    prob_away_win += p
                    away_win_scores.append(((h, a), p))
        
        # HYBRID INTELLIGENT SELECTION
        # Score 1: Most probable score from the most likely outcome (COHERENCE)
        outcomes = [
            (prob_home_win, home_win_scores, "home_win"),
            (prob_draw, draw_scores, "draw"),
            (prob_away_win, away_win_scores, "away_win")
        ]
        outcomes.sort(key=lambda x: x[0], reverse=True)
        
        most_likely_outcome_scores = outcomes[0][1]
        most_likely_outcome_scores.sort(key=lambda x: x[1], reverse=True)
        score_1 = most_likely_outcome_scores[0] if most_likely_outcome_scores else ((0, 0), 0)
        
        # Score 2: Second most probable score GLOBALLY (PRECISION)
        all_scores.sort(key=lambda x: x[1], reverse=True)
        # Find the second score that's different from score_1
        score_2 = ((0, 0), 0)
        for score, prob in all_scores:
            if score != score_1[0]:
                score_2 = ((score[0], score[1]), prob)
                break
        
        top_2_scores = [score_1, score_2]

        return {
            "home_team": home_team,
            "away_team": away_team,
            "expected_goals_home": round(home_xg, 2),
            "expected_goals_away": round(away_xg, 2),
            "win_prob": round(prob_home_win * 100, 1),
            "draw_prob": round(prob_draw * 100, 1),
            "loss_prob": round(prob_away_win * 100, 1),
            "most_likely_score": f"{top_2_scores[0][0][0]}-{top_2_scores[0][0][1]}",
            "score_prob": round(top_2_scores[0][1] * 100, 1),
            "second_likely_score": f"{top_2_scores[1][0][0]}-{top_2_scores[1][0][1]}",
            "second_score_prob": round(top_2_scores[1][1] * 100, 1)
        }

    def get_teams(self):
        return self.teams
