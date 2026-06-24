# Basic instructions to create a test Evaluator and Predictor

## Creating an Evaluator that reads in a sample JSON files that include DNA sequences

Make sure that you have Apptainer installed. Additional details and installation instructions can be found here: <https://apptainer.org/docs/user/main/quick_start.html>

The Evaluator container in this example will require 3 arguments in this order: HOST, PORT, OUTPUT_DIR.

To create a sample Evaluator using the scripts and data we provide for this example follow the instructions below:

### 1. Download the `test_evaluator_container` folder and explore the scripts to familiarize yourself

`evaluator_RestAPI.py`

- Loads and validates input data using `load_and_validate_data()`.
- Sends data to a predictor via HTTP and handles various response formats.
- Gracefully handles HTTP errors and malformed predictor responses.
- Saves raw predictions to a JSON file.
- Computes metrics only if the Predictor returns a successful response (HTTP 200).

`config.py`

- Sets the evaluator name and input file for predictions.  
- Defines output filename.
- Automatically sets data directory based on container or local execution.  
- Constructs full path to input file (`EVALUATOR_INPUT_PATH`).  
- Configures API communication:  
  - Request format, response format, Maximum retries/interval
- Prints input file path for validation.

`evaluator_content_handler.py`

- Sends HTTP requests with automatic retries on network failures.  
- Negotiates request and response formats with the Predictor (JSON/MsgPack).  
- Posts data to `<predictor_url>/predict` and returns the response.  
- Deserializes responses safely; raises errors if decoding fails.  
- Warns if actual response format differs from negotiated format.

`data_loader.py`

- Loads and validates evaluator input files (`.json`, `.msgpack`, `.mpk`).  
- Detects and reports duplicate keys (`DuplicateKeysError`).  
- Supports JSON string or file parsing with duplicate key checks.  
- Raises errors for missing files, invalid formats, or malformed data.  
- Returns validated data as a dictionary for downstream processing.

`evaluator_metrics_calculator.py`

- Calculates and saves fake correlation and cell-type specificity metrics.  
- Validates prediction tasks and handles missing/invalid data.  
- Saves results as CSV files with timestamps and metadata.  
- Main function: `calculate_and_save_metrics(predictions_data, output_dir)`.  
- Helper functions: `_calculate_fake_correlations` and `_calculate_fake_specificity`.

All of these scripts will be copied into the container in the `%files` section of the .def file.

### 2. Change paths in the `evaluator.def` to local corresponding paths

The `evaluator.def` is a definition file and will be used to create the Apptainer container. In this example we are only building a container with Python 3.9-slim and no other dependencies for simplicity. The `/predictions` folder is our `OUTPUT_DIR` where the returning predictions for this pseudo example will be stored. `evaluator_data` contains 2 sample JSON files, one is a very simple request and the other is more complicated. `evaluator_data` is mounted at run time to increase flexibility.

Change the `path_to/`  in the .def file to the local file path for the `evaluator_RestAPI.py` script to copy it into the container from a local directory.  

### 3. It's time to build the Evaluator container

```bash
cd test_evaluator_container/
mkdir predictions
apptainer build evaluator.sif evaluator.def
```

This will build the Evaluator container that automatically runs `evaluator_RestAPI.py`. In this example the Evaluator container only requires 3 arguments in this order: HOST, PORT, OUTPUT_DIR.

**`evaluator.sif` will be created in the `test_evaluator_container` folder.**

## Creating a Predictor that will return values for every possible request type

### 1. Download the `test_predictor_container` folder to create the sample Predictor

`config.py`

- Sets the base predictor name (e.g. `"TestPredictor"`).
- Automatically versions the Predictor name using the container's build-date label from `/.singularity.d/labels.json`.
  - Inside container: `"TestPredictor_20251128-180629_PST"` (sortable, human-readable).
  - Outside container (dev mode): `"TestPredictor_dev"` (*Optional*).
- Determines if running inside a container or not and sets paths accordingly (e.g. `HELP_FILE`).
- Configures supported request and response wire formats (e.g. `application/json`, `application/msgpack`).

`predictor_RestAPI.py`

- Imports configuration from `config.py` (`PREDICTOR_NAME`, `HELP_FILE`, `SUPPORTED_REQUEST_FORMATS`, `SUPPORTED_RESPONSE_FORMATS`).
- **GET `/formats`** - Returns supported request/response formats.  
- **GET `/help`** - Returns predictor metadata/help information.  
- **POST `/predict`** - Receives sequences and returns predictions.  
- Decodes, validates, and preprocesses evaluator requests.  
- Supports readout types: `point`, `track`, `interaction_matrix`.  
- Standardized error handling and JSON/MsgPack responses.  
- Adds predictor name to all responses; auto-adjusts paths for container use.

`predictor_content_handler.py`

- **`decode_request(supported_request_formats)`** - Decodes incoming JSON or MsgPack requests; raises `BadRequestError` on failure.  
- **`encode_response(payload, status_code=200, isError=False, supported_response_formats=None, predictor_name="UnknownPredictor")`** - Encodes responses as JSON or MsgPack; errors always use JSON.  
- Adds `predictor_name` to responses if missing.  
- Handles MIME negotiation based on `Content-Type` and `Accept` headers.  
- Integrates seamlessly with Flask request/response workflow.

`predictor_help_message.json`

- HELP file based on [GAME API specification](../API/help.md)

`schema_validation.py`

- **`validate_request_payload(payload)`** - Checks required keys and values; raises `BadRequestError` on failure.  
- **`preprocess_data(payload)`** - Applies flanking sequences, trims by prediction ranges, validates sequences; raises `PredictionFailedError` on issues.  
- Prepares payload for model inference with progress feedback via tqdm.

`error_checking_functions.py`

#### Mandatory Error Classes

`APIError` (base), `BadRequestError` (400), `PredictionFailedError` (422), `ServerError` (500).

More error classes with their status codes can also be added. 

#### Validation Functions

- `check_seqs_specifications()` - sequences valid, non-empty  
- `check_mandatory_keys()` / `check_key_values_readout()` - required JSON keys and readout  
- Prediction tasks - validate `name`, `type`, `cell_type`, `species`, `scale`  
- `check_prediction_ranges()` - positive integers, start $\leq$ end  
- Sequence IDs & flanking sequences - consistent and strings  

**`deBoerTest_model.py` Functions:**

- `fake_model_point(sequences)` &rarr; single random value per sequence  
- `fake_model_track(sequences)` &rarr; random float array per sequence  
- `fake_model_interaction_matrix(sequences)` &rarr; 3×3 random integer matrix, base64-encoded

All of these scripts will be copied into the container in the `%files` section of the .def file.

### 2. Change paths in `predictor.def` to local corresponding paths

Change the `path_to/` in the .def file to the local file path for the scripts.

### 3. Build the Predictor container

The Predictor container here uses python 3.9-slim and installs numpy and pandas.

  ```bash
  cd test_predictor_container
  apptainer build predictor.sif predictor.def
  ```

This will build the Predictor container that automatically runs `predictor_RestAPI.py`. In this example the Predictor container only requires 2 arguments in this order: HOST, PORT.

**`predictor.sif` will be created in the `test_predictor_container` folder.**

## Running the containers

To get the local host IP for the Predictor server you can use `hostname`, `hostname -I`, `hostname -i`, etc. **NOTE:** It is different for different HPC platforms.

Ports above 1024 are usually free to use on most computers/servers.

The Predictor needs to be started first and the Evaluator will connect to the Predictor's IP.

`apptainer run --containall -B path_to/predictor_data:/predictor_data predictor.sif HOST PORT`

`apptainer run --containall -B path_to/evaluator_data:/evaluator_data -B /path/to/predictions:/predictions evaluator.sif HOST PORT OUTPUT_DIR`

**Example:**

  ```bash
  apptainer run --containall -B path_to/test_predictor_container/predictor_data:/predictor_data predictor.sif 172.xx.xx.xx 5000
  ```

  ```bash
  apptainer run --containall -B path_to/test_evaluator_container/evaluator_data:/evaluator_data -B path_to/test_evaluator_container/predictions:/predictions evaluator.sif 172.xx.xx.xx 5000 /predictions
  ```

If the connection was successful a predictor response JSON file will be created in the `/path/to/predictions/`
