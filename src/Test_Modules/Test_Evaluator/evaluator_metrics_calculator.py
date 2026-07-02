'''Calculate and save the final evaluation metrics.'''

# NOTE: Every evaluator will do this slightly differently depending on how the data is presented.
# This is the FAKE/test evaluator: it does not compute real correlations, it emits placeholder
# values so the end-to-end pipeline (request -> predict -> response -> metrics file) can be tested.
# Output is written per the GAME Evaluator Output File Specification, matching the Agarwal evaluator.

import os
import sys
import json
import pandas as pd
import numpy as np
import itertools
from datetime import datetime, timezone

from config import EVALUATOR_NAME, EVALUATOR_INPUT_PATH

# Canonical column order from the Evaluator Output File Specification.
# All metric rows (per-task correlation AND cell-type specificity) share these columns
# and live in the same file, distinguished by the `description` column.
SCHEMA_COLUMNS = [
    "evaluator_name",
    "description",
    "predictor_name",
    "time_stamp",
    "metric",
    "value",
    "prediction_task(s)_data",
]


def _utc_timestamp():
    """UTC timestamp in the schema-mandated YYYYMMDD-HHMMSS.f format (e.g. 20260407-212607.595087)."""
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S.%f")


def _save_df_to_csv(df, filepath):
    """
    Appends a DataFrame to a CSV file, adding a header if the file is new.
    """
    if df.empty:
        print(f"No metrics to save for {os.path.basename(filepath)}. Skipping.")
        return

    try:
        file_exists = os.path.isfile(filepath)
        df.to_csv(filepath, mode='a', sep='\t', header=(not file_exists), index=False)
        print(f"DEBUG: Metrics file '{filepath}' exists: {file_exists}")
        if file_exists:
            print(f"Appended metrics to {filepath}")
        else:
            print(f"Created new metrics file {filepath}")
    except IOError as e:
        print(f"\nError: Could not save metrics to {filepath}. {e}", file=sys.stderr)


def _calculate_fake_correlations(task_results, predictor_name):
    """Calculates fake Pearson R correlation for each task."""
    all_task_correlation_results = []

    # FIX: iterate by unique task id (the dict key). The per-task display label
    # (cell type) is stored in results["label"] and used only for `description`.
    for task_id, results in task_results.items():
        # Get the fake score (NaN if invalid, random number if valid)
        fake_pearson_r = np.random.uniform(0.75, 0.99) if results["is_valid"] else "NaN"

        all_task_correlation_results.append({
            "evaluator_name": EVALUATOR_NAME,
            "description": f"de Boer Test Evaluator ({results['label']})",
            "predictor_name": predictor_name,
            "time_stamp": _utc_timestamp(),
            "metric": "pearson_r",
            "value": str(fake_pearson_r),
            # Serialized list-of-dicts (metadata only, predictions stripped out).
            "prediction_task(s)_data": str([results["metadata_no_preds"]]),
        })
    return all_task_correlation_results


def _calculate_fake_specificity(task_results, predictor_name):
    """Calculates fake cell-type specificity scores."""
    # FIX: pair over unique task ids (the dict keys), not cell types, so tasks that
    # share a cell type are no longer collapsed before pairing.
    all_task_ids = list(task_results.keys())
    specificity_results = []

    if len(all_task_ids) < 2:
        print("Not enough unique tasks (< 2) for specificity calculation. Skipping.")
        return specificity_results  # Return empty list

    # Create all unique pairs of tasks
    task_id_pairs = list(itertools.combinations(all_task_ids, 2))

    for id_1, id_2 in task_id_pairs:
        # Check if BOTH tasks in the pair are valid
        is_pair_valid = task_results[id_1]["is_valid"] and task_results[id_2]["is_valid"]

        # Get the fake score (NaN if invalid, random number if valid)
        fake_specificity_score = np.random.uniform(-1, 1) if is_pair_valid else "NaN"

        # Two-task metadata: each serialized as a list-of-dicts, joined by " - "
        # (same single-task format on each side, per the schema).
        meta_1 = str([task_results[id_1]["metadata_no_preds"]])
        meta_2 = str([task_results[id_2]["metadata_no_preds"]])

        specificity_results.append({
            "evaluator_name": EVALUATOR_NAME,
            # FIX: describe the pair with cell-type labels, but the pairing is over unique ids.
            "description": f"de Boer Test Evaluator ({task_results[id_1]['label']} - {task_results[id_2]['label']})",
            "predictor_name": predictor_name,
            "time_stamp": _utc_timestamp(),
            "metric": "specificity_pearson_r",
            "value": str(fake_specificity_score),
            "prediction_task(s)_data": f"{meta_1} - {meta_2}",
        })

    return specificity_results


def calculate_and_save_metrics(predictions_data, output_dir):
    """
    Calculates custom evaluation metrics and saves them to a single CSV file.
    This is the primary function to customize for a new evaluator.
    """
    print("----- Starting Fake Evaluation Calculation and Saving as CSV -----")

    # Load measured data
    try:
        print(f"Using measured data from: {EVALUATOR_INPUT_PATH}")
        with open(EVALUATOR_INPUT_PATH, 'r') as file:
            input_data = json.load(file)
        number_of_sequences = len(input_data["sequences"])
        print(f"Found {number_of_sequences} sequences in measured data for comparison.")

    except Exception as e:
        print(f"FATAL: Could not load measured data from {EVALUATOR_INPUT_PATH} to get sequence count. {e}", file=sys.stderr)
        return

    # Single output file per the Evaluator Output File Specification.
    summary_filepath = os.path.join(output_dir, f"evaluation_summary_{EVALUATOR_NAME}.csv")

    try:
        predictor_name = predictions_data.get("predictor_name", "Unknown")
        all_tasks = predictions_data.get("prediction_tasks", [])

        if not all_tasks or any(not task.get("predictions") for task in all_tasks):
            print("WARNING: 'prediction_tasks' key missing, empty, or one of the tasks has empty predictions.")
            return

        # Pre-computation: Validate all tasks *once*
        # This map stores whether each task is valid and its metadata
        task_results = {}
        for task in all_tasks:
            if not isinstance(task, dict):
                continue

            # FIX: key by the task's unique `name`. The Predictor API guarantees `name`
            # is unique per task; `cell_type_requested` is required but NOT unique, so the
            # previous key (cell_type_requested) silently overwrote tasks that shared a cell
            # type (e.g. expression and accessibility both in K562), dropping rows and pairs.
            task_id = task.get("name", "unknown")
            label = task.get("cell_type_requested", task_id)  # human-readable label for `description` only
            # FIX: default to {} (not []) so the "error" membership test is unambiguously a
            # dict-key check, matching the Predictor schema where `predictions` is an object.
            predictions = task.get("predictions", {})
            task_valid = True  # Assume valid

            if "error" in predictions:
                print(f"- Task '{task_id}' (Cell: {label}): Found 'error' in predictions. Marking as invalid.")
                task_valid = False

            task_results[task_id] = {
                "is_valid": task_valid,
                "label": label,  # FIX: store the cell-type label for descriptions
                "metadata_no_preds": {k: v for k, v in task.items() if k != "predictions"},
            }

        # Calculate Metrics
        correlation_results = _calculate_fake_correlations(task_results, predictor_name)
        specificity_results = _calculate_fake_specificity(task_results, predictor_name)

        # Combine into a single DataFrame so both metric types share one header / file.
        all_results = correlation_results + specificity_results
        if not all_results:
            print("No metric rows generated. Nothing to save.")
            return

        summary_df = pd.DataFrame(all_results)
        # Enforce schema column order (reindex is a no-op on order if all present).
        summary_df = summary_df.reindex(columns=SCHEMA_COLUMNS)

        # Save results to a single CSV
        _save_df_to_csv(summary_df, summary_filepath)

    except Exception as e:
        print(f"An unexpected error occurred during evaluation calculations: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()