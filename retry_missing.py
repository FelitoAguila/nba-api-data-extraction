import os
import logging

import pandas as pd
from tqdm import tqdm

from data_extractor import get_nba_players, get_player_career_stats
from utils import DATA_DIR, setup_logging

log = logging.getLogger(__name__)

PARQUET_PATH = f"{DATA_DIR}/player_career_stats_by_season.parquet"


def retry_missing_players():
    """Fetch only the players missing from the existing parquet file."""
    # Load existing data
    if os.path.exists(PARQUET_PATH):
        existing_df = pd.read_parquet(PARQUET_PATH)
        existing_ids = set(existing_df["PLAYER_ID"].unique())
    else:
        log.warning("No existing parquet found. Will fetch all players.")
        existing_df = pd.DataFrame()
        existing_ids = set()

    # Identify missing players
    all_players = get_nba_players()
    missing = [p for p in all_players if p["id"] not in existing_ids]

    if not missing:
        log.info("No missing players. Everything is up to date.")
        return

    log.info(f"Found {len(missing)} missing players. Fetching sequentially...")

    new_rows = []
    for player in tqdm(missing, desc="Retrying"):
        try:
            stats = get_player_career_stats(player["id"], timeout=90, retries=5)
            for season in stats:
                new_rows.append({**season, "player_name": player["full_name"]})
            log.info(f"  Recovered: {player['full_name']}")
        except Exception as e:
            log.error(f"  Final failure: {player['full_name']}: {e}")

    # Append and save
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        combined.to_parquet(PARQUET_PATH, index=False)
        log.info(
            f"Appended {len(new_rows)} rows. Total: {len(combined)} rows "
            f"from {len(combined['PLAYER_ID'].unique())} players."
        )
    else:
        log.info("No players recovered on retry.")


if __name__ == "__main__":
    setup_logging()
    retry_missing_players()
