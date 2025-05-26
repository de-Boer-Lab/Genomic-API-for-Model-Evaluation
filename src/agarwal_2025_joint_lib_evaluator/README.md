# Configuring Definition File and Running Evaluator Container for Agarwal et al. (2025)

For details regarding:

1. Creating wrapper functions for the API JSON structure
2. Configuring and Running the API:

    - Configuring containers using definition files
    - Purpose of definition files
    - Why containers are used and to learn more about them
please checkout this [documentation](https://github.com/de-Boer-Lab/Genomic-API-for-Model-Evaluation/tree/main/src/DREAM_RNN).

## Overview

This container includes:

- Evaluator API script for genomic sequence evaluation.
- Evaluator helper script for error checking functions.
- Installed Python dependencies required by the Evaluator.

This container is the Evaluator configured for the Genomic API for Model Evaluation (GAME), designed specifically to evaluate model predictions against the Agarwal et al. (2025) Joint Library dataset. The dataset consists of approximately 60,000 candidate cis-regulatory elements (cCREs), including enhancers and promoters systematically tested across HepG2, K562, and WTC11 cell lines, along with positive and negative control sequences. Each element is represented by a 230-bp oligonucleotide.

## Usage

We encourage using pre-built containers for this model that are hosted on Zenodo: <https://zenodo.org/records/15042469>.

However, if you are building the container using the provided definition file, ensure you have the following directory structure on the host:

    ```
    /path/to/evaluator_script_and_utils/
    ├── README.md
    ├── agarwal_evaluator.def
    ├── agarwal_evaluator_joint_lib.py
    ├── evaluator_data
    │   └── 2023-03-03628-s5/
    ├── evaluator_utils.py
    └── predictions/
    ```

### Build the container (SIF)

    ```
    apptainer build agarwal_2025_joint_lib_evaluator.sif agarwal_evaluator.def
    ```

### Bind these directories and run the container

    ```bash
    apptainer run \
      -B absolute/path/to/evaluator_data:/evaluator_data \
      -B absolute/path/to/predictions:/predictions \
      agarwal_2025_joint_lib_evaluator.sif PREDICTOR_HOST PREDICTOR_PORT /predictions
    ```

## Details

    - The container sends and receives data via a TCP socket and requires directories to be mounted.
    - Replace `PREDICTOR_HOST` and `PREDICTOR_PORT` with the server IP and port configuration.

## Purpose

    - Facilitates genomic sequence evaluation by interacting with the Predictor container.
    - Handles input/output through bound directories.

## Example Command

    ```bash
    apptainer run \
      -B absolute/path/to/evaluator_data:/evaluator_data \
      -B absolute/path/to/predictions:/predictions \
      agarwal_2025_joint_lib_evaluator.sif 172.16.47.244 5000 /predictions
    ```

    Arguments:
    1. `PREDICTOR_HOST`: IP address or hostname of the Predictor server.
    2. `PREDICTOR_PORT`: Port number the Predictor is listening on.
    3. `/predictions`: Mounted path inside the container for storing output predictions.

## Additional Notes about the `%environment` Block in the Definition File

    ```bash
    %environment
        # Prevent automatic binding of host directories
        export APPTAINER_NO_MOUNT="home,tmp,proc,sys,dev"
        export LC_ALL=C
        export PATH="/usr/local/bin:$PATH"
    ```

- `export APPTAINER_NO_MOUNT="home,tmp,proc,sys,dev"`:
*Why it is required:* By default, Apptainer automatically mounts host directories (like /home directory, /tmp, /proc, /sys, and /dev) into the container. This can inadvertently expose host data or cause conflicts. Setting this variable disables those automatic mounts so that only explicitly bound directories (using the -B flag) will be available inside the container.

- `export LC_ALL=C`:
This sets the container to use the default “C” (POSIX) locale for consistent sorting, formatting, and error messages, regardless of the host’s locale settings.

- `export PATH="/usr/local/bin:$PATH"`:
This prepends /usr/local/bin (as defined within the container) to the PATH, ensuring that container-specific executables in that directory take precedence.

### Additional Links for Reference

- [Apptainer Documentation:](https://apptainer.org/docs/user/latest/)
- [HEP Softwate Foundation -- Introduction to Apptainer/Singularity:](https://hsf-training.github.io/hsf-training-singularity-webpage/)
- [NSC: Using Apptainer on Berzelius](https://www.nsc.liu.se/support/systems/berzelius-software/berzelius-apptainer/)
