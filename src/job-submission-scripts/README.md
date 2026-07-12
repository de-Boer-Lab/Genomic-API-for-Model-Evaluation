# Job Submission Scripts

SLURM + Apptainer launch scripts for running **GAME** pipelines on an HPC cluster. `launch-pipeline.sh` submits a set of
containerized jobs — Matcher, Predictor(s), Predictor-Distributor (PD), and
Evaluator — as a dependency chain, and the jobs coordinate at runtime through a
handful of shared text files.

Every component runs as an Apptainer/Singularity container (`.sif`). Most Predictors
and the Matcher require a GPU; the Distributor and Evaluator run fine on CPU
nodes (confirm that your HPC CPU and GPU nodes have access to each other).

---

## Architecture

The pipeline is a chain of server jobs that hand off to one another by writing
and polling small coordination files in a shared directory. Each stage waits for
the previous stage to publish its `host:port` before it starts talking.

```
                 (full pipeline)

  Matcher ──▶ matcher_info.txt
                    │
                    ▼
  Predictor workers ──▶ worker_info_<ID>.txt   (one per array task)
                    │
                    ▼
  Distributor (PD) ──▶ health-checks each worker at /formats
                    ──▶ builds distributor_config.yaml
                    ──▶ predictor_info.txt + preds_ready.txt
                    │
                    ▼
  Evaluator ──▶ reads predictor_info.txt, connects, runs evaluation
```

The Distributor is a transparent orchestrator: it organizes a pool of Predictor
workers behind a single `host:port`, so the Evaluator always connects to one
endpoint regardless of pool size. In **direct** mode the PD and Matcher are
skipped and the Evaluator talks straight to a single predictor.

---

## Pipeline modes

`launch-pipeline.sh` supports three topologies, selected by its second argument:

| Mode | Invocation | Jobs launched | When to use |
|------|-----------|---------------|-------------|
| **Full** | `<COMBO_DIR> <N>` | Matcher → N workers → PD → Evaluator | Models that use the Matcher, run as a pool |
| **Direct** | `<COMBO_DIR> --direct` | 1 Predictor → Evaluator | Quick single-predictor runs, no PD, no Matcher |
| **No-Matcher** | `<COMBO_DIR> --no-matcher <N>` | N workers → PD → Evaluator | Foundation models (e.g. Evo2) that don't need the Matcher, still pooled |

The two flags that Prive predictor behavior are exported by the launcher into
`predictor_job.sh`:

- `USE_PD=true` → publish `worker_info_<ID>` for the Distributor pool;
  `false` → publish `predictor_info` + `preds_ready` directly.
- `USE_MATCHER=true` → wait for the Matcher and pass its `host:port` to the
  container; `false` → run without it.

---

## Quick start

```bash
# Full pipeline with 3 predictor workers
./launch-pipeline.sh enformer-fulco 3

# Direct: one predictor, one evaluator, no Matcher/PD
./launch-pipeline.sh evo2-consistency_point --direct

# Pool without the Matcher, 4 workers (foundation model)
./launch-pipeline.sh evo2-cagi5 --no-matcher 4
```

On launch, the script first clears stale coordination files from the combo
directory, then submits each job with an SLURM dependency on the one before it.
If any `sbatch` returns no job ID, the launcher aborts before queuing dependents.

---

## Directory layout

`launch-pipeline.sh` and `gpu-guard.sh` live at the top level. Each **combo
directory** (`<COMBO_DIR>`) holds the per-run job scripts and becomes the shared
coordination directory (`INFO_PATH`) for that run:

```
job-submission-scripts/
├── launch-pipeline.sh
├── gpu-guard.sh
├── <combo-dir>/                 # e.g. evo2-cagi5, enformer-fulco
│   ├── matcher_job.sh
│   ├── predictor_job.sh
│   ├── pd_job.sh
│   ├── evaluator_job.sh
│   └── (coordination files written here at runtime)
└── ...
```

The `*_job.sh` files at the top level are **templates**. Copy them into a combo
directory and fill in the container paths and mount points before launching.

---

## Configuration

Each job script has placeholder values to set before first use:

| Script | Set these |
|--------|-----------|
| `predictor_job.sh` | `PREDICTOR_CONTAINER_PATH`, `INFO_PATH`, `GPU_GUARD` |
| `matcher_job.sh` | `MATCHER_CONTAINER_PATH`, `INFO_PATH`, `GPU_GUARD` |
| `pd_job.sh` | `PD_CONTAINER_PATH`, `INFO_PATH` |
| `evaluator_job.sh` | `EVALUATOR_CONTAINER_PATH`, `EVALUATOR_DATA_DIR`, `PREDICTIONS_DIR`, `INFO_PATH` |

Each script's header also has a spot for cluster-specific scheduler directives
(`#SBATCH` keys for partitions, GPU allocation, array setup, output files). The
Predictor job **must** be submitted as an array job in pool modes — the launcher
does this for you via `--array=1-N`.

---

## Script reference

### `launch-pipeline.sh`
Orchestrator. Parses the mode, clears stale coordination files, and submits the
job chain with `sbatch --parsable --dependency=after:<jobid>`. `require_jobid`
aborts the whole launch if any submission fails to return an ID. Worker jobs are
submitted as an array (`--array=1-N`) with `USE_PD`/`USE_MATCHER` exported per
mode.

### `matcher_job.sh`
GPU job. Runs the GPU guard, discovers its own `host:port`, writes
`matcher_info.txt`, then runs the Matcher container. Workers poll for this file
before connecting.

### `predictor_job.sh`
GPU job, usually an array. Runs the GPU guard, then branches on
`USE_PD`/`USE_MATCHER`:

- **Pool + Matcher** — waits for `matcher_info.txt`, writes
  `worker_info_<ID>.txt` (`ID,host,port`), launches the container pointed at the
  Matcher.
- **Pool, no Matcher** — writes `worker_info_<ID>.txt`, launches the container
  with just its own `host:port`.
- **Direct** — writes `predictor_info.txt` + `preds_ready.txt` and launches the
  container directly for the Evaluator.

`WORKER_ID` comes from `SLURM_ARRAY_TASK_ID` (defaults to `1`).

### `pd_job.sh`
Distributor. Takes the worker count `N` as `$1`. Waits for all
`worker_info_<i>.txt` files, then HTTP-health-checks each worker at
`http://<ip>:<port>/formats` until it responds. Builds `distributor_config.yaml`
(a `predictor_pool` list), publishes its own `predictor_info.txt` +
`preds_ready.txt`, and runs the Distributor container with the config bind-mounted
to `/distributor_config.yaml`.

### `evaluator_job.sh`
CPU/GPU job. Waits for `predictor_info.txt` **and** `preds_ready.txt`, reads the
endpoint, then runs the Evaluator container with `EVALUATOR_DATA_DIR` mounted at
`/evaluator_data` and `PREDICTIONS_DIR` at `/predictions`. Results are written to
`/predictions`.

### `gpu-guard.sh`
Sourced helper defining `gpu_guard_or_die <sif> <label>`. Propagates SLURM's
`CUDA_VISIBLE_DEVICES` into the `--containall` container via
`APPTAINERENV_CUDA_VISIBLE_DEVICES`, then runs `nvidia-smi -L` inside the
container. If the GPU isn't visible, it exits non-zero so the job fails fast
instead of silently stalling/slowing on CPU. Framework-agnostic — used by the Matcher and
every predictor.

---

## Coordination files

All written into the combo directory (`INFO_PATH`) and cleared at the start of
each launch.

| File | Written by | Read by | Contents |
|------|-----------|---------|----------|
| `matcher_info.txt` | Matcher | Workers | `host:port` |
| `worker_info_<ID>.txt` | Each worker | PD | `ID,host,port` |
| `predictor_info.txt` | PD (pool) or Predictor (direct) | Evaluator | `host:port` |
| `preds_ready.txt` | PD or Predictor | Evaluator | `ready` |
| `distributor_config.yaml` | PD | Distributor container | `predictor_pool` YAML |

---

## Notes & gotchas

- **`after:` is intentional, not `afterok:`.** Every dependency uses `after:`,
  which fires once the predecessor *starts running* — not when it completes.
  These are long-lived server jobs that never "finish" on their own, so
  `afterok:` would deadlock the chain. 
- **Port selection.** Matcher/Predictor/PD each pick a random free port in the
  ephemeral range (49152–65535) by diffing `seq` against ports already in use
  (`ss`). No fixed ports to reserve.
- **Health-check timeout.** The PD retries the `/formats` check every 30s with no
  cap — the SLURM job's own time limit is the effective timeout.
- **Mounts.** Only the Evaluator bind-mounts host directories (`/evaluator_data`,
  `/predictions`); the others run `--containall` with just `--nv` for GPU access.