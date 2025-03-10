#!/bin/bash
#SBATCH --time=5:00:00           # Request 5 hours of runtime
#SBATCH --account=st-cdeboer-1-gpu      # Specify your allocation code
#SBATCH --nodes=1                 # Request 1 node
#SBATCH --ntasks=1                # Request 1 task
#SBATCH --cpus-per-task=1         # request 1 cpu per task
#SBATCH --gpus=2
#SBATCH --mem=32G                  # Request 2 GB of memory
#SBATCH --job-name=dream      # Specify the job name
#SBATCH -e /path/to/pred_err.txt           # Specify the error file.
#SBATCH -o /path/to/pred_output.txt           # Specify the output file

# Load necessary software modules
module load gcc/7.5.0
module load apptainer

# Navigate to the job's working directory
cd $SLURM_SUBMIT_DIR

gpu=$(hostname -I)
echo "Server running on $gpu"

# Save the server node hostname and port to a shared file
server_host=$(hostname -I | cut -d' ' -f2)
server_port=$((RANDOM % 5000 + 20000))  # Random port in range 20000-25000

echo "$server_host:$server_port" > /path/to/predictor_info.txt
echo "Server running on $server_host at port $server_port"

#Run command for the Predictor container
apptainer run --nv /scratch/st-cdeboer-1/iluthra/GAME_API/DREAMRNN/predictor.sif "$server_host" "$server_port"
