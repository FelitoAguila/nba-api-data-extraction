from data_extractor import get_nba_teams, get_nba_players, get_all_career_stats
from utils import DATA_DIR, save_to_parquet, setup_logging
import pandas as pd

setup_logging()

if __name__ == "__main__":
    # Teams
    teams_data = get_nba_teams()
    save_to_parquet(pd.DataFrame(teams_data), f"{DATA_DIR}/nba_teams.parquet")
    # Players
    players_data = get_nba_players()
    save_to_parquet(pd.DataFrame(players_data), f"{DATA_DIR}/nba_players.parquet")
    # Career stats (this one takes 30-60 min)
    career_stats = get_all_career_stats()
    save_to_parquet(career_stats, f"{DATA_DIR}/player_career_stats_by_season.parquet")
