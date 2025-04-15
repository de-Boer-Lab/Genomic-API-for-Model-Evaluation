# Evaluator Testing Script Using Dummy Predictor Container

This repository contains a shell script (`test_evaluator_container.sh`) that automates the testing process for new Evaluator containers against a (dummy) Predictor container for the (dummy) deBoerTest_model. You can also choose to test against a different test Predictor container of your choice: just adjust the path in the shell script, as needed.

## Features

- **Auto-Detection of Public IP:**  
  The script attempts to auto-detect the public IP using the `ip route` command. If auto-detection fails, it prompts the user to enter their IP manually.

- **Random Port Selection:**  
  It picks a random TCP port between 20000 and 25000 to avoid port conflicts during testing.

- **Container Management:**  
  - The Predictor container (specified by `test_predictor.sif`) is launched in the background and listens on the selected IP and port.
  - After waiting for the predictor to initialize, the Evaluator container is started with appropriate bind mounts for evaluator data and predictions.

## Prerequisites

- **Apptainer:**  
  Ensure Apptainer is installed and available on your system.

- **Container Images:**  
  - `test_predictor.sif` (Predictor container) must be available in the expected path
  - An Evaluator container image in SIF format

- **Directories:**  
  Provide absolute paths for:
  - The evaluator data directory
  - The predictions directory

## Usage

Run the script from the terminal with three required arguments:

```bash
./test_evaluator_container.sh <evaluator_container> <evaluator_data_dir> <predictions_dir>
```

### Example

```bash
./test_evaluator_container.sh /path/to/new_evaluator.sif \
                             /absolute/path/to/evaluator_data \
                             /absolute/path/to/predictions
```
