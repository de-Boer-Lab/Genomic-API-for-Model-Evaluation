# Jan 15, 2025
# gosai_evaluator.py
import os
import sys
import json
import time
import tqdm
import struct
import socket
import pandas as pd

from evaluator_utils import *

# Get the absolute path of the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# File name for input sequences
input_txt = "41586_2024_8070_MOESM4_ESM.txt"

#Determine if running inside a container or not
if os.path.exists("/.singularity.d"):
    # Running inside the container
    EVALUATOR_DATA_DIR = "/evaluator_data"
else:
    #Running outside the container
    EVALURATOR_DATA_DIR = os.path.join(SCRIPT_DIR, "evaluator_data")

EVALUATOR_INPUT_PATH = os.path.join(EVALUATOR_DATA_DIR, input_txt)

output_json_filename = f"gosai_mpra_predictions_{input_txt.replace(".txt", "")}.json"

# Set buffer size for TCP
BUFFER_SIZE = 65536

# Debug logs for validation
print(f"Using input file: {EVALUATOR_INPUT_PATH}")

def run_evaluator():
    host = sys.argv[1]
    port = int(sys.argv[2])
    output_dir = sys.argv[3]
    
    # Validate evaluator input file exists
    if not os.path.exists(EVALUATOR_INPUT_PATH):
        print(f"Error: Evaluator input file '{EVALUATOR_INPUT_PATH}' does not exist.")
        sys.exit(1)

    # Validate output directory; create if it does not
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory '{output_dir}' did not exist. Created it successfully!")
    
    # Compute the full RETURN_FILE_PATH using the provided output directory
    RETURN_FILE_PATH = os.path.join(output_dir, output_json_filename)
    print(f"Will save predictions to: {RETURN_FILE_PATH}")
        
    # Try creating a socket
    try:
        # create a socket object
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print ("server_error: Error creating socket: %s" % e)
        sys.exit(1)

    # Re-try Parameters
    RETRY_INTERVAL = 300 # 300 seconds (5 mins)
    MAX_RETRIES = 5
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
                print(f"Retrying in {RETRY_INTERVAL/60:.0f} minutes... (Attempt {attempt} of {MAX_RETRIES})")
                for _ in tqdm.tqdm(range(RETRY_INTERVAL), desc="Waiting to retry connection", unit="s"):
                    time.sleep(1)
            else:
                print(f"Tried connecting {attempt} times. Exceeded maximum number of retries. Exiting...")
                sys.exit(1)

    try:
        # Load in JSON file from evalutor_data if connection to Predictor container was successful
        # Create JSON string from input file since it is not in JSON format already
        df = pd.read_csv(EVALUATOR_INPUT_PATH, delimiter='\t')
        evaluator_json_str = create_json(df)
                
        # Check for duplicate keys in the generated JSON string.
        # Use the helper function that accepts a JSON string.
        jsonResult_dict = check_duplicates_from_string(evaluator_json_str)
        if jsonResult_dict is None:
            sys.exit(1)
        
        # Convert the validated JSON dictionary back to a JSON string for transmission.    
        jsonResult = json.dumps(jsonResult_dict)
    except json.JSONDecodeError as e:
        print("Invalid JSON syntax:", e)

    # first send the total bytes we are transmitting to the Predictor
    # This is used to stop the recv() process
    # send the evaluator json to the predictor server
    try:
        # Length prefixing
        # Send Evaluator JSON length as a 4-byte integer
        jsonResult_bytes = jsonResult.encode("utf-8")
        jsonResults_total_bytes = len(jsonResult_bytes)

        connection.sendall(struct.pack('>I', jsonResults_total_bytes))
        print(f"Sent evaluator request length {jsonResults_total_bytes} bytes")

        connection.sendall(jsonResult_bytes)

    except socket.error as e:
        print ("server_error: Error sending evaluator_file: %s" % e)
        sys.exit(1)

# ---------------------- %%%%%%%---------------
    # receive message from the server
    json_data_recv = b''
    while True:
        # Before receiving JSON from Predictor
        # Receive length of the incoming JSON message (4-byte integer)
        # Can change to 8-byte integer by changing .recv(4) to .recv(8)
        # and replacing format string '>I' to '>Q'
        # Step 1
        try:
            msg_length = connection.recv(4)
            if not msg_length:
                print("Failed to receive message length. Closing connection.")
                connection.close()
                break # Exit the loop if no message length is received

            # Unpack message length from 4 bytes
            msglen = struct.unpack('>I', msg_length)[0]
            print(f"Expecting {msglen} bytes of data from the Predictor.")
            # Can comment out print commands other than for errors
            
            # Initialize the progress bar
            progress = tqdm.tqdm(range(msglen), unit="B", 
                                 desc="Receiving Predictor Response",
                                 unit_scale=True)

            #Step 2
            # Now we want to receive the actual JSON in packets
            
            while len(json_data_recv) < msglen:
                packet = connection.recv(BUFFER_SIZE)
                if not packet:
                    print("Connection closed unexpectedly.")
                    break
                json_data_recv += packet
                progress.update(len(packet))
                #print(f"Received packet of {len(packet)} bytes, total received: {len(data)} bytes")
           
            # Close the progress bar when done
            progress.close()
            
            # Decode and display the received data if all of it is received
            if len(json_data_recv) == msglen:
                print("Predictor return received completely!")
                break
            else:
                print("Data received was incomplete or corrupted.")
                break


        except socket.error as e:
            print ("server_error: Error receiving predictions: %s" % e)
            sys.exit(1)

    # Parse and save Predictor response
    try:
        predictor_response_full = json_data_recv
        predictor_json = predictor_response_full.decode("utf-8")
        predictor_json = json.loads(predictor_json)
        
        output_file = RETURN_FILE_PATH
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(predictor_json, f, ensure_ascii=False, indent=4, separators=(",", ": ")) # // ADDED separators
        print(f"Predictions saved to {output_file}")
        
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error saving predictions: {e}")
        sys.exit(1)

# ---------------------- %%%%%%%---------------

    connection.close()
    print("Connection to server closed")

run_evaluator()
