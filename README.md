# HPS Luminosity Calculator

Calculate luminosity for HPS runs based on available EVIO files.

## Installation

```bash
pip install -e .
```

## Usage

### Command Line

```bash
# Basic usage
hps-lumi /path/to/hps/folders

# With custom CSV path
hps-lumi /path/to/hps/folders --csv /path/to/data.csv

# Verbose output (show per-run details)
hps-lumi /path/to/hps/folders --verbose
```

Or run as a module:
```bash
python -m hps_lumi_calculator.cli /path/to/hps/folders
```

### Python API

```python
from hps_lumi_calculator import LumiCalculator

calc = LumiCalculator(
    csv_path='data/sheet.csv',
    search_path='/path/to/hps/folders'
)

# Get results for all found run folders
results = calc.compute_all()

# Get total luminosity across all found runs
total = calc.total_luminosity()
```

## How It Works

1. Loads run data from a CSV file containing run numbers, expected EVIO file counts, and full luminosity values
2. Searches the specified path for folders matching the pattern `hps_XXXXX` (where XXXXX is a run number)
3. Counts the number of files in each folder
4. Computes luminosity as: `(found_files / expected_files) * full_luminosity`

## CSV Format

The CSV file should contain the following columns:
- `x`: Run number
- `evio_files_count`: Expected number of EVIO files
- `luminosity`: Full luminosity value for the run
