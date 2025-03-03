# borzoi_evaluator_API.py
import os
import sys
import json
import tqdm
import struct
import socket

from collections import Counter

# Get the absolute path of the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the input JSON file name
input_json = "evaluator_message_more_complex.json"

# Determine if running inside a container or not
if os.path.exists("/.singularity.d"):
    # Running inside the container
    EVALUATOR_DATA_DIR = "/evaluator_data"
    PREDICTIONS_DIR = "/predictions"
else:
    # Running outside the container
    EVALUATOR_SCRIPT_DIR = SCRIPT_DIR
    EVALUATOR_DATA_DIR = os.path.join(EVALUATOR_SCRIPT_DIR, "evaluator_data")
    PREDICTIONS_DIR = os.path.join(EVALUATOR_SCRIPT_DIR, "predictions")
    
EVALUATOR_INPUT_PATH = os.path.join(EVALUATOR_DATA_DIR, input_json)
RETURN_FILE_PATH = os.path.join(PREDICTIONS_DIR, f"borzoi_predictions_{input_json}")

# Validate input file path
if not os.path.exists(EVALUATOR_INPUT_PATH):
    print(f"Error: Input file '{EVALUATOR_INPUT_PATH}' does not exist.")
    sys.exit(1)

# Validate output directory
output_dir = os.path.dirname(RETURN_FILE_PATH)
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory '{output_dir}' did not exist. Created it successfully!")
    # sys.exit(1)
    
# Set buffer size for TCP
BUFFER_SIZE = 65536

# Debug logs for validation
print(f"Using input JSON: {EVALUATOR_INPUT_PATH}")
print(f"Will save predictions to: {RETURN_FILE_PATH}")

#function to check for duplicate keys in the JSON file
def check_duplicates(json_file_path):

    """
    Parses a JSON file to detect and report any duplicate keys at the same level in the same object.
    This function ensures that no keys are silently overwritten in dictionaries.

    The function uses a helper to track the number of times each key appears during parsing,
    leveraging the `object_pairs_hook` parameter of `json.load()` to intercept key-value pairs
    before they are processed into a dictionary. If duplicates are detected at any level, they
    are reported with their counts and paths. Keys reused in separate objects within arrays
    (e.g., lists) are not considered duplicates.

    Args:
        json_file_path (str): The path to the JSON file to parse and check for duplicates.

    Returns:
        None:
            - If no duplicates are found, returns None, prints "No duplicates found."
            - If duplicates are found, prints the duplicate keys and their counts and returns None.
    """

    # Initialize a dictionary to track duplicate keys and their counts
    duplicate_keys = {}

    # Helper function to detect duplicates during JSON parsing
    def detect_duplicates(pairs):

        """
        Detects duplicate keys during JSON parsing and counts occurrences of each key.

        This function intercepts the key-value pairs provided by `json.load` and ensures that
        duplicate keys are flagged. It constructs the dictionary normally but counts how often
        each key appears, recording any keys that occur more than once.

        Args:
            pairs (list of tuple): A list of key-value pairs at the current level of the JSON.

        Returns:
            dict: A dictionary created from the key-value pairs.
        """

        # Use a local Counter to count occurrences of keys at this level
        local_counts = Counter()
        result_dict = {}
        for key, value in pairs:
            # Increment the count for each key
            local_counts[key] += 1
            # If the key is a duplicate, record it in the duplicate_keys dictionary
            if local_counts[key] > 1:
                duplicate_keys[key] = local_counts[key]
            # Add the key-value pair to the resulting dictionary
            result_dict[key] = value
        return result_dict

    try:
        # Open and parse the JSON file, using the helper to track duplicates
        with open(json_file_path, 'r') as file:
            data = json.load(file, object_pairs_hook=detect_duplicates)

        # Report duplicates if any were found
        if duplicate_keys:
            print("Duplicate keys found:")
            for key, count in duplicate_keys.items():
                print(f"Key: {key}, Count: {count}")
            return None  # Indicate that the JSON contains duplicates
        else:
            print("No duplicates found.")
            return data

    except FileNotFoundError:
        # Handle the case where the file is not found
        print(f"File not found: {json_file_path}")
        return None
    except json.JSONDecodeError as e:
        # Handle invalid JSON format errors
        print(f"Invalid JSON in file '{json_file_path}': {e}")
        return None

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
        jsonResult = check_duplicates(EVALUATOR_INPUT_PATH)
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
        
        output_file = RETURN_FILE_PATH # // os.path.join(output_dir, os.path.basename(RETURN_FILE_PATH))
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