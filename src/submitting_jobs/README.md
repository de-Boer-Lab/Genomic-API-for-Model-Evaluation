# How to submit jobs using GAME

When jobs are submitted to a HPC cluster we cannot control which job will be started first which creates complications when trying to create server-client connections since the server must be started first. The following documentation outlines how to launch jobs using Evaluator and Predictor containers. 

There are a few ways that a server-client connection can be established when submitting jobs.

### Option 1: Server saves it's HOST/PORT and Client reads it in (recommended): 

1. The Predictor job script creates a `.txt` file that contains the HOST and PORT that the Predictor will run on. 

2. The Evaluator will run a while loop that checks and wait till this `.txt` file exists which signals that the Predictor has started running and also communicates the HOST and PORT it should connect to. 

3. The Predictor reads in the HOST and PORT and passes those into the `apptainer run` command. 

We recommend this approach as is works across all HPC systems and schedulers. 

### More options coming soon

Notes:

+ In some HPC platforms GPU nodes are isolated from CPU nodes. In this case the Evaluator must also be running on a GPU node to be able to connect to a Predictor.
+ Sometimes there are multiple IP addresses for a node and not all of them have public access. These are system-specific and a user should double-check this. In our HPC system the second IP address in the `hostname -I` list is always public and thus we extract this to use for the server-client connection. 
+ From the time the Predictor creates the `.txt` file till when the TCP connection is started there can be a slight delay. This delay can result in the Evaluator trying to connect to a connection that hasn't started yet. To mitigate this the client will include a re-try loop to connect to the server once it's up and running. 
