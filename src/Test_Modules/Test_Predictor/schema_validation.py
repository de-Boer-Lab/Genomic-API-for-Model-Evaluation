'''Validation and Preprocessing of Payload'''
import tqdm
from error_checking_functions import *

def validate_request_payload(payload):
    """
    Performs all validation checks on the incoming request payload.
    Returns a dictionary of errors. If the dictionary is empty, validation passed.
    """
    errors = {'bad_prediction_request': []}
    
    # First confirm all mandatory keys are present
    errors = check_mandatory_keys(payload.keys(), errors)
    if any(errors.values()):
        flagged_errors = [msg for sublist in errors.values() for msg in sublist]
        raise BadRequestError(flagged_errors)
    
    # Check for mandatory keys inside each task object.
    errors = check_prediction_task_mandatory_keys(payload['prediction_tasks'], errors)
    if any(errors.values()):
        # Fail immediately if any task is missing keys, before we try to access them.
        flagged_errors = [msg for sublist in errors.values() for msg in sublist]
        raise BadRequestError(flagged_errors)
    
    # Perform all other validation checks
    errors = check_key_values_readout(payload['readout'], errors)
    errors = check_prediction_task_name(payload['prediction_tasks'], errors)
    errors = check_prediction_task_type(payload['prediction_tasks'], errors)
    errors = check_prediction_task_cell_type(payload['prediction_tasks'], errors)
    errors = check_prediction_task_species(payload['prediction_tasks'], errors)
    errors = check_prediction_task_scale(payload['prediction_tasks'], errors)

    if 'prediction_ranges' in payload:
        errors = check_seq_ids(payload['prediction_ranges'], payload['sequences'], errors)
        errors = check_prediction_ranges(payload['prediction_ranges'], payload['sequences'], errors)

    if 'upstream_seq' in payload:
        errors = check_key_values_upstream_flank(payload['upstream_seq'], errors)
    if 'downstream_seq' in payload:
        errors = check_key_values_downstream_flank(payload['downstream_seq'], errors)

    if any(errors.values()):
        flagged_errors = [msg for sublist in errors.values() for msg in sublist]
        raise BadRequestError(flagged_errors)

def preprocess_data(payload):
    """
    Handles data preprocessing, like applying flanking sequences, prediction ranges,
    and checking sequence specs.
    
    Completes model-specific error checking.

    Returns processed sequences or raises a PredictionFailedError.
    """

    # Model-specific error checking: Readout type check
    readout_type = payload['readout']
    if not readout_type in ["point", "track", "interaction_matrix"]:
        raise BadRequestError(f"Test Predictor cannot process '{readout_type}' readout type.")

    sequences = payload.get('sequences', {})

    # Model-specific: Append flanking sequences if present
    if 'upstream_seq' in payload or 'downstream_seq' in payload:
        upstream_seq = payload.get('upstream_seq', "")
        downstream_seq = payload.get('downstream_seq', "")
        if upstream_seq or downstream_seq:
            print(
                f"Applying flanking:\
                    \n+{len(upstream_seq)} bases upstream,\
                    \n+{len(downstream_seq)} bases downstream"
                    )
            for seq_id, sequence in tqdm.tqdm(
                sequences.items(),
                desc="Flanking sequences", 
                unit="sequence",
                total=len(sequences),
                dynamic_ncols=True
            ):
                flanked = f"{upstream_seq}{sequence}{downstream_seq}"
                sequences[seq_id] = flanked

    # Check that the final sequences meet model specifications.
    # Since this is model-specific, it utilizes `PredictionFailedError`.
    errors = {'prediction_request_failed': []}
    errors = check_seqs_specifications(sequences, errors)

    #Check prediction ranges
    if 'prediction_ranges' in payload:
        for seq_id, pr in payload['prediction_ranges'].items():
            if pr: # Only process non-empty ranges
                start, end = pr

                if start >= len(sequences[seq_id]) or end >= len(sequences[seq_id]):
                    err_msg = f"Invalid range for '{seq_id}': index is out of bounds. The maximum valid index for a sequence of length {len(sequences[seq_id])} is {len(sequences[seq_id]) - 1}."
                    errors['prediction_request_failed'].append(err_msg)

    if any(errors.values()):
        flagged_errors = [msg for sublist in errors.values() for msg in sublist]
        raise PredictionFailedError(flagged_errors)

    # Apply prediction_ranges if provided
    if 'prediction_ranges' in payload:
        for seq_id, pr in payload['prediction_ranges'].items():
            if pr: # Only process non-empty ranges
                start, end = pr
                # Slice the sequence. `prediction_range` is start, end inclusive
                sequences[seq_id] = sequences[seq_id][start:end+1]
                print(f"Sequence '{seq_id}' trimmed to prediction range [{start}, {end}].")

    
    return sequences