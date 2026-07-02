# Submitting Jobs using GAME modules

When jobs are submitted to a HPC cluster we cannot control which jobs will be started first which can create complications when trying to create server-client connections since the server must be started first. The following documentation outlines how to launch jobs using Evaluator and Predictor containers.

## Predictor server saves its HOST/PORT and Evaluator client reads it in (recommended)

1. The Predictor job script creates a `.txt` file that contains the HOST and PORT that the Predictor will run on.
2. The Evaluator will run a while loop that checks and waits till this `.txt` file exists which signals that the Predictor has started running and also communicates the HOST and PORT it should connect to.
3. The Predictor reads in the HOST and PORT and passes those into the `apptainer run` command.

We recommend this approach as it should work across all HPC systems and schedulers. Sample scripts can be found here: [LINK]

**Notes:**

- In some HPC platforms GPU nodes are isolated from CPU nodes. In this case the Evaluator must also be running on a GPU node to be able to connect to a Predictor.
- Sometimes there are multiple IP addresses for a node and not all of them have public access. These are system-specific and a user should double-check this. In our HPC system the second IP address in the `hostname -I` list is always public and thus we extract this to use for the server-client connection.
- From the time the Predictor creates the `.txt` file till when the endpoint is exposed for connection, there can be a slight delay. This delay can result in the Evaluator trying to connect to a connection that hasn't started yet. To mitigate this the client includes a re-try loop to connect to the server once it's up and running.

## Adapt the sample scripts to your cluster

The sample scripts are a starting point, not a drop-in solution. They assume a specific scheduler, account format, GPU-request syntax, walltime cap, and filesystem layout, all of which vary by cluster, so check your cluster's own documentation for cluster-specific policies.

## Notes for larger runs

The recommended approach above handles one Predictor and one Evaluator. For large requests you can run several Predictor instances behind the Predictor Distributor (PD), which splits one request across the workers and reassembles the response. See the [Predictor Distributor](Predictor_distributor) documentation for the full workflow. A few things carry over to the job scripts:

- **Some Predictors don't need the Matcher:** The Matcher maps an Evaluator's requested tasks to a Predictor's outputs automatically, which removes manual-matching bias. A Predictor with its own internal mapping logic can skip it. This is a property of how the Predictor is built, not of the model class. Keep "use the Matcher" and "use the PD" as separate switches so either can run without the other.
- **Request size vs GPU memory:** A very large request can exceed GPU memory in a single forward pass. Splitting the request across more Predictor workers reduces each worker's share, which is usually easier than changing the Predictor, provided the Predictor's bottleneck is per-request compute, not model load time
- **Predictors may fail individual tasks:** A multi-task Predictor is allowed to fail one task (e.g. an unsupported track) and return an error for it while still returning predictions for the others. Evaluators should handle a per-task error by scoring the tasks that succeeded and marking the rest, rather than treating the whole response as failed.

## Common issues

- **Everything downstream hangs:** If the Predictor never writes its info file, the Evaluator waits forever. Almost every stuck pipeline traces back to a server-side job that failed before publishing, so check the earliest job's log first, not the one that looks stuck.
- **Stale coordination files:** Info files persist on shared storage between runs. Because the Evaluator connects as soon as it sees an info file, a leftover file from a previous run can point it at a dead endpoint. Clear the coordination files at the start of each launch.
