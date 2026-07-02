'''RESTful Test Evaluator Utilizing Flask'''

import os
import sys
import json
from requests.exceptions import RequestException, HTTPError

import config
from data_loader import load_and_validate_data
from evaluator_content_handler import *
import evaluator_metrics_calculator

def run_evaluator(predictor_ip, predictor_port, output_dir):
    """
    Preprocesses the data, sends request, receives response,
    saves the response, and returns file path.
    """
    
    # Validate output directory exists; create if it does not
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory '{output_dir}' did not exist. Created it successfully!")
        
    # Load and validate data, returns a JSON dictionary
    # This function will be Evaluator specific
    data_dict = load_and_validate_data()
    
    #Total number of sequences being sent to the Evaluator
    #This is used to confirm the correct number of predictions will be returned from the Predictor
    total_sequences = len(data_dict["sequences"])

    # Communicate with Predictor, send request, receive predictions
    predictor_url = f"http://{predictor_ip}:{predictor_port}"
    response_payload = None
    is_success_response = False # Flag to track if we got a 200 OK
    
    try:
        #Decide the request format and response format
        req_fmt, resp_fmt = negotiate_formats(predictor_url)
        
        # This call will return a 200 OK response OR raise HTTPError (4xx/5xx)
        response = get_predictions(predictor_url, data_dict, req_fmt, resp_fmt)
        
        is_success_response = True
        print("Predictor returned 200 OK.")
        response_payload = deserialize_response(response, resp_fmt)
        
    except HTTPError as http_err:
        # We got a 4xx/5xx. Treat the payload as an error report.
        print(f"Predictor returned HTTP {http_err.response.status_code}. Processing error payload...")
        is_success_response = False
        try:
            # Deserialize the error body (always JSON)
            response_payload = deserialize_response(http_err.response, "application/json") 
        except ValueError as decode_err:
            # Handle cases where the error response itself is malformed
            print(f"Could not decode the error response body: {decode_err}", file=sys.stderr)
            # Create a fallback error payload
            response_payload = {
                "predictor_name": "UnknownPredictor_ErrorResponse",
                "error": [{"server_error": f"Failed to decode error response (Status {http_err.response.status_code}). Body: {http_err.response.text[:500]}..."}]
            }
            
    if response_payload is None:
        print("FATAL: No response payload received or processed.", file=sys.stderr)
        # Create a fallback payload indicating a severe issue
        response_payload = {
            "predictor_name": "UnknownPredictor_NoResponse",
            "error": [{"evaluator_error": "No response payload could be processed after request."}]
        }
    
    # Save predictions
    predictor_name = response_payload.get("predictor_name", "UnknownPredictor").replace(" ", "_")
    output_filename = f"{config.output_filename_base}_from_{predictor_name}.json"
    saved_predictions_path = os.path.join(output_dir, output_filename)
        
    # Check sequence counts before saving
    for i, task in enumerate(response_payload.get("prediction_tasks", []), start=1):
        preds = task.get("predictions", {})
        if len(preds) != total_sequences:
            print(f"Warning: Task {i} ('{task.get('name')}') has {len(preds)} predictions, but {total_sequences} sequences were sent to the Predictor.")
    
    try:
        with open(saved_predictions_path, 'w', encoding='utf-8') as f:
            json.dump(response_payload, f, ensure_ascii=False, indent=4)
        print(f"Raw predictions saved to {saved_predictions_path}")
    except IOError as e:
        print(f"FATAL: Could not save predictions to {saved_predictions_path}. {e}", file=sys.stderr)
        return

    # Calculate and save final metrics
    if is_success_response:
        evaluator_metrics_calculator.calculate_and_save_metrics(response_payload, output_dir)
    else:
        print("Skipping metrics calculation because the Predictor did not return a 200 OK status.")

if __name__ == '__main__':
    # Check that mandatory arguments are passed to the script
    if len(sys.argv) != 4:
        print(f"Invalid arguments! Arguments must have: <container image/python script> <predictor_ip_address> <predictor_port> <mounted_output_directory>")
        sys.exit(1)
    
    # Call Evaluator here
    predictor_ip = sys.argv[1]
    predictor_port = int(sys.argv[2])
    output_dir_arg = sys.argv[3]
    
    try:
        run_evaluator(predictor_ip, int(predictor_port), output_dir_arg)
        print("Evaluation complete.")
        sys.exit(0)
        
    except (FileNotFoundError, ValueError) as e:
        print(f"FATAL ERROR (Data): {e}", file=sys.stderr)
        sys.exit(1)
    except RequestException as e:
        print(f"FATAL ERROR (Network): Could not connect to predictor at http://{predictor_ip}:{predictor_port}.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected fatal error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)