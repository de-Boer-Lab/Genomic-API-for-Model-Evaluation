# correlation_calculator.py
import pandas as pd
from scipy.stats import pearsonr
import numpy as np

# Get this function to only take df of measured values for each task rather than the entire measurement file

def calculate_task_correlation(
    measured_df: pd.DataFrame,
    single_task_data: dict,
    measured_value_column: str,
    seq_id_column: str,
    chromosome_column: str = None,
    chromosomes_to_filter: list = None
    ):
    
    """
    Calculates Pearson r and extracts metadata for single prediction task,
    usign pre-loaded measured_df and a single task data dictionary.
    
    Args:
        measured_df (pd.DataFrame): The dataframe of measured values loaded once by the caller (Evaluator __main__ block).
        single_task_data (dict): The dictionary with predictions and metadata for a single task from the `prediction_tasks` 
                                 list of a predictions JSON.
        measured_value_column (str): Column name in measured_df for correlation.
        id_column (str): Common identifier for sequences column (IDs or sequences).
        chromosome_column (str, optional): Chromosome column name in measured_df. Defaults to 'None'.
        chromosomes_to_filter (list, optional): List of chromosomes for filtering. Defaults to 'None'. 

    Returns:
        correlation_details (dict): Dictionary containing 'pearson_r' (float or None) and task metadata ("task_name", "task_type", "cell_type_actual")
    """
    
    # Extract metadata from single task data
    print(f"\n--- Extracting prediction_task metadata ---")
    task_name = single_task_data.get("name")
    task_type_actual = single_task_data.get("type_actual")
    cell_type_actual = single_task_data.get("cell_type_actual")
    predictions_dict =  single_task_data.get("predictions")
    
    pearson_r_value = None # If there's an error, default to None
    
    # --- Data Validation and processing ---
    print("\n--- Validating data ---")
    if not isinstance(predictions_dict, dict):
        print(f"WARNING: 'predictions' in task: '{task_name}'\
            \nCell type: {cell_type_actual}\
            \nType: {task_type_actual}\
            \nis not a valid dictionary or is missing.")
    elif not predictions_dict:
        print(f"WARNING: 'predictions' dictionary is empty in task: '{task_name}'\
            \nCell type: {cell_type_actual}\
            \nType: {task_type_actual}")
    elif seq_id_column not in measured_df.columns:
        print(f"ERROR: Sequence ID column '{seq_id_column}' not found in measured_df.\
            \nCannot merge for task: {task_name}.")
    elif measured_value_column not in measured_df.columns:
         print(f"ERROR: Measured value column '{measured_value_column}'\
             \nfor cell type '{cell_type_actual}' not found in measured_df.\
             \nCannot correlate task: '{task_name}'.") 
         # NOTE: More checks can be added.
    else:
        # Proceed with calculation if checks pass
        # Create DataFrame from Predictions
        print("\n--- Creating predictions_df ---")
        predictions_df = pd.DataFrame(list(predictions_dict.items()), columns=[seq_id_column, 'Predicted_Value'])
        predictions_df['Predicted_Value'] = predictions_df['Predicted_Value'].apply(
            lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x
            )
        
        # Now select only the necessary columns of measured_df
        columns_to_keep = [seq_id_column, measured_value_column]
        if (chromosome_column and chromosomes_to_filter and (chromosome_column in measured_df)):
            if chromosome_column not in columns_to_keep:
                columns_to_keep.append(chromosome_column)
                
        measured_df_subset = measured_df[columns_to_keep].copy()
        merged_df = pd.merge(measured_df_subset, predictions_df, on=seq_id_column, how="left")
        
        # Filter by chromosome (if needed)
        if (chromosomes_to_filter and chromosome_column and (chromosome_column in merged_df.columns)):
            print(f"Filtering chromosomes: {chromosomes_to_filter}...")
            merged_df[chromosome_column] = merged_df[chromosome_column].astype(str)
            # In order to handle None
            str_chromosomes_to_filter = [str(c) for c in chromosomes_to_filter]
            filtered_df = merged_df[merged_df[chromosome_column].isin(str_chromosomes_to_filter)]
        else:
            print("No chromosomes to filter.")
            filtered_df = merged_df # No chromosome filter
        
        # Columns for correlation calculation
        
        correlation_columns = ['Predicted_Value', measured_value_column]
        
        # Drop any rows that have NaNs for either column
        final_df = filtered_df.dropna(subset=correlation_columns)
        
        # Sanitize the final_df in case values are non-numeric
        if not final_df.empty:
            print("Sanitizing final_df in case values are non-numeric for correlation...")
            final_df.loc[:, 'Predicted_Value'] = pd.to_numeric(final_df['Predicted_Value'], errors='coerce')
            final_df.loc[:, measured_value_column] = pd.to_numeric(final_df[measured_value_column], errors='coerce')
            final_df = final_df.dropna(subset=correlation_columns) # Drop NaNs after converting to numeric

            # Calculate pearson r
            try:
                r, _ = pearsonr(final_df['Predicted_Value'], final_df[measured_value_column])
                print(f"Calculated Pearson r for {task_name}: {r}") 
                if np.isnan(r):
                    print(f"WARNING: Pearson r is NaN for task '{task_name}'")
                    pearson_r_value = None
                else:
                    pearson_r_value = float(r)
            except ValueError as e:
                print(f"ValueError during Pearson correlation calculation for task: '{task_name}': {e}")
        else:
            print(f"DataFrame is empty after numeric conversion and NaN drop for task: '{task_name}'")
            
    correlation_details = {
        'task_name': task_name, 
        'task_type': task_type_actual,
        'cell_type_actual': cell_type_actual,
        'pearson_r': pearson_r_value
    }
    return correlation_details
        
if __name__ == '__main__':
    print("--- Testing ---")
    
    dummy_measured_data = {
        'IDs': ['id1', 'id2', 'id3', 'id4', 'id5', 'id6'],
        'chr': ['1', '1', '2', '2', '1', '3'],
        'K562_log2FC': [0.5, 0.8, 1.2, 1.5, 0.6, 2.0],
        'HepG2_log2FC': [0.4, 0.7, 1.1, 1.6, 0.5, 1.9]
    }
    measured_df_test = pd.DataFrame(dummy_measured_data)

    dummy_task_k562 = {
        "name": "gosai_mpra_k562_task",
        "type_actual": "expression",
        "cell_type_actual": "K562",
        "predictions": {"id1": [0.45], "id2": [0.85], "id3": [1.1], "id4": [1.3], "id5": [0.55]}
    }
    
    print("\nTesting K562 Task:")
    result = calculate_task_correlation(
        measured_df=measured_df_test, 
        single_task_data=dummy_task_k562,
        measured_value_column='K562_log2FC', 
        seq_id_column='IDs'
    )
    print(f"Test Result K562: {result}")