#!/usr/bin/env python3
"""Find the highest and lowest single-week scoring games in league history."""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for espn_api imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from espn_api.football import League

load_dotenv()

LEAGUE_ID = os.getenv("LEAGUE_ID")
ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")
START_YEAR = int(os.getenv("START_YEAR", 2016))

if not LEAGUE_ID:
    print("Error: LEAGUE_ID environment variable is required")
    print("Copy .env.example to .env and fill in your values")
    sys.exit(1)


def get_owner_name(team) -> str:
    """Get consistent owner name from team, falling back to team name."""
    if team.owners and len(team.owners) > 0:
        owner = team.owners[0]
        first = owner.get('firstName', '')
        last = owner.get('lastName', '')
        if first or last:
            return f"{first} {last}".strip()
    return team.team_name


def get_pre_2019_scores(start_year: int) -> list:
    """Fetch scores for 2016-2018 using team.scores (regular season only)."""
    all_games = []

    for year in range(start_year, 2019):
        print(f"Fetching {year} season (regular season only)...")
        try:
            league = League(
                league_id=int(LEAGUE_ID),
                year=year,
                espn_s2=ESPN_S2,
                swid=SWID
            )

            # Use actual regular season count from league settings
            regular_season_weeks = league.settings.reg_season_count
            print(f"  Regular season: {regular_season_weeks} weeks")

            for team in league.teams:
                for week in range(regular_season_weeks):
                    if week >= len(team.scores) or week >= len(team.schedule):
                        continue

                    score = team.scores[week]
                    opponent = team.schedule[week]

                    # Skip bye weeks and unplayed games
                    if opponent == team or score is None or score == 0:
                        continue

                    owner_name = get_owner_name(team)
                    opponent_name = get_owner_name(opponent) if hasattr(opponent, 'owners') else str(opponent)

                    all_games.append({
                        'year': year,
                        'week': week + 1,
                        'team': owner_name,
                        'score': score,
                        'opponent': opponent_name,
                        'is_playoff': False,
                    })
        except Exception as e:
            print(f"  Warning: Could not fetch {year} season: {e}")

    return all_games


def get_2019_plus_scores(end_year: int) -> list:
    """Fetch scores for 2019+ using box_scores (includes playoffs, deduped)."""
    all_games = []
    seen_matchups = set()  # Track (year, team, opponent, score) to dedupe 2-week playoffs

    for year in range(2019, end_year + 1):
        print(f"Fetching {year} season...")
        try:
            league = League(
                league_id=int(LEAGUE_ID),
                year=year,
                espn_s2=ESPN_S2,
                swid=SWID
            )

            max_week = 17 if year < 2021 else 18

            for week in range(1, max_week + 1):
                try:
                    box_scores = league.box_scores(week)
                    for box in box_scores:
                        # Home team score
                        if box.home_team and box.home_score and box.home_score > 0:
                            home_name = get_owner_name(box.home_team)
                            away_name = get_owner_name(box.away_team) if box.away_team else "BYE"

                            # Dedupe key for 2-week playoff matchups (same teams, same score)
                            matchup_key = (year, home_name, away_name, box.home_score, box.is_playoff)
                            if box.is_playoff and matchup_key in seen_matchups:
                                continue
                            seen_matchups.add(matchup_key)

                            all_games.append({
                                'year': year,
                                'week': week,
                                'team': home_name,
                                'score': box.home_score,
                                'opponent': away_name,
                                'is_playoff': box.is_playoff,
                            })

                        # Away team score
                        if box.away_team and box.away_score and box.away_score > 0:
                            away_name = get_owner_name(box.away_team)
                            home_name = get_owner_name(box.home_team) if box.home_team else "BYE"

                            matchup_key = (year, away_name, home_name, box.away_score, box.is_playoff)
                            if box.is_playoff and matchup_key in seen_matchups:
                                continue
                            seen_matchups.add(matchup_key)

                            all_games.append({
                                'year': year,
                                'week': week,
                                'team': away_name,
                                'score': box.away_score,
                                'opponent': home_name,
                                'is_playoff': box.is_playoff,
                            })
                except Exception:
                    break

        except Exception as e:
            print(f"  Warning: Could not fetch {year} season: {e}")

    return all_games


def main():
    current_year = datetime.now().year
    print(f"Analyzing league history from {START_YEAR} to {current_year}...\n")

    all_games = []

    # Get pre-2019 scores (regular season only)
    if START_YEAR < 2019:
        all_games.extend(get_pre_2019_scores(START_YEAR))

    # Get 2019+ scores (all games, deduped)
    all_games.extend(get_2019_plus_scores(current_year))

    if not all_games:
        print("No games found!")
        return

    # Sort by score
    sorted_games = sorted(all_games, key=lambda x: x['score'], reverse=True)

    top_n = 25
    highest = sorted_games[:top_n]
    lowest = sorted_games[-top_n:][::-1]

    print("\n" + "=" * 60)
    print(f"HIGHEST SINGLE-WEEK SCORES (Top {top_n})")
    print("=" * 60)
    for i, game in enumerate(highest, 1):
        playoff_marker = " [P]" if game['is_playoff'] else ""
        print(f"{i:2}. {game['score']:6.2f} pts - {game['team']}")
        print(f"    Week {game['week']}, {game['year']} vs {game['opponent']}{playoff_marker}")
        print()

    print("=" * 60)
    print(f"LOWEST SINGLE-WEEK SCORES (Bottom {top_n})")
    print("=" * 60)
    for i, game in enumerate(lowest, 1):
        playoff_marker = " [P]" if game['is_playoff'] else ""
        print(f"{i:2}. {game['score']:6.2f} pts - {game['team']}")
        print(f"    Week {game['week']}, {game['year']} vs {game['opponent']}{playoff_marker}")
        print()

    # 2 QB Era (2020+) lowest scores
    two_qb_era_games = [g for g in all_games if g['year'] >= 2020]
    if two_qb_era_games:
        sorted_2qb = sorted(two_qb_era_games, key=lambda x: x['score'])
        lowest_2qb = sorted_2qb[:top_n]

        print("=" * 60)
        print(f"LOWEST SINGLE-WEEK SCORES - 2 QB ERA (2020+, Bottom {top_n})")
        print("=" * 60)
        for i, game in enumerate(lowest_2qb, 1):
            playoff_marker = " [P]" if game['is_playoff'] else ""
            print(f"{i:2}. {game['score']:6.2f} pts - {game['team']}")
            print(f"    Week {game['week']}, {game['year']} vs {game['opponent']}{playoff_marker}")
            print()

    # Summary stats
    all_scores = [g['score'] for g in all_games]
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total single-week games analyzed: {len(all_games)}")
    print(f"Average score: {sum(all_scores) / len(all_scores):.2f} pts")
    print(f"Highest ever: {max(all_scores):.2f} pts")
    print(f"Lowest ever: {min(all_scores):.2f} pts")
    print("\n[P] = Playoff game")
    if START_YEAR < 2019:
        print(f"Note: {START_YEAR}-2018 data excludes playoffs (2-week matchups not supported)")


if __name__ == "__main__":
    main()
