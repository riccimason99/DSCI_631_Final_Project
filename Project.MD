# DSCI ML FINAL PROJECT
Mason Ricci 
Mary 


## Description: 
For this project we attempt to predict what offensive play will be attempted by an NFL team during the regular season.

## Data; 
Our data source is https://www.kaggle.com/datasets/keonim/nfl-game-scores-dataset-2017-2023 
We use regular season NFL games from 2017-2025.


### **Target Variables**:
- This target variable called PlayAttempt and signifies what offensive play the team attempted during that play. It created by parsing the fields "Description" and "PlayOutcome" which are strings. Each play is either removed or classified as on of the following: run (by QB or Running Back), short_pass (less than ??? yards), long_pass (greater than or equal to ??? yards), field goal attempt, punt or a spike.

- If the ball was fumbled during a run the play is classified as a run 
- If the ball is fumbled by a reciver after a catch it is considered a long_pass or short_pass depending on where the cath was made
- If the ball was intercepted the play is classified as a short_pass or long_pass depending on where the interception was made.  
- We removed all sacs, fields goals, kickoffs or abnornal cases, we also removed QB fumbles as it would be impossible to determing if the play would reslt in or what the origina call was. Penelty plays and time outs are also removed


### **Features** 

- **Down**: 

- **YdsTo1stDown**: 

- **YdsToEndzone**: 

- **team_run_pct**: The likleyhood of a team running compared to long or short pass

- **team_short_pass_pct**: The likleyhood of a team attempting a short pass compared to a run or long pass

- **team_long_pass_pct**: The likleyhood of a team attempting a long pass compared to a run or short pass

**Calculation Methods for pct features:**

These three features represent a team's offensive play-calling tendencies, calculated as percentages of total offensive plays (Run + Short_Pass + Long_Pass). Special teams plays (punts, field goals) are excluded from the calculation as well as spikes.

To prevent data leakage, each game's tendency values are calculated using **only previous games**:

1. **For the first 3 games of a season**: Uses the team's complete data from the previous season (e.g., 2023 Week 1-3 uses all 2022 games for that team). This provides a realistic baseline of the team's established play-calling philosophy.

2. **For game 4 and beyond**: Uses a rolling window of all previous games from the current season (e.g., Week 5 uses Weeks 1-4 data from that team). This captures how the team's strategy evolves throughout the season.

3. **For 2017 (first season in dataset)**: Uses the **league-wide average** from all seasons (44.37% run, 50.78% short pass, 4.84% long pass) since is no previous season data available.

This approach ensures that no information from the current game or future games is used in predicting that game's play call, maintaining temporal integrity and preventing look-ahead bias. All plays within a single game receive the same tendency values, as those values are determined before the game begins. 