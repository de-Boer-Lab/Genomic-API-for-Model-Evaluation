# Contributing containers

We encourage you to explore the GAME modules page and begin with an Evaluator or Predictor codebase that most closely matches your own implementation. GAME's modules (and their corresponding code) is meant to be shared with the community, please include the code you use to build your containers on their independent Github Repositories (LINK MODULES PAGE).

**The scripts listed below are meant to be re-usable across all GAME modules with minimal changes. We suggest testing your Evaluators/Predictors with the test module containers to validate their functionality.** 

The core Test module containers can be found [here](https://github.com/de-Boer-Lab/Genomic-API-for-Model-Evaluation/tree/main/src/Test_Modules)

## Commands to run them
`apptainer run --containall -B /path_to/predictor_data:/predictor_data predictor.sif HOST PORT`

`apptainer run --containall -B /path_to/evaluator_data:/evaluator_data -B /path/to/predictions:/predictions evaluator.sif HOST PORT OUTPUT_DIR`


## Checklist for Predictor Modules

| File | Description | Edits Required |
|------|-------------|----------------|
| `config.py` | Sets the Predictor base name, automatically appends the container build timestamp for module-level versioning, determines container vs. dev paths, and configures supported request/response wire formats. | Edits required for each Predictor. |
| `predictor_RestAPI.py` | Includes GET `/formats` and `/help`, POST `/predict` methods; validates/preprocesses requests. | Edits required. |
| `predictor_content_handler.py` | Decodes requests, encodes responses (JSON/MsgPack), adds predictor name, handles MIME negotiation, integrates with Flask. | No edits required if dealing with JSON and MsgPack. |
| `schema_validation.py` | Validates payload keys/values; preprocesses sequences for inference; provides progress feedback. | Edits required for predictor-specific sections. |
| `error_checking_functions.py` | Error classes (`APIError`, `BadRequestError`, etc.); validation functions for sequences, keys, readouts, ranges, and consistency. | No edits required. |
| `<model_wrapper_script>` | Model specific code that sets up a callable for `predictor_RestAPI.py`. Like `predict_dream_rnn()`, `predict_borzoi()`, etc. | Edit to define model specific code for each Predictor. |
| `predictor_help_message.json` | HELP file per GAME API spec.  Must include `game_schema_version` (see [Predictor Help Classes](../API/help.md)) | Edits required for each Predictor. |
| `*_predictor.def` | Apptainer definition file for building the container. The build-date label is used automatically by `config.py` for [module-level versioning](../versioning.md). | Edits required for each Predictor. |

### Predictor Responsibilities

- Set up endpoints for `/formats`, `/help` and `/predict`
- Validate the requests, decline any requests the model can't fulfill
- Pre-process the data to add any adapters, and crop sequences if prediction ranges are sent
- Send sequences to the model, use Matcher if necessary
- Format predictions in API return formats, return HTTP error codes if necessary

## Checklist for Evaluator Modules

| File | Description | Edits Required |
|------|-------------|----------------|
| `config.py` | Sets the Evaluator base name, automatically appends the container build timestamp for module-level versioning, determines container vs. dev paths, and configures API communication settings (request/response format, retries, retry interval). | Edits required for each Evaluator. |
| `evaluator_RestAPI.py` | Loads/ validates input, sends data to predictor via HTTP, handles responses, saves raw predictions, computes metrics on success. | Minor edits based on Evaluator's Data |
| `evaluator_content_handler.py` | Sends HTTP requests with retries, negotiates formats (JSON/MsgPack), deserializes responses safely. | No edits required |
| `data_loader.py` | Loads and validates input files (`.json`, `.msgpack`, `.mpk`), checks for duplicates, returns validated dictionary. | Edit to load datasets |
| `evaluator_metrics_calculator.py` | Calculates/saves correlation and cell-type specificity metrics, handles invalid/missing data, outputs CSV with timestamps. | Edits required for evaluation metric calculation|
| `*evaluator.def` | Apptainer definition file for building the container. Must include `game_schema_version` in the `%labels` block. | Edits required for each Evaluator. |

### Evaluator Responsibilities

- Parsing data from the Evaluator data folder and transforming into one of the Predictor defined request formats
- Issue `POST` `/predict` request to the Predictors
- Receive and save predictions
- Calculate evaluation metrics and save in required format
