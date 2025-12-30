# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ESPN Fantasy API is a Python library that extracts data from ESPN's Fantasy API for multiple sports:
- Football (NFL) - full support
- Basketball (NBA) - full support
- Hockey (NHL) - in development
- Baseball (MLB) - in development
- Women's Basketball (WNBA) - in development

Supports both public and private leagues (private requires espn_s2 and swid cookies).

## Build & Test Commands

```bash
# Install dependencies (Python >=3.9, recommended)
python -m venv myenv
source myenv/bin/activate  # or myenv\Scripts\activate.bat on Windows
pip install -r requirementsV2.txt

# Install from pip (for users)
pip install espn_api

# Run all tests (Python >=3.9)
pytest

# Run tests for a specific sport
pytest tests/football/unit/
pytest tests/basketball/unit/

# Run a single test file
pytest tests/football/unit/test_league.py -v

# Run a single test method
pytest tests/football/unit/test_league.py::LeagueTest::test_error_status -v

# Legacy test runner (Python <3.9, uses nosetests)
python3 setup.py nosetests
```

## Architecture

### Package Structure

Each sport module (`espn_api/football/`, `espn_api/basketball/`, etc.) follows the same pattern:
- `league.py` - Main League class extending BaseLeague
- `team.py` - Team model
- `player.py` - Player stats model
- `box_score.py` / `box_player.py` - Game scoring data
- `matchup.py` - Head-to-head matchup data
- `constant.py` - Sport-specific constants (positions, scoring categories, activity types)
- `settings.py` - League configuration model

### Core Classes

**`base_league.py`** - Abstract base class providing:
- API authentication (espn_s2, SWID cookies)
- Data fetching methods (_fetch_league, _fetch_draft, _fetch_teams)
- Debug logging support

**`espn_api/requests/espn_requests.py`** - HTTP layer:
- Handles ESPN API endpoint formats (newer `/seasons/` vs older `/leagueHistory/`)
- Custom exceptions: `ESPNAccessDenied`, `ESPNInvalidLeague`, `ESPNUnknownError`

### Entry Points

```python
from espn_api.football import League
from espn_api.basketball import League
from espn_api.hockey import League
from espn_api.baseball import League
from espn_api.wbasketball import League

league = League(league_id=123, year=2024)

# Private league access
league = League(league_id=123, year=2024, espn_s2='cookie', swid='cookie')

# Debug mode (prints all API requests/responses)
league = League(league_id=123, year=2024, debug=True)
```

## Testing

- **Unit tests**: `tests/{sport}/unit/` - use mocked data from JSON fixtures in `tests/football/unit/data/`
- **Integration tests**: `tests/{sport}/integration/` - test against live ESPN API (run by CI daily)
- Tests use `requests_mock` to simulate API responses
- Test framework: unittest (matches existing codebase patterns)

## CI/CD

- `.github/workflows/espn-api.yml` - Unit tests on push/PR
- `.github/workflows/espn-api-test.yml` - Integration tests (daily schedule)
- `.github/workflows/package-release.yml` - Package releases to PyPI
