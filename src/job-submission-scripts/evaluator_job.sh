#!/bin/bash
# <HPC specific job scheduler directives go here (CPU node allocation is usually sufficient)>

# Directories to mount
EVALUATOR_DATA_DIR="<PATH_TO_EVALUATOR_DATA>"
PREDICTIONS_DIR="<PATH_TO_SAVE_PREDICTIONS>"

# Evaluator container path
EVALUATOR_CONTAINER_PATH="<PATH_TO_EVALUATOR_CONTAINER>.sif"
INFO_PATH="<PATH_TO_OUTPUTS>"

module load apptainer

# Navigate to the job's working directory
cd $SLURM_SUBMIT_DIR
echo $SLURM_SUBMIT_DIR

# Wait for the server info file
echo "Waiting for PD to publish its info..."
while [ ! -f "$INFO_PATH/predictor_info.txt" ]; do
    echo "Waiting for predictor_info.txt..."
    sleep 5
done

# ADDITION: Wait for Predictor(s) to signal it's actually ready
echo "Waiting for predictors to be ready..."
while [ ! -f "$INFO_PATH/preds_ready.txt" ]; do
    echo "Waiting for preds_ready.txt signal..."
    sleep 5
done

# Read the server's hostname and port
predictor_info=$(cat "$INFO_PATH/predictor_info.txt")
predictor_host=$(echo $predictor_info | cut -d':' -f1)
predictor_port=$(echo $predictor_info | cut -d':' -f2)

echo "Connecting to server at $predictor_host on port $predictor_port"

apptainer run --containall -B ${EVALUATOR_DATA_DIR}:/evaluator_data -B ${PREDICTIONS_DIR}:/predictions ${EVALUATOR_CONTAINER_PATH} "$predictor_host" "$predictor_port" /predictions
