# Predictor Distributor

One of the major bottlenecks in large scale model evaluation is the computational time required to make thousands or millions of predictions. The creation of massive genomics datasets will continue to increase rapidly and thus to further future proof GAME’s utility we designed Predictor Distributor (PD). PD is an optional module that serves as an intermediary between the Evaluator and the Predictor to accelerate model evaluation. It can launch multiple instances of identical Predictor modules, receive requests from an Evaluator, split and parallelize the predictions across the sequences, and return the aggregated predictions to the Evaluator. 

### Workflow
1. Start the Matcher module first.
2. Launch N identical Predictor instances, where N is determined by the user's HPC/GPU/memory resources and system thresholds.
3. Start the PD module once all Predictor instances are running; it serves as an intermediary between the Predictors and the Evaluator.
4. The Evaluator connects to the PD.
5. The PD receives the Evaluator request, partitions the metadata and sequences across the N Predictor instances, and sends each partition to its assigned Predictor.
6. After all Predictor responses are returned, the PD reassembles the results and sends the final combined predictions back to the Evaluator, where metrics are computed.

Additional details and code can be found here: {LINK}

### Usage
The PD container can be downloaded from Zenodo: [[ADD LINK HERE]].

**Run the Full GAME Workflow with PD**

Download Predictor, Evaluator, Matcher and PD containers and submission scripts from here: LINK

Make required edits for local/HPC paths.

1. `sbatch matcher_job.sh`
2. `sbatch --array=1-2 pd_worker_job.sh`
3. `sbatch pd_job.sh 2`
4. `sbatch evaluator_job.sh`