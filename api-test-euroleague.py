import pandas as pd
from euroleague_api.standings import get_standings
from euroleague_api.player_stats import get_player_stats_single_season
from euroleague_api.team_stats import get_team_stats_single_season

pd.set_option('display.max_columns', None)


#Team Standings
season=2023
round_number=15
endpoint='basicstandings'

team_standings_df = get_standings(season, round_number+1, endpoint)



#print(team_standings_df.head())

#Team Stats
endpoint = "traditional"
phase_type_code = None  # Provide a value for phase_type_code
statistic_mode = "PerGame"  # Provide a value for statistic_mode
team_stats_df = get_team_stats_single_season(endpoint, season, phase_type_code, statistic_mode)

#print("this is a:", team_stats_df.head())

#Player Stats
endpoint = "traditional"
phase_type_code = None  # Provide a value for phase_type_code
statistic_mode = "PerGame"  # Provide a value for statistic_mode
player_df = get_player_stats_single_season(endpoint, season, phase_type_code, statistic_mode)

# Display the resulting DataFrame
#print("this is a:", player_df.head())


# Save DataFrames to Excel files
team_standings_df.to_excel('team_standings.xlsx', index=False, sheet_name='TeamData')
team_stats_df.to_excel('team_stats.xlsx', index=False, sheet_name='TeamData')
player_df.to_excel('player_stats.xlsx', index=False, sheet_name='PlayerData')
