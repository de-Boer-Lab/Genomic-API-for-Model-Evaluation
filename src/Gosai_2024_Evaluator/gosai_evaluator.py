# gosai_evaluator.py
import os
import sys
import json
import time
import tqdm
import struct
import socket
import msgpack
import pandas as pd
from datetime import datetime, timezone

from evaluator_utils import *
from correlation_calculator import *

# Get the absolute path of the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# File name for input sequences
input_file = "41586_2024_8070_MOESM4_ESM.txt"

# Evaluator name
EVALUATOR_NAME = "gosai_mpra"

#Determine if running inside a container or not
if os.path.exists("/.singularity.d"):
    # Running inside the container
    EVALUATOR_DATA_DIR = "/evaluator_data"
else:
    #Running outside the container
    EVALUATOR_DATA_DIR = os.path.join(SCRIPT_DIR, "evaluator_data")

EVALUATOR_INPUT_PATH = os.path.join(EVALUATOR_DATA_DIR, input_file)

output_filename_base = f'{EVALUATOR_NAME}_predictions_{input_file.replace(".txt", "")}' # predictor_name will be added to this upon receiving the response

# Set buffer size for TCP
BUFFER_SIZE = 65536

# Debug logs for validation
print(f"Using input file: {EVALUATOR_INPUT_PATH}")

# ------ Configuration for Wire-Format ------
REQUEST_FORMAT = "JSON"
REQUEST_FORMAT = REQUEST_FORMAT.lower() # for case-insensitive matching

# Compute send format before connecting to Predictor
RESPONSE_FORMAT = "msgpack"
RESPONSE_FORMAT = RESPONSE_FORMAT.lower()

# Enable negotiation
def negotiate_format_with_predictor(connection):
    
    """
    1. Read the advertised formats from Predictor:
        - "predictor_supported_request_formats"    (what Predictor can RECEIVE)
        - "predictor_supported_response_formats" (what Predictor can SEND BACK)
    2. Choose send_format = REQUEST_FORMAT if in predictor_supported_request_formats else "json"
    3. Choose recv_format = RESPONSE_FORMAT if in predictor_supported_response_formats else "json"
    4. Send back {"request_format": send_format, "response_format": recv_format}
    
    Returns:
        Agreed (send_format, recv_format)
    """
    
    # Receive advert length from Predictor
    prefix = connection.recv(4)
    if not prefix:
        print("Failed to receive supported formats from Predictor.")
        sys.exit(1)    
    supported_fmt_len = struct.unpack(">I", prefix)[0]
    
    # Read the advert payload
    supported_fmt = b""
    while len(supported_fmt) < supported_fmt_len:
        chunk = connection.recv(BUFFER_SIZE)
        if not chunk:
            print("Could not receive Predictor's supported wire_format. Closing connection!")
            sys.exit(1)
        supported_fmt += chunk
        
    # Parse JSON advert
    try:
        supported = json.loads(supported_fmt.decode("utf-8"))
        pred_request_fmts = [f.lower() for f in supported.get("predictor_supported_request_formats")]
        pred_response_fmts = [f.lower() for f in supported.get("predictor_supported_response_formats")]
    except Exception as e:
        print("Error: Could not parse Predictor's supported formats")
        sys.exit(1)
        
    # JSON should always be accepted
    if "json" not in pred_request_fmts:
        pred_request_fmts.append("json")
    if "json" not in pred_response_fmts:
        pred_response_fmts.append("json")
    print(f"Predictor can receive: {pred_request_fmts}")
    print(f"Predictor can send back: {pred_response_fmts}")
    
    # Decide request format having parsed what Predictor can support
    if REQUEST_FORMAT in pred_request_fmts:
        send_format = REQUEST_FORMAT
    else:
        send_format = "json"
        if REQUEST_FORMAT != "json":
            print(f"WARNING: REQUEST_FORMAT='{REQUEST_FORMAT}' not supported by Predictor; Using JSON")
    
    # Decide response format
    if RESPONSE_FORMAT in pred_response_fmts:
        recv_format = RESPONSE_FORMAT
    else: 
        recv_format = "json"
        if RESPONSE_FORMAT != "json":
            print(f"WARNING: RESPONSE_FORMAT='{RESPONSE_FORMAT}' not supported by Predictor; Using JSON")
    
    # Send Evaluator decision back
    choice = json.dumps({
        "request_format": send_format,
        "response_format": recv_format
        }).encode('utf-8')
    connection.sendall(struct.pack(">I", len(choice)))
    connection.sendall(choice)
    print(f"Negotiated send format: {send_format}")
    print(f"Negotiated receive format: {recv_format}")
    return send_format, recv_format

def run_evaluator(host, port, output_dir):
    """
    Connects to Predictor, preprocesses, sends request, receives response,
    saves the response, and returns fill path to the file.

    Returns:
        output_file (str): The full path to the saved predictions JSON file; None if unable.
    """
    
    # Validate evaluator input file exists
    if not os.path.exists(EVALUATOR_INPUT_PATH):
        print(f"Error: Evaluator input file '{EVALUATOR_INPUT_PATH}' does not exist.")
        sys.exit(1)

    # Validate output directory; create if it does not
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory '{output_dir}' did not exist. Created it successfully!")
        
    # Try creating a socket
    try:
        # create a socket object
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print ("server_error: Error creating socket: %s" % e)
        sys.exit(1)
        
    # Re-try Parameters
    RETRY_INTERVAL = 30 # 30 seconds
    MAX_RETRIES = 50
    attempt = 0
    connected = False
    
    while attempt < MAX_RETRIES and not connected:
        try:
            # establish connection with predictor server
            connection.connect((host, port))
            print(f"Connected to Predictor on {host}:{port}")
            connected = True
        except socket.gaierror as e:
            print ("Address-related error connecting to server: %s" % e)
            sys.exit(1)
        except socket.error as e:
            attempt += 1
            print ("server_error: Connection error: %s" % e)
            if attempt < MAX_RETRIES:
                print(f"Retrying in {RETRY_INTERVAL} seconds... (Attempt {attempt} of {MAX_RETRIES})")
                for _ in tqdm.tqdm(range(RETRY_INTERVAL), desc="Waiting to retry connection", unit="s"):
                    time.sleep(1)
            else:
                print(f"Tried connecting {attempt} times. Exceeded maximum number of retries. Exiting...")
                sys.exit(1)
    
    # Negotiate wire format
    send_fmt, recv_fmt = negotiate_format_with_predictor(connection)

    # ----- PAYLOAD PREPROCESSING -----
    # Load and validate input
    try:
        # Load in JSON file from evalutor_data if connection to Predictor container was successful
        # Create JSON string from input file since it is not in JSON format already
        df = pd.read_csv(EVALUATOR_INPUT_PATH, delimiter='\t')
        evaluator_json_str = create_json(df)
                
         # Check for duplicate keys in the generated JSON string.
        # Use the helper function that accepts a JSON string.
        data_dict = check_duplicates_from_string(evaluator_json_str)
        if data_dict is None:
            sys.exit(1)
    except json.JSONDecodeError as e:
        print("Invalid JSON syntax:", e)
        sys.exit(1)
        
    # Prepare payload -- Serialize
    print(f"Serializing request to Predictor as '{send_fmt}'")
    if send_fmt == "msgpack":
        try:
            payload_bytes = msgpack.packb(data_dict, use_bin_type=True)
            print(f"Sending payload serialized as MsgPack")
        except Exception as e:
            print(f"Error packing MsgPack: {e}")
            sys.exit(1)
    else:
        try:
            payload_bytes = json.dumps(data_dict).encode("utf-8")
            print(f"Sending payload serialized as JSON")
        except Exception as e:
            print(f"Error packing JSON: {e}")
            sys.exit(1)

    # first send the total bytes we are transmitting to the Predictor
    # This is used to stop the recv() process
    # send the evaluator data to the predictor server
    try:
        payload_bytes_len = len(payload_bytes)
        connection.sendall(struct.pack(">I", payload_bytes_len))
        print(f"Sent evaluator request length {payload_bytes_len} bytes!")
        
        # Now send the actual payload
        connection.sendall(payload_bytes)
    except socket.error as e:
        print (f"server_error: Error sending payload: {e}")
        sys.exit(1)

# ---------------- RECEIVE RESPONSE ----------------
    # receive message from the server
    data_recv = b''
    while True:
        # Before receiving predictions/ payload from Predictor
        # Receive length of the incoming message (4-byte integer)
        # Can change to 8-byte integer by changing .recv(4) to .recv(8)
        # and replacing format string '>I' to '>Q'
        # Step 1: length prefix
        try:
            msg_length = connection.recv(4)
            if not msg_length:
                print("Failed to receive message length. Closing connection.")
                connection.close()
                break # Exit the loop if no message length is received

            # Unpack message length from 4 bytes
            msglen = struct.unpack('>I', msg_length)[0]
            print(f"Expecting {msglen} bytes of data from the Predictor.")
            
            # Initialize the progress bar
            progress = tqdm.tqdm(range(msglen), unit="B", 
                                 desc="Receiving Predictor Response",
                                 unit_scale=True, unit_divisor=1024)

            # Step 2: the payload
            # Now we want to receive the actual JSON in packets
            while len(data_recv) < msglen:
                packet = connection.recv(BUFFER_SIZE)
                if not packet:
                    print("Connection closed unexpectedly.")
                    break
                data_recv += packet
                progress.update(len(packet))
           
            # Close the progress bar when done
            progress.close()
            
            # Decode data if all of it is received
            if len(data_recv) == msglen:
                print("Predictor response received completely!")
                break
            else:
                print("Data received was incomplete or corrupted.")
                break

        except socket.error as e:
            print("server_error: Error receiving predictions: %s" % e)
            sys.exit(1)

# Parse and save Predictor response
    try:
        if recv_fmt == "msgpack":
            try:
                print("De-serializing Predictor response as MsgPack")
                predictor_data = msgpack.unpackb(data_recv, raw=False)
            # But in case of an error/help, Predictor will return JSON
            # Even if the agreed wire_fmt was not JSON
            except Exception:
                print("Error/ Help was received!")
                print("De-serializing Predictor response as JSON")
                predictor_data = json.loads(data_recv.decode("utf-8"))
        else:
            try:
                print("De-serializing Predictor response as JSON")
                predictor_data = json.loads(data_recv.decode("utf-8"))
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error saving predictions: {e}")
                sys.exit(1)
        
        # ADDITION: Construct file name after receiving predictor_name
        predictor_name_received = predictor_data.get("predictor_name", None)
        predictor_name = predictor_name_received.replace(" ", "_").replace("/", "_")
        output_json_filename = f"{output_filename_base}_from_{predictor_name}.json"
        
        # Compute the full RETURN_FILE_PATH using the provided output directory
        RETURN_FILE_PATH = os.path.join(output_dir, output_json_filename)
        print(f"Will save predictions to: {RETURN_FILE_PATH}")
        
        output_file = RETURN_FILE_PATH
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(predictor_data, f,                                                                                                  
                      ensure_ascii=False, indent=4, 
                      separators=(",", ": "))
        print(f"Predictions saved to {output_file}")
        return output_file # NOTE: This is now being returned so the __main__ block knows where the predictions are stored
    
    except Exception as e:
        print(f"Error saving predictions: {e}")
        sys.exit(1)
        return None
    finally:
        connection.close()
        print("Connection to server closed")   
    
if __name__ == '__main__':
    
    host_arg = sys.argv[1]
    port_arg = int(sys.argv[2])
    output_dir_arg = sys.argv[3]
    
    saved_predictions_path = run_evaluator(host_arg, port_arg, output_dir_arg)
    
    # Correlation calculation
    # NOTE: Every evaluator will do this slightly differently depending on how the data is presented  
    if os.path.exists(saved_predictions_path):
        print("----- Starting Evaluation Calculation and Saving as CSV -----")
        MEASURED_DATA_PATH = EVALUATOR_INPUT_PATH # NOTE: This may not be the same for other evaluators
        print(f"Using measured data from: {MEASURED_DATA_PATH}")
        print(f"Using predictions from: {saved_predictions_path}")
        print(f"Correlation metadata will be saved in {output_dir_arg}")
        
        seq_column = "IDs" # This can change depending on data
        measured_value_columns_map = {
            "K562": "K562_log2FC",
            "HEPG2": "HepG2_log2FC", 
            "SKNSH": "SKNSH_log2FC"
        }
        
        chromosome_column = "chr" # If provided
        chromosomes_to_filter_list = None 
        
        correlation_summary_filename = f"correlation_summary_{EVALUATOR_NAME}.csv"
        correlation_summary_filepath = os.path.join(output_dir_arg, correlation_summary_filename)
        
        # Initialize an empty list to get summary for all tasks
        all_task_correlation_results = []
        
        try:
            # Load measured data file and predictions file ONCE (not with every function call).
            # NOTE: Evaluator builders: If measured_file_path is not a tab-separated file,
            # this line (pd.read_csv) will need to be adjusted or replaced with the
            # appropriate pandas read function (e.g., pd.read_excel, pd.read_csv with different sep)
            # or custom loading logic (e.g., for .npy files).
            measured_df = pd.read_csv(MEASURED_DATA_PATH, sep='\t', header=0)
            
            # Now load predictions
            with open(saved_predictions_path, 'r') as f:
                predictions_file_content = json.load(f)
            
            # Extract Predictor Name
            predictor_name_base = predictions_file_content.get("predictor_name", None) # Resort to None if predictor name is not available
            
            if (
                "prediction_tasks" not in predictions_file_content or
                # Also flag cases in case prediction_tasks key is returned empty
                not predictions_file_content["prediction_tasks"] or
                # And flag if any 'predictions' keys are empty
                any(not key.get("predictions") for key in predictions_file_content["prediction_tasks"])
            ):
                print("WARNING: 'prediction_tasks' key missing, empty, or one of the tasks has empty predictions.")
            else:
                # Loop through each prediction_task from Predictor
                # Calculate the correlation for each task seperately
                for task_index, single_task_data_dict in enumerate(predictions_file_content["prediction_tasks"]):
                    if not isinstance(single_task_data_dict, dict):
                        print(f"WARNING: Task item at index {task_index} is not a dictionary. Skipping!")
                        continue
                    
                    # Extract metadata from this task
                    task_type_actual = single_task_data_dict.get("type_actual")
                    predicted_cell_type = single_task_data_dict.get("cell_type_actual")
                    # We also want to extract the cell_type_requested to map it to measured_value_columns_map
                    requested_cell_type = single_task_data_dict.get("cell_type_requested")
                    
                    # Find the correspoding measured data column from the map
                    measured_col_for_task = measured_value_columns_map.get(requested_cell_type)
                    
                    print(f"\nProcessing task {task_index+1} (Cell Type: {predicted_cell_type}). Correlating against measured column '{measured_col_for_task}'.")
                    
                    # Call the correlation calculation function
                    task_correlation_dict = calculate_task_correlation(
                        measured_df=measured_df,
                        single_task_data=single_task_data_dict,
                        measured_value_column=measured_col_for_task,
                        seq_id_column=seq_column # chromosome_column and chromosomes_to_filter_list can be added as arguments
                    )
                    
                    if task_correlation_dict:
                        pearson_r_value = task_correlation_dict.get('pearson_r')
                        
                        # Get UTC timestamp for predictor_name
                        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S.%f")
                        # And append it to the predictor_name
                        predictor_identifier = f"{predictor_name_base}_{task_index}_{timestamp}" if predictor_name_base else f"UnknownPredictor_{task_index}_{timestamp}"
                        
                        all_task_correlation_results.append({
                            "Evaluator": EVALUATOR_NAME,
                            "Predictor Identifier": predictor_identifier,
                            "Task": task_correlation_dict.get("task_type", None),
                            "Requested Cell Type": requested_cell_type,
                            "Predicted Cell Type": task_correlation_dict.get("cell_type_actual", None),
                            "Metric": f"Pearson r: {pearson_r_value}"
                        })

        except Exception as e:
            print(f"An error occurred during correlation calculation: {e}")
            
        # Once all the data is received, save them all into a summary CSV
        # print(all_task_correlation_results)
        if all_task_correlation_results:
            summary_df = pd.DataFrame(all_task_correlation_results)
            csv_file_exists: bool = os.path.isfile(correlation_summary_filepath)
            try:
                summary_df.to_csv(correlation_summary_filepath, mode='a',
                                  sep='\t', header=(not csv_file_exists), index=False)
                if csv_file_exists:
                    print("Appended to existing summary CSV file")
                else:
                    print("Created a new summary CSV file")
                print(f"Saved correlation summary to {correlation_summary_filepath}!")
            except IOError as e:
                print("\nNo correlation resuls were saved!")

    else:
        print("Evaluator run did not complete successfully.")
        print(f"Predictions file not found in '{saved_predictions_path}'.")
        print("Skipping correlation calculation!")
    