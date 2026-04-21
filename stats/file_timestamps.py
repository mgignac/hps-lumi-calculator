#!/usr/bin/env python3
"""
Scan a directory tree, extract file modification timestamps, and plot
file counts (cumulative and rate) as a function of time.
"""

import os
import argparse
import fnmatch
from datetime import datetime, timezone

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np


def collect_timestamps(root, pattern):
    timestamps = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if pattern and not fnmatch.fnmatch(fname, pattern):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                mtime = os.stat(fpath).st_mtime
                timestamps.append(datetime.fromtimestamp(mtime))
            except OSError:
                pass
    return timestamps


def bin_timestamps(timestamps, bin_minutes):
    if not timestamps:
        return [], [], []

    timestamps_sorted = sorted(timestamps)
    t_start = timestamps_sorted[0]
    t_end = timestamps_sorted[-1]

    bin_seconds = bin_minutes * 60
    total_seconds = (t_end - t_start).total_seconds()
    n_bins = max(1, int(np.ceil(total_seconds / bin_seconds)))

    bin_edges = [t_start.timestamp() + i * bin_seconds for i in range(n_bins + 1)]
    bin_centers = [datetime.fromtimestamp((bin_edges[i] + bin_edges[i + 1]) / 2)
                   for i in range(n_bins)]

    counts = [0] * n_bins
    for ts in timestamps_sorted:
        idx = int((ts.timestamp() - bin_edges[0]) / bin_seconds)
        idx = min(idx, n_bins - 1)
        counts[idx] += 1

    cumulative = list(np.cumsum(counts))
    return bin_centers, counts, cumulative


def format_xaxis(ax):
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right')


def main():
    parser = argparse.ArgumentParser(
        description='Plot file counts over time from directory modification timestamps'
    )
    parser.add_argument('directory',
                        help='Root directory to scan')
    parser.add_argument('--pattern', '-p', default=None,
                        help='Glob pattern to filter files (e.g. "*.slcio")')
    parser.add_argument('--bin', '-b', type=float, default=60.0, dest='bin_minutes',
                        help='Bin size in minutes (default: 60)')
    parser.add_argument('--output', '-o', default='file_timestamps.png',
                        help='Output plot filename (default: file_timestamps.png)')
    args = parser.parse_args()

    print(f"Scanning {args.directory} ...")
    if args.pattern:
        print(f"  File filter: {args.pattern}")

    timestamps = collect_timestamps(args.directory, args.pattern)

    if not timestamps:
        print("No files found.")
        return

    print(f"Found {len(timestamps)} file(s)")
    print(f"  Earliest: {min(timestamps)}")
    print(f"  Latest:   {max(timestamps)}")

    bin_centers, counts, cumulative = bin_timestamps(timestamps, args.bin_minutes)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Top: rate (files per bin)
    ax1.bar(bin_centers, counts, width=args.bin_minutes / (24 * 60),
            align='center', color='steelblue', edgecolor='none')
    ax1.set_ylabel(f'Files per {args.bin_minutes:.0f}-min bin')
    ax1.set_title(f'File production rate — {args.directory}')
    ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Bottom: cumulative
    ax2.step(bin_centers, cumulative, where='post', color='darkorange', linewidth=2)
    ax2.fill_between(bin_centers, cumulative, step='post', alpha=0.2, color='darkorange')
    ax2.set_ylabel('Cumulative file count')
    ax2.set_xlabel('Time')
    format_xaxis(ax2)

    total_label = f'Total: {len(timestamps)} files'
    if args.pattern:
        total_label += f' matching "{args.pattern}"'
    ax2.annotate(total_label, xy=(0.98, 0.05), xycoords='axes fraction',
                 ha='right', fontsize=9, color='gray')

    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"Plot saved to {args.output}")


if __name__ == '__main__':
    main()
