#!/bin/bash
# Usage:
#   ./launch-pipeline.sh <COMBO_DIR> <N>               Full pipeline:   Matcher + N workers + PD + Evaluator
#   ./launch-pipeline.sh <COMBO_DIR> --direct          Direct:          1 Predictor + 1 Evaluator (no Matcher, no PD)
#   ./launch-pipeline.sh <COMBO_DIR> --no-matcher <N>  Pool, no Matcher: N workers + PD + Evaluator
#                                                       (for foundation models like Evo2 that don't use the Matcher)
#
# Examples:
#   ./launch-pipeline.sh enformer-fulco 3
#   ./launch-pipeline.sh evo2-consistency_point --direct
#   ./launch-pipeline.sh evo2-cagi5 --no-matcher 4

COMBO_DIR=$1
MODE_ARG=$2

if [ -z "$COMBO_DIR" ] || [ -z "$MODE_ARG" ]; then
    echo "❌ Usage:"
    echo "   Full pipeline:     ./launch-pipeline.sh <COMBO_DIR> <N>"
    echo "   Direct:            ./launch-pipeline.sh <COMBO_DIR> --direct"
    echo "   Pool, no Matcher:  ./launch-pipeline.sh <COMBO_DIR> --no-matcher <N>"
    exit 1
fi

# Abort immediately if the previous sbatch returned no job ID
require_jobid() {
    if [ -z "$1" ]; then
        echo "❌ $2 submission failed -- aborting before dependent jobs are queued."
        exit 1
    fi
}

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMBO_PATH="${SCRIPT_ROOT}/${COMBO_DIR}"
INFO_PATH="${SCRIPT_ROOT}/${COMBO_DIR}"

# Shared Cleanup Block
if [ -d "$INFO_PATH" ]; then
    rm -f "${INFO_PATH}/matcher_info.txt" "${INFO_PATH}/worker_info_"*.txt \
          "${INFO_PATH}/predictor_info.txt" "${INFO_PATH}/preds_ready.txt" \
          "${INFO_PATH}/distributor_config.yaml"
    echo "🧹 Cleared coordination files in ${INFO_PATH}"
fi

# --- EXECUTION SWITCH MATRIX ---
if [ "$MODE_ARG" = "--direct" ]; then
    echo "🎯 Launching Direct Pipeline (No Matcher, No PD) on $(hostname)..."
    echo "------------------------------------------------------"

    JOB_ID_PRED=$(sbatch --parsable --export=ALL,USE_MATCHER=false,USE_PD=false "${COMBO_PATH}/predictor_job.sh")
    require_jobid "$JOB_ID_PRED" "Direct Predictor"
    echo "✅ [1/2] Direct Predictor submitted. Job ID: $JOB_ID_PRED"

    JOB_ID_EVAL=$(sbatch --parsable --dependency=after:$JOB_ID_PRED "${COMBO_PATH}/evaluator_job.sh")
    require_jobid "$JOB_ID_EVAL" "Evaluator"
    echo "✅ [2/2] Evaluator submitted.        Job ID: $JOB_ID_EVAL"

elif [ "$MODE_ARG" = "--no-matcher" ]; then
    NUM_WORKERS=$3
    if [ -z "$NUM_WORKERS" ]; then
        echo "❌ --no-matcher requires a worker count: ./launch-pipeline.sh <COMBO_DIR> --no-matcher <N>"
        exit 1
    fi
    echo "🧬 Launching No-Matcher Pipeline (PD + $NUM_WORKERS workers, NO Matcher) on $(hostname)..."
    echo "------------------------------------------------------"

    # Step 1: Workers (pool mode, no matcher). No matcher dependency -- submit now
    JOB_ID_WORKERS=$(sbatch --parsable \
        --export=ALL,USE_MATCHER=false,USE_PD=true --array=1-${NUM_WORKERS} \
        "${COMBO_PATH}/predictor_job.sh")
    require_jobid "$JOB_ID_WORKERS" "Workers"
    echo "✅ [1/3] Workers submitted.     Job ID: $JOB_ID_WORKERS (Array: 1-${NUM_WORKERS})"

    # Step 2: Distributor
    JOB_ID_PD=$(sbatch --parsable --dependency=after:$JOB_ID_WORKERS "${COMBO_PATH}/pd_job.sh" $NUM_WORKERS)
    require_jobid "$JOB_ID_PD" "Distributor"
    echo "✅ [2/3] Distributor submitted. Job ID: $JOB_ID_PD"

    # Step 3: Evaluator
    JOB_ID_EVAL=$(sbatch --parsable --dependency=after:$JOB_ID_PD "${COMBO_PATH}/evaluator_job.sh")
    require_jobid "$JOB_ID_EVAL" "Evaluator"
    echo "✅ [3/3] Evaluator submitted.   Job ID: $JOB_ID_EVAL"

else
    NUM_WORKERS=$MODE_ARG
    echo "🚀 Launching Full Pipeline with $NUM_WORKERS workers on $(hostname)..."
    echo "------------------------------------------------------"

    # Step 1: Matcher
    JOB_ID_MATCHER=$(sbatch --parsable "${COMBO_PATH}/matcher_job.sh")
    require_jobid "$JOB_ID_MATCHER" "Matcher"
    echo "✅ [1/4] Matcher submitted.     Job ID: $JOB_ID_MATCHER"

    # Step 2: Workers (pool mode, with matcher)
    JOB_ID_WORKERS=$(sbatch --parsable --dependency=after:$JOB_ID_MATCHER \
        --export=ALL,USE_MATCHER=true,USE_PD=true --array=1-${NUM_WORKERS} \
        "${COMBO_PATH}/predictor_job.sh")
    require_jobid "$JOB_ID_WORKERS" "Workers"
    echo "✅ [2/4] Workers submitted.     Job ID: $JOB_ID_WORKERS (Array: 1-${NUM_WORKERS})"

    # Step 3: Distributor
    JOB_ID_PD=$(sbatch --parsable --dependency=after:$JOB_ID_WORKERS "${COMBO_PATH}/pd_job.sh" $NUM_WORKERS)
    require_jobid "$JOB_ID_PD" "Distributor"
    echo "✅ [3/4] Distributor submitted. Job ID: $JOB_ID_PD"

    # Step 4: Evaluator
    JOB_ID_EVAL=$(sbatch --parsable --dependency=after:$JOB_ID_PD "${COMBO_PATH}/evaluator_job.sh")
    require_jobid "$JOB_ID_EVAL" "Evaluator"
    echo "✅ [4/4] Evaluator submitted.   Job ID: $JOB_ID_EVAL"
fi

echo "------------------------------------------------------"
echo "🎉 Pipeline execution initialized successfully!"