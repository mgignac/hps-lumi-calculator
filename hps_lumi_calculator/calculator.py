import csv
import os
import re
from pathlib import Path
from typing import Dict, Optional


class LumiCalculator:
    def __init__(self, csv_path: str, search_path: str, verbose: bool = False,
                 run_filter: Optional[int] = None, file_pattern: Optional[str] = None):
        """
        Initialize the luminosity calculator.

        Args:
            csv_path: Path to the CSV file containing run data.
            search_path: Path to search for hps_XXXXX folders.
            verbose: Print progress information.
            run_filter: Only process this specific run number.
            file_pattern: Only count files containing this string.
        """
        self.csv_path = Path(csv_path)
        self.search_path = Path(search_path)
        self.verbose = verbose
        self.run_filter = run_filter
        self.file_pattern = file_pattern
        self.run_data = {}
        self._load_csv()

    def _load_csv(self):
        """Load run data from CSV file."""
        if self.verbose:
            print('Loading CSV from {}'.format(self.csv_path))
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row['x']:
                    continue
                run_number = int(row['x'])
                self.run_data[run_number] = {
                    'evio_files_count': int(row['evio_files_count']),
                    'luminosity': float(row['luminosity']),
                }
        if self.verbose:
            print('Loaded {} runs from CSV'.format(len(self.run_data)))

    def find_run_folders(self) -> Dict[int, Path]:
        """
        Find all hps_XXXXX folders in the search path.

        Returns:
            Dictionary mapping run numbers to folder paths.
        """
        pattern = re.compile(r'^hps_(\d{5,6})$')
        folders = {}

        if not self.search_path.exists():
            return folders

        for item in self.search_path.iterdir():
            if item.is_dir():
                match = pattern.match(item.name)
                if match:
                    run_number = int(match.group(1))
                    if self.run_filter is not None and run_number != self.run_filter:
                        continue
                    folders[run_number] = item

        return folders

    def count_files(self, folder: Path) -> int:
        """Count the number of files in a folder."""
        count = 0
        for item in folder.iterdir():
            if item.is_file():
                if self.file_pattern is None or self.file_pattern in item.name:
                    count += 1
        return count

    def calculate_luminosity(self, run_number: int, found_files: int) -> Optional[float]:
        """
        Calculate the luminosity for a run based on found files.

        Args:
            run_number: The run number.
            found_files: Number of files found in the folder.

        Returns:
            Calculated luminosity or None if run not in data.
        """
        if run_number not in self.run_data:
            return None

        data = self.run_data[run_number]
        evio_count = data['evio_files_count']
        full_luminosity = data['luminosity']

        if evio_count == 0:
            return 0.0

        fraction = found_files / evio_count
        return fraction * full_luminosity

    def compute_all(self) -> Dict:
        """
        Compute luminosity for all found run folders.

        Returns:
            Dictionary with run numbers as keys and result dicts as values.
        """
        results = {}
        folders = self.find_run_folders()

        if self.verbose:
            print('Found {} run folders'.format(len(folders)))
            print('Processing runs...')

        for i, (run_number, folder) in enumerate(sorted(folders.items())):
            if self.verbose:
                print('  [{}/{}] Run {}'.format(i + 1, len(folders), run_number))
            found_files = self.count_files(folder)
            luminosity = self.calculate_luminosity(run_number, found_files)

            if run_number in self.run_data:
                data = self.run_data[run_number]
                results[run_number] = {
                    'folder': str(folder),
                    'found_files': found_files,
                    'expected_files': data['evio_files_count'],
                    'full_luminosity': data['luminosity'],
                    'computed_luminosity': luminosity,
                    'fraction': found_files / data['evio_files_count'] if data['evio_files_count'] > 0 else 0,
                }
            else:
                results[run_number] = {
                    'folder': str(folder),
                    'found_files': found_files,
                    'expected_files': None,
                    'full_luminosity': None,
                    'computed_luminosity': None,
                    'fraction': None,
                }

        return results

    def total_luminosity(self) -> float:
        """Calculate the total luminosity across all found runs."""
        results = self.compute_all()
        total = 0.0
        for run_data in results.values():
            if run_data['computed_luminosity'] is not None:
                total += run_data['computed_luminosity']
        return total
