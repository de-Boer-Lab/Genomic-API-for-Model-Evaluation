#!/bin/bash
# Script to test new Evaluator container against the deBoerTest_model Predictor container.
#
# This script is meant to auto-detect the public IP of the node (or prompts the user if 
# auto-detection fails), picks a random port in the range 20000-25000, starts the test 
# predictor container, waits for it to initialize, and then runs the evaluator container.
#
# Prerequisites:
#   - Apptainer is installed and configured
#   - The test predictor container image (test_predictor.sif) is available
#   - Evaluator container image and required data directories are provided
#
# Usage:
#   ./run_test.sh <evaluator_container> <evaluator_data_dir> <predictions_dir>
#
# Example:
#   ./run_test.sh /path/to/new_evaluator.sif /absolute/path/to/evaluator_data /absolute/path/to/predictions
#
# Arguments:
#   evaluator_container : Path to the evaluator container SIF file
#   evaluator_data_dir  : Absolute path to the directory containing evaluator data
#   predictions_dir     : Absolute path to the directory where predictions will be stored

# Hardcoded predictor container path
# Please change this depending on where the test_predictor.sif is saved
PREDICTOR_CONTAINER="test_predictor.sif"

# Check for evaluator container argument
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <evaluator_container> [evaluatator_data_dir] [predictions_dir]"
    exit 1
fi

# Set required arguments
EVALUATOR_CONTAINER="$1"
EVALUATOR_DATA_DIR="$2"
PREDICTIONS_DIR="$3"

# Auto-detect the server's public IP
SERVER_IP=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}')
# If iproute2 not installed or not on a linux platform, get IP manually
if [ -z "$SERVER_IP" ]; then
    read -p "Could not auto-detect IP address. Please enter your IP: " SERVER_IP
    echo "Using provided IP: $SERVER_IP"
else
    echo "🕵 Detected server IP: $SERVER_IP"
fi

# Now select a random port in the range 20000-25000
SERVER_PORT=$(((RANDOM % 5001) + 20000))
echo "🔌 Using random server port: $SERVER_PORT"

# Start the predictor container and wait for it to fully initialize
echo "Starting test predictor using IP and PORT... 🏁"
echo "Waiting for predictor to initialize... 🕙"
apptainer run "$PREDICTOR_CONTAINER" "$SERVER_IP" "$SERVER_PORT" &
sleep 60s
echo "Ready to test! 😎"

# Now start the evaluator container
echo "Starting the evaluator: $EVALUATOR_CONTAINER on HOST:PORT {$SERVER_IP:$SERVER_PORT}"
apptainer run -B "${EVALUATOR_DATA_DIR}":/evaluator_data \
              -B "${PREDICTIONS_DIR}":/predictions \
              "$EVALUATOR_CONTAINER" "$SERVER_IP" "$SERVER_PORT" /predictions
