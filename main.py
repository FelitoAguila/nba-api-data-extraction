from nba_teams_extractor import get_all_career_stats
import os

def save_to_parquet(df, filepath: str = "data/player_career_stats_by_season.parquet"):
    """Save a DataFrame to Parquet format, creating directories if needed."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_parquet(filepath, index=False)
    print(f"Saved {len(df)} rows to {filepath}")


if __name__ == "__main__":
    df = get_all_career_stats()
    save_to_parquet(df)