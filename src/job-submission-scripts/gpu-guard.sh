#!/bin/bash
# ============================================================================
# gpu_guard.sh -- shared GPU sanity guard for ANY CUDA/NVIDIA apptainer job
# (matcher, Enformer, Borzoi, ChromBPNet, DREAM-RNN, ...).
#
#      Verifies the GPU is visible INSIDE the container -- framework-agnostic,
#      using nvidia-smi, which --nv provides in every container. This is a
#      pure "can this job reach a GPU at all" test, which is exactly the
#      failure mode we keep hitting (device not reaching the container)
# ============================================================================

gpu_guard_or_die() {
    local sif="$1"
    local label="${2:-GPU job}"

    if [ -z "$sif" ]; then
        echo "[gpu_guard] FATAL: no container path passed to gpu_guard_or_die." >&2
        exit 1
    fi

    # Make SLURM's GPU assignment visible inside the --containall container.
    # Only set it when SLURM actually gave us one, so we never inject an empty
    # value (which would mean "no GPUs") into the clean single-node case.
    if [ -n "${CUDA_VISIBLE_DEVICES}" ]; then
        export APPTAINERENV_CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES}"
    fi

    echo "[gpu_guard] ${label}: checking GPU on $(hostname) (CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset})..."
    if apptainer exec --nv --containall "${sif}" nvidia-smi -L; then
        echo "[gpu_guard] ${label}: GPU OK."
    else
        echo "[gpu_guard] FATAL: ${label} sees no GPU inside the container on $(hostname); exiting." >&2
        echo "[gpu_guard]   Fir has requeue disabled, so this fails fast instead of retrying." >&2
        echo "[gpu_guard]   --exclusive should prevent this; fix the allocation and resubmit." >&2
        exit 1
    fi
}