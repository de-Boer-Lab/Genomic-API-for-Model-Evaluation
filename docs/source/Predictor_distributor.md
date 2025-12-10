# Predictor Distributor

One of the major bottlenecks in large scale model evaluation is the computational time required to make thousands or millions of predictions. The creation of massive genomics datasets will continue to increase rapidly and thus to further future proof GAME’s utility we designed Predictor Distributor (PD). PD is an optional module that acts as a transparent orchestration layer implementing a scatter-gather design. The PD acts as an intermediate module that impersonates a single Predictor server to the Evaluator, receiving one large request. It then assumes the role of a client to several, say `N`, independent Predictor worker instances, which are made available by the user to leverage computational resources, e.g. using Slurm on an HPC platform.

The PD first scatters the workload by dividing sequences and corresponding metadata into `N` smaller batches to be sent to the Predictor worker instances. These are dispatched concurrently to the `N` Predictor instances via asynchronous REST API requests.

The PD’s second critical role is stateful reassembly and validation. As it gathers the partial responses, it performs a distributed consistency check: verifying that automated task alignments from the Matcher, e.g. `type_actual`, `cell_type_actual`, etc., are consistent across all worker responses. If inconsistent, the PD aborts the process and returns an error, preventing the aggregation for biologically invalid and incompatible predictions. If consistent, it merges all the sequence-specific predictions, re-sorts the final payload in the order they were requested by the Evaluator, and returns a single, reassembled response.

### Workflow

1. Start the Matcher module first.
2. Launch N identical Predictor instances, where N is determined by the user's HPC, available GPUs, memory resources, and system thresholds.
3. Start the PD module once all Predictor instances are running; it serves as an intermediary between the Predictors and the Evaluator.
4. The Evaluator connects to the PD.
5. The PD receives the Evaluator request, partitions the metadata and sequences across the N Predictor instances, and sends each partition to its assigned Predictor.
6. After all Predictor responses are returned, the PD reassembles the results, performs validation checks, and sends the final combined predictions back to the Evaluator, where metrics are computed.

Additional details and code can be found here: {LINK}

### Usage

The PD container can be downloaded from Zenodo: [[ADD LINK HERE]].

**Run the Full GAME Workflow with PD**

Download Predictor, Evaluator, Matcher and PD containers and submission scripts from here: LINK

Make required edits for local/HPC paths.

1. `sbatch matcher_job.sh`
2. `sbatch --array=1-N pd_worker_job.sh`, where `N` is the number of nodes assigned for Predictor instances.
3. `sbatch pd_job.sh N`
4. `sbatch evaluator_job.sh`