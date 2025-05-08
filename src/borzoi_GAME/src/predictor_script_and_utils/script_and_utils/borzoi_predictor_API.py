# borzoi_predictor_API.py
import os
import sys
import json
import tqdm
import struct
import socket
import msgpack

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

# ------ ADDITION: Configuration for Wire-Format ------
PREDICTOR_SUPPORTED_FORMATS = ["json", "msgpack"] # Remove msgpack if not supported

# - Needs to advertise the formats it can support.
# - Negotiates with evaluator the wire-format to send predictions back in.
# - If Evaluator's preferred format is not what the Predictor can support, don't waste 
#   time and just send error back to Evaluator
# - Can receive JSON, TXT (converted to JSON string, so it arrives as JSON), MsgPack
# - If MessagePack is received, Predictor will have to convert it to JSON so the payload 
#   can pass through error checks and tasks and sequences can be extracted for the model.
# - If Evaluator's preferred format is JSON, send back as JSON (as normal).
# - If it is MessagePack, convert the JSON string to Msgpack before streaming to Evaluator

def send_payload(sock, payload_obj, wire_fmt):
    
    """
    Helper to pack and send JSON or MsgPack, prefix with 4-byte length, and send.
    
    Args:
        sock: Client socket
        payload_obj: Payload being sent to Evaluator
        wire_fmt: The format to send the payload_obj in
    
    Returns:
        None
    """
    try:
        if wire_fmt == "msgpack":
            body = msgpack.packb(payload_obj, use_bin_type=True)
        else:
            body = json.dumps(payload_obj).encode("utf-8")
        # Length-prefix
        sock.sendall(struct.pack(">I", len(body)))
        sock.sendall(body)
    except socket.error as e:
        print(f"server_error: Error sending payload: {e}")
        sock.close()

def negotiate_format_with_evaluator(client_socket):
    
    """
    1. Send supported formats from Predictor (as JSON)
    2. Receive preferred format from Evaluator before receiving payload (as JSON)
    Returns: 
        Agreed wire_format for payload, or
        None -- JSON-encoded error and close connection
    """
    
    # Advertise
    supported_fmts = {"formats": PREDICTOR_SUPPORTED_FORMATS}
    supported_fmts_bytes = json.dumps(supported_fmts).encode('utf-8')
    client_socket.sendall(struct.pack(">I", len(supported_fmts_bytes)))
    client_socket.sendall(supported_fmts_bytes)
    print(f"Advertised formats: {supported_fmts}")
    
    # Read Evaluator's choice
    # If choice in advertised formats, Evaluator gets it asks for
    # If not, JSON-encoded error and close connection
    prefix = client_socket.recv(4)
    if not prefix:
        client_socket.close()
        return None
    
    choice_len = struct.unpack(">I", prefix)[0]
    choice_recv = b""
    while len(choice_recv) < choice_len:
        chunk = client_socket.recv(BUFFER_SIZE) # This can change to receive the exact data length
        if not chunk:
            print("Could not receive Evaluator's preferred wire_format. Closing connection!")
            client_socket.close()
            return None
        choice_recv += chunk
        
    try:
        choice = json.loads(choice_recv.decode("utf-8"))["format"]
        print(f"Evaluator preferred format: {choice}")
    except Exception as e:
        send_payload(client_socket,
                     {"error": "bad_payload -- cannot parse format choice"},
                     "json")
        print(f"Error parsing evaluator choice: {e}")
        client_socket.close()
        return None
    
    # If unsupported, send error back as JSON and close
    if choice not in PREDICTOR_SUPPORTED_FORMATS:
        err = {"error":
            f"Unsupported format: '{choice}'. Supported: {PREDICTOR_SUPPORTED_FORMATS}"
            }
        send_payload(client_socket, err, "json")
        client_socket.close()
        return None
    
    return choice

def recv_message_loop(client_socket):
    
    # --- Perform the one-time handshake ---
    wire_format = negotiate_format_with_evaluator(client_socket)
    if wire_format is None:
        return None
    
    # Step 1: Receive total bytes (length) of the Evaluator's request 
    # Step 2: Receive file from Evaluator

    # ---------------------- Receive Evaluator JSON ----------------------
    while True:
        # Before receiving JSON from Evaluator
        # Receive length of the incoming JSON message (4-byte integer)
        # Can change to 8-byte integer by changing .recv(4) to .recv(8)
        # and replacing format string '>I' to '>Q'
        
        try:
            # Initialize data to store a new message on each iteration
            # Clear data_recv variable so multiple requests can be made
            data_recv = b'' # formerly, json_data_recv
            
            # Step 1: Read length prefix
            msg_length = client_socket.recv(4)
            if not msg_length:
                print("Failed to receive message length. Closing connection.")
                client_socket.close()
                break # Exit the loop if no message length is received

            # Unpack message length from 4 bytes
            msglen = struct.unpack('>I', msg_length)[0]
            print(f"Expecting {msglen} bytes of data from the Evaluator ({wire_format}).")
            
            # Step 2: Now receive the actual payload in packets
            # Initialize the progress bar
            progress = tqdm.tqdm(range(msglen), unit="B", 
                                 desc="Receiving Evaluator Request(s)",
                                 unit_scale=True, unit_divisor=1024)
            try:
                while len(data_recv) < msglen:
                    packet = client_socket.recv(BUFFER_SIZE) # can change
                    if not packet:
                        print("Connection closed unexpectedly.")
                        break
                    data_recv += packet
                    progress.update(len(packet))
            finally:
                # Close the progress bar when done
                progress.close()
            
            # Verify if all of the data is received
            if len(data_recv) == msglen:
                print("Evaluator request received completely")
                pass
            else:
                print("Data received was incomplete or corrupted.")
                break
                
        except Exception as e:
            print(f"Error while receiving data: {e}")
            client_socket.close()
            break  # Break the loop on exception
        
        # ---------------------- Process Received File ----------------------
        
        # --- Decode incoming payload into dict ---
        # This is to standardize payload received in any wire_format
        # so it can go through error-checking
        try:
            if wire_format == "msgpack":
                evaluator_json = msgpack.unpackb(data_recv, raw=False)
            else:
                evaluator_json = json.loads(data_recv.decode("utf-8"))
        except Exception as e:
            print(f"Error while decoding incoming payload: {e}")
            send_payload(client_socket, 
                         {"error": 
                             "bad_payload -- error while decoding incoming payload"},
                         wire_format)
            break

        # If only a "help" was requested return the predictor information file
        if evaluator_json['request'] == "help":
            # model builder should place help file in predictor folder
            print(f"Help requested! Sending {HELP_FILE}...")
            jsonResult_help = json.load(open(HELP_FILE))
            send_payload(client_socket, jsonResult_help, "json")
            client_socket.close()
            break

            # jsonResult_help = json.dumps(jsonResult_help)
            # try:
            #     jsonResult_help_bytes = jsonResult_help.encode("utf-8")
            #     jsonResult_help_total_bytes = len(jsonResult_help_bytes)
            #     client_socket.sendall(struct.pack('>I', jsonResult_help_total_bytes))
            #     client_socket.sendall(jsonResult_help_bytes)
            #     continue
            # except socket.error as e:
            #     print("server_error: Error sending help response: %s" % e)
            #     client_socket.close()
            #     print("Connection to client closed")
                
        # --- MODEL-SPECIFIC: Determine readout type ---
        readout_type = evaluator_json.get('readout', "track")
        is_point_readout = readout_type == "point"
        
        # Handle unsupported `interaction_matrix` readout
        if readout_type == "interaction_matrix":
            print("Borzoi cannot handle 'interaction_matrix' readout type. Exiting gracefully!")
            json_return_error = {'bad_prediction_request': 
                ["Borzoi cannot process 'interaction_matrix' readout type."]}
            send_payload(client_socket, json_return_error, "json")
            client_socket.close()
            print("Connection to client closed")
            break
            
            # json_string = json.dumps(json_return_error)
            # try:
            #     json_bytes = json_string.encode("utf-8")
            #     total_bytes = len(json_bytes)
            #     client_socket.sendall(struct.pack('>I', total_bytes))
            #     client_socket.sendall(json_bytes)
            #     continue
            # except socket.error as e:
            #     print("server_error: Error sending error response: %s" % e)
            # # finally:
            #     client_socket.close()
            #     # server.close()
            #     print("Connection to client closed")
            #     break
            #     # sys.exit(0)

        # re-usable error checking functions
        # group these functions
        json_return_error = {'bad_prediction_request': []}
        json_return_error = check_mandatory_keys(evaluator_json.keys(), json_return_error)
        json_return_error = check_request(evaluator_json['request'], json_return_error)
        json_return_error = check_prediction_task_mandatory_keys(evaluator_json['prediction_tasks'], json_return_error)
        # if any of the mandatory keys are missing immediately return an error to the evaluator
        if any(json_return_error.values()) == True:
            print("Validation error; sending error JSON!")
            send_payload(client_socket, json_return_error, "json")
            client_socket.close()
            break
        
            # json_string = json.dumps(json_return_error)
            # try:
            #     jsonResult_error_bytes = json_string.encode("utf-8")
            #     jsonResult_error_total_bytes = len(jsonResult_error_bytes)
            #     client_socket.sendall(struct.pack('>I', jsonResult_error_total_bytes))
            #     client_socket.sendall(jsonResult_error_bytes)
            #     continue
            # except socket.error as e:
            #     print("server_error: Error sending error response: %s" % e)
            # # finally:
            #     client_socket.close()
            #     # server.close()
            #     print("Connection to client closed")
            #     # sys.exit(1)
            #     break
        else:
            json_return_error = check_key_values_readout(evaluator_json['readout'], json_return_error)
            json_return_error = check_prediction_task_name(evaluator_json['prediction_tasks'], json_return_error)
            json_return_error = check_prediction_task_type(evaluator_json['prediction_tasks'], json_return_error)
            json_return_error = check_prediction_task_cell_type(evaluator_json['prediction_tasks'], json_return_error)
            json_return_error = check_prediction_task_species(evaluator_json['prediction_tasks'], json_return_error)
            if 'prediction_ranges' in evaluator_json.keys():
                json_return_error = check_seq_ids(evaluator_json['prediction_ranges'], evaluator_json['sequences'], json_return_error)
                json_return_error = check_prediction_ranges(evaluator_json['prediction_ranges'], json_return_error)

            if 'upstream_seq' in evaluator_json.keys() or 'downstream_seq' in evaluator_json.keys():
                json_return_error = check_key_values_upstream_flank(evaluator_json['upstream_seq'], json_return_error)
            if 'downstream_seq' in evaluator_json.keys():
                json_return_error = check_key_values_downstream_flank(evaluator_json['downstream_seq'], json_return_error)

            # --- MODEL SPECIFIC: Ensure this Borzoi Predictor only supports homo_sapiens ---
            for task in evaluator_json['prediction_tasks']:
                if task.get('species', '').lower() != "homo_sapiens":
                    json_return_error['bad_prediction_request'].append(
                        f"This predictor only supports species: homo_sapiens. Received '{task.get('species')}' for task '{task.get('name')}'."
                    )
                    break
            
            # if any errors were caught return them all to evaluator
            if any(json_return_error.values()) == True:
                print("Validation error; sending error JSON!")
                send_payload(client_socket, json_return_error, "json")
                client_socket.close()
                break
            
                # json_string = json.dumps(json_return_error)
                # try:
                #     jsonResult_error_bytes = json_string.encode("utf-8")
                #     jsonResult_error_total_bytes = len(jsonResult_error_bytes)
                #     client_socket.sendall(struct.pack('>I', jsonResult_error_total_bytes))
                #     client_socket.sendall(jsonResult_error_bytes)
                #     continue
                # except socket.error as e:
                #     print("server_error: Error sending error response: %s" % e)
                # # finally:
                #     client_socket.close()
                #     # server.close()
                #     print("Connection to client closed")
                #     # sys.exit(1)
                #     break

        # ---------------------- Process Sequences and Prediction Ranges ----------------------
        # Extract sequences to predict
        # Check that the sequences meet model specifications
        # Otherwise do any other formatting required for the model
        sequences = evaluator_json['sequences']
        
        # --- Add upstream and downstream flanking sequences, if provided by the evaluator ---
        # Default to empty string if not provided
        upstream_seq = evaluator_json.get('upstream_seq', "")
        downstream_seq = evaluator_json.get('downstream_seq', "")
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
                   
        # Can add any additional error checking functions here
        json_return_error_model = {'prediction_request_failed': []}
        json_return_error_model = check_seqs_specifications(sequences, json_return_error_model)
        
        # --- Process prediction_ranges if provided ---
        if 'prediction_ranges' in evaluator_json:
            prediction_ranges = evaluator_json['prediction_ranges']
            for seq_id, pr in prediction_ranges.items():
                # Only process non-empty ranges
                if pr:
                    # Unpack start and end indices
                    start, end = pr
                    # Check that the end index does not exceed sequence length
                    if end >= len(sequences[seq_id]):
                        json_return_error_model['prediction_request_failed'].append(
                            f"Prediction range for '{seq_id}' exceeds the sequence length!"
                        )
                    else:
                        # Slice the sequence. `prediction_range` is start, end inclusive
                        sequences[seq_id] = sequences[seq_id][start:end+1]
                        print(f"Sequence '{seq_id}' trimmed to prediction range [{start}, {end}].")

        # if anything is caught don't run the model and return to evaluator to fix
        if any(json_return_error_model.values()) == True:
            print("Sequence spec errors; sending error JSON")
            send_payload(client_socket, json_return_error_model, "json")
            client_socket.close()
            break
        
            # json_string = json.dumps(json_return_error_model)
            # try:
            #     jsonResult_bytes = json_string.encode("utf-8")
            #     jsonResults_total_bytes = len(jsonResult_bytes)
            #     client_socket.sendall(struct.pack('>I', jsonResults_total_bytes))
            #     client_socket.sendall(jsonResult_bytes)
            #     continue
            # except socket.error as e:
            #     print("server_error: Error sending error response: %s" % e)
            # # finally:
            #     client_socket.close()
            #     # server.close()
            #     print("Connection to client closed")
            #     # sys.exit(1)
            #     break

        # ---------------------- Extract Prediction Tasks and Run the Model ----------------------
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
        
        # --- ADDITION: Early bail-out if model returns error ---
        # Send the error to client and close this client
        if isinstance(task_predictions, str):
            # Wrap the error string into error payload 
            json_return_error_model[
                'prediction_request_failed'].append(task_predictions)
            print("Model error; sending error JSON")
            send_payload(client_socket, json_return_error_model, "json")
            client_socket.close()
            break
        
            # json_string = json.dumps(json_return_error_model)
            # try:
            #     json_bytes = json_string.encode("utf-8")
            #     total_bytes = len(json_bytes)
            #     client_socket.sendall(struct.pack('>I', total_bytes))
            #     client_socket.sendall(json_bytes)
            #     print("Sent prediction error back; closing connection with this Evaluator")
            #     continue
            # except socket.error as e:
            #     print("server_error: Error sending error response: %s" % e)
            #     client_socket.close()
            #     print("Connection to client closed")
            #     break

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

        # Convert dictionary to wire_format object and send back to evaluator
        send_payload(client_socket, json_return, wire_format)
        
        # Loop back for the next file, if provided, from the Evaluator
        
        # json_string = json.dumps(json_return)
        # try:
        #     jsonResult_bytes = json_string.encode("utf-8")
        #     jsonResults_total_bytes = len(jsonResult_bytes)
        #     client_socket.sendall(struct.pack('>I', jsonResults_total_bytes))
        #     client_socket.sendall(jsonResult_bytes)
        #     continue
        # except socket.error as e:
        #     print("server_error: Error sending prediction response: %s" % e)
        # # finally:
        #     client_socket.close()
        #     # server.close()
        #     print("Connection to client closed")
        #     # sys.exit(0)
        #     break

        # # ---------------------- Close Connection Sockets ----------------------
        # client_socket.close()
        # print("Connection to client closed")
        # # close server socket
        # server.close()

def run_predictor():

    predictor_ip = sys.argv[1]
    predictor_port = int(sys.argv[2])
    # cell_type_matcher_ip = sys.argv[3]
    # cell_type_matcher_port = sys.argv[4]

    #create error object
    json_return_error = {}

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind the socket to a specific address and port
    server.bind((predictor_ip, predictor_port))
    # listen for incoming connections
    server.listen(0)
    print(f"Listening on {predictor_ip}:{predictor_port}")
    
    # We want to have multiple evaluators to connect so predictor
    # can take multiple requests (and not just multiple tasks per evaluator)
    
    # This loop allows the Predictor server to stay running so that different Evaluators can connect
    while True:
        try:
            print("Waiting for an Evaluator to connect")
            # accept incoming connections
            client_socket, client_address = server.accept()
            print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
            # Once connected, receive request
            recv_message_loop(client_socket)
        except Exception as e:
            print(f"Error accepting client: {e}")
    
if __name__ == '__main__':
    run_predictor()