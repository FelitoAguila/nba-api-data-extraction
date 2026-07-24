import logging
import os
import pandas as pd

log = logging.getLogger(__name__)

DATA_DIR = "data"


def setup_logging(log_dir: str = "logs"):
    """Configure logging to both console and file."""
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(log_dir, "run.log")),
        ],
    )


def save_to_parquet(df: pd.DataFrame, filepath: str):
    """Save a DataFrame to Parquet, creating directories if needed."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_parquet(filepath, index=False)
    log.info(f"Saved {len(df)} rows to {filepath}")
