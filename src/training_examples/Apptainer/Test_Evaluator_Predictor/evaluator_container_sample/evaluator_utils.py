# evaluator_utils.py

import json
from collections import Counter

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