#!/bin/bash
# <HPC specific job scheduler directives go here (e.g., keys for GPU allocation, array setup, etc.)>
# NOTE: If using Pool mode, this should be submitted as an array job.

PREDICTOR_CONTAINER_PATH="<PATH_TO_PREDICTOR_CONTAINER>.sif"
INFO_PATH="<PATH_TO_OUTPUTS>"
GPU_GUARD="<PATH_TO_QSUB_SCRIPTS>/gpu_guard.sh"

module load apptainer
cd $SLURM_SUBMIT_DIR

# ---- GPU guard: confirm the container can reach a GPU BEFORE publishing ----
source "${GPU_GUARD}"
gpu_guard_or_die "${PREDICTOR_CONTAINER_PATH}" "Predictor"
# ---------------------------------------------------------------------------

# Network discovery (confirm `hostname -i` returns a address)
pred_host=$(hostname -i)
pred_port=$(comm -23 <(seq 49152 65535 | sort) <(ss -Htan | awk '{print $4}' | cut -d':' -f2 | sort -u) | shuf | head -n 1)

# --- ROUTING MATRIX ---
# Two independent flags set by launch-pipeline.sh:
#   USE_PD       = true  -> publish worker_info_<ID> for the Distributor pool
#                  false -> publish predictor_info + preds_ready directly (no PD)
#   USE_MATCHER  = true  -> wait for the Matcher and pass its host/port to the container
#                  false -> run without the Matcher (foundation models like enformer)
if [ "${USE_PD}" = "true" ]; then
    WORKER_ID=${SLURM_ARRAY_TASK_ID:-1}
    WORKER_INFO_FILE="$INFO_PATH/worker_info_${WORKER_ID}.txt"

    if [ "${USE_MATCHER}" = "true" ]; then
        echo "🔄 Mode: Pool + Matcher (Worker ${WORKER_ID})"
        while [ ! -f "$INFO_PATH/matcher_info.txt" ]; do
            echo "Worker ${WORKER_ID}: Waiting for Matcher..."
            sleep 5
        done
        matcher_info=$(cat "$INFO_PATH/matcher_info.txt")
        matcher_host=$(echo $matcher_info | cut -d':' -f1)
        matcher_port=$(echo $matcher_info | cut -d':' -f2)

        echo "${WORKER_ID},${pred_host},${pred_port}" > "$WORKER_INFO_FILE"
        echo "Worker ${WORKER_ID} on ${pred_host}:${pred_port} -> matcher ${matcher_host}:${matcher_port}"
        apptainer run --nv --containall ${PREDICTOR_CONTAINER_PATH} "$pred_host" "$pred_port" "$matcher_host" "$matcher_port"
    else
        echo "🧬 Mode: Pool, NO Matcher (Worker ${WORKER_ID}) -- foundation model"
        echo "${WORKER_ID},${pred_host},${pred_port}" > "$WORKER_INFO_FILE"
        echo "Worker ${WORKER_ID} on ${pred_host}:${pred_port} (no matcher)"
        apptainer run --nv --containall ${PREDICTOR_CONTAINER_PATH} "$pred_host" "$pred_port"
    fi
else
    echo "🚀 Mode: Direct (No PD, No Matcher)"
    echo "$pred_host:$pred_port" > "${INFO_PATH}/predictor_info.txt"
    echo "ready" > "${INFO_PATH}/preds_ready.txt"
    echo "Direct Predictor active on ${pred_host}:${pred_port}. Evaluator signaled."
    apptainer run --nv --containall ${PREDICTOR_CONTAINER_PATH} "$pred_host" "$pred_port"
fi
