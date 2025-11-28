### Contributing containers

We encourage you to explore the GAME modules page and begin with an Evaluator or Predictor codebase that most closely matches your own implementation.

The scripts listed below are meant to be re-usable across all GAME modules with minimal changes. 

#### Checklist for Predictor Modules

| File | Description | Edits Required |
|------|-------------|----------------|
| `predictor_RestAPI.py` | Includes GET `/formats` and `/help`, POST `/predict` methods; validates/preprocesses requests| Edits required|
| `predictor_content_handler.py` | Decodes requests, encodes responses (JSON/MsgPack), adds predictor name, handles MIME negotiation, integrates with Flask. |No edits required |
| `schema_validation.py` | Validates payload keys/values; preprocesses sequences for inference; provides progress feedback. | No edits required |
| `error_checking_functions.py` | Error classes (`APIError`, `BadRequestError`, etc.); validation functions for sequences, keys, readouts, ranges, and consistency. | No edits required. |
| `deBoerTest_model.py` | Model specific code | Edit to define model specific code for each Predictor. |
| `predictor_help_message.json` | HELP file per GAME API spec. | Edits required for each Predictor|

#### Predictor Responsibilites
- Set up endpoints for `/formats`, `/help` and `/predict`
- Validate the requests, decline any requests model's can't fulfill
- Pre-process the data to add any adapters, and crop sequences if prediction ranges are sent
- Send sequences to the model, use Matcher if necessary
- Format predictions in API return formats, return HTTP error codes if necessary

#### Checklist for Evaluator Modules

| File | Description | Edits Required |
|------|-------------|----------------|
| `evaluator_RestAPI.py` | Loads/validates input, sends data to predictor via HTTP, handles responses, saves raw predictions, computes metrics on success. | Minor edits based on Evaluator's Data|
| `config.py` | Sets evaluator name, input/output paths, configures API communication, prints paths for validation. | Edit |
| `evaluator_content_handler.py` | Sends HTTP requests with retries, negotiates formats (JSON/MsgPack), deserializes responses safely. | No edits required |
| `data_loader.py` | Loads and validates input files (`.json`, `.msgpack`, `.mpk`), checks for duplicates, returns validated dictionary. | Edit to load datasets |
| `evaluator_metrics_calculator.py` | Calculates/saves correlation and cell-type specificity metrics, handles invalid/missing data, outputs CSV with timestamps. | Edits required for evaluation metric calculation|

#### Evaluator Responsibilites
- Parsing data from the Evaluator data folder and transforming into one of the Predictor defined request formats
- Issue /POST /predict request to the Predictors
- Receive and save predictions
- Calculate evaluation metrics and save in required format