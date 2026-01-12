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
        df_list = []
        
        # Determine files to load
        files_to_load = []
        if self.data_file and os.path.exists(self.data_file):
            files_to_load.append(self.data_file)
        elif self.league_code:
            files_to_load = [
                os.path.join(self.data_dir, f) 
                for f in os.listdir(self.data_dir) 
                if f.endswith('.csv') and f.startswith(self.league_code)
            ]
            
        for file in files_to_load:
            try:
                # football-data.co.uk sometimes has encoding issues, try latin1 if utf-8 fails
                try:
                    df = pd.read_csv(file)
                except UnicodeDecodeError:
                    df = pd.read_csv(file, encoding='latin1')
                
                # Ensure date parsing works immediately to filter invalid rows early
                if 'Date' in df.columns:
                     df = df.dropna(subset=['Date'])
                
                # Keep only relevant columns
                if 'HomeTeam' in df.columns and 'AwayTeam' in df.columns and 'FTHG' in df.columns and 'FTAG' in df.columns:
                    # Load additional shot data if available, otherwise fill with 0
                    cols_to_keep = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']
                    
                    # Manage Shot Data (HS, AS, HST, AST)
                    for col in ['HST', 'AST', 'HS', 'AS']:
                        if col not in df.columns:
                            df[col] = 0
                        cols_to_keep.append(col)

                    # Manage Estimated xG columns if they exist in file
                    if 'Estimated_xG_Home' in df.columns:
                        cols_to_keep.append('Estimated_xG_Home')
                    if 'Estimated_xG_Away' in df.columns:
                        cols_to_keep.append('Estimated_xG_Away')

                    # Filter columns
                    df = df[cols_to_keep]
                    df_list.append(df)
            except Exception as e:
                print(f"Error loading {file}: {e}")
        
        if not df_list:
            return pd.DataFrame()
            
        full_df = pd.concat(df_list, ignore_index=True)
        # Filter out matches that haven't been played (no score)
        full_df = full_df.dropna(subset=['FTHG', 'FTAG'])
        
        # Calculate Estimated xG if not present (Simple Shot-Based Model)
        # Weight: 0.30 per Shot on Target, 0.07 per Shot off Target
        if 'Estimated_xG_Home' not in full_df.columns:
            full_df['ShotsOffTarget_Home'] = full_df['HS'] - full_df['HST']
            full_df['ShotsOffTarget_Away'] = full_df['AS'] - full_df['AST']
            
            full_df['Estimated_xG_Home'] = (full_df['HST'] * 0.32) + (full_df['ShotsOffTarget_Home'] * 0.06)
            full_df['Estimated_xG_Away'] = (full_df['AST'] * 0.32) + (full_df['ShotsOffTarget_Away'] * 0.06)
            
            # Fallback for rows where shot data might be missing (0 shots)
            # Use actual goals as a proxy if shots are 0 but goals > 0 (data error fix)
            mask_no_shots = (full_df['HS'] == 0) & (full_df['FTHG'] > 0)
            full_df.loc[mask_no_shots, 'Estimated_xG_Home'] = full_df.loc[mask_no_shots, 'FTHG'] * 0.8
            
            mask_no_shots_away = (full_df['AS'] == 0) & (full_df['FTAG'] > 0)
            full_df.loc[mask_no_shots_away, 'Estimated_xG_Away'] = full_df.loc[mask_no_shots_away, 'FTAG'] * 0.8

        return full_df

    def _train_model(self):
        """Calculates Attack and Defense strengths using Hybrid Model (Goals + xG) and Exponential Decay."""
        # Parse dates
        self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce', dayfirst=True)
        self.df = self.df.dropna(subset=['Date'])
        
        # Sort by date
        self.df = self.df.sort_values('Date').reset_index(drop=True)
        
        # Build Elo ratings
        self.elo_system = EloRatingSystem()
        self.elo_system.process_historical_data(self.df)
        
        # Current date reference
        latest_date = self.df['Date'].max()
        
        # Calculate age in days
        self.df['DaysAgo'] = (latest_date - self.df['Date']).dt.days
        
        # === 1. EXPONENTIAL TIME DECAY ===
        # Replaces rigid steps. E.g., decay_rate 0.005 means weight halves every ~140 days
        decay_rate = 0.006 
        self.df['Weight'] = np.exp(-decay_rate * self.df['DaysAgo'])
        
        # REMOVED: Rigid "last 5 matches" boost, replaced by separate Form Index calculation
        
        # Calculate weighted league averages (Hybrid)
        total_weight = self.df['Weight'].sum()
        
        avg_home_goals = (self.df['FTHG'] * self.df['Weight']).sum() / total_weight
        avg_away_goals = (self.df['FTAG'] * self.df['Weight']).sum() / total_weight
        
        avg_home_xg = (self.df['Estimated_xG_Home'] * self.df['Weight']).sum() / total_weight
        avg_away_xg = (self.df['Estimated_xG_Away'] * self.df['Weight']).sum() / total_weight
        
        # Global League Average (Hybrid: 40% Goals, 60% xG)
        # CHECK: If xG averages are extremely low (indicating missing data), fall back to 100% Goals
        if avg_home_xg < 0.5: # Threshold for "missing shot data"
            print(f"[INFO] Low xG detected ({avg_home_xg:.2f}). Switching to Goals-Only model for {self.league_code}.")
            self.avg_home_strength = avg_home_goals
            self.avg_away_strength = avg_away_goals
            self.weight_goals = 1.0
            self.weight_xg = 0.0
        else:
            self.weight_goals = 0.4
            self.weight_xg = 0.6
            self.avg_home_strength = (avg_home_goals * self.weight_goals) + (avg_home_xg * self.weight_xg)
            self.avg_away_strength = (avg_away_goals * self.weight_goals) + (avg_away_xg * self.weight_xg)
        
        # Calculate weighted stats per team with strict Home/Away separation
        def weighted_stats(group, is_home=True):
            total_w = group['Weight'].sum()
            if total_w == 0:
                return pd.Series({'hybrid_scored': 0, 'hybrid_conceded': 0})
            
            if is_home:
                # Scored at Home
                goals_scored = (group['FTHG'] * group['Weight']).sum() / total_w
                xg_scored = (group['Estimated_xG_Home'] * group['Weight']).sum() / total_w
                hybrid_scored = (goals_scored * self.weight_goals) + (xg_scored * self.weight_xg)
                
                # Conceded at Home
                goals_conceded = (group['FTAG'] * group['Weight']).sum() / total_w
                xg_conceded = (group['Estimated_xG_Away'] * group['Weight']).sum() / total_w
                hybrid_conceded = (goals_conceded * self.weight_goals) + (xg_conceded * self.weight_xg)
            else:
                # Scored Away
                goals_scored = (group['FTAG'] * group['Weight']).sum() / total_w
                xg_scored = (group['Estimated_xG_Away'] * group['Weight']).sum() / total_w
                hybrid_scored = (goals_scored * self.weight_goals) + (xg_scored * self.weight_xg)
                
                # Conceded Away
                goals_conceded = (group['FTHG'] * group['Weight']).sum() / total_w
                xg_conceded = (group['Estimated_xG_Home'] * group['Weight']).sum() / total_w
                hybrid_conceded = (goals_conceded * self.weight_goals) + (xg_conceded * self.weight_xg)
            
            return pd.Series({'scored': hybrid_scored, 'conceded': hybrid_conceded})
        
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
        
        # === TOURNAMENT POOLING (Fix for AFCON) ===
        # If we are in "Legacy/Goals Only" mode (AFCON), we should NOT split Home/Away stats.
        # Why? Because samples are small (3-4 games) and venues are neutral.
        # Splitting splits the sample size in half -> Noise.
        # Pooling makes "Mali" have one strength rating based on ALL games.
        if self.weight_xg == 0.0:
            print(f"[INFO] Tournament Mode detected for {self.league_code}. Pooling Home/Away stats.")
            
            # Simple Pooling: Average the Home and Away raw stats (if they exist)
            # We fillna(0) to handle cases where a team only played Home or only Away
            self.team_stats = self.team_stats.fillna(0)
            
            # Calculate Global Average per team
            # We treat Home and Away performances as equal contributors to "Form/Ability"
            self.team_stats['GlobalScored'] = (self.team_stats['AvgHomeGoalsScored'] + self.team_stats['AvgAwayGoalsScored']) / 2
            self.team_stats['GlobalConceded'] = (self.team_stats['AvgHomeGoalsConceded'] + self.team_stats['AvgAwayGoalsConceded']) / 2
            
            # Overwrite Home/Away specific stats with Global
            self.team_stats['AvgHomeGoalsScored'] = self.team_stats['GlobalScored']
            self.team_stats['AvgAwayGoalsScored'] = self.team_stats['GlobalScored']
            self.team_stats['AvgHomeGoalsConceded'] = self.team_stats['GlobalConceded']
            self.team_stats['AvgAwayGoalsConceded'] = self.team_stats['GlobalConceded']

        # Calculate Strength Metrics (using Hybrid values)
        # STRICT Separation: Home Attack only compares to Home Avg, etc.
        self.team_stats['HomeAttackStrength'] = self.team_stats['AvgHomeGoalsScored'] / self.avg_home_strength
        self.team_stats['AwayAttackStrength'] = self.team_stats['AvgAwayGoalsScored'] / self.avg_away_strength
        self.team_stats['HomeDefenseStrength'] = self.team_stats['AvgHomeGoalsConceded'] / self.avg_away_strength
        self.team_stats['AwayDefenseStrength'] = self.team_stats['AvgAwayGoalsConceded'] / self.avg_home_strength
        
        # Fill NaN with 1.0 (neutral strength)
        self.team_stats = self.team_stats.fillna(1.0)
        
        # Calculate Form Index for each team
        self._calculate_form_index()

    def predict_match(self, home_team, away_team, neutral_venue=False, modifiers=None):
        """
        Predicts match outcomes.
        neutral_venue: If True, uses average of Home/Away stats for both teams.
        modifiers: Dict like {'TeamName': {'attack': 1.1, 'defense': 0.9}}. 
                   (Attack > 1 is boost, Defense < 1 is boost).
        """
        if home_team not in self.team_stats.index or away_team not in self.team_stats.index:
            return {"error": f"Team not found."}

        # Get Team Stats with strict Home/Away logic
        h_attack = self.team_stats.loc[home_team, 'HomeAttackStrength']
        h_defense = self.team_stats.loc[home_team, 'HomeDefenseStrength']
        a_attack = self.team_stats.loc[away_team, 'AwayAttackStrength']
        a_defense = self.team_stats.loc[away_team, 'AwayDefenseStrength']
        
        # === MODIFIER CALCULATION (ADDITIVE LOGIC) ===
        # v5.2: Switch from Multiplicative (A*B*C) to Additive (1 + A + B + C) to prevent exponential blowouts
        
        # === LEGACY MODE FOR AFCON / INTERNATIONAL ===
        # User Feedback: AFCON predictions were better "at the start".
        # Advanced modifiers (Form, Elo) introduce noise for international teams 
        # because matches are too sparse (months apart).
        # We detect AFCON via the "Goals Only" mode trigger (weight_xg == 0) or specific code.
        is_legacy_mode = (self.weight_xg == 0.0) 
        
        if is_legacy_mode:
            # Force everything to Neutral (1.0) -> Pure Stats Model
            h_form = 1.0
            a_form = 1.0
            prestige_enabled = False
            elo_enabled = False
        else:
            h_form = self.form_ratings.get(home_team, 1.0)
            a_form = self.form_ratings.get(away_team, 1.0)
            prestige_enabled = True
            elo_enabled = True

        # === MODIFIER CALCULATION (ADDITIVE LOGIC) ===
        # v5.2: Switch from Multiplicative (A*B*C) to Additive (1 + A + B + C)
        
        # 1. Form Modifier (Relative to 1.0)
        h_form_mod = (h_form - 1.0)
        a_form_mod = (a_form - 1.0)
        
        # 2. Prestige Modifier (Relative to 1.0)
        h_prestige_mod = 0.0
        a_prestige_mod = 0.0
        
        if prestige_enabled:
            PRESTIGE_BOOSTS = {
                "Man City": 1.04, "Liverpool": 1.04, "Arsenal": 1.04,
                "Real Madrid": 1.04, "Barcelona": 1.04, "Bayern Munich": 1.04, "Leverkusen": 1.04,
                "Paris SG": 1.04, "Inter": 1.04,
                "Chelsea": 1.02, "Tottenham": 1.02, "Atletico Madrid": 1.02,
                "Dortmund": 1.02, "Leipzig": 1.02, "Juventus": 1.02, "Milan": 1.02,
                "Benfica": 1.02, "Porto": 1.02, "Sporting CP": 1.02
            }
            h_prestige_mod = PRESTIGE_BOOSTS.get(home_team, 1.0) - 1.0
            a_prestige_mod = PRESTIGE_BOOSTS.get(away_team, 1.0) - 1.0
        
        # 3. Elo Modifier (Relative to 1.0)
        elo_val = 0.0
        if elo_enabled:
            elo_diff = self.elo_system.get_rating_difference(home_team, away_team)
            elo_val = elo_diff / 1400
            elo_val = max(-0.25, min(elo_val, 0.25))
        
        # Calculate Total Modifiers (Additive)
        # Home Attack gets: Form + Prestige + (Elo if +)
        h_attack_boost = h_form_mod + h_prestige_mod + (elo_val if elo_val > 0 else 0)
        # Home Defense gets: Form (inv) + Prestige (inv) + (Elo if +)
        # Defense boost means "Lower is better" (multiplying by < 1)
        # We model this as reducing the CONCEDED goals
        h_defense_boost = - (h_form_mod + h_prestige_mod + (elo_val if elo_val > 0 else 0))

        a_attack_boost = a_form_mod + a_prestige_mod + (-elo_val if elo_val < 0 else 0)
        a_defense_boost = - (a_form_mod + a_prestige_mod + (-elo_val if elo_val < 0 else 0))
        
        # Apply Additive Modifiers
        h_attack *= (1.0 + h_attack_boost)
        h_defense *= (1.0 + h_defense_boost * 0.5) # Def modifiers have half impact (harder to defend perfectly)
        a_attack *= (1.0 + a_attack_boost)
        a_defense *= (1.0 + a_defense_boost * 0.5)

        # Get Neutral Venue Adjustments
        if neutral_venue:
            h_attack = (h_attack + self.team_stats.loc[home_team, 'AwayAttackStrength']) / 2
            h_defense = (h_defense + self.team_stats.loc[home_team, 'AwayDefenseStrength']) / 2
            a_attack = (a_attack + self.team_stats.loc[away_team, 'HomeAttackStrength']) / 2
            a_defense = (a_defense + self.team_stats.loc[away_team, 'HomeDefenseStrength']) / 2

        # Apply Manual Modifiers
        if modifiers:
            if home_team in modifiers:
                h_attack *= modifiers[home_team].get('attack', 1.0)
                h_defense *= modifiers[home_team].get('defense', 1.0)
            if away_team in modifiers:
                a_attack *= modifiers[away_team].get('attack', 1.0)
                a_defense *= modifiers[away_team].get('defense', 1.0)

        # === HEAD-TO-HEAD ADJUSTMENT ===
        h2h_matches = self.df[
            ((self.df['HomeTeam'] == home_team) & (self.df['AwayTeam'] == away_team)) |
            ((self.df['HomeTeam'] == away_team) & (self.df['AwayTeam'] == home_team))
        ]
        
        if len(h2h_matches) >= 3:
            h2h_home_goals = h2h_matches[h2h_matches['HomeTeam'] == home_team]['FTHG'].mean()
            h2h_away_goals = h2h_matches[h2h_matches['AwayTeam'] == away_team]['FTAG'].mean()
            
            if pd.notna(h2h_home_goals) and pd.notna(h2h_away_goals):
                h2h_weight = 0.25
                h_attack = h_attack * (1 - h2h_weight) + (h2h_home_goals / self.avg_home_strength) * h2h_weight
                a_attack = a_attack * (1 - h2h_weight) + (h2h_away_goals / self.avg_away_strength) * h2h_weight

        # Expected Goals (Lambda)
        avg_goals = (self.avg_home_strength + self.avg_away_strength) / 2 if neutral_venue else self.avg_home_strength
        
        home_xg = h_attack * a_defense * avg_goals
        away_xg = a_attack * h_defense * avg_goals

        # === SOFT SATURATION (Diminishing Returns) ===
        # Instead of a hard cap, we apply a "Soft Ceiling" function
        # If xG > 2.5, every extra point is worth less
        # f(x) = 2.5 + (x - 2.5) ^ 0.7  for x > 2.5
        def soft_saturate(val, threshold=2.5):
            if val <= threshold: return val
            return threshold + (val - threshold) ** 0.65
            
        home_xg = soft_saturate(home_xg)
        away_xg = soft_saturate(away_xg)
        
        # Calculate probabilties for scores 0-9
        max_goals = 10
        
        # 1. Base Poisson Probabilities
        home_probs = [poisson.pmf(i, home_xg) for i in range(max_goals)]
        away_probs = [poisson.pmf(i, away_xg) for i in range(max_goals)]
        
        # 2. Build Joint Probability Matrix
        prob_matrix = np.outer(home_probs, away_probs)
        
        # 3. Apply Dixon-Coles Adjustment
        prob_matrix = self._dixon_coles_adjustment(prob_matrix, home_xg, away_xg)

        # Calculate Outcome Probabilities and categorize scores
        prob_home_win = 0
        prob_draw = 0
        prob_away_win = 0
        
        home_win_scores = []
        draw_scores = []
        away_win_scores = []
        all_scores = [] 

        for h in range(max_goals):
            for a in range(max_goals):
                p = prob_matrix[h][a]
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
        
        # Normalize Probabilities
        total_prob = prob_home_win + prob_draw + prob_away_win
        if total_prob > 0:
            prob_home_win /= total_prob
            prob_draw /= total_prob
            prob_away_win /= total_prob
            
            for i in range(len(home_win_scores)):
                home_win_scores[i] = (home_win_scores[i][0], home_win_scores[i][1] / total_prob)
            for i in range(len(draw_scores)):
                draw_scores[i] = (draw_scores[i][0], draw_scores[i][1] / total_prob)
            for i in range(len(away_win_scores)):
                away_win_scores[i] = (away_win_scores[i][0], away_win_scores[i][1] / total_prob)
            all_scores = [((s[0], s[1]), p / total_prob) for (s, p) in all_scores]
        
        # HYBRID INTELLIGENT SELECTION
        outcomes = [
            (prob_home_win, home_win_scores, "home_win"),
            (prob_draw, draw_scores, "draw"),
            (prob_away_win, away_win_scores, "away_win")
        ]
        outcomes.sort(key=lambda x: x[0], reverse=True)
        
        most_likely_outcome_scores = outcomes[0][1]
        most_likely_outcome_scores.sort(key=lambda x: x[1], reverse=True)
        score_1 = most_likely_outcome_scores[0] if most_likely_outcome_scores else ((0, 0), 0)
        
        all_scores.sort(key=lambda x: x[1], reverse=True)
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

    def _calculate_form_index(self):
        """Calculates a Form Index based on last 5, 10, and 15 matches."""
        self.form_ratings = {}
        
        for team in self.teams:
            matches = self.df[(self.df['HomeTeam'] == team) | (self.df['AwayTeam'] == team)].sort_values('Date')
            
            if len(matches) < 5:
                self.form_ratings[team] = 1.0
                continue
                
            def get_performance(row):
                is_home = row['HomeTeam'] == team
                goals_for = row['FTHG'] if is_home else row['FTAG']
                goals_against = row['FTAG'] if is_home else row['FTHG']
                
                if goals_for > goals_against: result = 1.0
                elif goals_for == goals_against: result = 0.5
                else: result = 0.0
                return result

            perfs = matches.apply(get_performance, axis=1).values
            
            f5 = np.mean(perfs[-5:]) if len(perfs) >= 5 else 0.5
            f10 = np.mean(perfs[-10:]) if len(perfs) >= 10 else f5
            f15 = np.mean(perfs[-15:]) if len(perfs) >= 15 else f10
            
            raw_form = (f5 * 0.5) + (f10 * 0.3) + (f15 * 0.2)
            # Map [0, 1] to [0.9, 1.1] (Dampened from 0.8-1.2)
            form_multiplier = 0.9 + (raw_form * 0.2)
            
            self.form_ratings[team] = form_multiplier

    def _dixon_coles_adjustment(self, prob_matrix, home_xg, away_xg):
        """
        Applies Dixon-Coles adjustment to handle low-scoring draw dependencies.
        Rho is the dependence parameter (typically -0.1 to 0.1).
        We use a dynamic Rho based on league averages, but fixed -0.13 is standard for football.
        """
        rho = -0.13  # Standard interdependence parameter
        
        # Correction factors
        # 0-0
        if home_xg > 0 and away_xg > 0:
            prob_matrix[0, 0] *= (1 - (home_xg * away_xg * rho))
        
        # 0-1
        if home_xg > 0:
            prob_matrix[0, 1] *= (1 + (home_xg * rho))
            
        # 1-0
        if away_xg > 0:
            prob_matrix[1, 0] *= (1 + (away_xg * rho))
            
        # 1-1
        if home_xg > 0 and away_xg > 0:
            prob_matrix[1, 1] *= (1 - rho)
            
        return prob_matrix

    def get_teams(self):
        return self.teams
