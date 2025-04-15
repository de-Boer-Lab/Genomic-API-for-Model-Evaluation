# borzoiAPI_predictions.py
import os
import sys
import json
import tqdm
import numpy as np
import pandas as pd
from collections import defaultdict

BORZOI_SCRIPT_DIR = os.path.dirname(__file__)

sys.path.append(BORZOI_SCRIPT_DIR)
from borzoi_utils import *

sys.path.append(f"{BORZOI_SCRIPT_DIR}/baskerville/src")
from baskerville import seqnn
from baskerville import dna

sys.path.append(f"{BORZOI_SCRIPT_DIR}/borzoi/examples")
from borzoi_helpers import *

params_file = f"{BORZOI_SCRIPT_DIR}/borzoi/examples/params_pred.json"
targets_file = f"{BORZOI_SCRIPT_DIR}/borzoi/examples/targets_human.txt"

utils_path = f"{BORZOI_SCRIPT_DIR}/simplify_targets"
simplified_targets_file = f"{utils_path}/borzoi_human_targets_simplified.txt"
# Simplified targets file was created to easily map the requested type and cell type
# to the right tracks. The python script for that is in `simplify_targets/` directory.

saved_models_path = f"{BORZOI_SCRIPT_DIR}/borzoi/examples/saved_models"

# Sequence parameters
seq_len = 524288
n_folds = 4  # Use all 4 model folds. Can vary between 1 and 4 (inclusive).
rc = True    # Reverse-complement predictions

# 1. Load model parameters
def load_model_parameters():
    with open(params_file) as params_open:
        params = json.load(params_open)
    return params['model'], params['train']

# 2. Load target files
def load_targets():
    targets_df = pd.read_csv(targets_file, index_col=0, sep='\t')
    simplified_targets_df = pd.read_csv(simplified_targets_file, index_col=0, sep='\t')
    return targets_df, simplified_targets_df

# 3. Not filtering target index and slice_pair (Same as OG Borzoi codebase)
def load_target_index():
    targets_df, _ = load_targets()
    target_index = targets_df.index
    
    # Load strand pairing for reverse complement predictions
    if rc:
        strand_pair = targets_df.strand_pair
        target_slice_dict = {ix: i for i, ix in enumerate(target_index.values.tolist())}
        slice_pair = np.array([
            target_slice_dict[ix] if ix in target_slice_dict else ix for ix in strand_pair.values.tolist()
        ], dtype='int32')
        
    return target_index, slice_pair

# 4. Initialize model ensemble
def initilize_model_ensemble(target_index, slice_pair, params_model):
    models = []
    for fold_ix in range(n_folds) :

        model_file = f"{saved_models_path}/f3c{str(fold_ix)}/train/model0_best.h5"

        seqnn_model = seqnn.SeqNN(params_model)
        seqnn_model.restore(model_file, 0)
        seqnn_model.build_slice(target_index)
        if rc:
            seqnn_model.strand_pair.append(slice_pair)
        #seqnn_model.build_ensemble(rc, '0')
        seqnn_model.build_ensemble(rc, [0])
        models.append(seqnn_model)
        
    return models

# 5. Prediction Function -- Runs Once and Filters Predictions Based on Request Type
def predict_borzoi(sequences, request_tasks, is_point_readout=False):
    """
    Runs the Borzoi model ONCE on provided sequences across all tracks and 
    filters relevant averages track predictions based on request.
    Args:
        sequences (dict): A dictionary of key-value pairs (strings) {sequence_id: sequence}.
        request_tasks (set): A set of strings (request_type, cell_type) pairs 
                             to determine required tracks.
        is_point_readout (bool): If True, average 16352 bin predictions to single value.
    
    Returns:
        task_predictions (dict): 
            A dictionary of key-value pairs (strings) 
            {task_key: {sequence_id, [16352 predictions, averaged across desired tracks]}}
            
            For "all_tracks" tasks, predictions are not averaged over tracks
            and the full prediction matrix is returned (shape [1, 16352, 7611 tracks]).
    
    """
    print("Running Borzoi Model Predictions on ALL tracks before filtering...")
    
    # Load parameters, target indices, and models
    params_model, _ = load_model_parameters()
    target_index, slice_pair = load_target_index()
    models = initilize_model_ensemble(target_index, slice_pair, params_model)
    
    # 5.1. Collect all required track indices
    print("Collecting track indices for required tasks...")
    task_to_indices = {} # Dictionary to store required track indices from each task
    # Example: {('expression', 'H1'): [1, 3], 
    #           ('accessibility', 'K562'): [2],
    #           ('expression_pol2', 'H1'): [1, 3]} (fallback to RNA:H1, 
    #                                               since there are no CAGE:H1 tracks)
    
    track_to_tasks = defaultdict(set) # Maps each track index to a set of tasks that require it.
                                      # This prevents predicting on the same track twice.
    # Example: {1: {('expression', 'H1'), ('expression_pol2', 'H1')},  # Track 1 needed by both expression tasks
    #           3: {('expression', 'H1'), ('expression_pol2', 'H1')},  # Track 3 needed by both expression tasks
    #           2: {('accessibility', 'K562')}}  # Track 2 needed only by accessibility task
    
    unique_track_indices = set() # Stores all the unique tracks needed for prediction
                                 # ensuring we only process relevant tracks once!
    # Example: [1, 2, 3]
    
    for request_type, cell_type in request_tasks:
        print(f"Performing track selection for {request_type} and {cell_type}...")
        # Get track indices of desired tracks for filtering predictions
        targets_df, simplified_targets_df = load_targets()
        filtered_tracks = filter_evaluator_request(simplified_targets_df,
                                                request_type, cell_type)
        track_indices = filtered_tracks.index.tolist()
    
        if not track_indices:
            print(f"No matching tracks found for {request_type} and {cell_type}. Skipping...")
            continue
        # Avoid printing a huge list for "all_tracks" requests:
        if request_type.lower() == "all_tracks":
            print(f"Using all {len(track_indices)} track indices for ({request_type}, {cell_type}).")
        else:
            print(f"Using Track Indices for ({request_type}, {cell_type}): {track_indices}")
        task_to_indices[(request_type, cell_type)] = track_indices
        
        for index in track_indices:
            track_to_tasks[index].add((request_type, cell_type)) # Mapping track to tasks
            
        unique_track_indices.update(track_indices)
        
    # Convert to sorted list to maintain order -- easy to test
    unique_track_indices = sorted(list(unique_track_indices))
    
    if not unique_track_indices:
        print("No valid track indices found for any tasks.")
        return {}
    
    # Check if any request is an all_tracks request
    if any(rt.lower() == "all_tracks" for rt, _ in request_tasks):
        print(f"Unique required track indices for this task: ALL {len(unique_track_indices)} tracks.")
    else:
        print(f"Unique required track indices for all tasks: {unique_track_indices}")
    
    # 5.2. Process each sequence and run prediction
    #    - Iterate over sequences and run model prediction only for the required tracks
    print("Processing sequences and storing predictions only for required tracks...")
    task_predictions = {task: {} for task in task_to_indices}
    
    # Process each sequence
    for seq_id, sequence in tqdm.tqdm(sequences.items(),
                                      desc="Predictions in progress", 
                                      unit="sequence",
                                      total=len(sequences),
                                      dynamic_ncols=True):
        print(f"Predicting on sequence ID: {seq_id} 🧬")
        # Pad and encode sequence
        encoded_seq = dna.dna_1hot(seq=sequence, seq_len=seq_len)
        print(f"Shape of encoded sequence before predict_tracks: {encoded_seq.shape}")
        
        # Run model prediction once for all required tracks
        raw_predictions = predict_tracks(models, encoded_seq)[:, :, :, unique_track_indices]
        print(f"Shape of raw predictions: {raw_predictions.shape}")
        
        # Average across model folds to reduce (1, n_folds, 16352, num_tracks) -> (1, 16352, num_tracks)
        fold_averaged_predictions = np.mean(raw_predictions, axis=1)
        print(f"Shape of predictions after averaging model folds: {fold_averaged_predictions.shape}")
        
        # Now assign filtered predictions to each task to be averaged
        for task_key, indices in task_to_indices.items():
            # Extract relevant track predictions per task
            # Special case: for "all_tracks" request, return full predictions without averaging over tracks
            if task_key[0].lower() == "all_tracks":
                print(f"Assigning prediction for tasks: {task_key} (All tracks: [1, {len(indices)}])")
                task_predictions[task_key][seq_id] = np.vectorize(lambda x: float(f"{x:.7f}"))(fold_averaged_predictions).squeeze().tolist()
            else:
                print(f"Assigning prediction for tasks: {task_key} (Tracks: {indices})")
                selected_tracks = fold_averaged_predictions[:, :, 
                                [unique_track_indices.index(idx) for idx in indices]]
                # Average duplicate tracks per task
                print(f"Averaging duplicate track predictions for task {task_key} (Tracks: {indices})")
                avg_prediction = np.mean(selected_tracks, axis=-1, keepdims=True)
                
                if is_point_readout:
                    # "point" readout: Average across 16352 bins to a single value per sequence
                    print(f"Generating point readout for task: {task_key}")
                    point_prediction = np.mean(avg_prediction, axis=1, keepdims=True)
                    task_predictions[task_key][seq_id] = np.vectorize(lambda x: float(f"{x:.7f}"))(point_prediction).squeeze().tolist()
                else:
                    # "track" readout: Return full 16352 bin predictions
                    # Store predictions in task-specific dictionary
                    task_predictions[task_key][seq_id] = np.vectorize(lambda x: float(f"{x:.7f}"))(avg_prediction).squeeze().tolist()
    
    return task_predictions
