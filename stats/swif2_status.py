#!/usr/bin/env python3
"""
Parse and summarize swif2 status output for multiple workflows.
"""

import argparse
import subprocess

# Fields that are workflow-specific and should not be summed
EXCLUDED_FIELDS = {
    'workflow_id',
    'workflow_name',
    'workflow_user',
    'workflow_site',
    'create_ts',
    'update_ts',
    'summary_ts',
}

# Fields that should be summed across workflows (ordered for display)
NUMERIC_FIELDS = [
    'jobs',
    'undispatched',
    'dispatched',
    'dispatched_preparing',
    'dispatched_running',
    'dispatched_pending',
    'dispatched_other',
    'dispatched_reaping',
    'succeeded',
    'abandoned',
    'problems',
    'attempts',
    'max_concurrent',
    'input_mb_processed',
    'output_mb_generated',
]


def get_workflow_status(workflow_name):
    """
    Run swif2 status for a workflow and return the output.

    Returns the command output as a string, or None if the command fails.
    """
    try:
        result = subprocess.run(
            ['swif2', 'status', workflow_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Timeout getting status for {workflow_name}")
        return None
    except Exception as e:
        print(f"Error getting status for {workflow_name}: {e}")
        return None


def parse_status_output(output):
    """
    Parse swif2 status output into a dictionary.

    Returns a dict with field names as keys and values as strings.
    """
    data = {}
    for line in output.strip().split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            data[key] = value
    return data


def parse_numeric_value(value):
    """
    Parse a numeric value, handling comma-separated numbers.

    Returns an integer, or None if parsing fails.
    """
    try:
        return int(value.replace(',', ''))
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Parse swif2 status for multiple workflows'
    )
    parser.add_argument(
        'basename',
        help='Workflow basename (workflows will be basename_0, basename_1, ...)'
    )
    parser.add_argument(
        'max_workflows',
        type=int,
        help='Maximum number of workflows to query'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print status for each workflow'
    )
    args = parser.parse_args()

    # Aggregated totals
    totals = {field: 0 for field in NUMERIC_FIELDS}
    all_problem_types = set()
    workflows_queried = 0

    for i in range(args.max_workflows):
        workflow_name = f"{args.basename}_{i}"

        output = get_workflow_status(workflow_name)
        if not output:
            print(f"Could not get status for {workflow_name}")
            continue

        if args.verbose:
            print(f"=== {workflow_name} ===")
            print(output)

        data = parse_status_output(output)
        workflows_queried += 1

        # Sum numeric fields
        for field in NUMERIC_FIELDS:
            if field in data:
                value = parse_numeric_value(data[field])
                if value is not None:
                    totals[field] += value

        # Collect problem types
        if 'problem_types' in data and data['problem_types']:
            for ptype in data['problem_types'].split(','):
                all_problem_types.add(ptype.strip())

    # Print summary
    print(f"\n{'='*50}")
    print(f"SUMMARY ({workflows_queried} workflows)")
    print('='*50)

    for field in NUMERIC_FIELDS:
        value = totals[field]
        # Format large numbers with commas
        print(f"{field:25} = {value:,}")

    if all_problem_types:
        print(f"{'problem_types':25} = {','.join(sorted(all_problem_types))}")


if __name__ == '__main__':
    main()
