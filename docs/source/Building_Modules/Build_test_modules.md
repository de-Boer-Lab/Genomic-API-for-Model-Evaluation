# Basic instructions to create a [test Evaluator and Predictor](https://github.com/de-Boer-Lab/Genomic-API-for-Model-Evaluation/tree/main/src/Test_Modules)

## Creating an Evaluator that reads in a sample JSON file that includes DNA sequences

Make sure that you have Apptainer installed. Additional details and installation instructions can be found here: <https://apptainer.org/docs/user/main/quick_start.html>

The Evaluator container in this example requires 3 arguments in this order: `HOST`, `PORT`, `OUTPUT_DIR`.

To create a sample Evaluator using the scripts and data we provide for this example, follow the instructions below.

### 1. Download the `Test_Evaluator` folder and explore the scripts to familiarize yourself

#### `config.py`

- Sets the base **evaluator** name (e.g. `"test_evaluator_deBoer"`).
- Automatically versions the **Evaluator** name using the container's build-date label from `/.singularity.d/labels.json`.
  - Inside container: `"test_evaluator_deBoer_20251128-160727_PST"` (sortable, human-readable).
  - Outside container (dev mode): `"test_evaluator_deBoer_dev"`.
- Defines the output filename.
- Automatically sets the data directory based on container or local execution.
- Constructs the full path to the input file (`EVALUATOR_INPUT_PATH`).
- Configures API communication: request format, response format, and maximum retries / retry interval.
- Prints the input file path for validation.

#### `evaluator_RestAPI.py`

- Loads and validates input data using `load_and_validate_data()`.
- Sends data to a Predictor via HTTP and handles the negotiated response format.
- Gracefully handles HTTP errors and malformed Predictor responses.
- Saves raw predictions to a JSON file.
- Computes metrics only if the Predictor returns a successful response (HTTP 200).

#### `evaluator_content_handler.py`

- Sends HTTP requests with automatic retries on network failures.
- Negotiates request and response formats with the Predictor (JSON / MsgPack).
- Posts data to `<predictor_url>/predict` and returns the response.
- Deserializes responses safely; raises errors if decoding fails.
- Warns if the actual response format differs from the negotiated format.

#### `data_loader.py`

- Loads and validates the evaluator's input file. **The loader is evaluator-specific**: this sample supports `.json`, `.msgpack`, and `.mpk`, but you are free to extend it to read whatever format your evaluation needs (e.g. bigWig, BED, TSV, custom binaries). The only requirement is that the final request payload it produces conforms to the request schema.
- Detects and reports duplicate keys (`DuplicateKeysError`).
- Supports JSON string or file parsing with duplicate-key checks.
- Raises errors for missing files, unsupported file types, or malformed data.
- Returns validated data as a dictionary for downstream processing.

#### `evaluator_metrics_calculator.py`

- Calculates and saves placeholder correlation and cell-type specificity metrics.
- Validates prediction tasks and handles missing/invalid data.
- Saves results as a tab-separated CSV file with timestamps and metadata.
- Main function: `calculate_and_save_metrics(predictions_data, output_dir)`.
- Helper functions: `_calculate_fake_correlations` and `_calculate_fake_specificity`.

All of these scripts are copied into the container in the `%files` section of the `.def` file.

### 2. Adjust the `test-evaluator.def` to your local paths

The `test-evaluator.def` is an Apptainer definition file used to build the container. In this example we build on top of `python:3.13-slim` and install the Python packages the Evaluator needs (`numpy`, `tqdm`, `pandas`, `msgpack`, `requests`).

The `%files` section uses paths **relative to the directory you run the build from**, so the simplest workflow is to build from inside the evaluator folder (see step 3). If you build from elsewhere, update the `%files` source paths accordingly.

`evaluator_data` contains sample JSON request files (a simple request and a more complex one) and is **mounted at run time** for flexibility, rather than copied into the image. The `/predictions` folder is the `OUTPUT_DIR` where returned predictions are written.

> **Note:** the Evaluator reads the single file named by `input_file` in `config.py` (in this sample, `test_evaluator_request.json`), resolved under `evaluator_data/`. Either place a file with that name in `evaluator_data/`, or change `input_file` in `config.py` to match your file. This is a per-evaluator setting, not a framework-wide filename requirement.

### 3. Build the Evaluator container

```bash
cd Test_Evaluator/
mkdir -p predictions
apptainer build test-evaluator.sif test-evaluator.def
```

This builds the Evaluator container, which automatically runs `evaluator_RestAPI.py`. In this example the container requires 3 arguments in this order: `HOST`, `PORT`, `OUTPUT_DIR`.

**`test-evaluator.sif` will be created in the `Test_Evaluator` folder.**

## Creating a Predictor that returns values for every possible request type

This example Predictor is intentionally **model-free and CPU-only**: it ships no trained weights, needs no GPU (no `--nv`), and returns randomized values for any request. Its purpose is to exercise a new Evaluator end-to-end (request &rarr; predict &rarr; response &rarr; metrics) without a real model.

### 1. Download the `Test_Predictor` folder to create the sample Predictor

#### `config.py`

- Sets the base **predictor** name (e.g. `"test_predictor_deBoer"`).
- Automatically versions the **Predictor** name using the container's build-date label from `/.singularity.d/labels.json`.
  - Inside container: `"test_predictor_deBoer_20251128-180629_PST"` (sortable, human-readable).
  - Outside container (dev mode): `"test_predictor_deBoer_dev"`.
- Determines whether it is running inside a container and sets paths accordingly (e.g. `HELP_FILE`).
- Configures the supported request and response wire formats (`application/json`, `application/msgpack`).

#### `predictor_RestAPI.py`

- Imports configuration from `config.py` (`PREDICTOR_NAME`, `HELP_FILE`, `SUPPORTED_REQUEST_FORMATS`, `SUPPORTED_RESPONSE_FORMATS`).
- **GET `/formats`** — returns supported request/response formats.
- **GET `/help`** — returns Predictor metadata / help information.
- **POST `/predict`** — receives sequences and returns predictions.
- Decodes, validates, and preprocesses Evaluator requests.
- Supports readout types: `point`, `track`, `interaction_matrix`.
- Standardized error handling and JSON / MsgPack responses.
- Adds the Predictor name to all responses; auto-adjusts paths for container use.

#### `predictor_content_handler.py`

- **`decode_request(supported_request_formats)`** — decodes incoming JSON or MsgPack requests; raises `BadRequestError` on failure.
- **`encode_response(payload, status_code=200, isError=False, supported_response_formats=None, predictor_name="UnknownPredictor")`** — encodes responses as JSON or MsgPack; errors always use JSON.
- Adds `predictor_name` to responses if missing.
- Handles MIME negotiation based on the `Content-Type` and `Accept` headers.
- Integrates with the Flask request/response workflow.

#### `predictor_help_message.json`

- HELP file based on the [GAME Help Endpoint specification](../API/help.md).

#### `schema_validation.py`

- **`validate_request_payload(payload)`** — checks required keys and values; raises `BadRequestError` on failure.
- **`preprocess_data(payload)`** — applies flanking sequences, trims by prediction ranges, validates sequences; raises `PredictionFailedError` on issues.
- Prepares the payload for model inference with progress feedback via tqdm.

#### `error_checking_functions.py`

#### Mandatory Error Classes

`APIError` (base), `BadRequestError` (400), `PredictionFailedError` (422), `ServerError` (500).

Additional error classes with their status codes can also be added.

#### Validation Functions

- `check_seqs_specifications()` — sequences valid, non-empty.
- `check_mandatory_keys()` / `check_key_values_readout()` — required JSON keys and readout.
- Prediction-task checks — validate `name`, `type`, `cell_type`, `species`, and (optional) `scale`.
- `check_prediction_ranges()` — positive integers, start ≤ end.
- Sequence IDs and flanking sequences — consistent and strings.

**`deBoerTest_model.py` functions:**

- `fake_model_point(sequences)` &rarr; a single random scalar per sequence.
- `fake_model_track(sequences)` &rarr; a random float array per sequence (length equal to the sequence length).
- `fake_model_interaction_matrix(sequences)` &rarr; an N×N random integer matrix per sequence (N = sequence length), returned as a list of lists. For large matrices we recommend encoding via msgpack / msgpack-numpy.

All of these scripts are copied into the container in the `%files` section of the `.def` file.

### 2. Adjust the `test-predictor.def` to your local paths

The Predictor container builds on top of `python:3.13-slim` and installs the packages the Predictor needs: `numpy`, `pandas`, `tqdm`, `msgpack`, and `flask`.

As with the Evaluator, the `%files` section uses paths **relative to the directory you run the build from**; the simplest workflow is to build from inside the Predictor folder (step 3). If you build from elsewhere, update the `%files` source paths accordingly.

### 3. Build the Predictor container

```bash
cd Test_Predictor
apptainer build test-predictor.sif test-predictor.def
```

This builds the Predictor container, which automatically runs `predictor_RestAPI.py`. In this example the container requires 2 arguments in this order: `HOST`, `PORT`. (Any extra arguments — e.g. a Matcher configuration used by other Predictors — are ignored by this test Predictor.)

**`test-predictor.sif` will be created in the `Test_Predictor` folder.**

## Running the containers

To get the local host IP for the Predictor server you can use `hostname`, `hostname -I`, `hostname -i`, etc. **NOTE:** this differs across HPC platforms.

Ports above 1024 are usually free to use on most machines/servers.

**Start the Predictor first**, then start the Evaluator and point it at the Predictor's IP and port.

This test Predictor reads nothing from disk, so it needs no bind mounts:

```bash
apptainer run --containall test-predictor.sif HOST PORT
```

> Predictors that need model weights or reference data bake them into the image at build time via `%files` (as the reference DREAM-RNN predictor does with its `.pth` weights). A builder *may* choose to bind a folder at run time instead, but none of the reference predictors do, and the test Predictor needs no mounts at all.

The Evaluator mounts its input data and output directory at run time:

```bash
apptainer run --containall \
  -B path_to/evaluator_data:/evaluator_data \
  -B path_to/predictions:/predictions \
  test-evaluator.sif HOST PORT /predictions
```

**Example:**

```bash
# 1) Predictor (start first)
apptainer run --containall test-predictor.sif 172.xx.xx.xx 5000
```

```bash
# 2) Evaluator (connects to the Predictor's HOST/PORT)
apptainer run --containall \
  -B path_to/Test_Evaluator/evaluator_data:/evaluator_data \
  -B path_to/Test_Evaluator/predictions:/predictions \
  test-evaluator.sif 172.xx.xx.xx 5000 /predictions
```

If the connection succeeds, a Predictor-response JSON file and the evaluation metrics CSV will be created in `path_to/Test_Evaluator/predictions/`.