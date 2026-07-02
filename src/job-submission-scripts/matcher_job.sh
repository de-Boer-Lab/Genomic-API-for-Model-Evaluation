#!/bin/bash
# <HPC specific job scheduler directives go here (e.g., #SBATCH keys for GPU allocation, output files, etc.)>

# Load necessary software modules
MATCHER_CONTAINER_PATH="<PATH_TO_MATCHER_CONTAINER>.sif"
INFO_PATH="<PATH_TO_OUTPUTS>"
GPU_GUARD="<PATH_TO_QSUB_SCRIPTS>/gpu_guard.sh"

module load apptainer

# Navigate to the job's working directory
cd $SLURM_SUBMIT_DIR

# ---- GPU guard: confirm the container can reach a GPU BEFORE publishing ----
# matcher_info.txt. A GPU-less matcher exits here instead of stalling the
# pipeline on CPU.
source "${GPU_GUARD}"
gpu_guard_or_die "${MATCHER_CONTAINER_PATH}" "Matcher"
# ---------------------------------------------------------------------------

# Save the server node hostname and port to a shared file
# matcher_host=$(hostname -i | cut -d' ' -f1)
matcher_host=$(hostname -i)
matcher_port=$(comm -23 <(seq 49152 65535 | sort) <(ss -Htan | awk '{print $4}' | cut -d':' -f2 | sort -u) | shuf | head -n 1)

echo "$matcher_host:$matcher_port" > "$INFO_PATH/matcher_info.txt"
echo "Matcher is running on $matcher_host at port $matcher_port"

apptainer run --nv --containall ${MATCHER_CONTAINER_PATH} "$matcher_host" "$matcher_port"
