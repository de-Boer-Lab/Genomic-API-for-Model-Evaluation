'''
Configuration script for Test Predictor from the deBoer Lab.
- Determines if running inside a container or not
- Automatically versions the Predictor name using Apptainer's build-date label.
- Inside container:             "test_predictor_deBoer_20251128-180629_TZ"  (sortable, human-readable)
- Outside container (Dev mode): "test_predictor_deBoer_dev"
'''

import os
import json
from datetime import datetime

# --- Core Predictor Settings ---
# Base model name (gets a build-timestamp suffix inside the container).
predictor_base = "test_predictor_deBoer"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Versioned Predictor Name + Paths ---
if os.path.exists("/.singularity.d"):
    # Running inside the container
    print("Running inside the container...")

    # Read build timestamp from Apptainer's auto-generated labels file to version the name.
    try:
        with open('/.singularity.d/labels.json', 'r') as f:
            labels = json.load(f)
        raw_build_date = labels.get('org.label-schema.build-date', '')

        # Example format: "Friday_28_November_2025_18:6:29_PST"
        # Strip day-of-week and timezone, keep the core date+time.
        parts = raw_build_date.split('_')
        date_str = f"{parts[1]}_{parts[2]}_{parts[3]}_{parts[4]}"

        dt = datetime.strptime(date_str, "%d_%B_%Y_%H:%M:%S")
        build_timestamp = dt.strftime("%Y%m%d-%H%M%S")
        timezone_label = parts[5] if len(parts) > 5 else "UNK"
        PREDICTOR_NAME = f"{predictor_base}_{build_timestamp}_{timezone_label}"

    except Exception as e:
        print(f"Warning: Could not parse build timestamp from labels.json: {e}")
        PREDICTOR_NAME = f"{predictor_base}_unknown"
else:
    # Running outside the container (dev mode)
    print("Running outside the container...")
    PREDICTOR_NAME = f"{predictor_base}_dev"

HELP_FILE = os.path.join(SCRIPT_DIR, "predictor_help_message.json")

# --- Supported Wire Formats ---
# JSON is always supported even when not listed; msgpack is offered for large payloads.
SUPPORTED_REQUEST_FORMATS = [fmt.lower() for fmt in ["application/json", "application/msgpack"]]
SUPPORTED_RESPONSE_FORMATS = [fmt.lower() for fmt in ["application/json", "application/msgpack"]]
