# Configuring and Containerizing the Gosai et. al (2024) MPRA dataset

## **Overview**

This document outlines the structure of the API codebase for containerizing a MPRA Evaluator from: Gosai, S.J., Castro, R.I., Fuentes, N. et al. Machine-guided design of cell-type-targeting cis-regulatory elements. Nature 634, 1211–1220 (2024). <https://doi.org/10.1038/s41586-024-08070-z>

The data used in this Evaluator is from Supplementary Table 12.

---

## **1. Evaluator Structure**

The Gosai Evaluator is organized as follows:

    ```
    Gosai_2024_Evaluator/
    ├── Gosai_evaluator.def         # Evaluator container definition file
    ├── gosai_evaluator.py          # Script that reads in raw MPRA data, parses into JSON and connects to Predictors
    ├── evaluator_data   
    │   └── 41586_2024_8070_MOESM4_ESM.txt     # Raw dataset: Sequences and measured values 
    ├── test_container_flexibility.py   # Script that can be run with the container to use other datasets
    └── test_gosai_predictor    # Test Predictor
    ```

---

## **2. Understanding the API**

### **2.1. Evaluator API**

- **Purpose**: Interfaces with the Predictor API to send input and receive predictions. It handles input validation, data transfer, and output storage.
- **Core Script**: `gosai_evaluator.py`.
- **Key Features**
    1. **Dynamic Path Handling**:
        - Uses `os.path.exists` to determine if the script is running inside the container.
        - Adjusts paths to input (`EVALUATOR_INPUT_PATH`) accordingly.
    2. **JSON file creation**:
        - Read in .txt file from `/evaluator_data` in pandas dataframe.
        - Confirm that the column that will be used for sequence "keys" is unique (doesn't not container duplicates). Since this can cause issues with JSON file parsing.
        - Call `create_json()` function to creat the JSON file that will be sent to the predictor.
    3. **Socket Communication**:
        - Establishes a TCP socket connection with the Predictor server.
        - Implements length prefixing for the JSON payload to ensure reliable data transfer.
    4. **Data Transfer**:
        - Sends the input JSON file (after validation) to the Predictor API over the established connection.
        - Receives predictions as a JSON response, ensuring data integrity and completeness.
    5. **Output Management**:
        - Save the prediction results:
            - Outside the container: The host-mounted directory mapped to `/predictions/`.
        - Ensures output is saved in a consistent and accessible location.

---

### **Structure of the API JSON Format**

## **3. Configuring and Running the API** (Similar to [Basic Instructions for Test Evaluator and Predictor](https://github.com/de-Boer-Lab/Genomic-API-for-Model-Evaluation/tree/main/src/training_examples/Apptainer/Test_Evaluator_Predictor))

### 3.1 Configuring the Containers Using Definition Files

Containerizing the Evaluator involves creating **definition (.def) files** that specify the structure, dependencies, and environment of the container. This ensures a consistent and reproducible environment for running the Predictor and Evaluator APIs.

### **Purpose of [Definition Files](https://apptainer.org/docs/user/latest/definition_files.html)**

Definition files provide a declarative way to define:

1. **Base Image**: The starting point of the container (e.g., ubuntu or python:3.13-slim).
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
    - **Core Script**: The primary script, `gosai_evaluator.py`, is copied into the container.
    - **Dynamic Mounting**: Input (`/evaluator_data`) and output (`/predictions`) directories are mounted at runtime to allow flexibility in handling data without modifying the container.
3. **Environment Variables**:
    - Environment variables like `PATH` and `LD_LIBRARY_PATH` ensure the container uses the correct Conda environment for Python dependencies like NumPy. The `APPTAINER_NO_MOUNT` removes all local path mounts that are default in Apptainer. By removing any local path mounts the container does not have access to any locally installed packages.
4. **Runtime Needs**:
    - **Mounted Directories**: The Evaluator container dynamically binds host directories to `/evaluator_data` and `/predictions` within the container.
    - This ensures the Evaluator can process new inputs and save outputs without rebuilding the container.

---

### 3.2. Building The Containers

Once the definition files for the Evaluator and Predictor APIs are configured, the next step is to build the container images. This process involves using the `apptainer build` command to convert the `.def` files into Singularity Image Format (SIF) files.

### **Steps to Build the Containers**

1. **Set Up the Definition File**:
    - Ensure that the `.def` file includes all necessary files, directories, and dependencies.
    - Files that need to be copied into the container should be included in the  `%files`  section
    - Specific environment specific variables are listed in the  `%enviroment`  section
    - Key configurations like `chmod` for full directory and file access are defined in the `%post` section. Dependencies are installed in         this section.
    - Commands that the container will run should be included in  `%runscript` section. This Evaluator also allows you to run your own python file (see more details below).
    - Metadata for the container is included in the  `%labels` section and any help information that will be shown to the user should be           listed in the  `%help` section.
    - Additional information can be found here: <https://apptainer.org/docs/user/main/definition_files.html>

2. **Run the Build Command**: Use the `apptainer build` command to create the SIF file in their respective directories:

    Download Supp. Table 12 from: <https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-08070-z/MediaObjects/41586_2024_8070_MOESM14_ESM.txt> and place the 41586_2024_8070_MOESM4_ESM.txt file in `/evaluator_data/`. (Too large to store in Github)

        ```bash
        cd Gosai_2024_Evaluator
        
        apptainer build gosai_evaluator.sif gosai_evaluator.def
        ```

    - The first argument specifies the output SIF file.
    - The second argument specifies the definition file to use.
3. **Verify Build Success**:

    After the build completes, confirm the presence of the SIF files:

        ```bash
        ls -l *.sif
        ```

    - The resulting `gosai_evaluator.sif` should now be available in the working directory.

### **⚠️ Permissions Management ⚠️**

Read the section below in case you get permission errors when building the containers.

- During the container build, it’s critical to ensure that directories and files copied into the container or created inside it have the correct permissions. This is handled using `chmod` in the `%post` section of the `.def` files.

1. **Directories Created Inside the Container**:

    For the Evaluator container:

        ```bash
        chmod -R 755 /Gosai_2024_Evaluator
        ```

    - These directories are used for runtime-mounted data handling and must be accessible to ensure seamless input/output operations.
2. **Files Copied into the Container**:

    `gosai_evaluator.py` is copied into `/Gosai_2024_Evaluator/`

3. **Why Use `chmod`?**
    - Ensures all scripts, directories, and resources are accessible inside the container at runtime.
    - Prevents issues with restricted permissions that could cause runtime errors when reading or writing data.

---

### **3.3. Testing Gosai Evaluator with a Psuedo Prediction**

To confirm your Evaluator and message passing code work build a test Predictor with a fake model that returns random binary values for each sequence.

**Important: The Predictor container must be started before the Evaluator container. This is because the Evaluator relies on an active socket connection to the Predictor for communication.**

1. **Build a test Predictor API container**

  `cd test_gosai_predictor`
  Update paths to file that need to be copied into the container in .def file. `%files` section.

  ```bash
  apptainer build test_gosai_predictor.sif predictor_python_only.def
  ```

    - The first argument specifies the output SIF file.
    - The second argument specifies the definition file to use.
    
2. **Start the Predictor API container**

    Get your local host IP: `hostname -I`
    
    The Predictor API must be running first since it listens for incoming connections from the Evaluator. Use the following command to start the Predictor:
    
    ```bash
     apptainer run test_gosai_predictor.sif HOST PORT
    ```
    
    - Replace `HOST` with the server's IP, which can be found using `hostname -I`, and `PORT` with the desired [port number](https://www.geeksforgeeks.org/50-common-ports-you-should-know/).
    - The Predictor container will bind to the specified host and port and wait for connections.
    - Ensure that the port (e.g., `5000`) is open and not blocked by any firewall or network policies. Ports above 1024 are usually free to use on most computers/servers.
2. **Validate the server**
    - Ensure it listens on the specified host and port.
    - Example:

        ```
        apptainer run test_gosai_predictor.sif 172.16.47.243 5000
        Listening on 172.16.47.243:5000
        ```
        

---

### **3.4. Running the Evaluator API**

1. **Mount the required directories**

    After confirming that the Predictor is running, start the Evaluator container:

    ```bash
    apptainer run \
       -B /path/to/evaluator_data:/evaluator_data \
       -B /path/to/predictions:/predictions \
       gosai_evaluator.sif PREDICTOR_HOST PREDICTOR_PORT /predictions
    ```

2. **Key arguments**
    - `PREDICTOR_HOST`: IP address of the Predictor API server.
    - `PREDICTOR_PORT`: Port number for the Predictor API.
    - `/predictions`: Path to save predictions.
    - Example:

        ```bash
        apptainer run \
            -B /absolute/path/to/Gosai_2024_Evaluator/evaluator_data:/evaluator_data \
            -B /absolute/path/to/Gosai_2024_Evaluator/predictions:/predictions \
            gosai_evaluator.sif 172.16.47.243 5000 /predictions
        ```

3. **Confirm successful connection and returned predictions**

Check the `/predictions` folder for a `predictions.json` file.

**Why Runtime Mounting?**:

- Runtime mounting (-B) ensures flexibility:
  - The **Evaluator container** mounts directories like `/evaluator_data` and `/predictions` to read input and write output without requiring files to be embedded/created/copied inside the container.
  - The **Predictor container**, by contrast, does not need mounting for this container since all necessary files (e.g., model weights, helper scripts) are already copied into the container. In some cases you may want to use files that are not copied into the container at run time and these can be placed in the `/predictor_data` folder.

---

## **4. Example Input and Output JSON Files**

### **4.1. Input JSON**

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
    "sequences": [
        {
            "7:70038969:G:T:A:wC": "CCTGGTCTTTCTTGCTAAATAAACATATCGTGCATCATCCAGATCTTGCTGAAATTTGGGGGATATGCATTGAAGCAGCCCCTGTTTCTCCATGAAGGTTTATGTCTGTGAGCCTGGCTGTGCAGTTGGGAGGCCTGGGGGAGAGGTCATGCTTCTACCATGGCGTTTTCCATTTTCCTTAAAATGTGCCTCAGCAACAG",
            "1:192696196:C:T:A:wC": "CATAAAGATGAGGCTTGGCAAAGAACATCTCTCGGTGCCTCCCATTTCATTGTCCCTAAAGTAGAAGCTGAGTGTCATCATTTGTTAAAATTGGGGAAGTCTCCGAGGTGTGGGTTCATCAGAACAATAGCCACTGTTGCCTGTGGTCACAGTCACTGAAGCTGGGGTCCTGGTCACTACTCCAACAGCTGGGAGGCAGC",
            "1:211209457:C:T:A:wC": "CATAAAGCCAATCACTGAGATGACAAGTACTGCCAGGAAAGAAGGCTTTAATCGGGTATTGCAGCTGAAGAGATAGGAGAGCAGTCTCAAATCCATCTCTCTGACCAACTAAAATTGGGGGTTTATGTAGTGGGGAAGGAATGTAGCTACATGTGGGTAAACAGGAATTAGGGAGGGGTAGGGAAGAAGAGTTGGCCATC",
    .
    .
    .
    }
    ]
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
                "scale_prediction_actual": "linear",
                "species_requested": "homo_sapiens",
                "species_actual": "homo_sapiens",
                "predictions": {
                    "7:70038969:G:T:A:wC": [
                        0.3173099458217621
                    ],
                    "1:192696196:C:T:A:wC": [
                        0.33908841013908386
                    ],
                    "1:211209457:C:T:A:wC": [
                        0.37649109959602356
                    ]
            }
            }
            
        ]
    }
    ```

### **Running your own python script with this container**

This container allows you to also run your own python script (if it uses the same dependencies ex. packages in python).
The `%runscript` section does a check for if a python file was passed in as an argument. See example below:

    ```bash
    apptainer run -B /path_to/script_you_want_to_run/ -B /path_to/evaluator_data/:/evaluator_data -B /path_to/predictions/:/predictions gosai_evaluator.sif test_container_flexibility.py 172.16.47.244 5004 /predictions
    ```

The python script must alter its indexing for system arguments (HOST, PORT, OUTPUT_DIR) but can be used to read in any other MPRA dataset from the `/evaluator_data` folder, parsed into the correct API format and connect to a Predictor.
