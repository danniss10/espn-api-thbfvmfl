#!/usr/bin/env python3
"""Analyze correlation between draft position and points-for ranking."""

import os
import sys
from datetime import datetime
from collections import defaultdict
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
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

    # Collect data: (draft_position, points_for_rank) for each team-season
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

            # Skip if no draft data
            if not league.draft:
                print(f"  No draft data for {year}")
                continue

            # Get points-for rankings
            pf_rankings = get_points_for_rankings(league)

            # Get each team's draft position and points-for rank
            for team in league.teams:
                draft_pos = get_draft_position(league, team.team_id)
                pf_rank = pf_rankings.get(team.team_id)

                if draft_pos and pf_rank:
                    data_points.append({
                        'year': year,
                        'team': team.team_name,
                        'draft_position': draft_pos,
                        'points_for_rank': pf_rank,
                        'points_for': team.points_for
                    })

        except Exception as e:
            print(f"  Warning: Could not fetch {year}: {e}")

    if not data_points:
        print("No data found!")
        return

    print(f"\nCollected {len(data_points)} team-seasons of data")

    # Determine league size (max draft position)
    league_size = max(d['draft_position'] for d in data_points)
    print(f"League size: {league_size} teams")

    # Group points-for ranks by draft position
    ranks_by_draft_pos = defaultdict(list)
    for d in data_points:
        ranks_by_draft_pos[d['draft_position']].append(d['points_for_rank'])

    # Calculate average rank for each draft position
    avg_pf_rank_by_draft = {}
    for draft_pos, ranks in ranks_by_draft_pos.items():
        avg_pf_rank_by_draft[draft_pos] = np.mean(ranks)

    # Sort draft positions by average points-for rank (best first = lowest avg rank)
    draft_positions_sorted = sorted(avg_pf_rank_by_draft.keys(),
                                     key=lambda x: avg_pf_rank_by_draft[x])

    data = [ranks_by_draft_pos[pos] for pos in draft_positions_sorted]
    labels = [f"Pick {pos}" for pos in draft_positions_sorted]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    # Create box plot
    bp = ax.boxplot(data,
                    positions=range(len(draft_positions_sorted)),
                    widths=0.6,
                    patch_artist=True,
                    showmeans=True,
                    meanprops=dict(marker='D', markerfacecolor='red', markeredgecolor='red', markersize=6),
                    medianprops=dict(color='black', linewidth=2),
                    boxprops=dict(facecolor='lightblue', color='navy'),
                    whiskerprops=dict(color='navy'),
                    capprops=dict(color='navy'),
                    flierprops=dict(marker='o', markerfacecolor='gray', markersize=4, alpha=0.5))

    # Customize plot
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_xlabel('Draft Position (sorted by avg points-for rank)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Points For Rank (1 = Best)', fontsize=12, fontweight='bold')
    ax.set_title(f'Draft Position vs Points For Ranking\n({DRAFT_START_YEAR}-{current_year}, {len(data_points)} team-seasons)',
                 fontsize=14, fontweight='bold')

    # Invert y-axis so 1 (best) is at the top
    ax.invert_yaxis()

    # Set y-ticks to show all ranks
    ax.set_yticks(range(1, league_size + 1))

    # Add grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='D', color='w', markerfacecolor='red', markersize=8, label='Mean'),
        Line2D([0], [0], color='black', linewidth=2, label='Median'),
        plt.Rectangle((0, 0), 1, 1, facecolor='lightblue', edgecolor='navy', label='25th-75th Percentile'),
    ]
    ax.legend(handles=legend_elements, loc='lower right')

    # Add mean annotations
    for i, draft_pos in enumerate(draft_positions_sorted):
        mean = avg_pf_rank_by_draft[draft_pos]
        seasons = len(ranks_by_draft_pos[draft_pos])
        ax.annotate(f'{mean:.1f}',
                    xy=(i, mean),
                    xytext=(0, -15),
                    textcoords='offset points',
                    ha='center',
                    fontsize=9,
                    color='red',
                    fontweight='bold')

    plt.tight_layout()

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), 'draft_position_analysis.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nChart saved to: {output_path}")

    # Print summary table (sorted by avg rank)
    print("\n" + "=" * 60)
    print("AVERAGE POINTS-FOR RANK BY DRAFT POSITION (sorted best to worst)")
    print("=" * 60)
    print(f"{'Draft Pos':<12} {'Avg PF Rank':<12} {'Seasons':<10} {'Top 3 Rate':<12}")
    print("-" * 60)

    for draft_pos in draft_positions_sorted:
        ranks = ranks_by_draft_pos[draft_pos]
        avg_rank = np.mean(ranks)
        top_3_rate = len([r for r in ranks if r <= 3]) / len(ranks) * 100
        print(f"Pick {draft_pos:<7} {avg_rank:<12.2f} {len(ranks):<10} {top_3_rate:<12.1f}%")

    # Best and worst draft positions
    print("\n" + "=" * 60)
    best_pos = min(avg_pf_rank_by_draft, key=avg_pf_rank_by_draft.get)
    worst_pos = max(avg_pf_rank_by_draft, key=avg_pf_rank_by_draft.get)
    print(f"Best draft position: #{best_pos} (avg rank: {avg_pf_rank_by_draft[best_pos]:.2f})")
    print(f"Worst draft position: #{worst_pos} (avg rank: {avg_pf_rank_by_draft[worst_pos]:.2f})")

    # Open the saved image
    print("\nOpening chart...")
    import subprocess
    subprocess.run(['open', output_path], check=False)


if __name__ == "__main__":
    main()
