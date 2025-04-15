import json
import pandas as pd
from collections import Counter

def create_json(input_data):
    """
    Parses a pandas DataFrame to create a JSON object to be sent to a Predictor.
    
    Args:
        input_data: pandas DataFrame with DNA sequences.
            Expected to have columns 'IDs' and 'sequence'.
    
    Returns:
        str: JSON string in API format.
    """
    # These parameters are decided based on the sequence dataset.
    json_evaluator = {
        "request": "predict",
        "readout": "point"
    }
    json_evaluator["prediction_tasks"] = [
        {
            "name": "gosai_synthetic_sequences",
            "type": "expression", 
            "cell_type": "K562",
            "scale": "linear",
            "species": "homo_sapiens"
        }
    ]
    # Optionally add upstream/downstream sequences here:
    # json_evaluator["upstream_seq"] = ["ATGCTT"]
    # json_evaluator["downstream_seq"] = ["GATCA"]

    # Build the sequences dictionary from the DataFrame
    sequences = dict(zip(input_data.IDs, input_data.sequence))
    json_evaluator["sequences"] = sequences
    json_string = json.dumps(json_evaluator, indent=4)
    
    # # if you want to write the JSON to a local directory
    # with open(CWD + '/evalutor_data/evaluator_message_gosai.json', 'w', encoding='utf-8') as f:
    #     json.dump(json_evaluator, f, ensure_ascii=False, indent=4)

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