#!/usr/bin/env python3
"""Scatter plot of draft position vs points-for ranking."""

import os
import sys
from datetime import datetime
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib is required. Install with: pip install matplotlib")
    sys.exit(1)

from dotenv import load_dotenv
from espn_api.football import League

load_dotenv()

LEAGUE_ID = os.getenv("LEAGUE_ID")
ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")
# Start from 2019 when league expanded to 10 teams
DRAFT_START_YEAR = 2019


def get_draft_position(league, team_id):
    """Get a team's draft position (their round 1 pick)."""
    for pick in league.draft:
        if pick.round_num == 1 and pick.team and pick.team.team_id == team_id:
            return pick.round_pick
    return None


def get_points_for_rankings(league):
    """Get points-for rankings for all teams (1 = most points)."""
    teams_sorted = sorted(league.teams, key=lambda t: t.points_for, reverse=True)
    rankings = {}
    for rank, team in enumerate(teams_sorted, 1):
        rankings[team.team_id] = rank
    return rankings


def main():
    current_year = datetime.now().year
    print(f"Analyzing draft position vs points-for ranking from {DRAFT_START_YEAR} to {current_year}...\n")

    # Collect data
    data_points = []

    for year in range(DRAFT_START_YEAR, current_year + 1):
        print(f"Fetching {year} season...")
        try:
            league = League(
                league_id=int(LEAGUE_ID),
                year=year,
                espn_s2=ESPN_S2,
                swid=SWID
            )

            if not league.draft:
                print(f"  No draft data for {year}")
                continue

            pf_rankings = get_points_for_rankings(league)

            for team in league.teams:
                draft_pos = get_draft_position(league, team.team_id)
                pf_rank = pf_rankings.get(team.team_id)

                if draft_pos and pf_rank:
                    data_points.append({
                        'year': year,
                        'draft_position': draft_pos,
                        'points_for_rank': pf_rank,
                    })

        except Exception as e:
            print(f"  Warning: Could not fetch {year}: {e}")

    if not data_points:
        print("No data found!")
        return

    print(f"\nCollected {len(data_points)} team-seasons of data")

    # Extract x and y values
    x = [d['draft_position'] for d in data_points]
    y = [d['points_for_rank'] for d in data_points]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Scatter plot with jitter for visibility
    jitter = np.random.uniform(-0.15, 0.15, len(x))
    ax.scatter([xi + ji for xi, ji in zip(x, jitter)], y,
               alpha=0.6, s=80, c='steelblue', edgecolors='navy', linewidths=0.5)

    # Customize plot
    ax.set_xticks(range(1, 11))
    ax.set_yticks(range(1, 11))
    ax.set_xlabel('Draft Position', fontsize=12, fontweight='bold')
    ax.set_ylabel('Points For Rank (1 = Best)', fontsize=12, fontweight='bold')
    ax.set_title(f'Draft Position vs Points For Ranking\n({DRAFT_START_YEAR}-{current_year}, {len(data_points)} team-seasons)',
                 fontsize=14, fontweight='bold')

    # Invert y-axis so 1 (best) is at the top
    ax.invert_yaxis()

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), 'draft_position_scatter.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nChart saved to: {output_path}")

    # Open the saved image
    print("Opening chart...")
    import subprocess
    subprocess.run(['open', output_path], check=False)


if __name__ == "__main__":
    main()
