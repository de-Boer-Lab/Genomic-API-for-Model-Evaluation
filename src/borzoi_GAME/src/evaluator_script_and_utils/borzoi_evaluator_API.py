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
input_file = "evaluator_message_gosai_1seq_test.json"

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
REQUEST_FORMAT = "JSON" # fallback to "json" if advert does not contain msgpack
REQUEST_FORMAT = REQUEST_FORMAT.lower() # for case-insensitive matching

# Compute send format before connecting to Predictor
PREDICTION_FORMAT = "msgpack" if input_file.endswith(".msgpack") else "json"
PREDICTION_FORMAT = PREDICTION_FORMAT.lower()

# request_format and return_format should always have fallbacks based on what the predictor can support
# Idea is that if the evaluator can read what is advertised, it should be able to decide which format to send
# the request in (given some initial preference). JSON - JSON schema is always supported

# - Needs to have a preferred format it wants predictions back in.
# - Reads in the formats that the predictor supports.
# - If preferred MsgPack and Predictor can support it:
#     - Feed input JSON/TXT (which is already converted to JSON string)/MsgPack to evaluator’s send preference -- sent as first choice, with fallback]
#     - If MsgPack is the input, it will have to be converted to JSON string to get it to pass through check_duplicates function.
#     - Only when it passes that:
#       - Send payload to Predictor -- as MsgPack or JSON (input determines how it is sent).
#     - Receive MsgPack from Predictor.
#     - Convert that to JSON and store.
# - If preferred MsgPack but Predictor cannot handle it:
#     - Throw an error so as to not waste time predicting and sending large predictions as JSON
#     - The logic is that if predictor does not support msgpack, evaluator should never send or request msgpack -- that would be dumb
# - If preferred (return prediction wire_format) is JSON:
#     - If input is .json:
#       - Default JSON-JSON behaviour
#     - If input is .msgpack:
#       - convert to JSON string to pass through check_duplicates
#       - Wire MsgPack at send time (only if predictor can handle it)
#       - predictor will return JSON

# Function to send preferred format for receiveing predictions to Predictor
# Negotiate (for cases when Predictor cannot handle MsgPack)

# ADDITION: Enable negotiation
def negotiate_format_with_predictor(connection):
    
    """
    1. Read the advertised formats from Predictor:
        - "predictor_request_formats"    (what Predictor can RECEIVE)
        - "predictor_prediction_formats" (what Predictor can SEND BACK)
    2. Choose send_format = REQUEST_FORMAT if in predictor_request_formats else "json"
    3. Choose recv_format = PREDICTION_FORMAT if in predictor_prediction_formats else 
    4. Send back {"request_format": send_format, "prediction_format": recv_format}
    
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
        pred_request_fmts = [f.lower() for f in supported.get("predictor_request_formats")]
        pred_prediction_fmts = [f.lower() for f in supported.get("predictor_prediction_formats")]
    except Exception as e:
        print("Error: Could not parse Predictor's supported formats")
        sys.exit(1)
    print(f"Predictor can receive: {pred_request_fmts}")
    print(f"Predictor can send back: {pred_prediction_fmts}")
    
    # Decide request format having parsed what Predictor can support
    if REQUEST_FORMAT in pred_request_fmts:
        send_format = REQUEST_FORMAT
    else:
        send_format = "json"
        if REQUEST_FORMAT != "json":
            print(f"WARNING: REQUEST_FORMAT='{REQUEST_FORMAT}' not supported by Predictor; Using JSON")
    
    # Decide prediction format
    if PREDICTION_FORMAT in pred_prediction_fmts:
        recv_format = PREDICTION_FORMAT
    else: 
        recv_format = "json"
        if PREDICTION_FORMAT != "json":
            print(f"WARNING: PREDICTION_FORMAT='{PREDICTION_FORMAT}' not supported by Predictor; Using JSON")
    
    # Send Evaluator decision back
    choice = json.dumps({
        "request_format": send_format,
        "prediction_format": recv_format
        }).encode('utf-8')
    connection.sendall(struct.pack(">I", len(choice)))
    connection.sendall(choice)
    print(f"Negotiated send format: {send_format}")
    print(f"Negotiated receive format: {recv_format}")
    return send_format, recv_format
    
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
    send_fmt, recv_fmt = negotiate_format_with_predictor(connection)
    
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
    
    # Prepare payload -- Serialize
    print(f"Sending request to Predictor as {send_fmt}")
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