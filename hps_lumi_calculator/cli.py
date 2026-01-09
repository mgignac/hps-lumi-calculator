import argparse
import sys
from .calculator import LumiCalculator


def main():
    parser = argparse.ArgumentParser(
        description='Calculate luminosity for HPS runs based on available files'
    )
    parser.add_argument(
        'search_path',
        help='Path to search for hps_XXXXX folders'
    )
    parser.add_argument(
        '--csv', '-c',
        default='data/sheet.csv',
        help='Path to CSV file with run data (default: data/sheet.csv)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output for each run'
    )

    args = parser.parse_args()

    try:
        calc = LumiCalculator(args.csv, args.search_path, verbose=args.verbose)
    except FileNotFoundError as e:
        print('Error: {}'.format(e), file=sys.stderr)
        sys.exit(1)

    results = calc.compute_all()

    if not results:
        print('No hps_XXXXX folders found in {}'.format(args.search_path))
        sys.exit(0)

    if args.verbose:
        print('{:<10} {:>12} {:>12} {:>10} {:>14}'.format(
            'Run', 'Found', 'Expected', 'Fraction', 'Luminosity'
        ))
        print('-' * 62)

        for run_number in sorted(results.keys()):
            data = results[run_number]
            if data['computed_luminosity'] is not None:
                print('{:<10} {:>12} {:>12} {:>10.2%} {:>14.6f}'.format(
                    run_number,
                    data['found_files'],
                    data['expected_files'],
                    data['fraction'],
                    data['computed_luminosity']
                ))
            else:
                print('{:<10} {:>12} {:>12} {:>10} {:>14}'.format(
                    run_number,
                    data['found_files'],
                    'N/A',
                    'N/A',
                    'N/A'
                ))

        print('-' * 62)

    total = sum(
        r['computed_luminosity'] for r in results.values()
        if r['computed_luminosity'] is not None
    )
    print('Total luminosity: {:.6f}'.format(total))
    print('Runs found: {}'.format(len(results)))


if __name__ == '__main__':
    main()
