'''Calculate and save the final evaluation metrics.'''

# NOTE: Every evaluator will do this slightly differently depending on how the data is presented

import os
import sys
import json
import pandas as pd
import numpy as np
import itertools
from datetime import datetime, timezone

from config import EVALUATOR_NAME, EVALUATOR_INPUT_PATH

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
    
    for cell_type, results in task_results.items():
        # Get the fake score (NaN if invalid, random number if valid)
        fake_pearson_r = np.random.uniform(0.75, 0.99) if results["is_valid"] else "NaN"
        
        all_task_correlation_results.append({
            "Evaluator": EVALUATOR_NAME,
            "Description": f"de Boer Test Evaluator ({cell_type})",
            "Predictor_name": predictor_name,
            "Time_stamp": datetime.now(timezone.utc).isoformat(),
            'Metric': 'pearson_r',
            'Value': str(fake_pearson_r),
            'Prediction_task(s)_data': [results["metadata_no_preds"]]
        })
    return all_task_correlation_results

def _calculate_fake_specificity(task_results, predictor_name):
    """Calculates fake cell-type specificity scores."""
    all_cell_types = list(task_results.keys())
    specificity_results = []

    if len(all_cell_types) < 2:
        print("Not enough unique cell types (< 2) for specificity calculation. Skipping.")
        return specificity_results # Return empty list

    # Create all unique pairs of cell types
    cell_type_pairs = list(itertools.combinations(all_cell_types, 2))
    
    for cell_1, cell_2 in cell_type_pairs:
        # Check if BOTH tasks in the pair are valid
        is_pair_valid = task_results[cell_1]["is_valid"] and task_results[cell_2]["is_valid"]
        
        # Get the fake score (NaN if invalid, random number if valid)
        fake_specificity_score = np.random.uniform(-1, 1) if is_pair_valid else "NaN"
        
        specificity_results.append({
            "Evaluator": EVALUATOR_NAME,
            "Description": f"de Boer Test Evaluator ({cell_1} - {cell_2})",
            "Predictor_name": predictor_name,
            "Time_stamp": datetime.now(timezone.utc).isoformat(),
            "Metric": "specificity_pearson_r",
            "Value": str(fake_specificity_score),
            'Prediction_tasks_data': str(task_results[cell_1]['metadata_no_preds']) + " - " + str(task_results[cell_2]['metadata_no_preds'])
        })
        
    return specificity_results

def calculate_and_save_metrics(predictions_data, output_dir):
    """
    Calculates custom evaluation metrics and saves them to CSV files.
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

    # Define output paths
    correlation_filepath = os.path.join(output_dir, f"fake_correlation_summary_{EVALUATOR_NAME}.csv")
    specificity_filepath = os.path.join(output_dir, f"fake_cell_type_specific_expression_{EVALUATOR_NAME}.csv")

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
            if not isinstance(task, dict): continue
            
            task_name = task.get('cell_type_requested', 'unknown')
            predictions = task.get("predictions", [])
            task_valid = True # Assume valid
            
            if "error" in predictions:
                print(f"- Task (Cell: {task_name}): Found 'error' in predictions. Marking as invalid.")
                task_valid = False
            
            task_results[task_name] = {
                "is_valid": task_valid,
                "metadata_no_preds": {k: v for k, v in task.items() if k != "predictions"}
            }

        # Calculate Metrics
        correlation_results = _calculate_fake_correlations(task_results, predictor_name)
        specificity_results = _calculate_fake_specificity(task_results, predictor_name)
            
        # Save results to CSVs (using the new helper)
        _save_df_to_csv(pd.DataFrame(correlation_results), correlation_filepath)
        _save_df_to_csv(pd.DataFrame(specificity_results), specificity_filepath)

    except Exception as e:
        print(f"An unexpected error occurred during evaluation calculations: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()