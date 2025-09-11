#!/bin/bash
#SBATCH --time=1:00:00           # Request 1 hours of runtime
#SBATCH --account=st-cdeboer-1-gpu      # Specify your allocation code
#SBATCH --nodes=1                 # Request 1 node
#SBATCH --ntasks=1                # Request 1 task
#SBATCH --cpus-per-task=1         # request 1 cpu per task
#SBATCH --gpus=1
#SBATCH --mem=64G                  # Request 32 GB of memory
#SBATCH --job-name=llm_matcher      # Specify the job name
#SBATCH -e /path_to/matcher_err.txt           # Specify the error file. 
#SBATCH -o /path_to/matcher_output.txt           # Specify the output file
#SBATCH --mail-user=ishika.luthra@ubc.ca
#SBATCH --mail-type=ALL
# Load necessary software modules

module load gcc
module load apptainer
# Navigate to the job's working directory
cd $SLURM_SUBMIT_DIR
gpu=$(hostname -I)
echo "Matcher running on $gpu"
#gpu=$(hostname -I | cut -d' ' -f2)
# Save the server node hostname and port to a shared file
#server_host=$(hostname)
matcher_host=$(hostname -I | cut -d' ' -f2)
#Choose free port
matcher_port=$(comm -23 <(seq 5000 6000 | sort) <(ss -tuln | awk '{print $5}' | grep -oE '[0-9]+$' | sort -u) | shuf | head -n 1)


echo "$matcher_host:$matcher_port" > "$PWD/matcher_info.txt"
echo "Matcher is running on $matcher_host at port $matcher_port"

apptainer run --nv /path_to/llm_matcher/matcher_v1.sif "$matcher_host" "$matcher_port"
