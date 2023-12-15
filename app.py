import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Custom CSS to change the background color
custom_css = """
<style>
body {
    background-color: #c5c5c5; /* Replace with your desired background color */
}
</style>
"""


def load_data():
    file_path = "eurol.xlsx"  # Replace with your actual file name
    data = pd.read_excel(file_path)

    team_totals_file_path = "team-totals.xlsx"
    team_totals_data = pd.read_excel(team_totals_file_path)

    opponent_totals_file_path = "opponent-team-totals.xlsx"
    opponent_totals_data = pd.read_excel(opponent_totals_file_path)

    return data, team_totals_data, opponent_totals_data


def get_team_kpis(team_totals_data, selected_team):
    team_kpis = team_totals_data[team_totals_data['Team'] == selected_team].iloc[0]
    return team_kpis[['PPG', 'FG%', '3P%', '3PM', 'ORB', 'DRB']]


def get_top_players(data, selected_team, metric, top_n=5):
    team_data = data[data['Team'] == selected_team]
    top_players = team_data.nlargest(top_n, metric)
    return top_players[['Player', metric]]

# Function to get scoring distribution
def get_scoring_distribution(data, selected_team):
    team_data = data[data['Team'] == selected_team]
    total_points = team_data['PPG'].sum()
    team_data['Percentage of Total Points'] = (team_data['PPG'] / total_points) * 100
    return team_data[['Player', 'Percentage of Total Points']]

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


    st.set_page_config(page_title="Euroleague Dashboard", page_icon =":basketball:")



    # Apply the custom CSS
    st.markdown(custom_css, unsafe_allow_html=True)

    st.title(":basketball: :orange[Euroleague Dashboard ] :basketball:")
    logo_path = "images.png"  # Replace with the actual path to your logo image
    #st.image(logo_path, width=200,)

    st.caption('This is an analytics Dashboard aimed to quickly provide a general knowledge & analytics view on some of the most important metrics for each team playing in Euroleague.')


    # Load data from Excel files
    df, team_totals, opponent_totals = load_data()

    # List of teams as buttons
    teams = df['Team'].unique()


    # Add a team selection dropdown to the sidebar with custom styling
    st.sidebar.markdown("<h2 style='text-align: center;'>Select Team</h3>", unsafe_allow_html=True)
    selected_team = st.sidebar.selectbox("", teams)

    # Display team logo in the sidebar
    display_team_logo(team_logos, selected_team)

    # Display KPIs for the selected team
    st.header(f"Team Stats for {selected_team}", divider='orange')

    # Get KPIs for the selected team
    team_kpis = get_team_kpis(team_totals, selected_team)

    # Display KPIs in a row with st.success
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    box_style = "border: 0px solid #ddd; padding: 15px; background-color: rgba(1, 32, 32, 0.4); height: 130px; margin: 0px 5px 5px 0px; border-radius: 7px;"

    with col1:
        st.markdown(
            f"<div style='{box_style}'><p style='font-size:12px;'>POINTS PER GAME</p><p style='font-size:24px;'>{team_kpis['PPG']:.1f}</p></div>",
            unsafe_allow_html=True)


    with col2:
        st.markdown(
            f"<div style='{box_style}'><p style='font-size:12px;'>FIELD GOALS PERCENTAGE</p><p style='font-size:24px;'>{team_kpis['FG%']*100:.1f}%</p></div>",
            unsafe_allow_html=True)

    with col3:
        st.markdown(
            f"<div style='{box_style}'><p style='font-size:12px;'>3 POINTS PERCENTAGE</p><p style='font-size:24px;'>{team_kpis['3P%']*100:.1f}%</p></div>",
            unsafe_allow_html=True)

    with col4:
        st.markdown(
            f"<div style='{box_style}'><p style='font-size:12px;'>3 POINTS MADE</p><p style='font-size:24px;'>{team_kpis['3PM']:.1f}</p></div>",
            unsafe_allow_html=True)

    with col5:
        st.markdown(
            f"<div style='{box_style}'><p style='font-size:12px;'>DEFENSIVE REBOUNDS</p><p style='font-size:24px;'>{team_kpis['DRB']:.2f}</p></div>",
            unsafe_allow_html=True)

    with col6:
        st.markdown(
            f"<div style='{box_style}'><p style='font-size:12px;'>OFFENSIVE REBOUNDS</p><p style='font-size:24px;'>{team_kpis['ORB']:.2f}</p></div>",
            unsafe_allow_html=True)

    # Display KPIs for the opponent team vs selected team
    st.header(f"Team Stats opponent teams vs  {selected_team}", divider='orange')

    # Display KPIs for the selected team from opponent-team-totals
    opponent_kpis = get_team_kpis(opponent_totals, selected_team)

    # Display KPIs in a row with st.success for opponent-team-totals
    col7, col8, col9, col10, col11, col12 = st.columns(6)

    box_style2 = "border: 0px solid #ddd; padding: 15px; background-color: rgba(88, 0, 0, 0.4); height: 130px; margin: 0px 5px 5px 0px; border-radius: 7px;"

    with col7:
        st.markdown(
            f"<div style='{box_style2}'><p style='font-size:12px;'>POINTS PER GAME</p><p style='font-size:24px;'>{opponent_kpis['PPG']:.1f}</p></div>",
            unsafe_allow_html=True)

    with col8:
        st.markdown(
            f"<div style='{box_style2}'><p style='font-size:12px;'>FIELD GOALS PERCENTAGE</p><p style='font-size:24px;'>{opponent_kpis['FG%'] * 100:.1f}%</p></div>",
            unsafe_allow_html=True)

    with col9:
        st.markdown(
            f"<div style='{box_style2}'><p style='font-size:12px;'>3 POINTS PERCENTAGE</p><p style='font-size:24px;'>{opponent_kpis['3P%'] * 100:.1f}%</p></div>",
            unsafe_allow_html=True)

    with col10:
        st.markdown(
            f"<div style='{box_style2}'><p style='font-size:12px;'>3 POINTS MADE</p><p style='font-size:24px;'>{opponent_kpis['3PM']:.1f}</p></div>",
            unsafe_allow_html=True)

    with col11:
        st.markdown(
            f"<div style='{box_style2}'><p style='font-size:12px;'>DEFENSIVE REBOUNDS</p><p style='font-size:24px;'>{opponent_kpis['DRB']:.1f}</p></div>",
            unsafe_allow_html=True)

    with col12:
        st.markdown(
            f"<div style='{box_style2}'><p style='font-size:12px;'>OFFENSIVE REBOUNDS</p><p style='font-size:24px;'>{opponent_kpis['ORB']:.2f}</p></div>",
            unsafe_allow_html=True)


# Display top players tables
    st.header("Top 5 Players Categorized by :", divider='orange')

    # Create a 2x2 grid layout for top players
    top_players_layout = st.columns(2)

    # Top 5 players in PPG
    with top_players_layout[0]:
        st.subheader("Points per game:")
        top_ppg_players = get_top_players(df, selected_team, 'PPG')
        st.table(top_ppg_players.style.format({'PPG': '{:.2f}'}))

    # Top 5 players in RPG
    with top_players_layout[1]:
        st.subheader("Rebounds per game:")
        top_rpg_players = get_top_players(df, selected_team, 'RPG')
        st.table(top_rpg_players.style.format({'RPG': '{:.2f}'}))

    # Top 5 players in APG
    with top_players_layout[0]:
        st.subheader("Assists per game:")
        top_apg_players = get_top_players(df, selected_team, 'APG')
        st.table(top_apg_players.style.format({'APG': '{:.2f}'}))

    # Top 5 players in SPG
    with top_players_layout[1]:
        st.subheader("Steals per game:")
        top_spg_players = get_top_players(df, selected_team, 'SPG')
        st.table(top_spg_players.style.format({'SPG': '{:.2f}'}))



    # Filter data for the selected team
    team_data = team_totals[team_totals['Team'] == selected_team]
    opponent_data = opponent_totals[opponent_totals['Team'] == selected_team]

    # Create a bar chart
    chart_data = pd.DataFrame({
            'Category': ['Average Points Scored', 'Average Points Conceded'],
            'PPG': [team_data['PPG'].iloc[0], opponent_data['PPG'].iloc[0]]
        })

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(8, 4))
    ax = sns.barplot(x='PPG', y='Category', data=chart_data, palette=['#2ca02c', '#d62728'],)

    # Add labels
    for p in ax.patches:
        width = p.get_width()
        plt.text(width, p.get_y() + p.get_height() / 5, f'{width:.1f}', ha="left", va="center")

    plt.title(f"PPG Scored VS Conceded for {selected_team}")
    plt.xlabel("PPG")
    plt.ylabel("")

    # Access the Matplotlib figure
    fig = plt.gcf()

    # Set the background color
    fig.patch.set_facecolor('#F0F0F0')  # Replace with your desired color
    st.pyplot(fig)

    # Get scoring distribution for selected team from team totals
    scoring_distribution_team_totals = get_scoring_distribution(df, selected_team)

    # Create a vertical bar plot using Seaborn for team totals
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Player', y='Percentage of Total Points', data=scoring_distribution_team_totals, palette='viridis')
    plt.xlabel('Player')
    plt.ylabel('Percentage of Total Points')
    plt.title(f'Scoring Distribution for Team : {selected_team} ')
    plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability

    # Access the Matplotlib figure
    fig2 = plt.gcf()

    # Set the background color
    fig2.patch.set_facecolor('#F0F0F0')  # Replace with your desired color
    st.pyplot(fig2)


    # Add a "Made by" section at the bottom
    st.markdown("---")
    made_by_text = "Made by: Athanasios Kouras"
    st.markdown(made_by_text, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
