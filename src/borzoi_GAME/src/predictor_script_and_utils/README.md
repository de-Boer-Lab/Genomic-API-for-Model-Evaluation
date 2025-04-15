# Configuring Definition File and Running Predictor Container for Borzoi

For details regarding:

1. Creating wrapper functions for the API JSON structure
2. Configuring and Running the API:

    - Configuring containers using definition files
    - Purpose of definition files
    - Why containers are used and to learn more about them
please checkout this [documentation](https://github.com/de-Boer-Lab/Genomic-API-for-Model-Evaluation/tree/main/src/DREAM_RNN).

## Overview

This container for Predictor includes:
- Predictor script for sequence processing and error handling.
- Integrated Borzoi model with its dependencies and `borzoi-gpu` conda environment created using `borzoi_gpu_environment.yml`.
- Latest Baskerville and Borzoi repositories (as of 2025-02-25), which also contain helper scripts and 4 replicate model weights.
- Support scripts like
    - `api_preprocessing_utils.py`
    - `error_message_functions_updated.py`
    - `predictor_help_message.json`.

**NOTE:** This container ***requires a GPU*** for execution because the Borzoi model relied on TensorFlow's GPU-accelerated operations. Running on CPU may lead to excessive memory usage and thread allocation failures.

## Usage

We encourage using pre-built containers for this model that are hosted on Zenodo: <https://zenodo.org/records/14969579>.

However, if you are building the container using the provided definition file, ensure you have the following directory structure on the host:

```bash
path/to/predictor_script_and_utils
├── README.md
├── borzoi_API_script_and_utils
│   ├── baskerville/
│   ├── borzoi
│   │   ├── LICENSE
│   │   ├── README.md
│   │   ├── borzoi_logo.png
│   │   ├── data/
│   │   ├── download_models.sh
│   │   ├── env_vars.sh
│   │   ├── examples/
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   └── tutorials/
│   ├── borzoi_predict_codebase.py
│   ├── borzoi_utils.py
│   └── simplify_targets
│       ├── borzoi_human_targets_simplified.txt
│       └── parse_borzoi_target.py
├── borzoi_gpu_env.def
├── borzoi_gpu_environment.yml
├── predictor.def
├── borzoi_human_predictor.sif
└── script_and_utils
    ├── api_preprocessing_utils.py
    ├── borzoi_predictor_API.py
    ├── error_message_functions_updated.py
    └── predictor_help_message.json
```

### Model Availability

The model weights can be downloaded as .h5 files by running the `download_models.sh` to download all model replicates and annotations into the `/borzoi/examples/` folder. From the `borzoi_API_script_and_utils/`, run this command:

```bash
cd borzoi
./download_models.sh
```

**NOTE:** Downloading the model weights require python modules like `pyfaidx`. For more details regarding the models, please refer to [Borzoi Github Repository](https://github.com/calico/borzoi?tab=readme-ov-file#model-availability).

The saved models will be arranged as such (based on HUMAN training data only):

```bash
borzoi_API_script_and_utils/borzoi/examples/saved_models
├── f3c0
│   └── train
│       └── model0_best.h5
├── f3c1
│   └── train
│       └── model0_best.h5
├── f3c2
│   └── train
│       └── model0_best.h5
└── f3c3
    └── train
        └── model0_best.h5
```

### Build the container (SIF)

```bash
apptainer build borzoi_human_predictor.sif predictor.def
```

### Run the container

```bash
apptainer run --nv borzoi_human_predictor.sif HOST PORT
```

## Details

- The container receives data via a TCP socket and does not require mounted data directories.
- Replace `HOST` and `PORT` with the server and port configuration for the evaluator to connect to.
- The `--nv` flag sets up the environment of the container to use an NVIDIA GPU and CUDA libraries to run a CUDA-enabled application.

## Purpose

- Facilitates genomic model evaluation and prediction using the Borzoi model.
- It is designed to seamlessly integrate with other tools via API endpoints.

## Example Command

```bash
apptainer run --nv borzoi_human_predictor.sif 172.16.47.244 5000
```

## Arguments

1. `HOST`: IP address or hostname of the Predictor server.
2. `PORT`: Port number the Predictor is listening on.

## Additional Notes about the `%environment` Block in the Definition File

```bash
%environment
    # Prevent automatic binding of host directories
    export APPTAINER_NO_MOUNT="home,tmp,proc,sys,dev"
    # Prepend the borzoi-gpu conda environment's bin directory so its executables (like python3) are used
    export PATH="/opt/conda/envs/borzoi-gpu/bin:$PATH"
    # Set the library search path to prioritize libraries from the borzoi-gpu environment and CUDA libraries
    export LD_LIBRARY_PATH="/opt/conda/envs/borzoi-gpu/lib:/usr/local/cuda/lib64:$LD_LIBRARY_PATH"
    # Define CUDA_HOME pointing to the conda environment    
    export CUDA_HOME="/opt/conda/envs/borzoi-gpu"
    # Configure TensorFlow to use the newer cuDNN frontend API, rather than the legacy API
    export TF_CUDNN_USE_FRONTEND=1
```

- `export APPTAINER_NO_MOUNT="home,tmp,proc,sys,dev"`:
*Why it is required:* By default, Apptainer automatically mounts host directories (like /home directory, /tmp, /proc, /sys, and /dev) into the container. This can inadvertently expose host data or cause conflicts. Setting this variable disables those automatic mounts so that only explicitly bound directories (using the -B flag) will be available inside the container.

### Additional Links for Reference

- [Apptainer Documentation](https://apptainer.org/docs/user/latest/)
- [HEP Softwate Foundation -- Introduction to Apptainer/Singularity](https://hsf-training.github.io/hsf-training-singularity-webpage/)
- [NSC: Using Apptainer on Berzelius](https://www.nsc.liu.se/support/systems/berzelius-software/berzelius-apptainer/)
