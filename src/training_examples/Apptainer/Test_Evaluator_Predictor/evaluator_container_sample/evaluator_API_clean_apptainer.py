#Oct 30th, 2024
import socket
import json
import sys
import os
import struct
from collections import Counter

#function to check for duplicate keys in the JSON file
def check_duplicates(json_file_path):
    """
    Parses a JSON file to detect and report any duplicate keys. If no duplicates
    are found, the JSON data is read into a variable.

    The aim of this function is to count each key's occurrences before
    fully loading the JSON into a dictionary, allowing it to identify
    duplicate keys in the JSON file.

    Args:
        json_file_path (str): The path to the JSON file to parse and check for duplicates.

    Returns:
        dict or None: Returns the parsed JSON data as a dictionary if no duplicates are found.
                      Otherwise, prints the duplicate keys and returns None.
    """

    # Initialize a Counter to track key occurrences
    key_counts = Counter()

    # Use a helper function to track key occurrences while creating a dictionary
    def detect_duplicates(pairs):
        """
        Detects duplicate keys by counting their occurrences.

        This helper function intercepts key-value pairs as they are loaded
        and increments the count for each key in key_counts. The function
        also returns a dictionary of the pairs which is needed for json.load()
        to continue creating the JSON object.

        Args:
            pairs (list of tuple): List of (key, value) pairs from JSON parsing.

        Returns:
            dict: A dictionary created from key-value pairs.
        """
        # `pairs` is a list of key-value pairs in the order they appear in the JSON file
        for keys, value in pairs:
            # Increment the count for each key in `key_counts`
            key_counts[keys] += 1
        # Convert the pairs into a dictionary and feed into json.load
        return dict(pairs)

    try:
        # Load the JSON file with the custom function to detect duplicates
        with open(json_file_path, 'r') as file:
            data = json.load(file, object_pairs_hook=detect_duplicates)

        # Create a dictionary with only those keys that have a count greater than 1 (duplicates)
        duplicates = {keys: count for keys, count in key_counts.items() if count > 1}

        # Output the results
        if duplicates:
            print("Duplicate keys found:", duplicates)
            return None
        else:
            print("No duplicates found.")
            return data

    except FileNotFoundError:
        print(f"File not found: {json_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in file '{json_file_path}': {e}")
        return None

def run_evaluator():
    host = sys.argv[1]
    port = int(sys.argv[2])
    output_dir = sys.argv[3]
    #try creating a socket
    try:
        # create a socket object
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print ("server_error: Error creating socket: %s" % e)
        sys.exit(1)

    try:
        #establish connection with predictor server
        connection.connect((host, port))
        print(f"Connected to Predictor on {host}:{port}")
    except socket.gaierror as e:
        print ("Address-related error connecting to server: %s" % e)
        sys.exit(1)
    except socket.error as e:
        print ("server_error: Connection error: %s" % e)
        sys.exit(1)

    try:
        #load in JSON file from evalutor_data if Predictor container was successful
        cwd = os.getcwd()
        #this function will check the JSON keys for duplicates and if there are none it will return the file
        #jsonResult = check_duplicates(cwd + '/evaluator_data/evaluator_message_more_complex.json')
        #jsonResult = json.dumps(jsonResult)

        #if you don't want to use the check duplicate function use the code below
        jsonResult = json.load(open('/evaluator_data/evaluator_message_more_complex.json'))
        jsonResult = json.dumps(jsonResult)
        #print(jsonResult)
    except json.JSONDecodeError as e:
        print("Invalid JSON syntax:", e)

    #first send the total bytes we are transmitting to the Predictor
    #This is used to stop the recv() process
    #send the evaluator json to the predictor server
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
        #Step 1
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
            while len(json_data_recv) < msglen:
                packet = connection.recv(1024)
                if not packet:
                    print("Connection closed unexpectedly.")
                    break
                json_data_recv += packet
                #print(f"Received packet of {len(packet)} bytes, total received: {len(data)} bytes")

            # Decode and display the received data if all of it is received
            if len(json_data_recv) == msglen:
                print("Predictor return received compleatly")
                break
            else:
                print("Data received was incomplete or corrupted.")
                break


        except socket.error as e:
            print ("server_error: Error receiving predictions: %s" % e)
            sys.exit(1)

    predictor_response_full = json_data_recv
    predictor_json = predictor_response_full.decode("utf-8")
    predictor_json = json.loads(predictor_json)
    #print(predictor_json)

#save predictions to current working directory

    #cwd = os.getcwd()
    with open('/predictions/predictor_return_file.json', 'w', encoding='utf-8') as f:
        json.dump(predictor_json, f, ensure_ascii=False, indent=4)

# ---------------------- %%%%%%%---------------

    connection.close()
    print("Connection to server closed")

run_evaluator()
