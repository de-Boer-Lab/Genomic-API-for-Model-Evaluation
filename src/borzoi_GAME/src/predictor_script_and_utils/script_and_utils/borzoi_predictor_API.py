# borzoi_predictor_API.py
import os
import sys
import json
import tqdm
import struct
import socket

from error_message_functions_updated import *
from api_preprocessing_utils import *

# Get the absolute path of the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Determine if running inside a container or not
if os.path.exists('/.singularity.d'):
    # Running inside the container
    print("Running inside the container...🥡")
    BORZOI_DIR = "/predictor_script_and_utils/borzoi_API_script_and_utils"
    HELP_FILE = "/predictor_script_and_utils/script_and_utils/predictor_help_message.json"
else:
    # Running outside the container
    print("Running outside the container...📋")
    PREDICTOR_CONTAINER_DIR = os.path.dirname(SCRIPT_DIR)
    BORZOI_DIR = os.path.join(PREDICTOR_CONTAINER_DIR, "borzoi_API_script_and_utils")
    HELP_FILE = os.path.join(SCRIPT_DIR, 'predictor_help_message.json')

# Add BORZOI_DIR to the Python path
if BORZOI_DIR not in sys.path:
    sys.path.insert(0, BORZOI_DIR)

from borzoi_predict_codebase import *

# Set buffer size for TCP
BUFFER_SIZE = 65536

def run_predictor():

    evaluator_ip = sys.argv[1]
    evaluator_port = int(sys.argv[2])
    # cell_type_matcher_ip = sys.argv[3]
    # cell_type_matcher_port = sys.argv[4]

    #create error object
    json_return_error = {}

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind the socket to a specific address and port
    server.bind((evaluator_ip, evaluator_port))
    # listen for incoming connections
    server.listen(0)
    print(f"Listening on {evaluator_ip}:{evaluator_port}")

    # accept incoming connections
    client_socket, client_address = server.accept()
    print(f"Accepted connection from {client_address[0]}:{client_address[1]}")

    # Step 1: receive total bytes the Predictor expects to receive
    # Step 2: receive JSON from evaluator

    # Initialize data to store a new message on each iteration
    json_data_recv = b''

    while True:
        # Before receiving JSON from Evaluator
        # Receive length of the incoming JSON message (4-byte integer)
        # Can change to 8-byte integer by changing .recv(4) to .recv(8)
        # and replacing format string '>I' to '>Q'
        # Step 1
        try:
            msg_length = client_socket.recv(4)
            if not msg_length:
                print("Failed to receive message length. Closing connection.")
                client_socket.close()
                break # Exit the loop if no message length is received

            # Unpack message length from 4 bytes
            msglen = struct.unpack('>I', msg_length)[0]
            print(f"Expecting {msglen} bytes of data from the Evaluator.")
            
            # Initialize the progress bar
            progress = tqdm.tqdm(range(msglen), unit="B", 
                                 desc="Receiving Evaluator Request(s)",
                                 unit_scale=True, unit_divisor=1024)

            # Step 2
            # Now we want to receive the actual JSON in packets
            while len(json_data_recv) < msglen:
                packet = client_socket.recv(BUFFER_SIZE)
                if not packet:
                    print("Connection closed unexpectedly.")
                    break
                json_data_recv += packet
                progress.update(len(packet))
                # print(f"Received packet of {len(packet)} bytes, total received: {len(data)} bytes")
            
            # Close the progress bar when done
            progress.close()
            
            # Decode and display the received data if all of it is received
            if len(json_data_recv) == msglen:
                print("Evaluator request received completely")
                break
            else:
                print("Data received was incomplete or corrupted.")
                break
        except Exception as e:
            print(f"Error while receiving data: {e}")
            client_socket.close()
            break  # Break the loop on exception


# ---------------------- %%%%%%%---------------
    evaluator_request_full = json_data_recv
    evaluator_json = evaluator_request_full.decode("utf-8")
    evaluator_json = json.loads(evaluator_json)

    # group these functions
    json_return_error = {'bad_prediction_request': []}

    # if only a "help" was requested return the predictor information file
    if evaluator_json['request'] == "help":

        # model builder should place help file in predictor folder
        help_file = HELP_FILE
        print(f"Help requested! Sending {HELP_FILE}...")
        jsonResult_help = json.load(open(help_file))

        jsonResult_help = json.dumps(jsonResult_help)
        try:
            jsonResult_help_bytes = jsonResult_help.encode("utf-8")
            jsonResult_help_total_bytes = len(jsonResult_help_bytes)
            client_socket.sendall(struct.pack('>I', jsonResult_help_total_bytes))
            client_socket.sendall(jsonResult_help_bytes)
        except socket.error as e:
            print("server_error: Error sending help response: %s" % e)
        finally:
            client_socket.close()
            server.close()
            print("Connection to client closed")
            sys.exit(0)
            
    # --- MODEL-SPECIFIC: Determine readout type ---
    readout_type = evaluator_json.get('readout', "track")
    is_point_readout = readout_type == "point"
    
    # Handle unsupported `interaction_matrix` readout
    if readout_type == "interaction_matrix":
        print("Borzoi cannot handle 'interaction_matrix' readout type. Exiting gracefully!")
        json_return_error = {'bad_prediction_request': ["Borzoi cannot process 'interaction_matrix' readout type."]}
        json_string = json.dumps(json_return_error)
        try:
            json_bytes = json_string.encode("utf-8")
            total_bytes = len(json_bytes)
            client_socket.sendall(struct.pack('>I', total_bytes))
            client_socket.sendall(json_bytes)
        except socket.error as e:
            print("server_error: Error sending error response: %s" % e)
        finally:
            client_socket.close()
            server.close()
            print("Connection to client closed")
            sys.exit(0)

    # re-usable error checking functions
    json_return_error = check_mandatory_keys(evaluator_json.keys(), json_return_error)
    json_return_error = check_request(evaluator_json['request'], json_return_error)
    json_return_error = check_prediction_task_mandatory_keys(evaluator_json['prediction_tasks'], json_return_error)
    # if any of the mandatory keys are missing immediately return an error to the evaluator
    if any(json_return_error.values()) == True:
        json_string = json.dumps(json_return_error)
        try:
            jsonResult_error_bytes = json_string.encode("utf-8")
            jsonResult_error_total_bytes = len(jsonResult_error_bytes)
            client_socket.sendall(struct.pack('>I', jsonResult_error_total_bytes))
            client_socket.sendall(jsonResult_error_bytes)
        except socket.error as e:
            print("server_error: Error sending error response: %s" % e)
        finally:
            client_socket.close()
            server.close()
            print("Connection to client closed")
            sys.exit(1)
    else:
        json_return_error = check_key_values_readout(evaluator_json['readout'], json_return_error)
        json_return_error = check_prediction_task_name(evaluator_json['prediction_tasks'], json_return_error)
        json_return_error = check_prediction_task_type(evaluator_json['prediction_tasks'], json_return_error)
        json_return_error = check_prediction_task_cell_type(evaluator_json['prediction_tasks'], json_return_error)
        # json_return_error = check_prediction_task_species(evaluator_json['prediction_tasks'], json_return_error)
        if 'prediction_ranges' in evaluator_json.keys():
            json_return_error = check_seq_ids(evaluator_json['prediction_ranges'], evaluator_json['sequences'], json_return_error)
            json_return_error = check_prediction_ranges(evaluator_json['prediction_ranges'], json_return_error)

        if 'upstream_seq' in evaluator_json.keys() or 'downstream_seq' in evaluator_json.keys():
            json_return_error = check_key_values_upstream_flank(evaluator_json['upstream_seq'], json_return_error)
        if 'downstream_seq' in evaluator_json.keys():
            json_return_error = check_key_values_downstream_flank(evaluator_json['downstream_seq'], json_return_error)

        # if any errors were caught return them all to evaluator
        if any(json_return_error.values()) == True:
            json_string = json.dumps(json_return_error)
            try:
                jsonResult_error_bytes = json_string.encode("utf-8")
                jsonResult_error_total_bytes = len(jsonResult_error_bytes)
                client_socket.sendall(struct.pack('>I', jsonResult_error_total_bytes))
                client_socket.sendall(jsonResult_error_bytes)
            except socket.error as e:
                print("server_error: Error sending error response: %s" % e)
            finally:
                client_socket.close()
                server.close()
                print("Connection to client closed")
                sys.exit(1)

    # ---------------------- %%%%%%%---------------
    # Extract sequences to predict
    # Check that the sequences meet model specifications
    # Otherwise do any other formatting required for the model
    sequences = evaluator_json['sequences']
    # Can add any additional error checking functions here
    json_return_error_model = {'prediction_request_failed': []}
    json_return_error_model = check_seqs_specifications(sequences, json_return_error_model)

    # if anything is caught don't run the model and return to evaluator to fix
    if any(json_return_error_model.values()) == True:
        json_string = json.dumps(json_return_error_model)
        try:
            jsonResult_bytes = json_string.encode("utf-8")
            jsonResults_total_bytes = len(jsonResult_bytes)
            client_socket.sendall(struct.pack('>I', jsonResults_total_bytes))
            client_socket.sendall(jsonResult_bytes)
        except socket.error as e:
            print("server_error: Error sending error response: %s" % e)
        finally:
            client_socket.close()
            server.close()
            print("Connection to client closed")
            sys.exit(1)

    # ---------------------- %%%%%%%---------------
    # Start big loop here for all the prediction_tasks
    # Connect to cell type matching container in cases of multi-task models
    # cell_type_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # cell_type_socket.connect((cell_type_matcher_ip, cell_type_matcher_port))
    
    # Borzoi is vastly different from Dream-RNN Predictor codebase in the 
    # sense that it can perform track predictions.
    # Therefore, the first step is to collect all unique tasks
    request_tasks = set()  # Store unique (request_type, cell_type) pairs

    for prediction_task in evaluator_json['prediction_tasks']:
        request_type = prediction_task['type']
        cell_type = prediction_task['cell_type']
        request_tasks.add((request_type, cell_type))

    print(f"Unique tasks extracted: {request_tasks}") 
    
    # Then run Borzoi Model ONCE for all required tracks
    print("Running Borzoi model on collected tasks...")
    task_predictions = predict_borzoi(sequences, request_tasks, is_point_readout)

    # Now format predictions to API JSON structure
    # Create JSON to return
    json_return = {
        'request': evaluator_json['request'],
        'bin_size': 32,
        # Prediction task is an array of objects for all requested tasks
        'prediction_tasks': []
    }
    
    # Loop through all the prediction tasks
    for prediction_task in evaluator_json['prediction_tasks']:
        task_name = prediction_task['name']
        request_type = prediction_task['type']
        cell_type = prediction_task['cell_type']
        
        task_key = (request_type, cell_type)
        
        # Cell type predictor container is running, send the predictor's cell type and evaluator cell type to it
        # If you want to override the cell type container you can remove the following code
        # Send the predictor and evaluator cell type
        # cell_type_socket.sendall(b'Hello, cell type matcher dude!')
        # cell_type_matcher_return = cell_type_socket.recv(1024)

        # The following code will be model specific
        # Sample point prediction model
        # Model builders need to add the appropriate returns here
        
        # Retrieve the predictions for this task
        predictions = task_predictions.get(task_key, {})

        # Create structured response for the evaluator
        current_prediction_task = {
            'name': prediction_task['name'],
            'type_requested': request_type,
            'type_actual': request_type,  # If remapped, update this
            'cell_type_requested': cell_type,
            'cell_type_actual': cell_type,  # If remapped, update this
            'species_requested': prediction_task['species'],
            'species_actual': prediction_task['species'],
            'scale_prediction_requested': prediction_task.get('scale', "linear"),  # Default to linear
            'scale_prediction_actual': prediction_task.get('scale', "linear"),
            'aggregation_replicates': "mean",  # Since we average over tracks
            'aggregation_bins': "mean",        # Ensure track models are aggregated correctly
            'predictions': predictions
        }
        
        # Append results for current prediction task to the main JSON object
        json_return['prediction_tasks'].append(current_prediction_task)

    # Convert dictionary to JSON object and send back to evaluator
    json_string = json.dumps(json_return)
    try:
        jsonResult_bytes = json_string.encode("utf-8")
        jsonResults_total_bytes = len(jsonResult_bytes)
        client_socket.sendall(struct.pack('>I', jsonResults_total_bytes))
        client_socket.sendall(jsonResult_bytes)
    except socket.error as e:
        print("server_error: Error sending prediction response: %s" % e)
    finally:
        client_socket.close()
        server.close()
        print("Connection to client closed")
        sys.exit(0)

    # ---------------------- %%%%%%%---------------
    # close connection socket with the client
    client_socket.close()
    print("Connection to client closed")
    # close server socket
    server.close()

run_predictor()