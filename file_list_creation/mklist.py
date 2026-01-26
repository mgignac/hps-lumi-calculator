#!/usr/bin/env python3
"""
Sample a configurable fraction of files from each subfolder.
Perfect for creating train/validation splits, preview sets, or random samples.
"""

import argparse
import random
import glob
import pprint
from pathlib import Path
from typing import List, Dict


def sample_fraction_per_folder(
    root_dir: Path,
    fraction: float,
    extensions: None,
) -> Dict[str, List[Path]]:

    result: Dict[str, List[Path]] = {}

    processed_files = {}
    for batch in glob.glob("inputs/*"):
        with open(batch, "r") as f:
            for l in f.readlines():
                folder_name = l.split("/")[-2]
                if not processed_files.get(folder_name):
                    processed_files[folder_name] = []
                processed_files[folder_name].append(l.split("/")[-1].rstrip())
                    

    runs_with_detectors = []
    for det in glob.glob("/work/hallb/hps/mgignac/sw/hps-java/detector-data/detectors/*_v9_*"): 
        run = det[-5:]
        if not run.isdigit():
            continue
        run = int(run)
        if not run in runs_with_detectors:
            runs_with_detectors.append(run)

    for folder in root_dir.iterdir():
        if not folder.is_dir():
            continue

        folder_name = folder.name.split("/")[-1]

        if not 'hps_' in folder_name:
            continue

        run_num = folder_name[-5:]
        if not run_num.isdigit():
            print("Unexpected folder: ",folder.name)
            continue

        run_num = int(run_num)

        # Physics, excluding Mollers
        if run_num<14185 or run_num>14775:
            continue
        if run_num>=14628 and run_num<=14673:
            continue        

        if not run_num in runs_with_detectors:
            print("No detector for this run: ",run_num)
            continue        

        folder_processed = []
        if processed_files.get(folder_name):
            folder_processed = processed_files[folder_name]
            print("Number of files processed already: ",len(folder_processed))

        files = [
            p for p in folder.iterdir()
            if p.is_file() and not (p.name in folder_processed) and (
                extensions is None or
                p.suffix.lower() in {e.lower() for e in extensions}
            )
        ]

        total = len(files) + len(folder_processed)
        if total == 0:
            print(f"Skipping empty folder: {folder.name}")
            continue

        sample_size = max(20, int(total * fraction))
        sample_size = min(sample_size, total)

        random.shuffle(files)
        sampled = files[:sample_size]

        result[folder.name] = sampled
        print(f"{folder.name}: {total} → {len(sampled)} files "
              f"({len(sampled)/total*100:.1f}%)")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Sample a fraction of files from each subfolder",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "input_dir",
        type=str,
        help="Root directory containing subfolders with files"
    )

    parser.add_argument(
        "-f", "--fraction",
        type=float,
        default=0.1,
        help="Fraction of files to sample per folder (0.1 = 10%%)"
    )

    parser.add_argument(
        "-e", "--ext",
        type=str,
        nargs="+",
        help="Only consider files with these extensions (e.g. .jpg .png .mp4)"
    )

    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible sampling"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Write selected file paths to this text file (one per line)"
    )

    parser.add_argument(
        "--copy-to",
        type=str,
        default=None,
        help="Copy selected files to this directory (preserves folder structure)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be selected, don't write or copy"
    )

    args = parser.parse_args()

    root = Path(args.input_dir)
    if not root.is_dir():
        parser.error(f"Directory not found: {root}")

    if args.fraction <= 0 or args.fraction > 1:
        parser.error("--fraction must be between 0 and 1")

    print(f"Scanning: {root.resolve()}")
    print(f"Sampling {args.fraction*100:.1f}% of files per folder")
    if args.ext:
        print(f"Extensions: {', '.join(args.ext)}")
    if args.seed is not None:
        print(f"Random seed: {args.seed}")
    print("-" * 60)

    sampled = sample_fraction_per_folder(
        root_dir=root,
        fraction=args.fraction,
        extensions=args.ext,
    )

    # Flatten all selected paths
    all_selected = [p for files in sampled.values() for p in files]
    total_selected = len(all_selected)

    print(f"\nSELECTED {total_selected} files across {len(sampled)} folders")

    if args.dry_run:
        return

    # Optional: Save list to file
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            for p in all_selected:
                f.write(str(p) + "\n")
        print(f"List written to: {output_path}")

    # Optional: Copy files to destination
    if args.copy_to:
        dest = Path(args.copy_to)
        dest.mkdir(parents=True, exist_ok=True)
        copied = 0
        for folder_name, files in sampled.items():
            folder_dest = dest / folder_name
            folder_dest.mkdir(exist_ok=True)
            for src in files:
                dst = folder_dest / src.name
                # Avoid overwrite conflicts
                if dst.exists():
                    base = dst.stem
                    suffix = dst.suffix
                    counter = 1
                    while dst.exists():
                        dst = folder_dest / f"{base}_{counter}{suffix}"
                        counter += 1
                try:
                    import shutil
                    shutil.copy2(src, dst)
                    copied += 1
                except Exception as e:
                    print(f"Failed to copy {src}: {e}")
        print(f"Copied {copied} files to: {dest.resolve()}")


if __name__ == "__main__":
    main()
