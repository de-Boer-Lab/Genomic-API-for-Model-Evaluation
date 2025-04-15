# Configuring and Containerizing the DREAM-RNN Model with Genomic Model Evaluation API

## **Overview**

This document outlines the structure of the API codebase for DREAM-RNN and how it integrates with the containerized setup.

---

---

## **1. DREAM-RNN-API  Structure**

The DREAM-RNN-API is organized as follows:

```bash
DREAM_RNN/
├── dreamRNN_environment.yml          # Conda environment file
└── src
    ├── evaluator_container_apptainer
    │   ├── evaluator.def                                # Evaluator container definition file
    │   ├── evaluator.sif                                # Evaluator container image (not included on Github due to storage restrictions)
    │   ├── evaluator_API_clean_apptainer.py             # Evaluator API script
    │   ├── evaluator_data
    │   │   ├── evaluator_input_sample_test.json         # Sample input JSON for evaluator
    │   │   ├── evaluator_message_more_complex.json      # Complex evaluator input example
    │   │   └── evaluator_message_simple_test.json       # Simple evaluator input example
    │   └── predictions/
    └── predictor_container_apptainer
        ├── dreamRNN_API_script
        │   ├── data/
        │   ├── dreamRNN_predict.py                      # DREAM_RNN prediction script
        │   ├── dream_rnn_k562_model_weight              # Pre-trained model weights
        │   │   ├── all_losses.json
        │   │   ├── model_best.pth
        │   │   ├── optimizer_best.pth
        │   │   ├── scheduler_best.pth
        │   │   ├── test_metric.json
        │   │   └── val_metrics.json
        │   └── prixfixe/                                 # Model framework scripts
        ├── predictor.def                                 # Predictor container definition file
        ├── predictor.sif                                 # Predictor container image (not included on Github due to storage restrictions)
        └── script_and_utils                              # Additional utility scripts
            ├── api_preprocessing_utils.py
            ├── error_message_functions_updated.py
            ├── predictor_API_clean_apptainer.py
            └── predictor_help_message.json
```

---

---

## **2. Understanding the API**

### **2.1. Evaluator API**

- **Purpose**: Interfaces with the Predictor API to send input and receive predictions. It handles input validation, data transfer, and output storage.
- **Core Script**: `evaluator_API_clean_apptainer.py`.
- **Key Features**
    1. **Dynamic Path Handling**:
        - Uses `os.path.exists` to determine if the script is running inside the container.
        - Adjusts paths to input (`EVALUATOR_INPUT_PATH`) and output (`RETURN_FILE_PATH`) accordingly.
    2. **Input Validation**:
        - Ensures the presence of the required input JSON file and the output directory.
        - Validates the JSON file for duplicate keys using the `check_duplicates` function.
    3. **Socket Communication**:
        - Establishes a TCP socket connection with the Predictor server.
        - Implements length prefixing for the JSON payload to ensure reliable data transfer.
    4. **Data Transfer**:
        - Sends the input JSON file (after validation) to the Predictor API over the established connection.
        - Receives predictions as a JSON response, ensuring data integrity and completeness.
    5. **Output Management**:
        - Dynamically determines where to save the prediction results:
            - Inside the container: `/predictions/`.
            - Outside the container: The host-mounted directory mapped to `predictions/`.
        - Ensures output is saved in a consistent and accessible location.

---

### **2.2. Predictor API**

- **Purpose**: Handles incoming requests from the Evaluator API, validates and processes inputs, and generates predictions using the DREAM-RNN model.
- **Core Script**: `predictor_API_clean_apptainer.py`.
- **Supporting Scripts, Error Handling, Help Files**:
  - `api_preprocessing_utils.py`
  - `error_message_functions_updated.py`
  - `predictor_help_message.json`.
- [PrixFixe](https://github.com/de-Boer-Lab/random-promoter-dream-challenge-2022/blob/main/prixfixe/readme.MD) Framework.
- **Key Features**:
    1. **Dynamic Path Handling**:
        - Uses `os.path.exists` to determine if the script is running inside the container.
        - Adjusts the path to the DREAM-RNN model (`DREAM_DIR`) and helper files (`HELP_FILE`) accordingly.
    2. **Socket Communication**:
        - **Server Setup**: Creates and binds a TCP socket to listen for incoming requests from the Evaluator API.
        - **Length Prefixing**: Uses a 4-byte length prefix for receiving and sending JSON payloads reliably.
    3. **Request Validation**:
        - Validates mandatory keys (`request`, `prediction_tasks`, etc.) and values in the incoming JSON request using error-checking functions.
        - Returns error messages if any validation step fails.
    4. **Prediction Workflow**:
        - Extracts and validates sequences and prediction tasks.
        - Prepares and sends sequences to the DREAM-RNN model using `predict_dream_rnn`.
        - Generates a structured JSON response with:
            - Metadata (`type_actual`, `cell_type_actual`, etc.).
            - Prediction results.
    5. **Dynamic Help Handling**:
        - Returns a help message if the `request` is `"help"`, loading information from the `HELP_FILE`.
    6. **Data Transfer**:
        - Sends error messages, help content, or predictions back to the Evaluator API using length-prefixed JSON.

---

---

## Interlude: Creating a Wrapper Function for API JSON Structure

Before diving into the configuration and running of the API, it is important to ensure that the output of DREAM-RNN (the raw predictions) are structured in compliance with the API’s JSON format.

The Predictor API relies on the model’s output as the foundation for constructing its JSON response. The integration process becomes highly efficient as long as the model adheres to the `seq_id: expression_prediction` format, which DREAM-RNN does already.

### **Structure of the API JSON Format**

The API JSON format wraps predictions with metadata to describe tasks, cell types, and scaling. An example prediction JSON structure:

```json
{
    "request": "predict",
    "prediction_tasks": [
        {
            "name": "task1",
            "type_requested": "expression",
            "type_actual": "expression",
            "cell_type_requested": "HEPG2",
            "cell_type_actual": "K562",
            "scale_prediction_requested": "linear",
            "scale_prediction_actual": "linear",
            "species_requested": "homo_sapiens",
            "species_actual": "homo_sapiens",
            "predictions": {
                "seq1": [
                    0.3173099458217621
                ],
                "seq2": [
                    0.33908841013908386
                ],
                "random_seq": [
                    0.37649109959602356
                ],
                "enhancer": [
                    0.37649109959602356
                ],
                "control": [
                    0.37649109959602356
                ]
            }
        }
    ]
}
```

### Why Structure Predictions?

- **Standardization**: Ensures predictions are formatted with metadata and nested appropriately for the API.
- **Compatibility**: Bridges the gap between raw predictions and the API’s required JSON format.
- **Dynamic Handling**: Allows the system to scale across diverse input sequences and multiple prediction tasks, enhancing flexibility.

The wrapper allows for predictions to be made by the model when the `predict_dream_rnn(sequences, include_rev=True)` is called by the Predictor API, returning predictions in a dictionary format, such that they can just be appended into the API JSON schema.

---

---

## **3. Configuring and Running the API** (Similar to [Basic Instructions for Test Evaluator and Predictor](https://github.com/de-Boer-Lab/Genomic-API-for-Model-Evaluation/tree/main/src/training_examples/Apptainer/Test_Evaluator_Predictor))

### 3.1 Configuring the Containers Using Definition Files

Containerizing the DREAM-RNN API involves creating **definition (.def) files** that specify the structure, dependencies, and environment of the container. This ensures a consistent and reproducible environment for running the Predictor and Evaluator APIs.

### **Purpose of [Definition Files](https://apptainer.org/docs/user/latest/definition_files.html)**

Definition files provide a declarative way to define:

1. **Base Image**: The starting point of the container (e.g., ubuntu or python:3.9-slim).
2. **File Structure**: Which files to copy into the container during build and which directories to bind/mount at runtime.
3. **Dependencies**: System-level and Python libraries required for the API to function.
4. **Execution Environment**: Configurations such as environment variables, Python environments, and permissions.
5. **Entry point**: Specifies the script to run when the container starts.

### Why Containers for APIs?

1. **Reproducibility**: Containers guarantee the same environment across different systems.
2. **Modularity**: Encapsulates all dependencies, scripts, and configurations in a single container.
3. **Portability**: Allows seamless deployment on various platforms, whether it is local or HPC clusters.

### **Why These Specific Configurations?**

### **Evaluator API Container**

1. **Base Image**:
    - `python:3.13-slim` is chosen for its lightweight nature and Python-specific optimizations.
    - This base image minimizes overhead while supporting Python dependencies.
2. **File Inclusions**:
    - **Core Script**: The primary script, `evaluator_API_clean_apptainer.py`, is copied into the container.
    - **Dynamic Mounting**: Input (`/evaluator_data`) and output (`/predictions`) directories are mounted at runtime to allow flexibility in handling data without modifying the container.
3. **Environment Variables**:
    - Environment variables like `PATH` ensure the container correctly locates system-installed Python and its dependencies, such as `numpy` and `tqdm`.
    - This helps maintain a consistent execution environment inside the container.
4. **Runtime Needs**:
    - **Mounted Directories**: The Evaluator container dynamically binds host directories to `/evaluator_data` and `/predictions` within the container.
    - This ensures the Evaluator can process new inputs and save outputs without rebuilding the container.

### **Predictor API Container**

1. **Base Image**:
    - `python:3.13-slim` is chosen for its lightweight nature and Python-specific optimizations.
    - This base image minimizes overhead while supporting Python dependencies.
2. **File Inclusions**:
    - **Core Script**: `predictor_API_clean_apptainer.py`, responsible for processing requests and interacting with the model.
    - **Model-Related Files**:
        - `dreamRNN_predict.py`: Handles model loading and predictions.
        - Pre-trained model weights (`model_best.pth`).
    - **Supporting Scripts, Error Handling, Help Files**:
        - `api_preprocessing_utils.py` for general sequence preprocessing functions, like encoding, padding, specification checks, etc. Additional general functions may be added, if required.
        - `error_message_functions_updated.py` for error handling.
        - `predictor_help_message.json` to provide metadata about the API.
    - [PrixFixe](https://github.com/de-Boer-Lab/random-promoter-dream-challenge-2022/blob/main/prixfixe/readme.MD) **Framework**: Essential for the DREAM-RNN prediction pipeline.
3. **Environment Variables**:
    - `PATH` and `LD_LIBRARY_PATH` ensure the `dream` Conda environment is used during runtime, isolating dependencies required for prediction tasks.
4. **Runtime Needs**:
    - No mounting is required as the Predictor container is pre-packaged with all scripts, dependencies, and data files.
    - This design simplifies deployment, making the container self-contained and portable.

---

### 3.2. Building The Containers

Once the definition files for the Evaluator and Predictor APIs are configured, the next step is to build the container images. This process involves using the `apptainer build` command to convert the `.def` files into Singularity Image Format (SIF) files.

### **Steps to Build the Containers**

1. **Set Up the Definition File**:
    - Ensure that the `.def` file includes all necessary files, directories, and dependencies.
    - Files that need to be copied into the container should be included in the  `%files`  section
    - Specific environment specific variables are listed in the  `%enviroment`  section
    - Key configurations like `chmod` for full directory and file access are defined in the `%post` section. Dependencies are installed in this section.
    - Commands that the container will run should be included in  `%runscript` section
    - Metadata for the container is included in the  `%labels` section and any help information that will be shown to the user should be           listed in the  `%help` section.
    - Additional information can be found here: <https://apptainer.org/docs/user/main/definition_files.html>

2. **Run the Build Command**:
    - Use the `apptainer build` command to create the SIF file in their respective directories:

        ```bash
        apptainer build evaluator.sif evaluator.def
        apptainer build predictor.sif predictor.def
        ```

    - The first argument specifies the output SIF file (e.g., `evaluator.sif`).
    - The second argument specifies the definition file to use (e.g., `evaluator.def`).
3. **Verify Build Success**:
    - After the build completes, confirm the presence of the SIF files:

        ```bash
        ls -l *.sif
        ```

    - The resulting `evaluator.sif` and `predictor.sif` files should now be available in the working directory, within their own subdirectories: `prediction_container_apptainer`.

---

### **⚠️ Permissions Management ⚠️**

- During the container build, it’s critical to ensure that directories and files copied into the container or created inside it have the correct permissions. This is handled using `chmod` in the `%post` section of the `.def` files.

1. **Directories Created Inside the Container**:
    - For the Evaluator container:

        ```bash
        chmod -R 755 /evaluator_container_apptainer
        ```

    - These directories are used for runtime-mounted data handling and must be accessible to ensure seamless input/output operations.
2. **Files Copied into the Container**:
    - Files such as `predictor_API_clean_apptainer.py` or model weight files (`model_best.pth`) are copied into specific locations:

        ```bash
        chmod -R 755 /dreamRNN_API_script /prediction_container_apptainer
        chmod +x /opt/conda/envs/dream/bin/python3
        ```

    - Setting `+x` (execute) permissions for the Python interpreter ensures scripts execute properly.
3. **Why Use `chmod`?**
    - Ensures all scripts, directories, and resources are accessible inside the container at runtime.
    - Prevents issues with restricted permissions that could cause runtime errors when reading or writing data.

---

### **3.3. Running the Predictor API**

**Important: The Predictor container must be started before the Evaluator container. This is because the Evaluator relies on an active socket connection to the Predictor for communication.**

1. **Start the Predictor API container**

    The Predictor API must be running first since it listens for incoming connections from the Evaluator. Use the following command to start the Predictor:

    ```bash
    apptainer run predictor.sif HOST PORT
    ```

    - Replace `HOST` with the server's IP, which can be found using `hostname -I`, and `PORT` with the desired [port number](https://www.geeksforgeeks.org/50-common-ports-you-should-know/).
    - The Predictor container will bind to the specified host and port and wait for connections.
    - Ensure that the port (e.g., `5000`) is open and not blocked by any firewall or network policies. Ports above 1024 are usually free to use on most computers/servers.
2. **Validate the server**
    - Ensure it listens on the specified host and port.
    - Example:

        ```bash
        Listening on 172.16.47.244:5000
        ```

---

### **3.4. Running the Evaluator API**

1. **Mount the required directories**

    After confirming that the Predictor is running, start the Evaluator container:

    ```bash
    apptainer run \
       -B absolute/path/to/evaluator_data:/evaluator_data \
       -B absolute/path/to/predictions:/predictions \
       evaluator.sif PREDICTOR_HOST PREDICTOR_PORT /predictions
    ```

    When mounting directories in Apptainer, you can specify the source directory using either an absolute or a relative path. If a relative path is used, Apptainer resolves it based on the current working directory from which the command is executed. To avoid ambiguity and ensure clarity, it is recommended to always use absolute paths.

2. **Key arguments**
    - `PREDICTOR_HOST`: IP address of the Predictor API server.
    - `PREDICTOR_PORT`: Port number for the Predictor API.
    - `/predictions`: Path to save predictions (inside the container).
    - Example:

        ```bash
        apptainer run \
          -B /local/path/to/evaluator_data:/evaluator_data \
          -B /local/path/to/predictions:/predictions \
          evaluator.sif 172.16.47.244 5000 /predictions
        ```

**Why Runtime Mounting?**:

- Runtime mounting (-B) ensures flexibility:
  - The **Evaluator container** mounts directories like /evaluator_data and /predictions to read input and write output without requiring files to be embedded/copied/created inside the container.
  - The **Predictor container**, by contrast, does not need mounting for this container since all necessary files (e.g., model weights, helper scripts) are already copied into the container. In some cases you may want to use files that are not copied into the container at run time and these can be placed in the `/predictor_data` folder.

---

---

## **4. Example Input and Output JSON Files**

### **4.1. Input JSON**

- Located in the `evaluator_data/` directory.
- Example structure:

    ```json
    {
    "request": "predict",
    "readout": "point",
    "prediction_tasks": [
        {
        "name": "gosai_synthetic_sequences",
        "type": "expression",
        "cell_type": "K562",
        "scale": "linear",
        "species": "homo_sapiens"
        }
    ],
    "sequences":{
        "7:70038969:G:T:A:wC": "CCTGGTCTTTCTTGCTAAATAAACATATCGTGCATCATCCAGATCTTGCTGAAATTTGGGGGATATGCATTGAAGCAGCCCCTGTTTCTCCATGAAGGTTTATGTCTGTGAGCCTGGCTGTGCAGTTGGGAGGCCTGGGGGAGAGGTCATGCTTCTACCATGGCGTTTTCCATTTTCCTTAAAATGTGCCTCAGCAACAG",
        "1:192696196:C:T:A:wC": "CATAAAGATGAGGCTTGGCAAAGAACATCTCTCGGTGCCTCCCATTTCATTGTCCCTAAAGTAGAAGCTGAGTGTCATCATTTGTTAAAATTGGGGAAGTCTCCGAGGTGTGGGTTCATCAGAACAATAGCCACTGTTGCCTGTGGTCACAGTCACTGAAGCTGGGGTCCTGGTCACTACTCCAACAGCTGGGAGGCAGC",
        "1:211209457:C:T:A:wC": "CATAAAGCCAATCACTGAGATGACAAGTACTGCCAGGAAAGAAGGCTTTAATCGGGTATTGCAGCTGAAGAGATAGGAGAGCAGTCTCAAATCCATCTCTCTGACCAACTAAAATTGGGGGTTTATGTAGTGGGGAAGGAATGTAGCTACATGTGGGTAAACAGGAATTAGGGAGGGGTAGGGAAGAAGAGTTGGCCATC",
        "15:89574440:GT:G:A:wC": "CATAAAGGCAGTGTAGACCCAAACAGTGAGCAGTAGCAAGATTTATTACAAAGAGCGAAAGAAGAACGAAACCACATCGCAAAACGGAACTCCAGCCGGTTGCCACTACTGCCTCGGGCAGCCTGCTTTTATTCTCTTATCTGGCCCCACCCACATCCTGCTGATTGGTCCATTTTACAGAGAGTGGATTGGTCCATTT",
        "15:89574440:GT:G:R:wC": "CATAAAGGCAGTGTAGACCCAAACAGTGAGCAGTAGCAAGATTTATTACAAAGAGCGAAAGAAGAACGAAACCACATCGCAAAACGGAACTCCAGCCGGTTTGCCACTACTGCCTCGGGCAGCCTGCTTTTATTCTCTTATCTGGCCCCACCCACATCCTGCTGATTGGTCCATTTTACAGAGAGTGGATTGGTCCATTT"
        }
    }
    
    ```

### **4.2. Output JSON**

- Saved in the `predictions/` directory.
- Example structure:

    ```json
    {
    "request": "predict",
    "prediction_tasks": [
        {
            "name": "gosai_synthetic_sequences",
            "type_requested": "expression",
            "type_actual": "expression",
            "cell_type_requested": "K562",
            "cell_type_actual": "K562",
            "scale_prediction_requested": "linear",
            "scale_prediction_actual": "log",
            "species_requested": "homo_sapiens",
            "species_actual": "homo_sapiens",
            "predictions": {
                "7:70038969:G:T:A:wC": [
                    -0.4900762140750885
                ],
                "1:192696196:C:T:A:wC": [
                    -0.42054876685142517
                ],
                "1:211209457:C:T:A:wC": [
                    -0.251442551612854
                ],
                "15:89574440:GT:G:A:wC": [
                    1.1541708707809448
                ],
                "15:89574440:GT:G:R:wC": [
                    1.1637296676635742
                ]
            }
        }
    ]
    }
    ```

---

---
