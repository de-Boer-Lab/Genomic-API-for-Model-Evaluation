# evaluator_API_clean_apptainer.py
import os
import sys
import json
import time
import tqdm
import struct
import socket

from evaluator_utils import *

# Get the absolute path of the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the input JSON file name
input_json = "evaluator_message_gosai_5seqs.json"

# Determine if running inside a container or not
if os.path.exists("/.singularity.d"):
    # Running inside the container
    EVALUATOR_DATA_DIR = "/evaluator_data"
else:
    # Running outside the container
    EVALUATOR_CONTAINER_DIR = SCRIPT_DIR
    EVALUATOR_DATA_DIR = os.path.join(EVALUATOR_CONTAINER_DIR, "evaluator_data")
    
EVALUATOR_INPUT_PATH = os.path.join(EVALUATOR_DATA_DIR, input_json)
    
# Set buffer size for TCP
BUFFER_SIZE = 65536

# Debug logs for validation
print(f"Using input file: {EVALUATOR_INPUT_PATH}")

def run_evaluator():
    host = sys.argv[1]
    port = int(sys.argv[2])
    output_dir = sys.argv[3]
    
    # Validate input JSON file
    if not os.path.exists(EVALUATOR_INPUT_PATH):
        print(f"Error: Evaluator input file '{EVALUATOR_INPUT_PATH}' does not exist.")
        sys.exit(1)

    # Validate output directory
    if not os.path.exists(output_dir):
        print(f"Error: Output directory '{output_dir}' does not exist.")
        sys.exit(1)
        
    # Try creating a socket
    try:
        # create a socket object
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print ("server_error: Error creating socket: %s" % e)
        sys.exit(1)

    try:
        # establish connection with predictor server
        connection.connect((host, port))
        print(f"Connected to Predictor on {host}:{port}")
    except socket.gaierror as e:
        print ("Address-related error connecting to server: %s" % e)
        sys.exit(1)
    except socket.error as e:
        print ("server_error: Connection error: %s" % e)
        sys.exit(1)

    try:
        # load in JSON file from evalutor_data if Predictor container was successful
        jsonResult = check_duplicates_from_json(EVALUATOR_INPUT_PATH)
        if jsonResult is None:
            sys.exit(1)
        jsonResult = json.dumps(jsonResult)
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
                                 unit_scale=True, unit_divisor=1024)

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
        
        output_file = os.path.join(output_dir, os.path.basename(RETURN_FILE_PATH))
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(predictor_json, f, ensure_ascii=False, indent=4)
        print(f"Predictions saved to {output_file}")
        
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error saving predictions: {e}")
        sys.exit(1)

# ---------------------- %%%%%%%---------------

    connection.close()
    print("Connection to server closed")

run_evaluator()