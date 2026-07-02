'''deBoerTest Model Codebase
This is a "fake model" it will return predictions for any request type and
can be used to test new Evaluators
'''
import tqdm
import random
import numpy as np

from error_checking_functions import PredictionFailedError

def fake_model_point(sequences):
    """
    Takes sequences and returns a dictionary of single prediction values
    """
    try:
        predictions = {}
        # Use tqdm to show progress as we process each sequence.
        for seq_id in tqdm.tqdm(sequences, 
                                desc="Processing sequences (point prediction)",
                                unit="seq"):
            predictions[seq_id] = round(random.randint(0, 1), 5)
        return predictions
    except Exception as e:
        raise PredictionFailedError(f"An unexpected error occurred during fake model point prediction: {e}")

def fake_model_track(sequences):
    """
    Takes sequences and returns a dictionary of prediction tracks (arrays)
    """
    try:
        predictions = {}
        # Iterate over seq_id with a progress bar.
        for seq_id, seq in tqdm.tqdm(sequences.items(),
                                  desc="Processing sequences (track prediction)",
                                  unit="seq"):
            predictions[seq_id] = [float(f"{v: .5g}") for v in np.random.uniform(low=0, high=1, size=len(seq)).tolist()]
        return predictions
    except Exception as e:
        raise PredictionFailedError(f"An unexpected error occurred during fake model track prediction: {e}")
    
def fake_model_interaction_matrix(sequences):
    """
    Takes sequences and returns a dictionary of interaction matrices
    (one square matrix per sequence, as a list of lists).
    """
    try:
        predictions = {}
        # Iterate over seq_id with a progress bar.
        for seq_id, seq in tqdm.tqdm(sequences.items(),
                                desc="Processing sequences (interaction matrix)",
                                unit="seq"):
            interaction_matrix = np.random.randint(10, size=(len(seq), len(seq))).tolist()
            #This is just an example matrix stored as a list of lists, for large scale predictions we suggest encoding via msgpack/msgpack-numpy
            predictions[seq_id] = interaction_matrix
        return predictions
    except Exception as e:
        raise PredictionFailedError(f"An unexpected error occurred during fake model interaction matrix prediction: {e}")
