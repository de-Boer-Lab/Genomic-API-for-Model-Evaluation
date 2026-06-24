# Get started by using pre-built GAME modules

GAME modules can be run interactively by users or using our submission scripts [LINK]. To parallelize predictions you can use [Predictor Distributor](Predictor_distributor.md) .

Predictor run command:

`apptainer run --containall predictor.sif HOST PORT`

To use a container with  NVIDIA GPU:

`apptainer run --containall --nv predictor.sif HOST PORT`

To use a container with GPU + Matcher:

`apptainer run --containall --nv predictor.sif HOST PORT MATCHER_HOST MATCHER_PORT`

**NOTE:** **For AMD GPUs and ROCm framework, please refer to [Apptainer's Documentation](https://apptainer.org/docs/user/1.0/gpu.html#amd-gpus-rocm).**

Evaluator run command:

```bash
apptainer run --containall \
    -B /path/to/evaluator_data:/evaluator_data  \
    -B /path/to/predictions:/predictions  \
    evaluator.sif HOST PORT /predictions
```

Updated list of current GAME modules can be found here: [LINK]

## Running the DREAM-RNN container (Matcher not required) with a sample dataset

To run a test prediction using the DREAM-RNN container and sample Evaluator container:

1. Download the containers from Zenodo: [LINK]

    ```bash
    mkdir DREAMRNN
    mkdir test_evaluator
    ```

    ```bash
    cd DREAMRNN
    wget -O dream_rnn_predictor.sif [LINK]
    ```

    ``` bash
    cd test_evaluator
    wget -O evaluator.sif [LINK]
    wget -O evaluator_data.zip [LINK]
    unzip evaluator_data.zip
    mkdir predictions
    ```

    **Note:** if you run into issues downloading the `evaluator_data` folder you may need to manually download it off Zenodo.

2. Get the IP Address of where the Predictor is running

    Note: PORTs above 1024 are usually free to use

    `hostname -I` (**NOTE:** This could be different for different HPC platforms -- `-I`, `-i`, no flag, etc.)

3. Start the DREAMRNN Predictor with the IP address and PORT arguments

    `apptainer run --containall --nv predictor.sif HOST PORT`

    Example:
    `apptainer run --containall --nv predictor.sif 172.16.47.243 5000`

4. Start the test Evaluator

    ```bash
    apptainer run --containall \
        -B /path/to/evaluator_data:/evaluator_data  \
        -B /path/to/predictions:/predictions  \
        evaluator.sif HOST PORT /predictions
    ```

    Example:

    ```bash
    apptainer run --containall \
        -B /path/to/evaluator_data:/evaluator_data  \
        -B /path/to/predictions:/predictions  \
        evaluator.sif 172.16.47.243 5000 /predictions
    ```

    The `-B` mounts local directories so that the Evaluator container can read in the JSON file from a local folder and write the prediction to the locally created `/predictions` folder.

5. If the Evaluator-Prediction communication was successful a JSON file will be found in the `predictions/` folder.

Yay! You just completed a successful communication between the DREAMRNN model and a test sequence set with GAME :)

```bash
{
    "predictor_name": "DREAM-RNN_Human_K562_20260601-173514_EDT",
    "prediction_tasks": [
        {
            "name": "gosai_synthetic_sequences",
            "type_requested": "expression",
            "type_actual": ["expression"],
            "cell_type_requested": "K562",
            "cell_type_actual": "K562",
            "scale_prediction_requested": "log",
            "scale_prediction_actual": "log",
            "species_requested": "homo_sapiens",
            "species_actual": "homo_sapiens",
            "predictions": {
                "7:70038969:G:T:A:wC": 
                    -0.4900762140750885
                ,
                "1:192696196:C:T:A:wC": 
                    -0.4205487370491028
                ,
                "1:211209457:C:T:A:wC": 
                    -0.2514425814151764
                ,
                "15:89574440:GT:G:A:wC": 
                    1.1541708707809448
                ,
                "15:89574440:GT:G:R:wC": 
                    1.1637296676635742
                
            }
        }
    ]
}
```

## Running Enformer container (with Matcher) with a sample dataset

Coming soon
