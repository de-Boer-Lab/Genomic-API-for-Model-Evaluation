# Jan 15, 2025
import socket
import json
import sys
import os
import struct
from collections import Counter
#from create_json import *
import pandas as pd
import tqdm

# Get the current working directory
CWD = os.getcwd()
def create_json(input_data):

    """
    Parses a pandas dataframe to create a JSON object to be sent to a Predictor
    Args:
        input_data: pandas dataframe with DNA sequences

    Returns:
        json object in API format
    """
    #these paramters are decided based on the sequence dataset
    json_evaluator = {'request': 'predict', 'readout': 'point'}
    json_evaluator['prediction_tasks'] = [{'name': 'gosai_synthetic_sequences', 'type': 'expression', 'cell_type': 'K562', 'scale': 'linear', 'species': 'homo_sapiens'}]

    #option flanking sequences can be added here for MPRAs
    #json_evaluator['upstream_seq'] = ['ATGCTT']
    #json_evaluator['downstream_seq'] = ['GATCA']

    sequences = dict(zip(input_data.IDs, input_data.sequence))
    json_evaluator['sequences'] = sequences
    json_evaluator = json.dumps(json_evaluator)

    #if you want to write the JSON to a local directory
    # with open(CWD + '/evalutor_data/evaluator_message_gosai.json', 'w', encoding='utf-8') as f:
    #     json.dump(json_evaluator, f, ensure_ascii=False, indent=4)

    return(json_evaluator)

# File name for input sequences
input_txt = "41586_2024_8070_MOESM4_ESM.txt"

#Determine if running inside a container or not
if os.path.exists("/evaluator_data"):
    # Running inside the container
    EVALUATOR_INPUT_PATH = os.path.join("/evaluator_data", input_txt)

else:
    #Running outside the container
    EVALUATOR_INPUT_PATH = os.path.join(CWD, "evaluator_data", input_txt)

print(EVALUATOR_INPUT_PATH)
# Validate input file path
if not os.path.exists(EVALUATOR_INPUT_PATH):
    print(f"Error: Input file '{EVALUATOR_INPUT_PATH}' does not exist.")
    sys.exit(1)


# Debug logs for validation
print(f"Using input data: {EVALUATOR_INPUT_PATH}")
#print(f"Will save predictions to: {RETURN_FILE_PATH}")

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


    input_data = pd.read_csv(EVALUATOR_INPUT_PATH, sep='\t', header=0)

    # #check if duplicate ID's exist since they will be used as keys for the sequences
    # duplicated_rows = input_data['IDs'][input_data['IDs'].duplicated()]

    #only create JSON object if the values you way to use for the sequence keys are not duplicates
    jsonResult = create_json(input_data)

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

            # Unpack meesage length from 4 bytes
            msglen = struct.unpack('>I', msg_length)[0]
            print(f"Expecting {msglen} bytes of data from the Predictor.")
            # Can comment out print commands other than for errors

            #Step 2
            # Now we want to receive the actual JSON in packets
            progress = tqdm.tqdm(range(msglen), unit="B", desc="Receiving Predictor Message", unit_scale=True, unit_divisor=1024)

            while len(json_data_recv) < msglen:
                packet = connection.recv(65536)
                if not packet:
                    print("Connection closed unexpectedly.")
                    break
                json_data_recv += packet
                progress.update(len(packet))

                #print(f"Received packet of {len(packet)} bytes, total received: {len(data)} bytes")

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

        output_file = os.path.join(output_dir + '/predictions.json')
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
