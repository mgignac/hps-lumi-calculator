#!/usr/bin/env python3
"""
Parse and summarize swif2 status output for multiple workflows.
"""

import argparse
import subprocess
from collections import defaultdict

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
        help='Workflow basename (workflows will be basename_1, basename_2, ...)'
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
    problem_type_counts = defaultdict(int)
    workflows_queried = 0

    # Per-workflow stats for rate calculations
    workflow_stats = []

    for i in range(1, args.max_workflows + 1):
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

        # Track per-workflow stats
        wf_stats = {
            'name': workflow_name,
            'jobs': 0,
            'succeeded': 0,
            'problems': 0,
        }

        # Sum numeric fields
        for field in NUMERIC_FIELDS:
            if field in data:
                value = parse_numeric_value(data[field])
                if value is not None:
                    totals[field] += value
                    if field in wf_stats:
                        wf_stats[field] = value

        workflow_stats.append(wf_stats)

        # Collect and count problem types
        if 'problem_types' in data and data['problem_types']:
            for ptype in data['problem_types'].split(','):
                ptype = ptype.strip()
                if ptype:
                    problem_type_counts[ptype] += 1

    # Print summary
    print(f"\n{'='*50}")
    print(f"SUMMARY ({workflows_queried} workflows)")
    print('='*50)

    for field in NUMERIC_FIELDS:
        value = totals[field]
        # Format large numbers with commas
        print(f"{field:25} = {value:,}")

    if problem_type_counts:
        print(f"\n{'='*50}")
        print("PROBLEM TYPES (count of workflows with each type)")
        print('='*50)
        for ptype in sorted(problem_type_counts.keys()):
            print(f"{ptype:25} = {problem_type_counts[ptype]:,}")

    # Print success/failure rates
    print(f"\n{'='*50}")
    print("SUCCESS/FAILURE RATES")
    print('='*50)

    # Overall rates
    total_jobs = totals['jobs']
    total_succeeded = totals['succeeded']
    total_problems = totals['problems']

    if total_jobs > 0:
        total_completed = total_succeeded + total_problems
        overall_completion_rate = (total_completed / total_jobs) * 100
        overall_success_rate = (total_succeeded / total_jobs) * 100
        overall_failure_rate = (total_problems / total_jobs) * 100
        print(f"\nOverall ({total_jobs:,} jobs):")
        print(f"  Completion:   {overall_completion_rate:.2f}% ({total_completed:,}/{total_jobs:,})")
        print(f"  Success rate: {overall_success_rate:.2f}% ({total_succeeded:,}/{total_jobs:,})")
        print(f"  Failure rate: {overall_failure_rate:.2f}% ({total_problems:,}/{total_jobs:,})")
    else:
        print("\nOverall: No jobs found")

    # Per-workflow rates
    print(f"\nPer-workflow rates:")
    print(f"{'Workflow':<30} {'Jobs':>10} {'Complete%':>11} {'Success%':>10} {'Failure%':>10}")
    print('-' * 73)

    for wf in workflow_stats:
        jobs = wf['jobs']
        if jobs > 0:
            completed = wf['succeeded'] + wf['problems']
            completion_rate = (completed / jobs) * 100
            success_rate = (wf['succeeded'] / jobs) * 100
            failure_rate = (wf['problems'] / jobs) * 100
            print(f"{wf['name']:<30} {jobs:>10,} {completion_rate:>10.2f}% {success_rate:>9.2f}% {failure_rate:>9.2f}%")
        else:
            print(f"{wf['name']:<30} {jobs:>10,} {'N/A':>11} {'N/A':>10} {'N/A':>10}")


if __name__ == '__main__':
    main()
