'''POST Request with Retry Loop and Deserialize Response in Negotiated MIME Type'''

import sys
import time
import tqdm
import json
import msgpack
import requests
import config

def _make_request_with_retry(http_method, url, **kwargs):
    """
    A single, robust retry function for all network requests.
    Handles connection errors with a constant retry interval.
    """
    
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = requests.request(http_method, url, **kwargs)
            # Raise an error for 4xx/5xx responses
            response.raise_for_status() 
            return response

        # Only retry on network errors, not HTTP errors
        except requests.exceptions.RequestException as e:
            # Don't retry on 4xx/5xx errors, which are not network failures
            if isinstance(e, requests.exceptions.HTTPError):
                raise e
            
            print(f"Network request failed (Attempt {attempt}/{config.MAX_RETRIES})")
            if attempt < config.MAX_RETRIES:
                print(f"Retrying in {config.RETRY_INTERVAL} seconds...")
                for _ in tqdm.tqdm(range(config.RETRY_INTERVAL),
                                   desc="Waiting to retry connection", unit="s"):
                    time.sleep(1)
            else:
                print(f"Tried connecting {attempt} times. Exceeded maximum number of retries. Failed to get formats from Predictor. Exiting...")
                raise e
            

def negotiate_formats(predictor_url):
    """Gets formats from predictor and negotiates the ones to use."""
    formats_url = f"{predictor_url}/formats"
    print(f"--- Negotiating formats with Predictor at {formats_url} ---")

    # The helper function will use timeout=None by default
    # Use 'get' to pull the supported formats from a Predictor
    response = _make_request_with_retry('get', formats_url)
    supported = response.json()

    #Formats the Predictor can handle
    pred_request_fmts = [f.lower() for f in supported.get("predictor_supported_request_formats", [])]
    pred_response_fmts = [f.lower() for f in supported.get("predictor_supported_response_formats", [])]
    
    #All Evaluators and Predictors can handle JSON
    if "application/json" not in pred_request_fmts: 
        pred_request_fmts.append("application/json")
    if "application/json" not in pred_response_fmts:
        pred_response_fmts.append("application/json")
    print(f"Predictor can receive: {pred_request_fmts}")
    print(f"Predictor can send back: {pred_response_fmts}")
    
    # Decide request format having parsed what Predictor can support
    if config.REQUEST_FORMAT in pred_request_fmts:
        negotiated_request_fmt = config.REQUEST_FORMAT
    else:
        negotiated_request_fmt = "application/json"
        if config.REQUEST_FORMAT != "application/json":
            print(f"WARNING: REQUEST_FORMAT='{config.REQUEST_FORMAT}' not supported by Predictor; Using JSON")
    
    # Decide response format
    if config.RESPONSE_FORMAT in pred_response_fmts:
        negotiated_response_fmt = config.RESPONSE_FORMAT
        
    else: 
        negotiated_response_fmt = "application/json"
        if config.RESPONSE_FORMAT != "application/json":
            print(f"WARNING: RESPONSE_FORMAT='{config.RESPONSE_FORMAT}' not supported by Predictor; Using JSON")
    
    print(f"Negotiated Request Format: {negotiated_request_fmt}")
    print(f"Negotiated Response Format: {negotiated_response_fmt}")
    return negotiated_request_fmt, negotiated_response_fmt


def get_predictions(predictor_url, data_dict, negotiated_req_fmt, negotiated_resp_fmt):
    """Posts the data to the predictor and returns the deserialized response."""
    predict_url = f"{predictor_url}/predict"
    
    # Prepare and serialize request
    # Append headers to request JSON
    headers = {"Content-Type": negotiated_req_fmt,
               "Accept": negotiated_resp_fmt}

    print(f"Serializing request as '{negotiated_req_fmt}'")
    if negotiated_req_fmt == "application/msgpack":
        payload_bytes = msgpack.packb(data_dict, use_bin_type=True)
    else:
        payload_bytes = json.dumps(data_dict).encode("utf-8")

    print(f"--- Posting {len(payload_bytes)} bytes to {predict_url} ---")
    
    response = _make_request_with_retry(
        'post', predict_url, 
        headers=headers, data=payload_bytes)
    
    return response

def deserialize_response(response, negotiated_resp_fmt):
    """Safely deserializes a response object based on its Content-Type."""

    response_fmt_actual = response.headers.get("Content-Type","").lower()
    if response_fmt_actual:
        print("Content-Type header was found in response")

        if negotiated_resp_fmt not in response_fmt_actual:
            print(f"Warning: Response format '{response_fmt_actual}' does NOT match negotiated format '{negotiated_resp_fmt}'")
        
        try:
            if "application/msgpack" in response_fmt_actual:
                print(f"De-serializing Predictor response as MsgPack")
                return msgpack.unpackb(response.content, raw=False)
            else:
                # Default to JSON, which handles success and error payloads
                print(f"De-serializing Predictor response as JSON")
                return response.json()
        except (json.JSONDecodeError, msgpack.exceptions.UnpackException) as e:
            print(f"Failed to decode response from Predictor: {e}", file=sys.stderr)
            # Raise a specific error type that the main block can catch
            raise ValueError(f"Failed to decode predictor response: {e}") from e   
    else:
        print("No Content-Type header was found in response, attempting to decode as JSON")
        try:
            return response.json()

        except (json.JSONDecodeError) as e:
            print(f"Failed to decode response from Predictor: {e}", file=sys.stderr)
            # Raise a specific error type that the main block can catch
            raise ValueError(f"Failed to decode predictor response: {e}") from e