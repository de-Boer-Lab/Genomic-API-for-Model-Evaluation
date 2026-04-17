# Versioning

GAME distinguishes between two types of versioning: the **API schema** and the **individual module**.

## API Schema Version (`game_schema_version`)

The `game_schema_version` tracks which version of the GAME API specification a module implements. The schema version covers the entire GAME release &mdash; the Evaluator request spec, Predictor response spec, and Matcher spec. Changes to the API specification (e.g. the addition, removal, or modification of keys) will be accompanied by a schema version increment and published release notes. The `game_schema_version` field is set manually by the module builder in the help file and should be updated when the module is modified to conform to a new version of the GAME API.

### Compatibility policy

The schema version follows a `MAJOR.MINOR` format:

- **Minor increments** (e.g. `1.0` &rarr; `1.1` &rarr; `1.2`): Represent the addition of optional keys that some modules may use but others can safely ignore if they don't need those keys or values. Modules built for any version within the same major release (e.g. `1.*`) are compatible with each other.
- **Major increments** (e.g. `1.*` &rarr; `2.0`): Represent mandatory changes such as the addition, removal, or renaming of required keys. Modules built for an older major version may not be compatible and should be updated.

### Where to store it

- **Predictors**: Set `game_schema_version` in the `predictor_help_message.json`. This is returned via the `GET /help` endpoint
- **Evaluators, Matcher, & Predictor Distributor (PD)**: Set `game_schema_version` in the `%labels` block of the Apptainer definition file (`.def`).

Predictor, Evaluator, Matcher, and PD schema versions are also tracked in the [GAME Modules](https://github.com/de-Boer-Lab/GAME_modules) repository.

**NOTE:** PD is a transparent orchestration layer between the Evaluator and Predictor. It forwards payloads without inspecting or modifying the schema, so it does not need to be updated when the API specification changes. Its `game_schema_version` label tracks which version of GAME it was built alongside, not a schema it enforces.

### How to check it

Before running an evaluation, Predictor's schema version can be verified with:

```bash
curl -X GET http://HOST:PORT/help
```

For Evaluators, Matcher, and the PD, the schema version from the container can be inspected with:

```bash
apptainer inspect --labels <image>.sif | grep game_schema_version
```

## Module-level version

Module-level versioning (via `predictor_name` / `evaluator_name` / `matcher_version`) tracks the specific build of a container. This is handled automatically by reading the container's build-date label from Apptainer's `/.singularity.d/labels.json` and appending it to the module's base name in `config.py`. The format is `YYYYMMDD-HHMMSS_TZ`, producing names like `DREAM-RNN_Human_K562_20260407-140628_PDT` or `"Matcher_20260414-171101_PDT"`.

This automatic versioning ensures that every rebuild of a container produces a unique, sortable identifier &mdash; allowing Evaluators to distinguish between different builds of the same Predictor, even when the API schema version has not changed. This is especially important when model weights, preprocessing logic, or dependencies are updated between builds, which can impact their prediction and therefore their evaluation outcomes.

<!-- ### Compatibility Properties (Internal Notes for now)

Predictors are **forward compatible**: they process only the keys they recognize and ignore unknown fields. A Predictor built for schema v2 will accept requests from a v3 Evaluator that includes new fields &mdash; the unknown keys are simply ignored. However, Predictors are **not guaranteed to be backward compatible**: a Predictor built for a newer schema version may require keys that an older Evaluator does not send, resulting in a validation error (HTTP 400).

Evaluators are **not backward compatible**: they may depend on response fields introduced in newer schema versions. For example, a track Evaluator that expects `trim_upstream` in the response will default to 0 if the field is missing from an older Predictor's response &mdash; producing silently incorrect alignment rather than an error. Evaluators are, however, **forward compatible**: they ignore unknown response keys, so a v2 Evaluator will not break when receiving responses from a v3 Predictor that includes new fields. -->

## Recommended Behaviour for Version Mismatches

Users SHOULD check the module's `game_schema_version` before issuing prediction requests. If a version mismatch is detected, the recommended behavior is to **log a warning and proceed** with the evaluation. The Predictor's built-in validation will reject genuinely incompatible requests with the appropriate HTTP error code, and Evaluators should handle missing or unexpected response fields gracefully by defaulting to safe values (e.g. `None`) and recording the mismatch in the evaluation output.

<!-- Users MAY choose to refuse connections to incompatible modules, but this is left to the Evaluator builder's discretion. -->

Regardless of schema compatibility, Predictor builders are always free to decline any prediction request they cannot fulfill (e.g. unsupported species, readout type, or sequence length) by returning the appropriate HTTP error code and a descriptive error message.
