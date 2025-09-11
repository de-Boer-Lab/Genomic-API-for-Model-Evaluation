#!/bin/bash
#SBATCH --time=1:00:00           # Request 1 hours of runtime
#SBATCH --account=st-cdeboer-1-gpu      # Specify your allocation code
#SBATCH --nodes=1                 # Request 1 node
#SBATCH --ntasks=2                # Request 1 task
#SBATCH --cpus-per-task=1         # request 1 cpu per task
#SBATCH --gpus=1
#SBATCH --mem=32G                  # Request 32 GB of memory
#SBATCH --job-name=borzoi      # Specify the job name
#SBATCH -e /path_to/pred_err.txt           # Specify the error file. The %j will be replaced by the Slurm job id.
#SBATCH -o /path_to/pred_output.txt           # Specify the output file
#SBATCH --mail-user=ishika.luthra@ubc.ca
#SBATCH --mail-type=ALL
# Load necessary software modules

module load gcc
module load apptainer
# Navigate to the job's working directory
cd $SLURM_SUBMIT_DIR
gpu=$(hostname -I)
echo "Predictor running on $gpu"

predictor_host=$(hostname -I | cut -d' ' -f2)
#Choose free port to connect on
predictor_port=$(comm -23 <(seq 5000 6000 | sort) <(ss -tuln | awk '{print $5}' | grep -oE '[0-9]+$' | sort -u) | shuf | head -n 1)


#Get matcher information
# Wait for the server info file
while [ ! -f "$PWD/matcher_info.txt" ]; do
    echo "Waiting for Matcher info..."
    sleep 5
done

# Read the Matcher's hostname and port
matcher_info=$(cat "$PWD/matcher_info.txt")
matcher_host=$(echo $matcher_info | cut -d':' -f1)
matcher_port=$(echo $matcher_info | cut -d':' -f2)

echo "$predictor_host:$predictor_port" > "$PWD/predictor_info.txt"
echo "Predictor running on $predictor_host at port $predictor_port"

apptainer run --nv --containall /path_to/borzoi_human_predictor.sif "$predictor_host" "$predictor_port" "$matcher_host" "$matcher_port"
