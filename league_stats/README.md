# League Stats Scripts

Scripts to analyze your ESPN Fantasy Football league history.

## Setup

1. Create and activate a virtual environment from the project root:
   ```bash
   cd /path/to/espn-api
   python3 -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

2. Install the project in development mode plus script dependencies:
   ```bash
   pip install -e . && pip install python-dotenv
   ```

3. Configure your league credentials:
   ```bash
   cd league_stats
   cp .env.example .env
   # Edit .env with your values
   ```

   Required environment variables:
   - `LEAGUE_ID` - Your league ID (from the URL of your league page)
   - `ESPN_S2` - Your espn_s2 cookie (for private leagues)
   - `SWID` - Your SWID cookie (for private leagues)
   - `START_YEAR` - (Optional) First season to analyze, defaults to 2018

## Running Scripts

From the project root with your venv activated:

```bash
python league_stats/highest_lowest_scores.py
```

## Available Scripts

- `highest_lowest_scores.py` - Find the highest and lowest scoring games in league history
- `score_distribution.py` - Visualize score distributions by year (box plot with mean, median, quartiles)
