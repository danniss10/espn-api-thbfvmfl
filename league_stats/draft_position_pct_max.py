#!/usr/bin/env python3
"""Visualize avg percentage of max points-for by draft position."""

import os
import sys
from datetime import datetime
import numpy as np
from collections import defaultdict

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


def main():
    current_year = datetime.now().year
    print(f"Analyzing draft position vs % of max points-for from {DRAFT_START_YEAR} to {current_year}...\n")

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

            # Find max points for this season
            max_pf = max(team.points_for for team in league.teams)

            for team in league.teams:
                draft_pos = get_draft_position(league, team.team_id)

                if draft_pos and team.points_for > 0:
                    pct_of_max = (team.points_for / max_pf) * 100
                    data_points.append({
                        'year': year,
                        'draft_position': draft_pos,
                        'points_for': team.points_for,
                        'pct_of_max': pct_of_max,
                    })

        except Exception as e:
            print(f"  Warning: Could not fetch {year}: {e}")

    if not data_points:
        print("No data found!")
        return

    print(f"\nCollected {len(data_points)} team-seasons of data")

    # Group by draft position and calculate average
    pct_by_pos = defaultdict(list)
    for d in data_points:
        pct_by_pos[d['draft_position']].append(d['pct_of_max'])

    positions = sorted(pct_by_pos.keys())
    avg_pcts = [np.mean(pct_by_pos[pos]) for pos in positions]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Bar chart
    bars = ax.bar(positions, avg_pcts, color='steelblue', edgecolor='navy', linewidth=1.5)

    # Color the best bar green and worst bar red
    best_idx = avg_pcts.index(max(avg_pcts))
    worst_idx = avg_pcts.index(min(avg_pcts))
    bars[best_idx].set_color('green')
    bars[worst_idx].set_color('red')

    # Add value labels on bars
    for i, (pos, pct) in enumerate(zip(positions, avg_pcts)):
        ax.text(pos, pct + 0.5, f'{pct:.1f}%', ha='center', fontsize=10, fontweight='bold')

    # Customize plot
    ax.set_xticks(positions)
    ax.set_xticklabels([f'Pick {p}' for p in positions], fontsize=11)
    ax.set_xlabel('Draft Position', fontsize=12, fontweight='bold')
    ax.set_ylabel('Avg % of Max Points For', fontsize=12, fontweight='bold')
    ax.set_title(f'Draft Position vs Percentage of Max Points For\n({DRAFT_START_YEAR}-{current_year}, {len(data_points)} team-seasons)',
                 fontsize=14, fontweight='bold')

    # Set y-axis limits
    ax.set_ylim(min(avg_pcts) - 5, 100)

    # Add grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    plt.tight_layout()

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), 'draft_position_pct_max.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nChart saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 50)
    print("AVG % OF MAX POINTS-FOR BY DRAFT POSITION")
    print("=" * 50)
    for pos in positions:
        avg = np.mean(pct_by_pos[pos])
        print(f"Pick {pos}: {avg:.1f}%")

    # Open the saved image
    print("\nOpening chart...")
    import subprocess
    subprocess.run(['open', output_path], check=False)


if __name__ == "__main__":
    main()
