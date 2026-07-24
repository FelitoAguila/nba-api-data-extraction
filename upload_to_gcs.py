import os
import logging

from dotenv import load_dotenv
from google.cloud import storage

from utils import DATA_DIR, setup_logging

load_dotenv()

log = logging.getLogger(__name__)


def upload_parquet_files(
    bucket_name: str, destination_prefix: str, data_dir: str = DATA_DIR
):
    """Upload all parquet files from data_dir to a GCS bucket."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    parquet_files = [f for f in os.listdir(data_dir) if f.endswith(".parquet")]

    if not parquet_files:
        log.warning(f"No parquet files found in {data_dir}/")
        return

    for filename in parquet_files:
        filepath = os.path.join(data_dir, filename)
        blob_path = f"{destination_prefix}/{filename}"
        try:
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(filepath)
            log.info(f"Uploaded gs://{bucket_name}/{blob_path}")
        except Exception as e:
            log.error(f"Failed to upload {filename}: {e}")


if __name__ == "__main__":
    setup_logging()

    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        log.error("GOOGLE_APPLICATION_CREDENTIALS not set. Check your .env file.")
        raise SystemExit(1)

    bucket_name = os.environ.get("NBA_DATA_BUCKET")
    if not bucket_name:
        log.error("NBA_DATA_BUCKET not set. Check your .env file.")
        raise SystemExit(1)

    destination_prefix = os.environ.get("GCS_PREFIX")

    upload_parquet_files(bucket_name, destination_prefix)
