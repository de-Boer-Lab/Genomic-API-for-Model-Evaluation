# Help Endpoint

## Retrieve information about Predictor classes

We highly encourage detailed `help` responses to organize and document Predictor containers.

Predictor Response:

| Key  | Value type     | Description       | Example Values |
|------|---------------|-------------------------------------------|-------------------|
| `model`                 | `string`- Optional  | Model name.                                                                                                         | "model": "deBoer Lab test" |
| `game_schema_version`               | `string`- Optional  | The version of the GAME API schema that this Predictor implements. This is distinct from module-level versioning, which is handled automatically by the container build timestamp appended to `predictor_name` (see below).                                                                                 | "game_schema_version": "2.0"|
| `publication`               | `string`- Optional  | Citation for original paper.                                                                                | "publication": "Luthra et. al, 2024"|
| `features`              | `array of strings`- Optional   | List of features that the model predicts for each of the cells in `cell_types`.                                                 | "features": ["accessibility", "accessibility", "binding_h3K4me3","binding_ctcf","expression", "expression", "expression"] |
| `cell_types`              | `array of strings`- Optional   | Cell types that correspond to predicted features in `features`. Length of "cell_types" should be the same as "features" or length 1.                                              | "cell_types": ["iPSC", "Hepg2", "iPSC", "iPSC", "iPSC", "HepG2",  "K562"] |
| `species`               | `array of strings`- Optional  | Species that correspond to predicted features in `features`. Length of "species" should be the same as "features" or length 1.                                               | "species": ["homo_sapiens"]|
| `container_authors`                | `string`- Optional  | Author/authors of container builders.                                                                 |  "container_authors": "Ishika Luthra" |
| `model_authors`                | `string`- Optional  | Paper author/authors.                                                                  |  "model_authors": "Ishika Luthra" |
| `input_size`            | `Integer`- Optional | Number of base pairs of sequence that the model takes as input.                                                  | "input_size" : 500500 |
| `bin_size`            | `Integer`- Optional | For models that predict across genomic tracks what is the base pair resolution.                                     | "bin_size": 10|
| `expression_strand_specific` | `Boolean`- Optional | For models that predict expression, is the expression prediction strand specific or not. | "expression_strand_specific": true|

## Note on Versioning

GAME distinguishes between two types of versioning:

1. **API schema version** (`game_schema_version`): Tracks which version of the GAME API specification a module implements. The schema version covers the entire GAME release &mdash; the Evaluator request spec, Predictor response spec, and Matcher spec all move together as one versioned contract. Changes to the API specification (e.g. the addition, removal, or modification of keys) will be accompanied by a schema version increment and published release notes. The `game_schema_version` field is set manually by the module builder in the help file and should be updated when the module is modified to conform to a new version of the GAME API.

2. **Module-level version** (via `predictor_name` / `evaluator_name`): Tracks the specific build of a container. This is handled automatically by reading the container's build-date label from Apptainer's `/.singularity.d/labels.json` and appending it to the module's base name in `config.py`. The format is `YYYYMMDD-HHMMSS_TZ`, producing names like `DREAM-RNN_Human_K562_20260407-140628_PDT`.
*Internal implementation note:* Modules running outside of a container (in development mode) append `_dev` instead.

This automatic versioning ensures that every rebuild of a container produces a unique, sortable identifier &mdash; allowing Evaluators to distinguish between different builds of the same Predictor, even when the API schema version has not changed. This is especially important when model weights, preprocessing logic, or dependencies are updated between builds.

### Compatibility Properties

Predictors are **forward compatible**: they process only the keys they recognize and ignore unknown fields. A Predictor built for schema v2 will accept requests from a v3 Evaluator that includes new fields &mdash; the unknown keys are simply ignored. However, Predictors are **not guaranteed to be backward compatible**: a Predictor built for a newer schema version may require keys that an older Evaluator does not send, resulting in a validation error (HTTP 400).

Evaluators are **not backward compatible**: they may depend on response fields introduced in newer schema versions. For example, a track Evaluator that expects `trim_upstream` in the response will default to 0 if the field is missing from an older Predictor's response &mdash; producing silently incorrect alignment rather than an error. Evaluators are, however, **forward compatible**: they ignore unknown response keys, so a v2 Evaluator will not break when receiving responses from a v3 Predictor that includes new fields.

### Recommended Behavior for Version Mismatches

Evaluators SHOULD check the Predictor's `game_schema_version` via the `/help` endpoint before issuing prediction requests. If a version mismatch is detected, the recommended behavior is to **log a warning and proceed** with the evaluation. The Predictor's built-in validation will reject genuinely incompatible requests with the appropriate HTTP error code, and Evaluators should handle missing or unexpected response fields gracefully by defaulting to safe values (e.g. `None`) and recording the mismatch in the evaluation output. Evaluators MAY choose to refuse connections to incompatible Predictors, but this is left to the Evaluator builder's discretion.
