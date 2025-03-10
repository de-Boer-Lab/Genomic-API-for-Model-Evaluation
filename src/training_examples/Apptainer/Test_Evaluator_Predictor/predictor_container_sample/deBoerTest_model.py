import socket
import json
import numpy as np
import random
import base64


## model specific checks that cause a "prediction_request_failed" error
def check_seqs_specifications(sequences, json_return_error_model):
    max_length = 2000
    for sequence in sequences:
        value = sequences[sequence]
        key = sequence

        if len(value) > 2000:
            json_return_error_model['prediction_request_failed'].append("length of a sequence in " + key + " is greater than 2000")
        if "N" in value:
            json_return_error_model['prediction_request_failed'].append("sequence in " + key + " has an invalid character present")
    return(json_return_error_model)SB

def fake_model_point(sequences, json_dict):
    predictions = {}

    for sequence in sequences:
        value = sequences[sequence]
        key = sequence
        predictions[key] = random.randint(0, 1)
    json_dict['predictions'] = predictions
    return(json_dict)

def fake_model_track(sequences, json_dict):
    predictions = {}

    for sequence in sequences[0]:
        value = sequences[sequence]
        key = sequence
        predictions[key] = list(np.random.randint(low = 0,high=50,size=100))

    json_dict['predictions'] = predictions

    return(json_dict)

def fake_model_interaction_matrix(sequences, json_dict):
    predictions = {}

    for sequence in sequences[0]:
        value = sequences[sequence]
        key = sequence
        interaction_matrix = np.random.randint(10, size=(3, 3))
        predictions[key] = base64.b64encode(np.random.randint(10, size=(3, 3)))

    json_dict['predictions'] = [predictions]
    return(json_dict)
