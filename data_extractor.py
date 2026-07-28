from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import playercareerstats, leaguegamefinder
import requests_cache
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm
import pandas as pd
import logging

log = logging.getLogger(__name__)


def get_nba_teams() -> list[dict]:
    """Fetches NBA teams using the nba_api."""
    log.info("Fetching NBA teams...")
    return teams.get_teams()


def get_nba_players() -> list[dict]:
    """Fetches NBA players using the nba_api."""
    log.info("Fetching NBA players...")
    return players.get_players()


def get_player_career_stats(
    player_id: str, timeout: int = 60, retries: int = 3
) -> list[dict]:
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
                wait = 2**attempt  # 1s, 2s, 4s
                time.sleep(wait)
            else:
                raise e


def get_all_career_stats(max_workers: int = 3) -> pd.DataFrame:
    """
    Fetches career stats for all NBA players with controlled parallelism and retries.
    """
    requests_cache.install_cache("nba_cache", expire_after=86400)
    all_players = get_nba_players()
    log.info(f"Found {len(all_players)} players. Fetching career stats...")

    def fetch_player(player):
        try:
            stats = get_player_career_stats(player["id"])
            return {
                "player_id": player["id"],
                "player_name": player["full_name"],
                "seasons": stats,
            }
        except Exception as e:
            log.error(f"Failed: {player['full_name']}: {e}")
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
    log.info(f"Done. {len(df)} player-seasons fetched from {len(results)} players.")
    return df


def _get_season_label(season_year: int) -> str:
    return f"{season_year}-{str(season_year + 1)[2:]}"


def _get_current_season_year() -> int:
    now = datetime.now()
    return now.year - 1 if now.month <= 9 else now.year


def get_all_game_logs(
    season_type_nullable: str = "Regular Season",
    start_season_year: int = 1979,
    timeout: int = 60,
    retries: int = 3,
) -> pd.DataFrame:
    """
    Fetches player-level game logs for every NBA season using LeagueGameFinder.

    Iterates season-by-season to stay under the NBA API's 30K row limit.
    Each season's DataFrame is held in memory one at a time, then all are
    concatenated and numeric columns are downcast to minimize memory usage.

    Args:
        season_type_nullable: One of "Regular Season", "Playoffs", "PlayIn", "Pre Season".
        start_season_year: First season year to fetch (e.g. 1979 for 1979-80).
        timeout: HTTP timeout per request in seconds.
        retries: Number of retry attempts per season on failure.

    Returns:
        pd.DataFrame with one row per player-game and columns including
        SEASON_ID, TEAM_ID, GAME_ID, GAME_DATE, PTS, REB, AST, etc.
    """
    current_year = _get_current_season_year()
    seasons = [_get_season_label(y) for y in range(start_season_year, current_year + 1)]

    log.info(
        f"Fetching {len(seasons)} seasons of {season_type_nullable} player game logs "
        f"({seasons[0]} to {seasons[-1]})..."
    )

    requests_cache.install_cache("nba_cache", expire_after=86400)

    all_dfs: list[pd.DataFrame] = []

    for season in tqdm(seasons, desc="Seasons"):
        for attempt in range(retries):
            try:
                finder = leaguegamefinder.LeagueGameFinder(
                    player_or_team_abbreviation="P",
                    season_type_nullable=season_type_nullable,
                    season_nullable=season,
                    timeout=timeout,
                )
                season_df = finder.league_game_finder_results.get_data_frame()
                log.info(f"  {season}: {len(season_df)} rows")
                all_dfs.append(season_df)
                break
            except Exception as e:
                if attempt < retries - 1:
                    wait = 2**attempt
                    log.warning(f"  {season} attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    log.error(f"  {season}: FAILED after {retries} attempts: {e}")

        time.sleep(0.5)

    if not all_dfs:
        log.error("No data fetched.")
        return pd.DataFrame()

    df = pd.concat(all_dfs, ignore_index=True)
    log.info(f"Concatenated {len(df)} total rows from {len(all_dfs)} seasons.")

    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="float")

    log.info(
        f"Final DataFrame: {len(df)} rows, "
        f"{df.memory_usage(deep=True).sum() / 1024**2:.1f} MB"
    )
    return df
