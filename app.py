import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
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


# Additional imports for API calls
from euroleague_api import standings
from euroleague_api import get_player_stats_single_season
from euroleague_api import get_team_stats_single_season



# Function to get data from the API
@st.cache_data(ttl=1800)  # 86400 seconds = 1 day
def get_api_data(season, round_number):
    total = 35
    endpoint_standings = 'basicstandings'
    try:
        for i in range(1,total):
            standings(season, i, endpoint_standings)
    except:
        check=i-1

    round_number=check
    # Team Standings

    team_standings_df = standings(season, round_number, endpoint_standings)

    # Team Stats
    endpoint_team_stats = "traditional"
    phase_type_code = None
    statistic_mode = "PerGame"
    team_stats_df = get_team_stats_single_season(endpoint_team_stats, season, phase_type_code, statistic_mode)

    # Player Stats
    endpoint_player_stats = "traditional"
    phase_type_code = None
    statistic_mode = "PerGame"
    player_df = get_player_stats_single_season(endpoint_player_stats, season, phase_type_code, statistic_mode)

    return team_standings_df, team_stats_df, player_df, round_number

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
        st.sidebar.image(team_logos[selected_team], use_column_width=True, output_format="PNG")
    else:
        st.sidebar.warning(f"Logo not found for {selected_team}")

# Define the path to the folder containing team logos
logos_folder_path = "logos"

# Load team logos
team_logos = load_team_logos(logos_folder_path)


def main():


    st.set_page_config(page_title="Euroleague Dashboard", page_icon =":basketball:", layout='wide')

    # Apply the custom CSS
    st.markdown(custom_css, unsafe_allow_html=True)

    st.title(":basketball: :orange[Euroleague Dashboard ] :basketball:")
    logo_path = "images.png"  # Replace with the actual path to your logo image




    st.caption('This is an analytics Dashboard aimed to quickly provide a general knowledge on some of the most important metrics for each team playing in Euroleague.')

    # Load data from api
    team_standings_df, team_totals, players_data, round_number = get_api_data(season=2023,round_number=1)

    # Display the last refresh time in the Streamlit app
    st.info(
        f'All data used for calculations are fetched from [euroleague-api](https://pypi.org/project/euroleague-api/), refreshing automatically. Latest Round : '+str(round_number),
        icon="ℹ️")

    #team_standings_df, team_totals_data, opponent_totals_data = load_data()




    # List of teams as buttons
    teams = team_standings_df['club.tvCode'].unique()


    # Add a team selection dropdown to the sidebar with custom styling
    st.sidebar.markdown("<h2 style='text-align: center;'>Select Team</h3>", unsafe_allow_html=True)
    selected_team = st.sidebar.selectbox("", teams)

    # Display team logo in the sidebar
    display_team_logo(team_logos, selected_team)


    # Button to show/hide standings table
    show_standings_button = st.sidebar.button("Show Standings")

    # Get the top team for each metric
    top_teams = get_top_teams(team_totals)

    # Display the top team for each metric in the same format as the existing KPIs
    st.header("Top Team for Each Metric (on Average)", divider='orange')

    top_teams_layout = st.columns(6)

    for i, (kpi, (metric_value, team_name)) in enumerate(top_teams.items()):
        with top_teams_layout[i]:
            box_style_metric = "border: 2px solid #8B4000; padding: 15px; background-color: rgba(206,206,206, 0.0); height: 130px; width: 100%; margin: 10px auto; border-radius: 2px;"
            box_style_ranking = "border: 0px solid #ddd; padding: 15px; background-color: rgba(255,255,255, 0.0); height: 60px; width: 100%; margin: 10px auto; border-radius: 25px;"

            # Check if metric_value is a numeric type
            if isinstance(metric_value, (int, float)):
                metric_html = f"<div style='{box_style_metric}'><p style='font-size:16px;'>{kpi}</p><p style='font-size:28px;'>{metric_value:.1f}</p></div>"
            else:
                metric_html = f"<div style='{box_style_metric}'><p style='font-size:16px;'>{kpi}</p><p style='font-size:28px;'>{metric_value}</p></div>"

            ranking_html = f"<div style='{box_style_ranking}'><p style='font-size:16px;'>RANKING :1 ({team_standings_df['club.editorialName'].iloc[team_standings_df[team_standings_df['club.tvCode'] == team_name].index[0]]})</p></div>"

            st.markdown(metric_html, unsafe_allow_html=True)
            st.markdown(ranking_html, unsafe_allow_html=True)

    # Check if the button is clicked and show the standings table in the sidebar
    if show_standings_button:
        st.sidebar.table(team_standings_df[['position', 'club.editorialName', 'gamesPlayed','gamesWon','gamesLost']].rename(
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

    # Display charts for the selected team
    st.header(f"Charts for {selected_team} ", divider='orange')
    # Get scoring distribution for selected team from team totals
    scoring_distribution_team_totals = get_scoring_distribution(players_data, selected_team)

    # Set the maximum width and height for both charts
    max_width = 800
    max_height = 400

    # Create a vertical bar plot using Seaborn for team totals
    plt.figure(figsize=(min(max_width / 80, len(scoring_distribution_team_totals)), min(max_height / 6, 6)))
    sns.barplot(x='player.name', y='Percentage of Total Points', data=scoring_distribution_team_totals,
                palette='viridis')
    plt.xlabel('')
    plt.ylabel('Percentage of Total Points')
    plt.title(f'Scoring Distribution for Team: {selected_team}')
    plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability

    # Ensure tight layout
    plt.tight_layout()

    # Access the Matplotlib figure
    fig1 = plt.gcf()

    # Set the background color
    fig1.patch.set_facecolor('#F0F0F0')  # Replace with your desired color

    # Save the Matplotlib figure to a BytesIO object
    img_buf1 = io.BytesIO()
    fig1.savefig(img_buf1, format='png')
    img_buf1.seek(0)

    # Display the image with limited width using st.image
    st.image(img_buf1, width=max_width)



    # Filter the DataFrame for the selected team
    selected_team_data = team_standings_df[team_standings_df['club.tvCode'] == selected_team]

    st.divider()

    # Calculate the average for 'pointsFor' and 'pointsAgainst'
    avg_points_for = team_kpis['pointsScored']
    avg_points_against = selected_team_data['pointsAgainst'].sum() / selected_team_data['gamesPlayed'].sum()

    # Combine the average points for and against into a DataFrame
    avg_data = pd.DataFrame({
        'Metric': ['Average Points Scored', 'Average Points Conceded'],
        'Value': [avg_points_for, avg_points_against]
    })

    # Set a color palette for the bars
    colors = ['#32612D', '#FF0000']

    # Adjust the width of the bars (e.g., 0.8 for 80% of the available space)
    bar_width = 0.4

    # Create a vertical bar plot
    plt.figure(figsize=(min(max_width / 80, len(scoring_distribution_team_totals)), min(max_height / 6, 6)))
    sns.barplot(x='Metric', y='Value', data=avg_data, palette=colors, width=bar_width)

    # Add labels to each bar
    for i, value in enumerate(avg_data['Value']):
        plt.text(i, value + 0.1, f'{value:.1f}', ha='center', va='bottom')

    plt.xlabel(' ')
    plt.ylabel('Average Points')
    plt.title(f'Averages Points SCORED vs CONCEDED for Team: {selected_team}')

    # Display the plot
    plt.show()

    # Ensure tight layout
    plt.tight_layout()

    # Access the Matplotlib figure
    fig2 = plt.gcf()

    # Set the background color
    fig2.patch.set_facecolor('#F0F0F0')  # Replace with your desired color

    # Save the Matplotlib figure to a BytesIO object
    img_buf2 = io.BytesIO()
    fig2.savefig(img_buf2, format='png')
    img_buf2.seek(0)

    # Display the image with limited width using st.image
    st.image(img_buf2, width=max_width)



    # Add a "Made by" section at the bottom
    st.markdown("---")
    made_by_text = "Made by: [Athanasios Kouras](https://www.linkedin.com/in/athanasios-kouras-276b17214/)"
    st.markdown(made_by_text, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
