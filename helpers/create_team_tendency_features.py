"""
Create team offensive tendency features based on historical play calling.
This calculates how often a team runs vs passes (short/long) based on previous games.

To prevent data leakage:
- For 2017: Use overall average from ALL seasons (2017-2024)
- For other years: Use previous season's average
"""

import pandas as pd
import numpy as np


def calculate_season_means(df, season=None):
    """
    Calculate the league-wide average percentages for Run, Short_Pass, and Long_Pass
    for a specific season or overall.
    
    Parameters:
    df: DataFrame with 'PlayCall' column already classified (also works with 'Play_Call')
    season: int or None - if provided, calculate for that season only
    
    Returns:
    dict: Dictionary with keys 'Run', 'Short_Pass', 'Long_Pass' containing percentages as decimals
    """
    # Determine which column name is used for play classification
    play_call_col = 'PlayCall' if 'PlayCall' in df.columns else 'Play_Call'
    
    # Filter to only offensive plays (exclude special teams)
    offensive_plays = df[df[play_call_col].isin(['Run', 'Short_Pass', 'Long_Pass'])].copy()
    
    # If season specified, filter to that season
    if season is not None:
        offensive_plays = offensive_plays[offensive_plays['Season'] == season]
    
    # Count each play type
    play_counts = offensive_plays[play_call_col].value_counts()
    total_plays = len(offensive_plays)
    
    if total_plays == 0:
        return {'Run': 0.0, 'Short_Pass': 0.0, 'Long_Pass': 0.0}
    
    # Calculate percentages (as decimals, e.g., 0.45 = 45%)
    season_means = {
        'Run': play_counts.get('Run', 0) / total_plays,
        'Short_Pass': play_counts.get('Short_Pass', 0) / total_plays,
        'Long_Pass': play_counts.get('Long_Pass', 0) / total_plays
    }
    
    season_label = f"{season}" if season else "ALL SEASONS"
    print("=" * 60)
    print(f"LEAGUE AVERAGES FOR {season_label}")
    print("=" * 60)
    for play_type, percentage in season_means.items():
        print(f"{play_type:12s}: {percentage:6.2%}")
    print("=" * 60)
    print()
    
    return season_means


def calculate_team_tendencies(team_plays):
    """
    Calculate a team's offensive tendencies based on their play history.
    
    This function automatically filters to only Run, Short_Pass, and Long_Pass.
    You can pass in a DataFrame with ALL play types (Field_Goal, Punt, Spike, etc.)
    and it will skip the irrelevant ones.
    
    Parameters:
    team_plays: DataFrame with plays for one team (can include all play types)
                Must have 'PlayCall' column (also works with 'Play_Call')
    
    Returns:
    dict: {'Run': 0.xxx, 'Short_Pass': 0.xxx, 'Long_Pass': 0.xxx, 'num_plays': X, 'num_games': X}
          Returns None if no plays available
    """
    if len(team_plays) == 0:
        return None
    
    # Determine which column name is used for play classification
    play_call_col = 'PlayCall' if 'PlayCall' in team_plays.columns else 'Play_Call'
    
    # Filter to only offensive plays (automatically excludes Field_Goal, Punt, Spike, etc.)
    offensive_plays = team_plays[team_plays[play_call_col].isin(['Run', 'Short_Pass', 'Long_Pass'])]
    
    if len(offensive_plays) == 0:
        return None
    
    # Count each play type
    play_counts = offensive_plays[play_call_col].value_counts()
    total_plays = len(offensive_plays)
    
    # Calculate percentages
    tendencies = {
        'Run': play_counts.get('Run', 0) / total_plays,
        'Short_Pass': play_counts.get('Short_Pass', 0) / total_plays,
        'Long_Pass': play_counts.get('Long_Pass', 0) / total_plays,
        'num_plays': total_plays,
        'num_games': team_plays['GameId'].nunique() if 'GameId' in team_plays.columns else 0
    }
    
    return tendencies


def add_team_tendency_features(df_season, df_previous_season=None, global_means=None, team_col='TeamWithPossessionShort'):
    """
    Add team offensive tendency features to a season's dataframe.
    
    For each game, calculates team tendencies based on PREVIOUS games only (no data leakage).
    
    Logic:
    - If < 3 games played this season → Use previous season's team data (or global mean if no previous season)
    - If >= 3 games played this season → Use current season's previous games
    
    Parameters:
    df_season: DataFrame for current season (must have Season, Week (int 1-17), and team_col columns)
    df_previous_season: DataFrame for previous season (optional, None for 2017)
    global_means: dict with 'Run', 'Short_Pass', 'Long_Pass' percentages (for 2017 or fallback)
    team_col: str, name of column with team abbreviations (default: 'TeamWithPossessionShort')
    
    Note: Only regular season games should be included (Week 1-17)
    
    Returns:
    DataFrame with new columns added: team_run_pct, team_short_pass_pct, team_long_pass_pct
    """
    # Make a copy to avoid modifying original
    df = df_season.copy()
    
    # Create GameId if it doesn't exist
    if 'GameId' not in df.columns:
        df['GameId'] = (df['Week'].astype(str) + '_' + 
                       df['Date'].astype(str) + '_' + 
                       df['HomeTeam'] + '_' + df['AwayTeam'])
    
    # Sort by week (integer 1-17) to ensure chronological order
    # Week is now an integer representing regular season weeks only
    df = df.sort_values(['Week', 'GameId']).reset_index(drop=True)
    
    # Initialize the new columns with NaN
    df['team_run_pct'] = np.nan
    df['team_short_pass_pct'] = np.nan
    df['team_long_pass_pct'] = np.nan
    
    # Get unique teams
    teams = df[team_col].unique()
    
    print(f"\nProcessing {len(teams)} teams for season {df['Season'].iloc[0]}...")
    
    # Process each team
    for team in teams:
        # Get all games for this team, in order
        team_mask = df[team_col] == team
        team_games = df[team_mask]['GameId'].unique()
        
        # For each game this team plays
        for game_idx, game_id in enumerate(team_games):
            game_mask = (df[team_col] == team) & (df['GameId'] == game_id)
            
            # Count how many games this team has played so far THIS season (before this game)
            num_games_played = game_idx  # 0 for first game, 1 for second, etc.
            
            # Decide where to get tendency data from
            if num_games_played < 3:
                # Use previous season's data for this team (or global mean if no previous season)
                if df_previous_season is not None:
                    # Get all plays from previous season for this team
                    prev_team_plays = df_previous_season[df_previous_season[team_col] == team]
                    tendencies = calculate_team_tendencies(prev_team_plays)
                    
                    if tendencies is None:
                        # Team didn't exist in previous season or no data, use global mean
                        tendencies = {
                            'Run': global_means['Run'],
                            'Short_Pass': global_means['Short_Pass'],
                            'Long_Pass': global_means['Long_Pass']
                        }
                else:
                    # No previous season (e.g., 2017), use global mean
                    tendencies = {
                        'Run': global_means['Run'],
                        'Short_Pass': global_means['Short_Pass'],
                        'Long_Pass': global_means['Long_Pass']
                    }
            else:
                # Use this season's previous games (games 0 through game_idx-1)
                previous_games = team_games[:game_idx]
                prev_game_mask = (df[team_col] == team) & (df['GameId'].isin(previous_games))
                prev_plays = df[prev_game_mask]
                
                tendencies = calculate_team_tendencies(prev_plays)
                
                if tendencies is None:
                    # Shouldn't happen, but fallback to global mean
                    tendencies = {
                        'Run': global_means['Run'],
                        'Short_Pass': global_means['Short_Pass'],
                        'Long_Pass': global_means['Long_Pass']
                    }
            
            # Assign the same tendencies to ALL plays in this game for this team
            df.loc[game_mask, 'team_run_pct'] = tendencies['Run']
            df.loc[game_mask, 'team_short_pass_pct'] = tendencies['Short_Pass']
            df.loc[game_mask, 'team_long_pass_pct'] = tendencies['Long_Pass']
    
    print(f"Added team tendency features for {len(teams)} teams")
    
    return df


# ============================================================================
# TEST/DEMO CODE
# ============================================================================
# This section demonstrates how to use the functions above.
# Run this file directly to see examples of each function in action.
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("TESTING TEAM TENDENCY FEATURE ENGINEERING")
    print("="*60)
    print("\nThis demo shows how to add team tendency features to prevent data leakage.")
    print("Each team's tendencies are calculated from PREVIOUS games only.\n")
    
    print("\n" + "="*60)
    print("Chunk 1: League Averages Calculation")
    print("="*60)
    
    # Load multiple seasons to calculate overall average
    from helpers.Create_Target_Variable import classify_play_call
    
    all_seasons = []
    for year in [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]:
        df = pd.read_csv(f'Classify Plays/{year}_plays.csv')
        df['Season'] = year
        df['PlayCall'] = df.apply(classify_play_call, axis=1)
        df = df[df['PlayCall'].notna()]
        all_seasons.append(df)
        print(f"Loaded {year}: {len(df):,} plays")
    
    # Combine all seasons
    df_all = pd.concat(all_seasons, ignore_index=True)
    print(f"\nTotal plays: {len(df_all):,}\n")
    
    # Calculate overall average (used as global mean for 2017 or teams without previous season data)
    overall_means = calculate_season_means(df_all, season=None)
    
    # Can also calculate season-specific averages if needed:
    # means_2017 = calculate_season_means(df_all, season=2017)  # For use in 2018
    # means_2018 = calculate_season_means(df_all, season=2018)  # For use in 2019
    
    print("\n" + "="*60)
    print("Chunk 2: Team Tendencies Calculation")
    print("="*60)
    
    # Get plays for one team (e.g., Kansas City Chiefs in 2017)
    df_2017 = df_all[df_all['Season'] == 2017].copy()
    
    # Find a team - use TeamWithPossession column
    team_col = 'TeamWithPossession'
    
    # Create a GameId if it doesn't exist (combination of Week, Date, and teams)
    if 'GameId' not in df_2017.columns:
        df_2017['GameId'] = df_2017['Week'].astype(str) + '_' + df_2017['Date'].astype(str) + '_' + df_2017['HomeTeam'] + '_' + df_2017['AwayTeam']
    
    # Get plays for first team we find
    sample_team = df_2017[team_col].value_counts().index[0]
    team_plays = df_2017[df_2017[team_col] == sample_team].copy()
    
    print(f"\nSample Team: {sample_team}")
    print(f"Total plays: {len(team_plays)}")
    
    # Calculate their tendencies
    tendencies = calculate_team_tendencies(team_plays)
    
    if tendencies:
        print(f"\nTeam Tendencies:")
        print(f"  Run:        {tendencies['Run']:.2%}")
        print(f"  Short Pass: {tendencies['Short_Pass']:.2%}")
        print(f"  Long Pass:  {tendencies['Long_Pass']:.2%}")
        print(f"  Total offensive plays: {tendencies['num_plays']}")
        print(f"  Games played: {tendencies['num_games']}")
    
    print("\n" + "="*60)
    print("Chunk 3: Add Team Tendency Features to DataFrame")
    print("="*60)
    
    # Test with 2018 season using 2017 as previous season
    df_2018 = df_all[df_all['Season'] == 2018].copy()
    df_2017 = df_all[df_all['Season'] == 2017].copy()
    
    print(f"\n2018 plays: {len(df_2018):,}")
    print(f"2017 plays: {len(df_2017):,}")
    
    # Add team tendency features
    df_2018_with_features = add_team_tendency_features(
        df_season=df_2018,
        df_previous_season=df_2017,
        global_means=overall_means,
        team_col='TeamWithPossession'  # Using full name since that's what we have
    )
    
    # Show results for one team
    sample_team = df_2018_with_features['TeamWithPossession'].value_counts().index[0]
    team_df = df_2018_with_features[df_2018_with_features['TeamWithPossession'] == sample_team]
    
    print(f"\n{sample_team} - Sample of tendency features by week:")
    print("-" * 80)
    
    # Group by week and show first value (all plays in a game have same values)
    weekly_tendencies = team_df.groupby('Week', sort=False)[
        ['team_run_pct', 'team_short_pass_pct', 'team_long_pass_pct']
    ].first()
    
    # Show first 10 weeks
    print(weekly_tendencies.head(10))
    
    print(f"\nNote: Weeks 1-3 should use 2017 {sample_team} data")
    print(f"Week 4+ should use rolling 2018 data (previous games)")
    
    # Verify all plays in one game have same values
    first_game = team_df['GameId'].iloc[0]
    game_plays = team_df[team_df['GameId'] == first_game]
    print(f"\n✓ Verification: All {len(game_plays)} plays in first game have same tendency values:")
    print(f"  Run: {game_plays['team_run_pct'].nunique()} unique value(s)")
    print(f"  Short Pass: {game_plays['team_short_pass_pct'].nunique()} unique value(s)")
    print(f"  Long Pass: {game_plays['team_long_pass_pct'].nunique()} unique value(s)")
    
    print("\n" + "="*60)
    print("USAGE EXAMPLE FOR YOUR OWN DATA:")
    print("="*60)
    print("""
# To use this on your own data:

from create_team_tendency_features import add_team_tendency_features, calculate_season_means

# 1. Load your data (must have PlayCall or Play_Call column with classifications)
df_2019 = pd.read_csv('your_2019_data.csv')
df_2018 = pd.read_csv('your_2018_data.csv')  # Previous season

# 2. Calculate global means (for fallback/2017)
global_means = calculate_season_means(df_all_seasons, season=None)

# 3. Add features
df_2019_with_features = add_team_tendency_features(
    df_season=df_2019,
    df_previous_season=df_2018,
    global_means=global_means,
    team_col='TeamWithPossessionShort'  # Or whichever column has team names
)

# Now df_2019_with_features has three new columns:
# - team_run_pct
# - team_short_pass_pct  
# - team_long_pass_pct
""")
