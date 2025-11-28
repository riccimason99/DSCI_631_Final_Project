# import 2017_plays.csv
import pandas as pd

# read the csv file
df = pd.read_csv('Classify Plays/2017_plays.csv')


def classify_play_call(row):
    """
    Classify plays into categories: Run, Short_Pass, Long_Pass, Field_Goal, Punt
    Returns None for plays that should be removed.
    
    Parameters:
    row: pandas Series containing PlayDescription and PlayOutcome columns
    
    Returns:
    str or None: Play category or None if play should be removed
    """
    desc = str(row['PlayDescription']).lower()
    outcome = str(row['PlayOutcome']).lower()
    
    # Remove: Kickoffs
    if 'kickoff' in outcome or 'kicks' in desc and 'punts' not in desc:
        return None
    
    # Remove: Sacks
    if 'sack' in outcome or 'sacked' in desc:
        return None
    
    # Remove: QB Fumbles (fumbles by QB before passing)
    if 'fumbles (aborted)' in desc:
        return None
    
    # Remove: Extra Points
    if 'extra point' in outcome or 'extra point' in desc:
        return None
    
    # Remove: Two-Point Conversions
    if 'two point' in outcome or 'two-point' in desc or 'two point' in desc:
        return None
    
    # Remove: Timeouts
    if 'timeout' in outcome:
        return None
    
    # Remove: Standalone Penalties (not part of another play)
    if 'penalty' in outcome and 'yard' not in outcome:
        return None
    
    # Remove: Throwaways (intentional incomplete passes)
    if 'threw' in desc and 'away' in desc:
        return None
    if 'throws' in desc and 'away' in desc:
        return None
    if 'intentional grounding' in desc:
        return None
    
    # Field Goals (including blocked)
    if 'field goal' in outcome or 'field goal' in desc:
        return 'Field_Goal'
    
    # Punts (including blocked)
    if 'punt' in outcome or 'punts' in desc:
        return 'Punt'
    
    # Passes - Long (deep passes, including completions, incompletions, interceptions, fumbles after catch)
    if 'pass deep' in desc or ('pass intended' in desc and 'deep' in desc):
        return 'Long_Pass'
    
    # Passes - Short (short passes, including completions, incompletions, interceptions, fumbles after catch)
    if 'pass short' in desc or ('pass intended' in desc and 'short' in desc):
        return 'Short_Pass'
    
    # Generic pass patterns (if not caught by short/deep)
    if 'pass' in desc and 'pass' in outcome:
        # Default to short pass if not specified
        return 'Short_Pass'
    
    # Incomplete passes
    if 'pass incomplete' in outcome:
        # Try to determine if it was short or deep from description
        if 'deep' in desc:
            return 'Long_Pass'
        elif 'short' in desc:
            return 'Short_Pass'
        else:
            return None  # Default to none if we cant determine if it was short or deep
    
    # Interceptions - classified by the original throw distance
    if 'intercept' in desc:
        if 'deep' in desc:
            return 'Long_Pass'
        elif 'short' in desc:
            return 'Short_Pass'
        else:
            return None  # Default to none if we cant determine if it was short or deep
    
    # Runs (including QB scrambles, RB runs, and RB fumbles)
    if 'scrambles' in desc:
        return 'Run'
    
    if 'run' in outcome or any(direction in desc for direction in ['left tackle', 'right tackle', 'left guard', 'right guard', 
                                                                     'left end', 'right end', 'up the middle', 'middle']):
        return 'Run'
    
    # Touchdowns - need to determine what type of play it was
    if 'touchdown' in outcome:
        # Check if it was a pass TD
        if 'pass' in desc:
            if 'deep' in desc:
                return 'Long_Pass'
            else:
                return 'Short_Pass'
        # Check if it was a run TD
        elif any(keyword in desc for keyword in ['left tackle', 'right tackle', 'left guard', 'right guard', 
                                                   'left end', 'right end', 'up the middle', 'scrambles']):
            return 'Run'
    
    # If we can't classify it, return None to remove it
    return None


def add_play_call_classification(df):
    """
    Apply play call classification to a dataframe and return the dataframe with new column.
    Removes rows where Play_Call is None.
    
    Parameters:
    df: pandas DataFrame with PlayDescription and PlayOutcome columns
    
    Returns:
    pandas DataFrame: DataFrame with Play_Call column added and unclassified rows removed
    """
    # Apply classification
    df['Play_Call'] = df.apply(classify_play_call, axis=1)
    
    # Remove rows that couldn't be classified
    df_clean = df[df['Play_Call'].notna()].copy()
    
    print(f"\nOriginal rows: {len(df):,}")
    print(f"Rows after classification: {len(df_clean):,}")
    print(f"Rows removed: {len(df) - len(df_clean):,} ({((len(df) - len(df_clean)) / len(df) * 100):.2f}%)")
    print(f"\nPlay Call Distribution:")
    print(df_clean['Play_Call'].value_counts())
    
    return df_clean


def process_play_file(input_path, output_path=None):
    """
    Process a new_format play CSV file and add Play_Call classification.
    
    Parameters:
    input_path: str - path to input CSV file
    output_path: str - path to save output CSV (optional, if None will just return dataframe)
    
    Returns:
    pandas DataFrame: processed dataframe with Play_Call column
    """
    print(f"\nProcessing: {input_path}")
    print("=" * 60)
    
    # Read the file
    df = pd.read_csv(input_path)
    
    # Apply classification
    df_clean = add_play_call_classification(df)
    
    # Save if output path provided
    if output_path:
        df_clean.to_csv(output_path, index=False)
        print(f"\nSaved to: {output_path}")
    
    return df_clean