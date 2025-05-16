# evaluator_utils.py

import json
from collections import Counter

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

# function to check for duplicate keys in the JSON file
def check_duplicates_from_json(json_file_path):
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