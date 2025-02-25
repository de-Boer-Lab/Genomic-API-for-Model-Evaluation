# Configuring Definition File and Running Predictor Container for DREAM-RNN

## Overview

This container for Predictor includes:
    - Predictor script for sequence processing and error handling.
    - Integrated DREAM-RNN model with its dependencies and DREAM conda environment created using `dreamRNN_environment.yml`.
    - Pre-trained model weights (`model_best.pth`) for predictions.
    - Support scripts like `api_preprocessing_utils.py`, `error_message_functions_updated.py`, and `predictor_help_message.json`.

## Usage

We encourage using pre-built containers for this model that are hosted on Zenodo: <https://zenodo.org/records/14861069>.

However, if you are building the container using the provided definition file, ensure you have the following directory structure on the host:

```bash
/path/to/DREAM_RNN/src/predictor_container_apptainer/
├── predictor.def
├── predictor.sif
├── dreamRNN_API_script
│   ├── data
│   │   ├── evaluator_input_sample_test.json
│   │   ├── evaluator_message_more_complex.json
│   │   └── evaluator_message_simple_test.json
│   ├── dreamRNN_predict.py
│   ├── dream_rnn_k562_model_weight
│   │   └── model_best.pth
│   └── prixfixe
├── script_and_utils
│   ├── api_preprocessing_utils.py
│   ├── error_message_functions_updated.py
│   ├── predictor_API_clean_apptainer.py
│   └── predictor_help_message.json
```

### Build the container (SIF)

```bash
apptainer build predictor.sif predictor.def
```

### Run the container

```bash
apptainer run predictor.sif HOST PORT
```

## Details

- The container receives data via a TCP socket and doesn’t require mounted data directories.
- Replace `HOST` and `PORT` with the server and port configuration for the evaluator.

## Purpose

- Facilitates genomic model evaluation and prediction using the DREAM-RNN framework.
- It is designed to seamlessly integrate with other tools via API endpoints.

## Example Command

```bash
apptainer run predictor.sif 172.16.47.244 5000
```

## Arguments

1. `HOST`: IP address or hostname of the Predictor server.
2. `PORT`: Port number the Predictor is listening on.

## Additional Notes about the `%environment` Block in the Definition File

```bash
%environment
    # Prevent automatic binding of host directories
    export APPTAINER_NO_MOUNT="home,tmp,proc,sys,dev"
    export LC_ALL=C
    export PATH="/opt/conda/envs/dream/bin:$PATH"
    export LD_LIBRARY_PATH="/opt/conda/envs/dream/lib:$LD_LIBRARY_PATH"
```

- `export APPTAINER_NO_MOUNT="home,tmp,proc,sys,dev"`:
*Why it is required:* By default, Apptainer automatically mounts host directories (like /home directory, /tmp, /proc, /sys, and /dev) into the container. This can inadvertently expose host data or cause conflicts. Setting this variable disables those automatic mounts so that only explicitly bound directories (using the -B flag) will be available inside the container.

- `export LC_ALL=C`:
This sets the container to use the default “C” (POSIX) locale for consistent sorting, formatting, and error messages, regardless of the host’s locale settings.

- `export PATH="/opt/conda/envs/dream/bin:$PATH"`:
This modifies the `PATH` so that executables in the Conda environment (`dream`) are prioritized. This is important for the use of the Python interpreter and other tools installed in that environment over any system defaults.

- `export LD_LIBRARY_PATH="/opt/conda/envs/dream/lib:$LD_LIBRARY_PATH"`
This ensures that the dynamic linker finds the libraries from the Conda environment first, which is crucial for using the correct versions of shared libraries.

### Additional Links for Reference

- [Apptainer Documentation:](https://apptainer.org/docs/user/latest/)
- [HEP Softwate Foundation -- Introduction to Apptainer/Singularity:](https://hsf-training.github.io/hsf-training-singularity-webpage/)
