#!/bin/bash
# <HPC specific job scheduler directives go here (CPU node allocation is usually sufficient)>

PD_CONTAINER_PATH="<PATH_TO_DISTRIBUTOR_CONTAINER>.sif"
INFO_PATH="<PATH_TO_OUTPUTS>"


module load apptainer

# Set path for config file
# Since this will be mounted at runtime, its path can be anywhere
# Now it is always written in INFO_PATH
CONFIG_FILE="${INFO_PATH}/distributor_config.yaml"

# Navigate to the job's working directory
cd $SLURM_SUBMIT_DIR

# Get the total number of workers from a command-line argument
N_WORKERS=$1
if [ -z "$N_WORKERS" ]; then
    echo "FATAL: Must provide number of workers as an argument."
    exit 1
fi

echo "PredictorDistributor is starting..."
echo "Waiting for $N_WORKERS workers..."

# Loop from 1 to N_WORKERS and wait for each worker's info file
for i in $(seq 1 $N_WORKERS); do
    INFO_FILE="${INFO_PATH}/worker_info_${i}.txt"
    while [ ! -f "$INFO_FILE" ]; do
        echo "Waiting for $INFO_FILE..."
        sleep 5
    done
    echo "Found worker $i info: $(cat $INFO_FILE)"
done

echo "All worker info files found. Now waiting for workers to expose their endpoints..."

# HTTP health check -- verify each worker is actually responding
for i in $(seq 1 $N_WORKERS); do
    INFO_FILE="${INFO_PATH}/worker_info_${i}.txt"
    worker_info=$(cat "$INFO_FILE")
    worker_ip=$(echo $worker_info | cut -d',' -f2)
    worker_port=$(echo $worker_info | cut -d',' -f3)
    
    worker_url="http://${worker_ip}:${worker_port}"
    
    echo "Health checking Worker $i at ${worker_url}..."
    
    # Keep trying until the endpoint responds - job time limit is the timeout
    while true; do
        # Use curl with generous timeouts - this is a startup health check, not production traffic
        if curl -s -f --connect-timeout 10 --max-time 20 "${worker_url}/formats" > /dev/null 2>&1; then
            echo "Worker $i is healthy and responding at ${worker_url}"
            break
        else
            echo "Worker $i: Health check failed, retrying in 30s..."
            sleep 30
        fi
    done
done

echo "ALL $N_WORKERS are serving. Building distributor_config.yaml..."

# Add the static parts of the config file
echo "base_url_template: \"http://{pred_ip}:{pred_port}\"" >> $CONFIG_FILE
echo "predictor_pool:" >> $CONFIG_FILE

# Add each worker to the pool by reading their info files
for i in $(seq 1 $N_WORKERS); do
    INFO_FILE="${INFO_PATH}/worker_info_${i}.txt"
    worker_info=$(cat "$INFO_FILE")
    worker_ip=$(echo $worker_info | cut -d',' -f2)
    worker_port=$(echo $worker_info | cut -d',' -f3)

    # Append this info into the YAML file
    echo "  - id: \"worker_${i}\"" >> $CONFIG_FILE
    echo "    pred_ip: \"${worker_ip}\"" >> $CONFIG_FILE
    echo "    pred_port: \"${worker_port}\"" >> $CONFIG_FILE
done

echo " --- FINAL CONFIG FILE --- "
cat $CONFIG_FILE
echo " ------------------------- "

# Get PD IP and PORT
distributor_host=$(hostname -i)
distributor_port=$(comm -23 <(seq 49152 65535 | sort) <(ss -Htan | awk '{print $4}' | cut -d':' -f2 | sort -u) | shuf | head -n 1)
echo "Using free port: $distributor_port"

# Publish the PD's info into the file that the Evaluator expects
echo "$distributor_host:$distributor_port" > "${INFO_PATH}/predictor_info.txt"
echo "PredictorDistributor running on $distributor_host at port $distributor_port"

# ADDITION: Signal that the PD is starting and is ready for Evaluator
# Calling it preds_ready since PD is meant to be a transparent orchestrator between Evaluator and Predictor Instances
# This should still be able to work even when not using the distributor
echo "ready" > "${INFO_PATH}/preds_ready.txt"
echo "PD ready signal sent to evaluator"

# Run the Distributor container, binding the config file we just built
apptainer run --containall -B "$CONFIG_FILE":/distributor_config.yaml ${PD_CONTAINER_PATH} "$distributor_host" "$distributor_port"
