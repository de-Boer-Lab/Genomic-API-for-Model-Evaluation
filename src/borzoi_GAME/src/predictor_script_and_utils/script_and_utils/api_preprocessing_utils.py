# api_preprocessing_utils.py

## model specific checks that cause a "prediction_request_failed" error
def check_seqs_specifications(sequences, json_return_error_model):
    """
    Validates input DNA sequences for the Borzoi model.

    Checks for invalid characters ('N') in sequences and logs errors if found.
    The Borzoi model does not impose a maximum sequence length; 
    sequences longer than 524,288 bases will be truncated internally.

    Args:
        sequences (dict): A dictionary with sequence IDs as keys and DNA sequences as values.
        json_return_error_model (dict): Dictionary to log prediction request errors.

    Returns:
        dict: Updated json_return_error_model with any validation errors.
    """
    for sequence in sequences:
        value = sequences[sequence]
        key = sequence

        if "N" in value:
            json_return_error_model['prediction_request_failed'].append(
                f"sequence in {key} has an invalid character present"
            )
            
    return json_return_error_model

# Borzoi has its own functions to preprocess the sequences; 
# and hence the functions below were not utilized.

def pad_sequence(seq, target_length):
    """
    Pad a sequence, without adapters, with 'N' until it reached the target length.
    
    Args:
        seq (str): The input sequence.
        target_length (int): Model-dependent desired length of the sequence before
                             adding adapters.
    
    Returns:
        padded_seq: The padded sequence.
    """
    seq_len = len(seq)
    
    # If sequence length is less than target_length, excluding adapters, simply
    # pad with Ns until it is target_length and then add the adapters.
    if seq_len < target_length:
        total_padding = target_length - seq_len
        right_padding = 'N' * (total_padding // 2)
        left_padding = 'N' * (total_padding - len(right_padding))
        padded_seq = left_padding + seq + right_padding
        return padded_seq
    
    # When the sequence length, excluding adapters, is the target_length,
    # simply add adapters to each side.
    elif seq_len == target_length:
        return seq
    
    # The condition for when sequence length is greater than the target length  
    # (not including adapter sequences on each side), is a work in progress.
    else:
        truncated_seq =  seq[:target_length] # For now, just truncate [Work in progress]
        return truncated_seq
    
def add_adapters(seq, upstream_adapter, downstream_adapter):
    """
    Add upstream and downstream adapter sequences to a given sequence.
    
    Args:
        seq (str): The input sequence after padding, if needed. 
        upstream_adapter (str): Upstream adapter sequence to prepend.
        downstream_adapter (str): Downstream adapter sequence to append.
        
    Returns:
        seq_with_adapters (str): The sequence with adapters added.
    """
    seq_with_adapters = upstream_adapter + seq + downstream_adapter
    return seq_with_adapters

# One-hot encode sequences
def one_hot_encode(seq):
    """
    Convert a sequence to a one-hot encoded representation.

    Args:
        seq (str): Sequence consisting of 'A', 'T', 'G', 'C', and 'N'.

    Returns:
        list: A one-hot encoded list for the sequence.
    """
    mapping = {'A': [1, 0, 0, 0],
               'G': [0, 1, 0, 0],
               'C': [0, 0, 1, 0],
               'T': [0, 0, 0, 1],
               'N': [0, 0, 0, 0]}
    return [mapping.get(base, [0, 0, 0, 0]) for base in seq]

# Full preprocessing pipeline for a sequence
def process_sequence(seq, target_length, seq_size,
                     upstream_adapter, downstream_adapter):
    """
    Process a sequence by padding, adding adapters, and encoding.

    Args:
        seq (str): The input sequence.
        target_length (int): Length of the sequence before adding adapters (200 for Dream-RNN).
        seq_size (int): Model-specific final sequence size (230 for Dream-RNN)
        upstream_adapter (str): Upstream adapter sequence to prepend.
        downstream_adapter (str): Downstream adapter sequence to append.

    Returns:
        list: A one-hot encoded list with padding and adapters applied.
    """
    # Step 1: Pad the sequence
    padded_seq = pad_sequence(seq, target_length)
    
    # Step 2: Add adapter sequence/ primers
    seq_with_adapters = add_adapters(padded_seq, upstream_adapter, downstream_adapter)

    # Step 3: One-hot encode the sequence
    encoded_seq = one_hot_encode(seq_with_adapters)
    
    return encoded_seq