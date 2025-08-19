#!/bin/bash
#SBATCH --time=1:00:00           # Request 1 hours of runtime
#SBATCH --account=st-cdeboer-1-gpu      # Specify your allocation code
#SBATCH --nodes=1                 # Request 1 node
#SBATCH --ntasks=1                # Request 1 task
#SBATCH --cpus-per-task=1         # request 1 cpu per task
#SBATCH --gpus=1
#SBATCH --mem=32G                  # Request 32 GB of memory
#SBATCH --job-name=consistency     # Specify the job name
#SBATCH -e /path_to/eval_err.txt           # Specify the error file. The %j will be replaced by the Slurm job id.
#SBATCH -o /path_to/eval_output.txt           # Specify the output file
#SBATCH --mail-user=ishika.luthra@ubc.ca
#SBATCH --mail-type=ALL
# Load necessary software modules

module load gcc
module load apptainer

# Navigate to the job's working directory
cd $SLURM_SUBMIT_DIR

# Wait for the server info file
while [ ! -f "$PWD/predictor_info.txt" ]; do
    echo "Waiting for server info..."
    sleep 5
done

# Read the server's hostname and port
predictor_info=$(cat "$PWD/predictor_info.txt")
predictor_host=$(echo $predictor_info | cut -d':' -f1)
predictor_port=$(echo $predictor_info | cut -d':' -f2)

echo "Connecting to server at $predictor_host on port $predictor_port"

apptainer run --nv --containall -B /path_to/evaluator_data_small_test:/evaluator_data -B /path_to/predictions_borzoi:/predictions /path_to/Consistency_evaluator_point_K562.sif "$predictor_host" "$predictor_port" /predictions/
