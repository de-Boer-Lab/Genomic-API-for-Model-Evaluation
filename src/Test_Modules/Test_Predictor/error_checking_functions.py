'''Error Classes and Error Checking Functions for Predictor'''

import numpy as np

# ERROR CLASSES
# Error classes can be added here to easily keep track of error status codes

class APIError(Exception):
    """
    Base class for all custom API errors.
    This allows us to catch all our custom errors with a single handler.
    """
    def __init__(self, message, status_code, error_key):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_key = error_key
        
class BadRequestError(APIError):
    """
    For errors where the request is unacceptable (e.g. malformed JSON, missing keys).
    Corresponds to the 'bad_prediction_request' key.
    """
    def __init__(self, message="The request was unacceptable."):
        super().__init__(message, status_code=400, error_key='bad_prediction_request')

class PredictionFailedError(APIError):
    """
    For errors where the request was valid, but the model could not complete the prediction.
    Corresponds to the 'prediction_request_failed' key.
    """
    def __init__(self, message="The model prediction was incomplete."):
        super().__init__(message, status_code=422, error_key='prediction_request_failed')

class ServerError(APIError):
    """
    For backend issues (e.g. memory errors, unexpected crashes).
    Corresponds to the 'server_error' key.
    """
    def __init__(self, message="An unexpected issue occurred on the server."):
        super().__init__(message, status_code=500, error_key='server_error')

# ------------------------

# ERROR CHECKING FUNCTIONS

# Model-specific check: "prediction_request_failed" error
def check_seqs_specifications(sequences, json_return_error_model):
    """
    Check that sequences conform to model specs.
    - Valid bases: "A", "T", "C", "G", "N"
    - No empty sequences
    """
    # max_length = int(5e9)
    valid_bases = {"A", "T", "C", "G", "N"}
    for seq_id, seq in sequences.items():

        if not seq:
            json_return_error_model["prediction_request_failed"].append(f"sequence '{seq_id}' is empty")
        
        invalid_chars = set(seq.upper()) - valid_bases
        if invalid_chars:
            json_return_error_model['prediction_request_failed'].append(f"sequence '{seq_id}' has invalid character(s): {invalid_chars}")
    
    return(json_return_error_model)

# check the the mandatory_keys exist in the .json files
def check_mandatory_keys(evaluator_keys, json_return_error):

    mandatory_keys = ["readout", "prediction_tasks", "sequences"] # NOTE: "request" removed
    evaluator_keys_set = set(evaluator_keys)
    missing = list(sorted(set(mandatory_keys) - evaluator_keys_set))
    if missing:
        json_return_error['bad_prediction_request'].append(
            f"The following mandatory top-level keys are missing from the JSON: {', '.join(missing)}"
        )
    return json_return_error

def check_key_values_readout(readout_value, json_return_error):
    readout_options = ["point","track", "interaction_matrix"]

    if readout_value not in readout_options:

        json_return_error['bad_prediction_request'].append("readout requested is not recognized. Please choose from ['point', 'track', 'interaction_matrix']")
    else:
        pass
    if isinstance(readout_value, str) == True:
        pass
    else:
        json_return_error['bad_prediction_request'].append("'readout' value should be a string")

    if type(readout_value) == list:
        json_return_error['bad_prediction_request'].append("'readout' should only have 1 value")

    else:
        pass
    return(json_return_error)

def check_prediction_task_mandatory_keys(prediction_tasks, json_return_error):
 
    for index, prediction_task in enumerate(prediction_tasks):
        mandatory_keys = ["name", "type", "cell_type", "species"]
        # print(index, prediction_task)
        task_keys = set(prediction_task.keys())
        # print(task_keys)
        missing = list(sorted(set(mandatory_keys) - task_keys))
        
        if missing:
            # Get the name, using index as fallback
            task_identifier = prediction_task.get("name", f"at index {index}")
            
            error_msg = (f"Mandatory keys missing from prediction_task '{task_identifier}': "
                         f"{', '.join(missing)}")
            print(error_msg)
            json_return_error['bad_prediction_request'].append(error_msg)
            
    return json_return_error

def check_prediction_task_name(prediction_tasks, json_return_error):

    #loop through object to check each array
    for prediction_task in prediction_tasks:
        if type(prediction_task['name']) == list:
            json_return_error['bad_prediction_request'].append("'name' should only have 1 value")

        else:
            pass
        if isinstance(prediction_task['name'], str) == True:
            pass
        else:
            json_return_error['bad_prediction_request'].append("'name' value should be a string")



    return(json_return_error)



def check_prediction_task_type(prediction_tasks, json_return_error):

    # loop through object to check each array
    for prediction_task in prediction_tasks:
        # print(prediction_task)
        prediction_task_options = ["accessibility", "expression"]
        if type(prediction_task['type']) == list:
            json_return_error['bad_prediction_request'].append("'type' should only have 1 value")

        else:

            if isinstance(prediction_task['type'], str) == True:

                if (prediction_task['type'] in prediction_task_options or
                    prediction_task['type'].startswith(('binding_', 'expression_', 'conformation_'))):
                    pass
                else:
                    json_return_error['bad_prediction_request'].append("prediction type " + str(prediction_task['type']) + " is not recognized")

                pass
            else:
                json_return_error['bad_prediction_request'].append("'type' value should be a string")

    return(json_return_error)


def check_prediction_task_cell_type(prediction_tasks, json_return_error):

    #loop through object to check each array
    for prediction_task in prediction_tasks:
        if type(prediction_task['cell_type']) == list:
            json_return_error['bad_prediction_request'].append("'cell_type' should only have 1 value")

        else:
            if isinstance(prediction_task['cell_type'], str) == True:
                pass
            else:
                json_return_error['bad_prediction_request'].append("'cell_type' value should be a string")

    return(json_return_error)


def check_prediction_task_species(prediction_tasks, json_return_error):

    #loop through object to check each array
    for prediction_task in prediction_tasks:
        if type(prediction_task['species']) == list:
            json_return_error['bad_prediction_request'].append("'species' should only have 1 value")

        else:

            if isinstance(prediction_task['species'], str) == True:
                pass
            else:
                json_return_error['bad_prediction_request'].append("'species' value should be a string")

    return(json_return_error)


def check_prediction_task_scale(prediction_tasks, json_return_error):

    #loop through object to check each array
    for prediction_task in prediction_tasks:
        if 'scale' in prediction_task:
            if type(prediction_task['scale']) == list:
                json_return_error['bad_prediction_request'].append("'scale' should only have 1 value")

            else:

                prediction_scale_options = ["linear", "log"]

                if prediction_task['scale'] not in prediction_scale_options:

                    json_return_error['bad_prediction_request'].append("scale requested is not recognized. Please choose from ['log', 'linear']")
                else:
                    pass
                if isinstance(prediction_task['scale'], str) == True:
                    pass
                else:
                    json_return_error['bad_prediction_request'].append("'scale' value should be a string")
        else:
            pass
    return(json_return_error)

def check_prediction_ranges(prediction_ranges, sequences, json_return_error):
    """
    Checks that prediction_ranges are formatted correctly.
    Now includes checks for positive integers and start <= end.
    """
    for key, value in prediction_ranges.items():
        
        if not isinstance(value, list):
            json_return_error['bad_prediction_request'].append(f"Values for '{key}' in 'prediction_ranges' must be in a list")
            
        if not value:
            continue
        
        if len(value) != 2:
            json_return_error['bad_prediction_request'].append(f"Range array for '{key}' in 'prediction_ranges' must have 2 elements")
        
        if not all(isinstance(num, int) for num in value):
            json_return_error['bad_prediction_request'].append(f"Values in '{key}' in 'prediction_ranges' must be integers")
        
        start = value[0]
        end = value[1]
        
        if start < 0 or end < 0:
            json_return_error['bad_prediction_request'].append(f"Invalid range for '{key}' in 'prediction_ranges': indices must be positive. Received [{start}, {end}]")
            
        if start > end:
            json_return_error['bad_prediction_request'].append(f"Invalid range for '{key}' in 'prediction_ranges': start index ({start}) cannot be greater than end index ({end}). Received [{start}, {end}]")


    return json_return_error

##check that seqids have valid characters
## apparently this is done by default in .json loads
#it works for some but not all

#check that keys in sequences match those in prediction ranges
def check_seq_ids(prediction_ranges, sequences, json_return_error):
    if prediction_ranges.keys() == sequences.keys():
        pass
    else:
        json_return_error['bad_prediction_request'].append("sequence ids in prediction_ranges do not match those in sequences")
    return(json_return_error)


def check_key_values_upstream_flank(upstream_seq, json_return_error):

    if type(upstream_seq) == list:
        json_return_error['bad_prediction_request'].append("'upstream_seq' should only have 1 value")
    else:

        if isinstance(upstream_seq, str) == True:
            pass
        else:
            json_return_error['bad_prediction_request'].append("'upstream_seq' value should be a string")

    return(json_return_error)



def check_key_values_downstream_flank(downstream_seq, json_return_error):
    if type(downstream_seq) == list:
        json_return_error['bad_prediction_request'].append("'downstream_seq' should only have 1 value")
    else:

        if isinstance(downstream_seq, str) == True:
            pass
        else:
            json_return_error['bad_prediction_request'].append("'downstream_seq' value should be a string")

    return(json_return_error)