#!/usr/bin/env python3
"""Visualize score distributions by team for the 2 QB era (2020+)."""

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
except ImportError:
    print("matplotlib is required. Install with: pip install matplotlib")
    sys.exit(1)

from league_data import get_all_scores, START_YEAR

# 2 QB era starts in 2020
TWO_QB_ERA_START = 2020


def main():
    current_year = datetime.now().year
    print(f"Fetching league data from {START_YEAR} to {current_year}...\n")

    all_games = get_all_scores(START_YEAR, current_year)

    if not all_games:
        print("No games found!")
        return

    # Filter to 2 QB era only (2020+)
    two_qb_games = [g for g in all_games if g['year'] >= TWO_QB_ERA_START]
    print(f"\nFiltered to 2 QB era: {len(two_qb_games)} games from {TWO_QB_ERA_START}+")

    # Group scores by team_id and track latest owner name
    scores_by_team_id = defaultdict(list)
    latest_name_by_team_id = {}

    for game in two_qb_games:
        team_id = game.get('team_id')
        if team_id is None:
            continue
        scores_by_team_id[team_id].append(game['score'])
        # Keep updating - last one will be the latest
        latest_name_by_team_id[team_id] = game['team']

    # Sort teams by mean score (highest first)
    team_ids_sorted = sorted(scores_by_team_id.keys(),
                              key=lambda t: np.mean(scores_by_team_id[t]),
                              reverse=True)

    data = [scores_by_team_id[team_id] for team_id in team_ids_sorted]
    team_labels = [latest_name_by_team_id[team_id] for team_id in team_ids_sorted]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    # Create box plot
    bp = ax.boxplot(data,
                    positions=range(len(team_ids_sorted)),
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
    ax.set_xticklabels(team_labels, fontsize=10, rotation=45, ha='right')
    ax.set_xlabel('Team Owner', fontsize=12, fontweight='bold')
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title(f'Fantasy Football Score Distribution by Team - 2 QB Era ({TWO_QB_ERA_START}+)',
                 fontsize=14, fontweight='bold')

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
    ax.legend(handles=legend_elements, loc='upper right')

    # Add mean annotations above each box
    for i, team_id in enumerate(team_ids_sorted):
        scores = scores_by_team_id[team_id]
        mean = np.mean(scores)
        games = len(scores)
        ax.annotate(f'{mean:.1f}',
                    xy=(i, mean),
                    xytext=(0, 10),
                    textcoords='offset points',
                    ha='center',
                    fontsize=8,
                    color='red')

    plt.tight_layout()

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), 'score_distribution_by_team.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nChart saved to: {output_path}")

    # Print summary table
    print("\n" + "=" * 50)
    print("TEAM STATS - 2 QB ERA (sorted by mean)")
    print("=" * 50)
    print(f"{'Team':<25} {'Mean':>8} {'Median':>8} {'Min':>8} {'Max':>8} {'Games':>6}")
    print("-" * 50)
    for team_id in team_ids_sorted:
        scores = scores_by_team_id[team_id]
        name = latest_name_by_team_id[team_id]
        print(f"{name:<25} {np.mean(scores):>8.2f} {np.median(scores):>8.2f} "
              f"{min(scores):>8.2f} {max(scores):>8.2f} {len(scores):>6}")

    # Open the saved image
    print("Opening chart...")
    import subprocess
    subprocess.run(['open', output_path], check=False)


if __name__ == "__main__":
    main()
