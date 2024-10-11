import streamlit as st
import pandas as pd
import os
import plotly.express as px
import time
from schedule import every, repeat, run_pending
from datetime import datetime
import io


# Custom CSS to change the background color
custom_css = """
<style>
body {
    background-color: #c5c5c5; /* Replace with your desired background color */
}
</style>
"""


# Updated imports for euroleague-api
from euroleague_api.standings import Standings
from euroleague_api.player_stats import PlayerStats
from euroleague_api.team_stats import TeamStats



# Modify the get_api_data function to use the updated API calls
@st.cache_data(ttl=1800)  # 30 minutes cache
def get_api_data(season):
    # Initialize API classes
    standings_api = Standings()
    player_stats_api = PlayerStats()
    team_stats_api = TeamStats()

    # Get the latest round number
    round_number = None
    for i in range(1, 35):  # Assuming max 34 rounds
        try:
            standings = standings_api.get_standings(season=season, round_number=i)
            if standings is not None:
                round_number = i
        except Exception:
            break

    if round_number is None:
        round_number = 1  # Default to 1 if no valid round found

    # Get team standings
    team_standings_df = standings_api.get_standings(season=season, round_number=round_number)

    # Get TRADITIONAL team stats
    team_stats_df = team_stats_api.get_team_stats_single_season(
        endpoint='traditional',
        season=season,
        phase_type_code='RS',
        statistic_mode="PerGame"
    )
    # Get ADVANCED team stats
    advanced_team_stats_df = team_stats_api.get_team_stats_single_season(
        endpoint='advanced',
        season=season,
        phase_type_code='RS',
        statistic_mode="Accumulated"
    )


    # Get TRADITIONAL player stats
    player_df = player_stats_api.get_player_stats_single_season(
        endpoint='traditional',
        season=season,
        phase_type_code='RS',
        statistic_mode="PerGame"
    )

    # Get ADVANCED player stats
    advanced_player_df = player_stats_api.get_player_stats_single_season(
        endpoint='advanced',
        season=season,
        phase_type_code='RS',
        statistic_mode="Accumulated"
    )

    return team_standings_df, team_stats_df, advanced_team_stats_df, player_df, advanced_player_df, round_number

def get_team_kpis(team_totals_data, selected_team):
    # Get the KPIs for the selected team
    team_kpis = team_totals_data[team_totals_data['team.tvCodes'] == selected_team].iloc[0]

    # Create a dictionary to store the rankings for each KPI
    rankings = {}

    # Define the KPIs
    kpis = ['pointsScored', 'twoPointersPercentage', 'threePointersPercentage', 'threePointersMade',
            'offensiveRebounds', 'defensiveRebounds', 'foulsCommited', 'foulsDrawn']

    # Calculate the ranking for each KPI
    for kpi in kpis:
        # Sort the teams based on the KPI in descending order and get the index (ranking)
        ranking = team_totals_data.sort_values(by=kpi, ascending=False).index.get_loc(team_kpis.name) + 1
        # Store the ranking in the dictionary
        rankings[kpi] = ranking

    # Add the rankings as new columns to the team_kpis DataFrame
    for kpi, ranking in rankings.items():
        team_kpis[f'{kpi}_Ranking'] = ranking

    return team_kpis[['pointsScored', 'twoPointersPercentage', 'threePointersPercentage', 'threePointersMade',
                       'defensiveRebounds', 'offensiveRebounds', 'foulsCommited', 'foulsDrawn',
                      'pointsScored_Ranking', 'twoPointersPercentage_Ranking', 'threePointersPercentage_Ranking',
                      'threePointersMade_Ranking', 'offensiveRebounds_Ranking', 'defensiveRebounds_Ranking','assists','turnovers']]

def get_top_teams(team_totals_data):
    # Create a dictionary to map original KPI names to display names
    kpi_display_names = {
        'pointsScored': 'POINTS PER GAME',
        'twoPointersPercentage': 'FIELD GOALS PERCENTAGE',
        'threePointersPercentage': '3 POINTS PERCENTAGE',
        'threePointersMade': '3 POINTS MADE',
        'defensiveRebounds': 'DEFENSIVE REBOUNDS',
        'offensiveRebounds': 'OFFENSIVE REBOUNDS'
    }

    # Create a dictionary to store the top team for each metric
    top_teams = {}

    # Calculate the top team for each metric
    for kpi, display_name in kpi_display_names.items():
        # Get the top team for the current metric
        top_team_row = team_totals_data.sort_values(by=kpi, ascending=False).iloc[0]
        # Extract metric value and team name
        metric_value = top_team_row[kpi]
        team_name = top_team_row['team.tvCodes']
        # Store the metric value and team name in the dictionary
        top_teams[display_name] = (metric_value, team_name)

    return top_teams


def get_top_players(players_data, selected_team, metric, display_name, top_n=5):
    team_data = players_data[players_data['player.team.tvCodes'] == selected_team]

    # Convert the metric column to numeric
    team_data[metric] = pd.to_numeric(team_data[metric], errors='coerce')

    # Drop rows with NaN values in the metric column
    team_data = team_data.dropna(subset=[metric])

    top_players = team_data.nlargest(top_n, metric)

    # Define a mapping for the column names
    column_mapping = {'player.name': 'Player', metric: display_name}

    # Rename the columns based on the mapping
    top_players.rename(columns=column_mapping, inplace=True)

    return top_players[['Player', display_name]]

# Function to get top players based on PIR
def get_top_players_pir(players_data, selected_team, top_n=3):
    team_data = players_data[players_data['player.team.tvCodes'] == selected_team]
    top_players = team_data.nlargest(top_n, 'pir')
    return top_players[['player.name', 'pir', 'player.imageUrl','pointsScored', 'totalRebounds', 'assists', 'steals']]  # Directly use 'player.imageUrl'

# Function to get scoring distribution
def get_scoring_distribution(players_data, selected_team):
    team_data = players_data[players_data['player.team.tvCodes'] == selected_team]
    total_points = team_data['pointsScored'].sum()
    team_data['Percentage of Total Points'] = (team_data['pointsScored'] / total_points) * 100
    return team_data[['player.name', 'Percentage of Total Points']]

# Function to load team logos
def load_team_logos(folder_path):
    logos = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".png"):
            team_name = file_name.split(".")[0]
            logos[team_name] = os.path.join(folder_path, file_name)
    return logos

# Function to display team logo
def display_team_logo(team_logos, selected_team):
    if selected_team in team_logos:
        st.image(team_logos[selected_team], width=150, output_format="PNG")
    else:
        st.warning(f"Logo not found for {selected_team}")

# Define the path to the folder containing team logos
logos_folder_path = "logos"

# Load team logos
team_logos = load_team_logos(logos_folder_path)


def main():
    st.set_page_config(page_title="Euroleague Dashboard", page_icon=":basketball:", layout='wide')


    st.markdown(custom_css, unsafe_allow_html=True)

    st.title(":basketball: :orange[Euroleague Dashboard ] :basketball:")
    logo_path = "images.png"  # Replace with the actual path to your logo image

    st.caption('This is an analytics Dashboard aimed to quickly provide a general overview on some of the most important metrics for each team playing in Euroleague.')

    # Create a session state variable for the selected season
    if 'selected_season' not in st.session_state:
        st.session_state.selected_season = 2024  # Default to 2024

    # Load data based on selected season
    team_standings_df, team_totals, advanced_team_stats_df, players_data, advanced_player_df,  round_number = get_api_data(season=st.session_state.selected_season)

    pd.set_option('display.max_columns', 500)
    print(advanced_player_df.head())

    st.info(
        f'All data used for calculations are fetched from [euroleague-api](https://pypi.org/project/euroleague-api/), refreshing automatically.',
        icon="ℹ️"
    )

    # Display the last refresh time in the app with selected season
    st.success(
        f'#### **Selected Season:** {st.session_state.selected_season}    \n'
        f'#### **Latest Round:** {round_number}'
    )

    # Buttons for season selection under the info message
    col1, col2 = st.columns(2)  # Create two columns for layout

    with col1:
        if st.button('Season 2023'):
            st.session_state.selected_season = 2023  # Set selected season to 2023
            team_standings_df, team_stats_df, advanced_team_stats_df, player_df, advanced_player_df, round_number = get_api_data(
                season=st.session_state.selected_season)

    with col2:
        if st.button('Season 2024'):
            st.session_state.selected_season = 2024  # Set selected season to 2024
            team_standings_df, team_stats_df, advanced_team_stats_df, player_df, advanced_player_df, round_number = get_api_data(
                season=st.session_state.selected_season)

    # List of teams as buttons
    teams = team_standings_df['club.tvCode'].unique()

    # Add a team selection dropdown to the sidebar with custom styling
    st.markdown("<h1 style='text-align: center;'>Select Team</h1>", unsafe_allow_html=True)
    selected_team = st.selectbox("Select Team", teams, key='top_team_selectbox')

    display_team_logo(team_logos, selected_team)

    # Button to show/hide standings table
    show_standings_button = st.button("Show Standings")

    # Get the top team for each metric
    top_teams = get_top_teams(team_totals)

    # Display the top team for each metric in the same format as the existing KPIs
    st.header("Top Team for Each Metric (on Average)", divider='orange')

    top_teams_layout = st.columns(6)
    pd.set_option('display.max_columns', None)  # None means no limit


    for i, (kpi, (metric_value, team_name)) in enumerate(top_teams.items()):
        with top_teams_layout[i]:
            box_style_metric = "border: 2px solid #8B4000; padding: 15px; background-color: rgba(206,206,206, 0.0); height: 130px; width: 100%; margin: 10px auto; border-radius: 2px;"
            box_style_ranking = "border: 0px solid #ddd; padding: 15px; background-color: rgba(255,255,255, 0.0); height: 60px; width: 100%; margin: 10px auto; border-radius: 25px;"

            # Check if metric_value is a numeric type
            if isinstance(metric_value, (int, float)):
                metric_html = f"<div style='{box_style_metric}'><p style='font-size:16px;'>{kpi}</p><p style='font-size:28px;'>{metric_value:.1f}</p></div>"
            else:
                metric_html = f"<div style='{box_style_metric}'><p style='font-size:16px;'>{kpi}</p><p style='font-size:28px;'>{metric_value}</p></div>"

            ranking_html = f"<div style='{box_style_ranking}'><p style='font-size:16px;'>RANKING :1 ({team_standings_df['club.abbreviatedName'].iloc[team_standings_df[team_standings_df['club.tvCode'] == team_name].index[0]]})</p></div>"

            st.markdown(metric_html, unsafe_allow_html=True)
            st.markdown(ranking_html, unsafe_allow_html=True)

    # Check if the button is clicked and show the standings table in the sidebar
    if show_standings_button:
        st.sidebar.table(team_standings_df[['position', 'club.abbreviatedName', 'gamesPlayed','gamesWon','gamesLost']].rename(
            columns={'position': 'Position', 'club.editorialName': 'Team', 'gamesPlayed': 'Games', 'gamesWon': 'Won', 'gamesLost': 'Lost'}
        ).set_index('Position', drop=True))

    # Display KPIs for the selected team
    st.header(f"Team Stats for {selected_team} (on Average)", divider='orange')

    # Get KPIs for the selected team
    team_kpis = get_team_kpis(team_totals, selected_team)

    # Display KPIs in a row with st.success
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    box_style = "border: 1px solid #32612D; padding: 15px; background-color: rgba(206,206,206, 0.3); height: 130px; width: 100%; margin: 0px auto; border-radius: 7px;"
    box_style6 = "border: 0px solid #ddd; padding: 15px; background-color: rgba(255,255,255, 0.3); height: 60px; width: 100%; margin: 10px auto; border-radius: 25px;"

    selected_team_data = team_standings_df[team_standings_df['club.tvCode'] == selected_team]

    # Calculate the average for 'pointsFor' and 'pointsAgainst'
    #avg_points_for = selected_team_data['pointsFor'].sum() / selected_team_data['gamesPlayed'].sum()

    with col1:

        points_per_game_html = f"<div style='{box_style}'><p style='font-size:16px;'>POINTS PER GAME</p><p style='font-size:28px;'>{team_kpis['pointsScored']:.1f}</p></div>"
        points_per_game_ranking_html = f"<div style='{box_style6}'><p style='font-size:16px;'>RANKING : {team_kpis['pointsScored_Ranking']:}</p></div>"

        st.markdown(points_per_game_html, unsafe_allow_html=True)
        st.markdown(points_per_game_ranking_html, unsafe_allow_html=True)

    with col2:
        # Extract the numeric part of the string and convert to float
        two_pointers_percentage_str = team_kpis['twoPointersPercentage']
        numeric_percentage = float(two_pointers_percentage_str.rstrip('%'))

        field_goals_percentage_html = f"<div style='{box_style}'><p style='font-size:16px;'>FIELD GOALS PERCENTAGE</p><p style='font-size:28px;'>{numeric_percentage:.1f}%</p></div>"
        twoPointersPercentage_Ranking_html = f"<div style='{box_style6}'><p style='font-size:16px;'>RANKING : {team_kpis['twoPointersPercentage_Ranking']:}</p></div>"
        st.markdown(field_goals_percentage_html, unsafe_allow_html=True)
        st.markdown(twoPointersPercentage_Ranking_html, unsafe_allow_html=True)

    with col3:
        three_pointers_percentage_str = team_kpis['threePointersPercentage']
        numeric_three_pointers_percentage = float(three_pointers_percentage_str.rstrip('%'))

        three_pointers_percentage_html = f"<div style='{box_style}'><p style='font-size:16px;'>3 POINTS PERCENTAGE</p><p style='font-size:28px;'>{numeric_three_pointers_percentage:.1f}%</p></div>"
        threePointersPercentage_Ranking_html = f"<div style='{box_style6}'><p style='font-size:16px;'>RANKING : {team_kpis['threePointersPercentage_Ranking']:}</p></div>"
        st.markdown(three_pointers_percentage_html, unsafe_allow_html=True)
        st.markdown(threePointersPercentage_Ranking_html, unsafe_allow_html=True)

    with col4:
        threePointersMade_html = f"<div style='{box_style}'><p style='font-size:16px;'>3 POINTS MADE</p><p style='font-size:28px;'>{team_kpis['threePointersMade']:.1f}</p></div>"
        threePointersMadeRanking_html = f"<div style='{box_style6}'><p style='font-size:16px;'>RANKING : {team_kpis['threePointersMade_Ranking']:}</p></div>"

        st.markdown(threePointersMade_html, unsafe_allow_html=True)
        st.markdown(threePointersMadeRanking_html, unsafe_allow_html=True)

    with col5:
        defensiveRebounds_html = f"<div style='{box_style}'><p style='font-size:16px;'>DEFENSIVE REBOUNDS</p><p style='font-size:28px;'>{team_kpis['defensiveRebounds']:.1f}</p></div>"
        defensiveReboundsRanking_html = f"<div style='{box_style6}'><p style='font-size:16px;'>RANKING : {team_kpis['defensiveRebounds_Ranking']:}</p></div>"

        st.markdown(defensiveRebounds_html, unsafe_allow_html=True)
        st.markdown(defensiveReboundsRanking_html, unsafe_allow_html=True)

    with col6:
        offensiveRebounds_html = f"<div style='{box_style}'><p style='font-size:16px;'>OFFENSIVE REBOUNDS</p><p style='font-size:28px;'>{team_kpis['offensiveRebounds']:.1f}</p></div>"
        offensiveReboundsRanking_html = f"<div style='{box_style6}'><p style='font-size:16px;'>RANKING : {team_kpis['offensiveRebounds_Ranking']:}</p></div>"

        st.markdown(offensiveRebounds_html, unsafe_allow_html=True)
        st.markdown(offensiveReboundsRanking_html, unsafe_allow_html=True)

    # Display KPIs for the opponent team vs selected team
    st.header(f"Form for {selected_team}", divider='orange')

    # Display KPIs in a row with st.success
    col7, col8, col9, col10 = st.columns(4)

    box_style2 = "border: 1px solid #ddd; padding: 15px; background-color: rgba(255,255,255,0.1); height: 130px; width: 80%; margin: 10px auto; border-radius: 7px;"
    box_style3 = "border: 2px solid #32612D; padding: 15px; background-color: rgba(206,206,206, 0.3); height: 130px; width: 100%; margin: 10px auto; border-radius: 7px;"
    box_style4 = "border: 2px solid #FF0000; padding: 15px; background-color: rgba(206,206,206, 0.3); height: 130px; width: 100%; margin: 10px auto; border-radius: 7px;"
    box_style5 = "border: 1px solid #ddd; padding: 15px; background-color: rgba(255,255,255,0.1); height: 180px; width: 80%; margin: 10px auto; border-radius: 7px;"

    with col7:
        selected_team_games_won = \
        pd.to_numeric(team_standings_df.loc[team_standings_df['club.tvCode'] == selected_team, 'gamesWon'],
                      errors='coerce').dropna().iloc[0]
        selected_team_games_lost = \
        pd.to_numeric(team_standings_df.loc[team_standings_df['club.tvCode'] == selected_team, 'gamesLost'],
                      errors='coerce').dropna().iloc[0]

        st.markdown(
            f"<div style='{box_style3}'><p style='font-size:18px;'>GAMES WON</p><p style='font-size:40px;'>{int(selected_team_games_won)}</p></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='{box_style4}'><p style='font-size:18px;'>GAMES LOST</p><p style='font-size:40px;'>{int(selected_team_games_lost)}</p></div>",
            unsafe_allow_html=True
        )

    with col8:
        home_record_html = f"<div style='{box_style2}'><p style='font-size:18px;'>HOME RECORD</p><p style='font-size:30px;'>{team_standings_df.loc[team_standings_df['club.tvCode'] == selected_team, 'homeRecord'].iloc[0]}</p></div>"
        away_record_html = f"<div style='{box_style2}'><p style='font-size:18px;'>AWAY RECORD</p><p style='font-size:30px;'>{team_standings_df.loc[team_standings_df['club.tvCode'] == selected_team, 'awayRecord'].iloc[0]}</p></div>"

        st.markdown(home_record_html, unsafe_allow_html=True)
        st.markdown(away_record_html, unsafe_allow_html=True)

    with col9:
        selected_team_last_5_form = \
        team_standings_df.loc[team_standings_df['club.tvCode'] == selected_team, 'last5Form'].values[0]
        # Remove single quotes, square brackets from the string
        selected_team_last_5_form = str(selected_team_last_5_form).replace("'", "").replace("[", "").replace("]", "")

        st.markdown(
            f"<div style='{box_style5}'><p style='font-size:18px;'>LAST FIVE GAME (W - L)</p><p style='font-size:30px;'>{selected_team_last_5_form}</p></div>",
            unsafe_allow_html=True
        )

    # 4th column with a bar chart
    with col10:

        # Calculate the ratio
        if team_kpis['turnovers'] != 0:
            ratio_value = team_kpis['assists'] / team_kpis['turnovers']
        else:
            ratio_value = 0  # or any other suitable value

        # Combine AVG assists, AVG turnovers, and RATIO in the same box with RATIO on the next line
        combined_html = f"<div style='{box_style5}'><p style='font-size:18px;'>AVG ASSISTS / AVG TURNOVERS</p><p style='font-size:30px;'>{team_kpis['assists']:.1f} / {team_kpis['turnovers']:.1f}</p><p style='font-size:16px;'>RATIO (higher = better): {ratio_value:.2f}</p></div>"

        # Display the combined box
        st.markdown(combined_html, unsafe_allow_html=True)



    # Add a row with three columns to show top players based on PIR
    st.header(f"Top 3 Players Based on PIR (Performance Index Rating) for {selected_team}", divider='orange')

    # Create a 1x3 grid layout for top players
    top_players_layout = st.columns(3)

    # Get top players based on PIR
    top_pir_players = get_top_players_pir(players_data, selected_team)

    # Display top players in each column
    for i, (col, player_info) in enumerate(zip(top_players_layout, top_pir_players.iterrows())):
        col.subheader(f"#{i + 1} {player_info[1]['player.name']}")

        # Create a box with player image, PIR, and additional statistics
        with col:
            st.image(player_info[1]['player.imageUrl'],
                     width=130)  # Display player image with a maximum width of 100 pixels

            # Display PIR value with font size 20 and bold
            st.markdown(f"<p style='font-size: 22px;'><strong>PIR: {player_info[1]['pir']:.2f}</strong></p>",
                        unsafe_allow_html=True)

            # Convert percentage string to numeric for formatting
            avg_points = float(player_info[1]['pointsScored'])
            avg_rebounds = float(player_info[1]['totalRebounds'])
            avg_assists = float(player_info[1]['assists'])

            # Calculate total of average points, rebounds, and assists
            total_avg = avg_points + avg_rebounds + avg_assists

            # Display additional statistics with font size 15
            st.markdown(f"Avg Points: {avg_points:.2f}", unsafe_allow_html=True)
            st.markdown(f"Avg Rebounds: {avg_rebounds:.2f}", unsafe_allow_html=True)
            st.markdown(f"Avg Assists: {avg_assists:.2f}", unsafe_allow_html=True)
            # Display total of average points, rebounds, and assists
            st.markdown(f"**Total Pts/Rebs/Asts: {total_avg:.2f}**", unsafe_allow_html=True)

            st.divider()


# Display top players tables
    st.header("Top 5 Players Categorized by :", divider='orange')

    # Create a 2x2 grid layout for top players
    top_players_layout = st.columns(2)

    # Top 5 players in PPG
    with top_players_layout[0]:
        st.subheader("Points per game:")
        top_ppg_players = get_top_players(players_data, selected_team, 'pointsScored', 'Points')
        st.table(top_ppg_players.style.format({'Points': '{:.2f}'}))

    # Top 5 players in RPG
    with top_players_layout[1]:
        st.subheader("Rebounds per game:")
        top_rpg_players = get_top_players(players_data, selected_team, 'totalRebounds', 'Rebounds')
        st.table(top_rpg_players.style.format({'Rebounds': '{:.2f}'}))

    # Top 5 players in APG
    with top_players_layout[0]:
        st.subheader("Assists per game:")
        top_apg_players = get_top_players(players_data, selected_team, 'assists', 'Assists')
        st.table(top_apg_players.style.format({'Assists': '{:.2f}'}))

    # Top 5 players in SPG
    with top_players_layout[1]:
        st.subheader("Steals per game:")
        top_spg_players = get_top_players(players_data, selected_team, 'steals', 'Steals')
        st.table(top_spg_players.style.format({'Steals': '{:.2f}'}))


    # Add a team selection dropdown to the sidebar with custom styling
    st.markdown("<h1 style='text-align: center;'>Select Team for Charts</h1>", unsafe_allow_html=True)
    selected_team = st.selectbox("Select Team for Charts", teams,
                                           key='chart_team_selectbox')  # Unique key added here

    # Display charts for the selected team
    st.header(f"Charts for {selected_team}", divider='orange')

    # Get scoring distribution for selected team from team totals
    scoring_distribution_team_totals = get_scoring_distribution(players_data, selected_team)

    # Create a Plotly bar chart
    fig = px.bar(
        scoring_distribution_team_totals,
        x='player.name',
        y='Percentage of Total Points',
        title=f'Scoring Distribution for Team: {selected_team}',
        labels={'player.name': 'Player', 'Percentage of Total Points': 'Percentage of Total Points'},
        color_discrete_sequence=['#32612D']
    )


    # Update layout
    fig.update_layout(
        xaxis_title='',  # Hide x-axis title
        showlegend=False,  # Hide legend
        xaxis_tickangle=-45,  # Rotate x-axis labels for better readability
        plot_bgcolor='#fbf7f5',  # Set background color
        height=400,  # Set a maximum height
    )

    fig.update_traces(textposition='outside', width=0.5)

    # Display the Plotly figure in Streamlit
    st.plotly_chart(fig, use_container_width=True)  # Responsive chart



    # Filter the DataFrame for the selected team
    selected_team_data = team_standings_df[team_standings_df['club.tvCode'] == selected_team]
    selected_team_data_advanced = advanced_team_stats_df[advanced_team_stats_df['team.tvCodes'] == selected_team]
    selected_team_data_players = advanced_player_df[advanced_player_df['player.team.tvCodes'] == selected_team]

    st.divider()

    # Calculate the average for 'pointsFor' and 'pointsAgainst'
    avg_points_for = team_kpis['pointsScored']
    avg_points_against = selected_team_data['pointsAgainst'].sum() / selected_team_data['gamesPlayed'].sum()

    # Combine the average points for and against into a DataFrame
    avg_data = pd.DataFrame({
        'Metric': ['Average Points Scored', 'Average Points Conceded'],
        'Value': [avg_points_for, avg_points_against]
    })

    # Set colors for the bars
    colors = ['#32612D', '#FF0000']

    fig2 = px.bar(
        avg_data,
        x='Metric',
        y='Value',
        title=f'Average Points SCORED vs CONCEDED for Team: {selected_team}',
        color='Metric',
        color_discrete_sequence=colors,
        labels={'Metric': 'Metrics', 'Value': 'Average Points'},  # Added label for Metric
        text='Value'  # Display the average points as text on the bars
    )

    # Update layout to customize appearance
    fig2.update_layout(
        xaxis_title='',  # Hide x-axis title
        yaxis_title='Average Points',  # Y-axis title
        plot_bgcolor='#fbf7f5',  # Set background color
        height=500,  # Increase height for more space (adjust as needed)
        showlegend=False,  # Hide legend
        margin=dict(t=60, b=20, l=40, r=20)  # Add margin to the plot
    )

    # Update the text position above the bars
    fig2.update_traces(
        textposition='outside',  # Position text above bars
        width=0.2,
        textfont_size=16,
        textfont_color='#232b2b'  # Set text color to black
    )

    # Customize text appearance
    fig2.update_traces(textfont_size=16)  # Set font size

    # Display the Plotly figure in Streamlit
    st.plotly_chart(fig2, use_container_width=True)  # Responsive chart

    st.divider()

    euroleague_colors = ['#6BAF85', '#E7A86D', '#7A6A9D']

    # Extract the percentages for two-pointers, three-pointers, and free throws
    points_from_two = selected_team_data_advanced['pointsFromTwoPointersPercentage'].values[0].strip('%')
    points_from_three = selected_team_data_advanced['pointsFromThreePointersPercentage'].values[0].strip('%')
    points_from_free = selected_team_data_advanced['pointsFromFreeThrowsPercentage'].values[0].strip('%')

    # Convert the string values to float
    points_from_two = float(points_from_two)
    points_from_three = float(points_from_three)
    points_from_free = float(points_from_free)

    # Create a donut chart using the actual values from the data
    fig3 = px.pie(
        names=['Two-Pointers', 'Three-Pointers', 'Free Throws'],
        values=[points_from_two, points_from_three, points_from_free],
        title=f'Shot Distribution for {selected_team}',
        color_discrete_sequence=euroleague_colors,
        hole=0.5  # Set the hole size for the donut chart
    )

    # Update traces for text properties
    fig3.update_traces(
        textfont_size=14,  # Set text size to 16
        textfont_color='#232b2b',  # Set text color to #232b2b
        textinfo='percent+label'  # Display percentage and label
    )

    # Hide the legend if not needed
    fig3.update_layout(showlegend=False)

    # Display the donut chart in Streamlit
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # Assuming 'selected_team' contains the selected team's TV code (e.g., 'EA7', 'PAO', etc.)
    selected_team_data_players = advanced_player_df[advanced_player_df['player.team.tvCodes'] == selected_team]

    # Convert necessary columns to numeric after stripping '%'
    selected_team_data_players['threePointAttemptsRatio'] = selected_team_data_players[
        'threePointAttemptsRatio'].str.strip('%').astype(float)
    selected_team_data_players['twoPointAttemptsRatio'] = selected_team_data_players['twoPointAttemptsRatio'].str.strip(
        '%').astype(float)
    selected_team_data_players['freeThrowsRate'] = selected_team_data_players['freeThrowsRate'].str.strip('%').astype(
        float)

    # Sort by highest three-point, two-point, and free-throw made rates
    top_3pm_players = selected_team_data_players.sort_values(by='threePointAttemptsRatio', ascending=False).head(7)
    top_2pm_players = selected_team_data_players.sort_values(by='twoPointAttemptsRatio', ascending=False).head(7)
    top_ftm_players = selected_team_data_players.sort_values(by='freeThrowsRate', ascending=False).head(7)

    # Define custom color palettes
    three_point_colors = ['#4C7A5C', '#6BAF85', '#A2D3A4']  # Custom colors for Top 3-Point Makers
    two_point_colors = ['#D68A3D', '#E7A86D', '#F0B89C']  # Custom colors for Top 2-Point Makers
    free_throw_colors = ['#6A5ACD', '#7A6A9D', '#BFA5D8']  # Custom colors for Top Free-Throw Makers

    # Create Pie Chart for Three-Point Makes (3PM)
    fig_3pm = px.pie(
        top_3pm_players,
        names='player.name',
        values='threePointAttemptsRatio',
        title='Top 3-Point Makers (%)',
        color_discrete_sequence=three_point_colors
    )
    fig_3pm.update_traces(
        textinfo='value+label',
        textfont_size=10,  # Make label text smaller
        textfont_color='#232b2b'
    )
    fig_3pm.update_layout(
        showlegend=False,  # Remove legend
        paper_bgcolor='#D3D3D3',  # Set a light background color for the entire figure
        plot_bgcolor='#D3D3D3',  # Set the same or a slightly different color for the plotting area
        title_font = dict(color='#232b2b')
    )

    # Create Pie Chart for Two-Point Makes (2PM)
    fig_2pm = px.pie(
        top_2pm_players,
        names='player.name',
        values='twoPointAttemptsRatio',
        title='Top 2-Point Makers (%)',
        color_discrete_sequence=two_point_colors
    )
    fig_2pm.update_traces(
        textinfo='value+label',
        textfont_size=10,  # Make label text smaller
        textfont_color='#232b2b'
    )
    fig_2pm.update_layout(
        showlegend=False,  # Remove legend
        paper_bgcolor='#D3D3D3',  # Set a light background color for the entire figure
        plot_bgcolor='#D3D3D3',  # Set the same or a slightly different color for the plotting area
        title_font = dict(color='#232b2b')
    )

    # Create Pie Chart for Free Throws Made (FTM)
    fig_ftm = px.pie(
        top_ftm_players,
        names='player.name',
        values='freeThrowsRate',
        title='Top Free-Throw Makers (%)',
        color_discrete_sequence=free_throw_colors
    )
    fig_ftm.update_traces(
        textinfo='value+label',
        textfont_size=10,  # Make label text smaller
        textfont_color='#232b2b'
    )
    fig_ftm.update_layout(
        showlegend=False,  # Remove legend
        paper_bgcolor='#D3D3D3',  # Set a light background color for the entire figure
        plot_bgcolor='#D3D3D3',  # Set the same or a slightly different color for the plotting area
        title_font = dict(color='#232b2b')
    )

    # Use Streamlit columns to display the charts side by side
    col1, col2, col3 = st.columns(3)

    # Display each pie chart in its respective column
    with col1:
        st.plotly_chart(fig_3pm, use_container_width=True)

    with col2:
        st.plotly_chart(fig_2pm, use_container_width=True)

    with col3:
        st.plotly_chart(fig_ftm, use_container_width=True)


    # Add a "Made by" section at the bottom
    st.markdown("---")
    made_by_text = "Made by: [Athanasios Kouras](https://www.linkedin.com/in/athanasios-kouras-276b17214/)"
    st.markdown(made_by_text, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
