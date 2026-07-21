from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import playercareerstats
import requests_cache
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import pandas as pd

def get_nba_teams() -> list[dict]:
    """
        Fetches NBA teams using the nba_api.

        Returns:
            list[dict]: A list of dictionaries, each representing an NBA team.
        
        Example: 
            [{'id': 1610612737, 'full_name': 'Atlanta Hawks', 'abbreviation': 'ATL', 'nickname': 'Hawks',
                'city': 'Atlanta', 'state': 'Atlanta', 'year_founded': 1949}, ...]
 
    """
    nba_teams = teams.get_teams()
    return nba_teams

def get_nba_players() -> list[dict]:
    """
        Fetches NBA players using the nba_api.

        Returns:
            list[dict]: A list of dictionaries, each representing an NBA player.
        
        Example: 
            [{'id': 76001, 'full_name': 'Alaa Abdelnaby', 'first_name': 'Alaa', 'last_name': 'Abdelnaby'}, ...]
 
    """
    nba_players = players.get_players()
    return nba_players

def get_player_career_stats(player_id: str, timeout: int = 60, retries: int = 3) -> list[dict]:
    """
    Fetches career stats for a specific NBA player with retry logic.
    """
    for attempt in range(retries):
        try:
            career = playercareerstats.PlayerCareerStats(
                player_id=player_id, timeout=timeout
            )
            career_stats = career.get_data_frames()[0].to_dict(orient="records")
            return career_stats
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait)
            else:
                raise e


def get_all_career_stats(max_workers: int = 3) -> pd.DataFrame:
    """
    Fetches career stats for all NBA players with controlled parallelism and retries.
    """
    requests_cache.install_cache("nba_cache", expire_after=86400)
    all_players = get_nba_players()
    print(f"Found {len(all_players)} players. Fetching career stats...")
    def fetch_player(player):
        try:
            stats = get_player_career_stats(player["id"])
            return {
                "player_id": player["id"],
                "player_name": player["full_name"],
                "seasons": stats,
            }
        except Exception as e:
            print(f"  Failed after retries: {player['full_name']}: {e}")
            return None
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_player, p): p for p in all_players}
        for f in tqdm(as_completed(futures), total=len(all_players), desc="Fetching"):
            result = f.result()
            if result:
                results.append(result)
    rows = []
    for r in results:
        for season in r["seasons"]:
            rows.append({**season, "player_name": r["player_name"]})
    df = pd.DataFrame(rows)
    print(f"Done. {len(df)} player-seasons fetched from {len(results)} players.")
    return df

if __name__ == "__main__":
    nba_teams = get_nba_teams()
    nba_players = get_nba_players()
    print(f"Number of teams fetched: {len(nba_teams)}")
    print(f"Number of players fetched: {len(nba_players)}")