# nba-api-data-extraction

> A Python toolkit to extract NBA data from [nba_api](https://github.com/swar/nba_api) and store it locally as Parquet files, with optional upload to Google Cloud Storage.

## Why this project

I'm a huge sports fan, and of course an NBA fan (let's go Sixers!). I often want to do some analysis like "how good was VJ Edgecombe's rookie season?" or "how many NBA players have scored more 3s than Maxey in their first 5 years in the league?" Things like that. And the issue is always the same: the data.

`nba-api` is a good resource, but it has some issues such as request limits, etc. It would be much better to have my own dataset locally or in the cloud. That would mean faster access, processing, etc. So, this project tries to make `nba-api` data more accessible for NBA fans like me. For now, this does not try to be a complex pipeline to run live on schedule. It is just a collection of useful scripts to extract and download some NBA data locally as Parquet files, and optionally load it into Google Cloud Storage, which is cheap and gives you all the cloud advantages. Then, you can use that data to perform your analysis, to build dashboards or maybe to power your very own AI app (which I plan to do). 

## What you get

For now, this resource will give you three Parquet files ready for analysis:

| File | Content | Rows |
|---|---|---|
| `nba_teams.parquet` | All NBA teams (id, name, abbreviation, city, etc.) | 30 |
| `nba_players.parquet` | All players (id, full name, first/last name) | ~5,100 |
| `player_career_stats_by_season.parquet` | Season-by-season career stats for every player | ~30,000+ |

This is a work in progress, so more data will be downloaded in future commits.

## Project structure

```
nba-api-extraction/
├── main.py                     # Orchestrator -- fetches all data and saves parquet files
├── data_extractor.py           # Core functions for fetching NBA data via nba_api
├── retry_missing.py            # Fetches only players missing from the existing parquet
├── upload_to_gcs.py            # Uploads parquet files to Google Cloud Storage
├── utils.py                    # Shared utilities (logging, parquet saving)
├── .env.example                # Template for environment variables
├── pyproject.toml              # Project dependencies
├── data/                       # Output parquet files (gitignored)
└── logs/                       # Log files (gitignored)
```

## Quick start

You need git, uv and python 3.12 installed in your machine.

### 1. Clone and install

```bash
git clone https://github.com/your-username/nba-api-extraction.git
cd nba-api-extraction
uv sync
```

### 2. Fetch the data

```bash
uv run main.py
```

This fetches teams, players, and career stats from the NBA API and saves them as Parquet files in the `data/` folder. The career stats fetch takes 30-60 minutes due to API rate limits -- there's a progress bar and logs to keep you informed.

### 3. Check logs

```bash
cat logs/run.log
```

### 4. Retry missing players (optional)

Some players may fail to fetch on the first run due to API timeouts. To retry only the missing ones:

```bash
uv run retry_missing.py
```

This is much faster (a few minutes) since it only targets the missing players.

## Scripts

| Script | Purpose | When to use |
|---|---|---|
| `main.py` | Fetches all NBA data and saves parquet files | First run, or to refresh all data |
| `retry_missing.py` | Fetches only players missing from the existing parquet | After `main.py` to recover failed players |
| `upload_to_gcs.py` | Uploads parquet files to a GCS bucket | When you want cloud access to the data |

## Data schema

### Teams (`nba_teams.parquet`)

| Column | Type | Example |
|---|---|---|
| id | int | 1610612737 |
| full_name | string | Atlanta Hawks |
| abbreviation | string | ATL |
| nickname | string | Hawks |
| city | string | Atlanta |
| state | string | Atlanta |
| year_founded | int | 1949 |

### Players (`nba_players.parquet`)

| Column | Type | Example |
|---|---|---|
| id | int | 76001 |
| full_name | string | Alaa Abdelnaby |
| first_name | string | Alaa |
| last_name | string | Abdelnaby |

### Career stats (`player_career_stats_by_season.parquet`)

| Column | Type | Example |
|---|---|---|
| PLAYER_ID | int | 76001 |
| PLAYER_NAME | string | Alaa Abdelnaby |
| SEASON_ID | string | 1990-91 |
| TEAM_ID | int | 1610612738 |
| TEAM_ABBREVIATION | string | POR |
| PLAYER_AGE | int | 23 |
| GP | int | 72 |
| GS | int | 0 |
| MIN | float | 1250.0 |
| FGM | float | 310.0 |
| FGA | float | 620.0 |
| FG_PCT | float | 0.5 |
| FG3M | float | 0.0 |
| FG3A | float | 5.0 |
| FG3_PCT | float | 0.0 |
| FTM | float | 100.0 |
| FTA | float | 150.0 |
| FT_PCT | float | 0.667 |
| OREB | float | 100.0 |
| DREB | float | 200.0 |
| REB | float | 300.0 |
| AST | float | 50.0 |
| STL | float | 30.0 |
| BLK | float | 20.0 |
| TOV | float | 40.0 |
| PF | float | 120.0 |
| PTS | float | 720.0 |

## Google Cloud Storage (optional)

If you want to upload your parquet files to GCS:

### 1. Set up your `.env`

Copy the example and fill in your values:

```bash
cp .env.example .env
```

```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
NBA_DATA_BUCKET=your-bucket-name
GCS_PREFIX=nba/dataset/raw
```

### 2. Upload

```bash
uv run upload_to_gcs.py
```

Files are uploaded to `gs://your-bucket/nba/dataset/raw/`.

## Tech stack

| Dependency | Why |
|---|---|
| [nba_api](https://github.com/swar/nba_api) | Python client for the NBA stats API |
| [pandas](https://pandas.pydata.org/) | Data manipulation and Parquet I/O |
| [pyarrow](https://arrow.apache.org/docs/python/index.html) | Parquet file format support |
| [requests-cache](https://requests-cache.readthedocs.io/) | Caches API responses to disk, avoids re-fetching |
| [tqdm](https://tqdm.github.io/) | Progress bars for long-running fetches |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Loads environment variables from `.env` |
| [google-cloud-storage](https://cloud.google.com/python/docs/reference/storage/latest) | Uploads parquet files to GCS |

## Future improvements

- Incremental updates -- fetch only new seasons instead of re-fetching everything
- Additional endpoints -- playoff stats, team stats, draft data
- Data validation -- verify completeness before saving
- Scheduled runs -- automate periodic data refreshes
- dbt integration -- transform raw parquet into analytics-ready tables

## License

This project is open source and available under the [MIT License](LICENSE).
