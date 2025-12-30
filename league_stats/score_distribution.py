#!/usr/bin/env python3
"""Visualize score distributions by year using box plots."""

import os
import sys
from datetime import datetime
from collections import defaultdict
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib is required. Install with: pip install matplotlib")
    sys.exit(1)

from league_data import get_all_scores, START_YEAR


def main():
    current_year = datetime.now().year
    print(f"Fetching league data from {START_YEAR} to {current_year}...\n")

    all_games = get_all_scores(START_YEAR, current_year)

    if not all_games:
        print("No games found!")
        return

    # Group scores by year
    scores_by_year = defaultdict(list)
    for game in all_games:
        scores_by_year[game['year']].append(game['score'])

    # Sort years
    years = sorted(scores_by_year.keys())
    data = [scores_by_year[year] for year in years]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    # Create box plot
    bp = ax.boxplot(data,
                    positions=range(len(years)),
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
    ax.set_xticklabels(years, fontsize=11)
    ax.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Fantasy Football Score Distribution by Year', fontsize=14, fontweight='bold')

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

    # Add stats annotations
    for i, year in enumerate(years):
        scores = scores_by_year[year]
        mean = np.mean(scores)
        ax.annotate(f'{mean:.1f}',
                    xy=(i, mean),
                    xytext=(0, 10),
                    textcoords='offset points',
                    ha='center',
                    fontsize=8,
                    color='red')

    # Add vertical line at 2020 (2 QB era)
    if 2020 in years:
        idx_2020 = years.index(2020)
        ax.axvline(x=idx_2020 - 0.5, color='green', linestyle='--', linewidth=2, alpha=0.7)
        ax.text(idx_2020 - 0.4, ax.get_ylim()[1] - 5, '2 QB Era →',
                fontsize=10, color='green', fontweight='bold')

    plt.tight_layout()

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), 'score_distribution.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nChart saved to: {output_path}")

    # Also show the plot
    plt.show()


if __name__ == "__main__":
    main()
