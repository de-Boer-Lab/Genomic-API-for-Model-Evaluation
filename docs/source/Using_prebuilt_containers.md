# Get started by using pre-built GAME modules

GAME modules can be run interactively by users or using our [submission scripts](https://github.com/de-Boer-Lab/Genomic-API-for-Model-Evaluation/tree/main/src/job-submission-scripts). To parallelize predictions you can use [Predictor Distributor](Predictor_distributor.md) .

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

An updated list of current GAME modules can be found here: [Modules](https://github.com/de-Boer-Lab/GAME_modules/tree/main)

## Running the DREAM-RNN container (Matcher not required) with a sample dataset

To run a test prediction using the DREAM-RNN container and sample Evaluator container:

1. Download the containers from [Hugging Face](https://huggingface.co/datasets/deBoerLab/DREAMRNN_Predictor_GAME):

    ```bash
    mkdir DREAMRNN
    mkdir test_evaluator
    ```

    ```bash
    cd DREAMRNN
    wget https://huggingface.co/datasets/deBoerLab/DREAMRNN_Predictor_GAME/resolve/main/dream_rnn_predictor.sif
    ```

    ```bash
    cd ../test_evaluator
    wget -O test-evaluator.sif https://huggingface.co/datasets/deBoerLab/TestContainers_GAME/resolve/main/test-evaluator.sif
    mkdir evaluator_data
    wget -O evaluator_data/test_evaluator_request.json https://huggingface.co/datasets/deBoerLab/TestContainers_GAME/resolve/main/evaluator_data/test_evaluator_request.json
    mkdir predictions
    cd ..
    ```

    **Note:** if you run into issues downloading `test_evaluator_request.json`, you can download it manually from the [TestContainers_GAME dataset page](https://huggingface.co/datasets/deBoerLab/TestContainers_GAME) on Hugging Face.

2. Get the IP Address of where the Predictor is running

    Note: PORTs above 1024 are usually free to use

    `hostname -I` (**NOTE:** This could be different for different HPC platforms -- `-I`, `-i`, no flag, etc.)

3. Start the DREAMRNN Predictor with the IP address and PORT arguments

    ```bash
    apptainer run --containall --nv DREAMRNN/dream_rnn_predictor.sif HOST PORT
    ```

    Example:

    ```bash
    apptainer run --containall --nv DREAMRNN/dream_rnn_predictor.sif 172.16.47.243 5000
    ```

    The Predictor runs in the foreground and stays running while it waits for requests. Leave this terminal open and start a second one for step 4.

4. Start the test Evaluator

    ```bash
    apptainer run --containall \
        -B /path/to/evaluator_data:/evaluator_data  \
        -B /path/to/predictions:/predictions  \
        test_evaluator/test-evaluator.sif HOST PORT /predictions
    ```

    Example:

    ```bash
    apptainer run --containall \
        -B ./test_evaluator/evaluator_data:/evaluator_data  \
        -B ./test_evaluator/predictions:/predictions  \
        test_evaluator/test-evaluator.sif 172.16.47.243 5000 /predictions
    ```

    The `-B` mounts local directories so that the Evaluator container can read in the JSON file from a local folder and write the prediction to the locally created `/predictions` folder.

5. If the Evaluator-Predictor communication was successful a JSON file will be found in the `test_evaluator/predictions/` folder.

Yay! You just completed a successful communication between the DREAMRNN model and a test sequence set with GAME :)

```json
{
    "predictor_name": "DREAM-RNN_Human_K562_20260430-012244_PDT",
    "prediction_tasks": [
        {
            "name": "K562_linear",
            "type_requested": "expression",
            "type_actual": [
                "expression"
            ],
            "cell_type_requested": "K562",
            "cell_type_actual": "K562",
            "scale_prediction_requested": "linear",
            "scale_prediction_actual": "linear",
            "species_requested": "homo_sapiens",
            "species_actual": "homo_sapiens",
            "predictions": {
                "short_seq": 21.833628430386128,
                "boundary_1000": 0.8041965209535046,
                "long_seq": 0.9411978956039309,
                "range_at_start": 2.1278552307487035,
                "range_at_end": 2.1278552307487035,
                "full_range": 2.1278552307487035,
                "empty_range": 2.1278552307487035
            }
        }
    ]
}
```