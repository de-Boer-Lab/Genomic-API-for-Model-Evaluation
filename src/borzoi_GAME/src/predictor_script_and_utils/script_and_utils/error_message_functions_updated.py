#Oct 30, 2024
#Error checking functions
# error_message_functions_updated.py
import socket
import json
import numpy as np
import random
import base64

#check the the mandatory_keys exsist in the .json files
def check_mandatory_keys(evaluator_keys, json_return_error):

    mandatory_keys = ["request", "readout", "prediction_tasks", "sequences"]
    np.in1d(mandatory_keys, evaluator_keys).all()
    missing = list(sorted(set(mandatory_keys) - set(evaluator_keys)))
    print(missing)
    if not missing:
        pass
    else:
        json_return_error['bad_prediction_request'].append(("The following keys are missing from the json: " + ' '.join(missing)))
    return(json_return_error)


#check the task requested is correct
def check_request(request_types, json_return_error):

    request_options = ["predict", "help"]
    if request_types not in request_options:
        json_return_error['bad_prediction_request'].append(("request is not recognized. Please choose from: 'predict','help'"))

    else:
        pass
        #return("task requested exists in the predictor")

    if isinstance(request_types, str) == True:
        pass
    else:
        json_return_error['bad_prediction_request'].append("'request' value should be a string")

    if type(request_types) == list:
        json_return_error['bad_prediction_request'].append("'request' should only have 1 value")
    else:
        pass

    return(json_return_error)

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

    #loop through object to check each array
    for prediction_task in prediction_tasks:
        #first check that the mandatory keys exist
        mandatory_keys = ["name", "type", "cell_type", "species"]
        missing = list(sorted(set(mandatory_keys) - set(prediction_task.keys())))
        if not missing:
            pass
        else:
            json_return_error['bad_prediction_request'].append(("The following keys are missing from prediction_task: " + prediction_task['name'] + ' ' + str(missing)))

    return(json_return_error)


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

    #loop through object to check each array
    for prediction_task in prediction_tasks:
        print(prediction_task)
        prediction_task_options = ["accessibility", "expression", "chromatin_confirmation",
                                   "all_tracks"] # Adding an option for all_tracks here
        if type(prediction_task['type']) == list:
            json_return_error['bad_prediction_request'].append("'type' should only have 1 value")

        else:

            if isinstance(prediction_task['type'], str) == True:

                if prediction_task['type'] in prediction_task_options or prediction_task['type'].startswith('binding_') or prediction_task['type'].startswith('expression_'): # Added expression_
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


### check that prediction_ranges are integers and subarrays are 2 elements each

def check_prediction_ranges(prediction_ranges, json_return_error):
    for key, value in prediction_ranges.items():
        # If value is an empty list, assume full sequence is used and skip further checking.
        if isinstance(value, list) and len(value) == 0:
            continue
        
        # Check that the value is a list
        if not isinstance(value, list):
            json_return_error['bad_prediction_request'].append(
                f"Prediction range for '{key}' should be a list."
            )
            continue

        # Check that exactly two elements are provided
        if len(value) != 2:
            json_return_error['bad_prediction_request'].append(
                f"Prediction range for '{key}' must contain exactly two elements (start and end)."
            )
            continue

        start, end = value

        # Check that both elements are integers
        if not isinstance(start, int) or not isinstance(end, int):
            json_return_error['bad_prediction_request'].append(
                f"Both start and end for prediction range '{key}' must be integers."
            )
            continue

        # Check that indices are non-negative
        if start < 0 or end < 0:
            json_return_error['bad_prediction_request'].append(
                f"Prediction range for '{key}' contains negative values."
            )

        # Check that start index is less than or equal to end index
        if start > end:
            json_return_error['bad_prediction_request'].append(
                f"In prediction range for '{key}', start index ({start}) is greater than end index ({end})."
            )
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

######
# Changes made on March 26, 2025:
# Added passing filter for `all_tracks` and type that starts with `expression_`
# filter_evaluator_request() will handle the input error if error_message_functions_updated.py does not.