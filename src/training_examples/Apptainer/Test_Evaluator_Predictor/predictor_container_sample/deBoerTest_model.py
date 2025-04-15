import numpy as np
import random
import base64
import tqdm


## model specific checks that cause a "prediction_request_failed" error
def check_seqs_specifications(sequences, json_return_error_model):
    max_length = 400000
    for sequence in sequences:
        value = sequences[sequence]
        key = sequence

        if len(value) > max_length:
            json_return_error_model['prediction_request_failed'].append(
                f"length of a sequence in {key} is greater than {max_length} bases"
                )
        if "N" in value:
            json_return_error_model['prediction_request_failed'].append(
                f"sequence in {key} has an invalid character present: N"
                )
    return(json_return_error_model)

def fake_model_point(sequences, json_dict):
    predictions = {}
    # Use tqdm to show progress as we process each sequence.
    for sequence in tqdm.tqdm(sequences, desc="Processing sequences (point prediction)", unit="seq"):
        predictions[sequence] = random.randint(0, 1)
    json_dict['predictions'] = predictions
    return json_dict

def fake_model_track(sequences, json_dict):
    predictions = {}
    # Iterate over sequences with a progress bar.
    for sequence in tqdm.tqdm(sequences,
                              desc="Processing sequences (track prediction)",
                              unit="seq"):
        predictions[sequence] = list(np.random.randint(low=0, high=50, size=100))
    json_dict['predictions'] = predictions
    return json_dict

def fake_model_interaction_matrix(sequences, json_dict):
    predictions = {}
    # Iterate over sequences with a progress bar.
    for sequence in tqdm.tqdm(sequences,
                              desc="Processing sequences (interaction matrix)",
                              unit="seq"):
        interaction_matrix = np.random.randint(10, size=(3, 3))
        # Convert the matrix to bytes then to a base64-encoded string.
        predictions[sequence] = base64.b64encode(interaction_matrix.tobytes()).decode('utf-8')
    json_dict['predictions'] = [predictions]
    return json_dict
