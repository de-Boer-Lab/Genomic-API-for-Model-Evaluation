# borzoi_evaluator_API.py -- Example Evaluator
import os
import sys
import json
import time
import tqdm
import struct
import socket
import msgpack

from evaluator_utils import *

# Get the absolute path of the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the input file name
# This example Evaluator can only take .json/.msgpack inputs
# ALERT: Variable names will change -- JSON-specific names will be changed
input_file = "evaluator_message_more_complex.json"

# Determine if running inside a container or not
if os.path.exists("/.singularity.d"):
    # Running inside the container
    EVALUATOR_DATA_DIR = "/evaluator_data"
else:
    # Running outside the container
    EVALUATOR_DATA_DIR = os.path.join(SCRIPT_DIR, "evaluator_data")
    
EVALUATOR_INPUT_PATH = os.path.join(EVALUATOR_DATA_DIR, input_file)
    
# Set buffer size for TCP
BUFFER_SIZE = 65536

# Debug logs for validation
print(f"Using input file: {EVALUATOR_INPUT_PATH}")

# ------ ADDITION: Configuration for Wire-Format ------
EVAL_PREFERRED_FORMAT = "MsgpAck" # or "json"

EVAL_PREFERRED_FORMAT = EVAL_PREFERRED_FORMAT.lower() # for case-insensitive matching

# - Needs to have a preferred format it wants predictions back in.
# - Reads in the formats that the predictor supports.
# - If preferred MsgPack and Predictor can support it:
#     - Feed input JSON/TXT (which is already converted to JSON string)/MsgPack to evaluator’s send preference [.json and .txt sent as JSONs, .msgpack is sent as MsgPack]
#     - If MsgPack is the input, it will have to be converted to JSON string to get it to pass through check_duplicates function.
#     - Only when it passes that:
#       - Send payload to Predictor -- as MsgPack or JSON (input determines how it is sent).
#     - Receive MsgPack from Predictor.
#     - Convert that to JSON and store.
# - If preferred MsgPack but Predictor cannot handle it:
#     - Throw an error so as to not waste time predicting and sending large predictions as JSON
# - If preferred (return prediction wire_format) is JSON:
#     - If input is .json:
#       - Default JSON ↔ JSON behaviour
#     - If input is .msgpack:
#       - convert to JSON string to pass through check_duplicates
#       - Wire MsgPack at send time (only if predictor can handle it)
#       - predictor will return JSON

# Function to send preferred format for receiveing predictions to Predictor
# Negotiate (for cases when Predictor cannot handle MsgPack)

# ADDITION: Enable negotiation
def negotiate_format_with_predictor(connection):
    
    """
    1. Read the advertised formats from Predictor (received as JSON)
    2. If EVAL_PREFERRED_FORMAT is supported, send back {"format": ...}
    3. Otherwise exit with error.
    Returns:
        Agreed wire_format
    """
    
    # Receive advert from Predictor
    prefix = connection.recv(4)
    if not prefix:
        print("Failed to receive supported formats from Predictor.")
        sys.exit(1)
        
    supported_fmt_len = struct.unpack(">I", prefix)[0]
    supported_fmt = b""
    while len(supported_fmt) < supported_fmt_len:
        chunk = connection.recv(BUFFER_SIZE)
        if not chunk:
            print("Could not receive Predictor's supported wire_format. Closing connection!")
            sys.exit(1)
        supported_fmt += chunk
    try:
        supported = [fmt.lower() for fmt in json.loads(supported_fmt.decode("utf-8"))["formats"]]
        print(f"Predictor supports: {supported}")
    except Exception as e:
        print("Error: Could not parse Predictor's supported formats")
        sys.exit(1)
    
    if EVAL_PREFERRED_FORMAT not in supported:
        print(f"Error: preferred wire format '{EVAL_PREFERRED_FORMAT}' not supported by Predictor. Exiting!")
        sys.exit(1)
        
    # Send Evaluator choice
    choice = json.dumps({"format": EVAL_PREFERRED_FORMAT}).encode('utf-8')
    connection.sendall(struct.pack(">I", len(choice)))
    connection.sendall(choice)
    print(f"Negotiated wire-format: {EVAL_PREFERRED_FORMAT}")
    return EVAL_PREFERRED_FORMAT
    
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
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory '{output_dir}' did not exist. Created it successfully!")
        
    RETURN_FILE_PATH = os.path.join(output_dir, f"borzoi_predictions_{input_file}")
        
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
    wire_fmt = negotiate_format_with_predictor(connection)
    
    # Load in input file from evalutor_data if Predictor connection was successful
    # Validate it though check_duplicates function
    # ADDITION: Load and validate
    if input_file.endswith(".json"): 
        # If input is .txt, adjust accordingly and 
        # use `check_duplicates_from_string`, 
        # assuming JSON string was created using `create_json`
        try:
            data_dict = check_duplicates_from_json(EVALUATOR_INPUT_PATH)
            if data_dict is None:
                sys.exit(1)
        except json.JSONDecodeError as e:
            print("Invalid JSON syntax:", e)
            sys.exit(1)
    else:
        # .msgpack -> raw dict -> JSON string -> check_duplicates_from_string
        try:
            with open(EVALUATOR_INPUT_PATH, "rb") as f:
                raw = msgpack.unpackb(f.read(), raw=False)
        except Exception as e:
            print(f"Error unpacking MsgPack: {e}")
            sys.exit(1)
        
        json_str = json.dumps(raw)
        data_dict = check_duplicates_from_string(json_str)
    
    if data_dict is None:
        print("Couldn't load and validate the input data!")
        sys.exit(1)
    
    # Prepare payload -- serialize
    if wire_fmt == "msgpack":
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

# ---------------------- %%%%%%%---------------
    # Receive message from the server
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
            # Can comment out print commands other than for errors
            
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
            print ("server_error: Error receiving predictions: %s" % e)
            sys.exit(1)

    # Parse and save Predictor response
    try:
        if wire_fmt == "msgpack":
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
        
        output_file = RETURN_FILE_PATH
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(predictor_data, f,
                      ensure_ascii=False, indent=4, 
                      separators=(",", ": "))
        print(f"Predictions saved to {output_file}")
    except Exception as e:
        print(f"Error saving predictions: {e}")
        sys.exit(1)
    finally:
        connection.close()
        print("Connection to server closed")   
    
if __name__ == '__main__':
    run_evaluator()