import json
import pandas as pd
from collections import Counter

def create_json_from_xlsx(input_file_path):
    
    """
    Parses an Excel file, extracts to Pandas DataFrame to create a JSON object to be sent to a Predictor.
    
    Args:
        input_file_path (str): Path to the XLSX file.

    Returns:
        json_evaluator (str): JSON string in API format.
    """
    
    # Read the Excel file, treating the second row as the header (skipping the empty first row)
    df = pd.read_excel(input_file_path, header=1)
    
    # Extract the first column (seq_id (names)) and the last column (sequences -- "230nt sequence (15nt 5' adaptor - 200nt element - 15nt 3' adaptor)")
    names = df.iloc[:, 0]      # sequence ID
    sequences = df.iloc[:, -1] # sequences
    
    # Create a dictionary, mapping each sequence name to its corresponding sequence
    sequence_dict = dict(zip(names, sequences))
    
    # Define the prediction tasks as a separate variable
    prediction_tasks = [
        {
            "name": "agarwal_joint_lib_wtc11",
            "type": "expression",
            "cell_type": "WTC11",
            "scale": "linear",
            "species": "homo_sapiens"
        },
        {
            "name": "agarwal_joint_lib_k562",
            "type": "expression",
            "cell_type": "K562",
            "scale": "linear",
            "species": "homo_sapiens"
        },
        {
            "name": "agarwal_joint_lib_hepg2",
            "type": "accessibility",
            "cell_type": "HEPG2",
            "scale": "linear",
            "species": "homo_sapiens"
        }
    ]
    
    # Build the JSON evaluator object
    evaluator_dict = {
        "request": "predict",
        "readout": "point",
        "prediction_tasks": prediction_tasks,
        "sequences": sequence_dict
    }
    
    # Convert the dictionary to a JSON string with indentation for readability
    json_string = json.dumps(evaluator_dict, indent=4)
    
    return json_string


# Function to check for duplicate keys in the JSON file
# UPDATED FROM PREVIOUS EVALUATORS -- takes JSON string instead of file path
# to support all input format types.
# The OG function is below this one.

def check_duplicates_from_string(json_string):

    """
    Parses a JSON string to detect and report any duplicate keys at the same level in the same object.
    This function ensures that no keys are silently overwritten in dictionaries.

    The function uses a helper to track the number of times each key appears during parsing,
    leveraging the `object_pairs_hook` parameter of `json.loads()` to intercept key-value pairs
    before they are processed into a dictionary. If duplicates are detected at any level, they
    are reported with their counts. Keys reused in separate objects within arrays (e.g., lists) 
    are not considered duplicates.

    Args:
        json_string (str): The JSON content as a string to parse and check for duplicates.

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

        This function intercepts the key-value pairs provided by `json.loads` and ensures that
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
        # Parse the JSON string using the helper to track duplicates
        data = json.loads(json_string, object_pairs_hook=detect_duplicates)

        # Report duplicates if any were found
        if duplicate_keys:
            print("Duplicate keys found:")
            for key, count in duplicate_keys.items():
                print(f"Key: {key}, Count: {count}")
            return None # Return None if duplicates are found
        else:
            print("No duplicates found.")
            return data # Return the parsed data if no duplicates.
    except json.JSONDecodeError as e:
        # Handle invalid JSON format errors
        print(f"Invalid JSON: {e}")
        return None
    
# Function for check duplicates if input file is in JSON format

def check_duplicates_from_json(json_file_path):
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

    # Import necessary libraries
    from collections import Counter
    import json

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
            return None # Return None if duplicates are found
        else:
            print("No duplicates found.")
            return data # Return the parsed data if no duplicates.

    except FileNotFoundError:
        # Handle the case where the file is not found
        print(f"File not found: {json_file_path}")
        return None
    except json.JSONDecodeError as e:
        # Handle invalid JSON format errors
        print(f"Invalid JSON in file '{json_file_path}': {e}")
        return None