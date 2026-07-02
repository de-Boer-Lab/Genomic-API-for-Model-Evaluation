import os
import sys
import json
from flask import Flask
from error_checking_functions import *
from schema_validation import *
from deBoerTest_model import *
from predictor_content_handler import decode_request, encode_response

import config
PREDICTOR_NAME = config.PREDICTOR_NAME
HELP_FILE = config.HELP_FILE
SUPPORTED_REQUEST_FORMATS = config.SUPPORTED_REQUEST_FORMATS
SUPPORTED_RESPONSE_FORMATS = config.SUPPORTED_RESPONSE_FORMATS

# --- Flask App and Central Error Handler ---
app = Flask(__name__)
# One of these works to maintain order when using jsonify()
app.config["JSON_SORT_KEYS"] = False
app.json.sort_keys = False

def create_error_response(error_key, messages, status_code):
    """ 
    Formats error response into a standardized JSON structure.
    
    Args:
        error_key (str): The category of the error (e.g. 'bad_prediction_request', 'prediction_request_failed').
        messages (list or str): A list of error message strings or a single message.
        status_code (int): Standard HTTP error status code based on the error.
    
    Returns:
        dict: A dictionary formatted for the standardized JSON error response.
    """
    if not isinstance(messages, list):
        messages = [str(messages)]
    error_payload = {"error": [{error_key: msg} for msg in messages]}
    print(error_payload)
    return error_payload, status_code

@app.errorhandler(APIError)
def handle_api_error(error):
    """This single handler catches all of our custom API errors."""
    # Get raw payload and status code
    payload, status_code = create_error_response(error.error_key, error.message, error.status_code)
    
    return encode_response(
        payload, 
        status_code=status_code,
        isError=True,
        predictor_name=PREDICTOR_NAME)
    
@app.after_request
def after_request_callback(response):
    """This function runs after each request is processed."""
    print(f"\n--- Sending predictions back to Evaluator. ---")
    print(f"--- Request Complete. {PREDICTOR_NAME} Predictor is listening on http://{predictor_ip}:{predictor_port} ---\n")
    return response

# --- API Endpoints ---
@app.route('/formats', methods=['GET'])
def formats_endpoint():
    """Provides the Predictor's supported formats"""
    supported_fmts = {
        "predictor_supported_request_formats": SUPPORTED_REQUEST_FORMATS,
        "predictor_supported_response_formats": SUPPORTED_RESPONSE_FORMATS
    }
    try:
        return encode_response(
            supported_fmts,
            status_code=200,
            predictor_name=PREDICTOR_NAME,
            supported_response_formats=SUPPORTED_RESPONSE_FORMATS)
    except Exception as e:
        raise ServerError(f"Error serializing supported format for /format endpoint: {e}")

@app.route('/help', methods=['GET'])
def help_endpoint():
    """Provides the Predictor's help/metadata information."""
    try:
        with open(HELP_FILE, 'r') as f:
            help_data = json.load(f)
        return encode_response(
            help_data,
            status_code=200,
            predictor_name=PREDICTOR_NAME,
            supported_response_formats=SUPPORTED_RESPONSE_FORMATS)
    except Exception as e:
        raise ServerError(f"Error reading help file: {e}")

@app.route('/predict', methods=['POST'])
def predict():
    """The main endpoint for receiving sequences and returning predictions."""
    
    try:
        #Decode incoming request, using the headers or JSON default
        evaluator_request = decode_request(SUPPORTED_REQUEST_FORMATS)
            
        # Validate the payload using the imported function
        # These functions will raise an APIError on failure,
        # which will be caught automatically by @app.errorhandler
        validate_request_payload(evaluator_request)

        # Preprocess the data using the imported function
        sequences = preprocess_data(evaluator_request)
        readout_type = evaluator_request.get('readout')
        
        # Assemble the response
        json_return = {}
        if readout_type in ("track", "interaction_matrix"):
            json_return['bin_size'] = 1
        json_return['prediction_tasks'] = []

        for task in evaluator_request['prediction_tasks']:
            # Run Model Inference
            if readout_type == "point":
                model_predictions = fake_model_point(sequences)
            elif readout_type == "track":
                model_predictions = fake_model_track(sequences)
            elif readout_type == "interaction_matrix":
                model_predictions = fake_model_interaction_matrix(sequences)
            else:
                raise PredictionFailedError(f"Unsupported readout type: '{readout_type}'")
 
            task_response = {
                'name': task['name'],
                'type_requested': task['type'],
                'type_actual': [task['type']],
                'cell_type_requested': task['cell_type'],
                'cell_type_actual': 'test_cell',
                'species_requested': task['species'],
                'species_actual': 'test_species',
                'predictions': model_predictions
            }
            
            if 'scale' in task:
                task_response['scale_prediction_requested'] = task['scale']
                task_response['scale_prediction_actual'] = 'linear'  # fake model is always linear

            json_return['prediction_tasks'].append(task_response)
            
        return encode_response(
            json_return,
            status_code=200,
            predictor_name=PREDICTOR_NAME,
            supported_response_formats=SUPPORTED_RESPONSE_FORMATS)
    
    except Exception as e:
        # If it's already an APIError, re-raise it for the handler
        if isinstance(e, APIError):
            raise e
        # Otherwise, wrap the unknown error in a ServerError
        raise ServerError(f"An unexpected internal error occurred: {e}.")


# --- Run Flask ---
if __name__ == '__main__':
    
    if len(sys.argv) < 3:
        print(f"Invalid arguments! Must provide at least: <ip_address> <port>")
        sys.exit(1)
        
    try:
        predictor_ip = sys.argv[1]
        predictor_port = int(sys.argv[2])
    except ValueError:
        print(f"Error: Port must be an integer. Received '{sys.argv[2]}'.")
        sys.exit(1)

    # This will log that extra args were ignored, which is good
    if len(sys.argv) > 3:
        print(f"Ignoring {len(sys.argv) - 3} extra command-line arguments (e.g. Matcher config). This predictor does not use Matcher.")
        
    predictor_ip = sys.argv[1]
    predictor_port = int(sys.argv[2])
    
    print(f"{PREDICTOR_NAME} Predictor is running on http://{predictor_ip}:{predictor_port}")
    app.run(host=predictor_ip, port=predictor_port, threaded=True, debug=False)

