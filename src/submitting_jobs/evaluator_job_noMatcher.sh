#!/bin/bash
#SBATCH --time=5:00:00           # Request 5 hours of runtime
#SBATCH --account=st-cdeboer-1-gpu      # Specify your allocation code
#SBATCH --nodes=1                 # Request 1 node
#SBATCH --ntasks=1                # Request 1 task
#SBATCH --cpus-per-task=1         # request 1 cpu per task
#SBATCH --gpus=1
#SBATCH --mem=2G                  # Request 2 GB of memory
#SBATCH --job-name=gosai     # Specify the job name
#SBATCH -e /path/to/eval_err.txt           # Specify the error file.
#SBATCH -o /path/to/eval_output.txt           # Specify the output file

# Load necessary software modules
module load gcc/7.5.0
module load apptainer

# Navigate to the job's working directory
cd $SLURM_SUBMIT_DIR

# Wait for the server info file
while [ ! -f /path/to/predictor_info.txt ]; do
    echo "Waiting for server info..."
    sleep 5
done

# Read the server's hostname and port
server_info=$(cat /path/to/predictor_info.txt)
server_host=$(echo $server_info | cut -d':' -f1)
server_port=$(echo $server_info | cut -d':' -f2)

echo "Connecting to server at $server_host on port $server_port"
#Run command for the Evaluator container
apptainer run --nv --containall -B /path_to/evaluator_data/:/evaluator_data -B /path_to/predictions/:/predictions /path_to/gosai_evaluator.sif "$server_host" "$server_port" /predictions/
