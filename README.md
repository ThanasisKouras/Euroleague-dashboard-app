# Euroleague-dashboard-app
A Euroleague analytics application, refreshing automatically using data from [euroleague-api](https://pypi.org/project/euroleague-api/).
This application aims to quickly provide basic & advanced data analysis for each euroleague team for any selected season. (Currently season 2023-2024 is selected)
# View the live web-app :
  **URL:** https://euroleague-dashboard.streamlit.app/
## How to read the Euroleague Dashboard Analytics app :

- On the left side of the app a selection button for each team is available. Selecting a team shows specific data for this team
  - The button **Show Standings** shows the overall standings on the board and how many Wins / Losses each team has.
- Basic **KPIs** are used for each team to show the performance on the most important stats. **Ranking** calculations are used among others to show team standings on each section. Other calculations such as **assists/turnovers ratio**, **last 5 games form**, **Wins/Losses** based on Home/Away give an overview on how the selected team perfoms under certain circumstances
- For each team selected, 3 top players are shown based on the **PIR (Performance Index Rating)**. Additionally total stats (Pts/Rebs/Ast) are shown for each one of these players
- Tables showing the top 5 performing players for each team in **Points, Rebounds, Assists, Steals**
- The **Chart Section** shows the contribution on scoring for most players to analyse if the impact of a player is crucial or not. It also shows how many points each team scores on average, and how many points concedes on each game
  This dashboard can be updated in the future for more charts to be shown.
