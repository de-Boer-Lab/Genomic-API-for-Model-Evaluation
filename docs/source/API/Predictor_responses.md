# Predictor API Schema

## Predictor response

| Key                 | Value type - Required/Optional                   | Description: Value options  | Example   |
|--------------|--------------|-------------------------------|--------------|
| `predictor_name` | `string`- Required           | Unique identifier for the Predictor. Constructed automatically in `config.py` by appending the container's build timestamp (read from Apptainer's `/.singularity.d/labels.json`) to the model's base name. The format is `{ModelName}_{YYYYMMDD-HHMMSS}_{TZ}`.                                                                        | `"predictor_name": "deBoerTestModel_20260127-171101_PST"`      |
| `matcher_version` | `string`- Optional           | If a Matcher was used by the Predictor, the `matcher_version` returned by the Matcher should be passed through to the Evaluator. This is the build-timestamped Matcher name, following the same versioning convention as `predictor_name`.                                                                                                                                                                         | `"matcher_version": "Matcher_20260127-171101_PST"`      |
| `bin_size` | `integer` - Required for track and interactive matrix based models           | Resolution of the model's predictions.                                                                                                                                                    | `"bin_size" : 1`          |
| `prediction_tasks`  | `array of objects` - Required        | Each object must contain the following keys: `name`, `type_requested`,`type_actual`, `cell_type_requested`, `cell_type_actual`, `species_requested`, `species_actual`,`predictions`, `scale_prediction_requested` (optional), `scale_prediction_actual` (optional), `aggregation` (optional object).| "prediction_tasks": [<br> {<br>   "name": "task1",<br>   "type_requested": "expression",<br>  "type_actual": ["expression"],<br>  "cell_type_requested": "K562",<br>  "cell_type_actual": "bone_marrow_cell_line",<br>  "species_requested": "homo_sapiens",<br>  "species_actual": "homo_sapiens",<br>  "scale_prediction_requested": "linear", <br>  "scale_prediction_actual": "linear",<br>  "aggregation": {"bins": "mean"},<br>   "predictions": { <br>     "seq1": [12.2, 5, 6, ..],<br>     "seq2": [1.1, 12, 0.00, ..],<br>    "random_seq": [100.1, 50, 0.5, ..],<br>    "enhancer": [4, 3.0, 0.001, ..],<br>    "control": [0, 0, 0, ..] <br>   }<br> }<br>]|
| `name`  | `string` - Required        | Unique identifier for each prediction task array matched from Evaluator.| `"name": "task_for_model"`|
| `type_requested`  | `string` - Required        | Prediction type requested: [`"accessibility"`, `"binding_molecule"`, `"expression"`, `"conformation_{isoform}"`, like `"conformation_chromatin"`]. `"binding_<molecule>"` can be for any type of binding assay (ex. CHIP-Seq, H3k27ac) and the text trailing the "_" should be all lower case.                                                                                                                                                                                        | `"type_requested": "expression"`                                                                                                                                         |
| `type_actual`  | `array of string(s)` or `null` - Required | Prediction type(s) completed by Predictor. In many cases will be the assay the model predicted. If multiple tracks were averaged in a multi-task model they should be included here. ex. ["dnase", "atac-seq"]. `null` if the task could not be performed (see {ref}`Tasks the Predictor cannot perform <tasks-cannot-perform>`). | `"type_actual": ["dnase"]`|
|`cell_type_requested`       | `string`- Required | Cell type requested by the Evaluator.                                   | `"cell_type_requested": "HEPG2"`|
| `cell_type_actual`       | `string` or `null` - Required | Cell type returned by Predictor. Predictor can choose to use the Matcher module, which will return the closest matched cell type that the Predictor has. Cell type agnostic Predictors should return "NA". `null` if the task could not be performed (see {ref}`Tasks the Predictor cannot perform <tasks-cannot-perform>`). | `"cell_type_actual": "HEPG2"` |
| `species_requested`        | `string` - Required       | What species was requested by the Evaluator.  | `"species_requested": "homo_sapiens"` |
|`species_actual`        | `string` or `null` - Required | What species was used by the Predictor. `null` if the task could not be performed (see {ref}`Tasks the Predictor cannot perform <tasks-cannot-perform>`). | `"species_actual": "homo_sapiens"`|
| `scale_prediction_requested` | `string` - Optional            | Evaluator requested scaling for predictions: ["linear", "log"].                                                                                                                                                    | `"scale_prediction_requested": "log"`       |
| `scale_prediction_actual` | `string` or `null` - Optional | How did the Predictor scale the predictions (if at all): ["linear", "log"] . `null` if the task could not be performed (see {ref}`Tasks the Predictor cannot perform <tasks-cannot-perform>`). | `"scale_prediction_actual": "log"`    |
|`aggregation`      | `object`- Optional           | Contains information about how replicates, bins and/or tracks were aggregated. Values can be any descriptive string and Predictor builders only need to include those that they used.                                                                                                                    | "aggregation": {<br>   "replicates": "mean",<br>   "bins": "mean",<br>  "tracks": "special mathematical formula"<br> }  |
| `predictions`      | `object`- Required | A mapping of sequence IDs to prediction values. Keys are sequence ID strings; values are scalars/floats for point requests, 1-D array of floats for track requests or nested lists/numpy arrays (msgpack-numpy responses) for interaction matrix requests. The sequence ID keys are matched to the Evaluator sequence ID keys automatically by Predictor. For a task the Predictor could not perform, this is an error object instead: `{"error": [{"<error_key>": "<message>"}]}` (see {ref}`Tasks the Predictor cannot perform <tasks-cannot-perform>`). |"predictions": {<br>   "seq1": [12.2, 5, 6, ..],<br>   "seq2": [1.1, 12, 0.00, ..],<br>  "random_seq": [100.1, 50, 0.5, ..],<br>  "enhancer": [4, 3.0, 0.001, ..],<br>  "control": [0, 0, 0, ..] <br> } |
| `trim_upstream` | `object` - Conditional | Returned only for `track` readout requests, as a key **inside each object of `prediction_tasks`** (a per-task key, not a top-level key). A collection of key-value pairs mapping sequence IDs to integers. The integer specifies the number of base pairs in the first predicted bin that fall upstream of the actual sequence or requested `prediction_range`. <br> <br> Evaluators use this exact offset to perfectly align the model's binned predictions back to the original genomic coordinates. | "trim_upstream": {<br>   "seq1": 5 ,<br>   "seq2": 0,<br>  "random_seq": 2,<br>  "enhancer": 1 ,<br>  "control":  0 <br> } |

## Notes:
In development mode (outside a container), `_dev` is appended to the `predictor_name` instead. This ensures every container rebuild produces a unique, sortable identifier, allowing Evaluators to distinguish between builds even when the model name has not changed. <br>  <br> This is especially important for Predictors that have undergone updates that led to different predictions. 

`species_requested` is the `species` from the Evaluator request and has the definition given there: the species of the cells in which the experiment was performed, regardless of where the input sequences originate (see the Notes in the [Evaluator API Schema](Evaluator_requests.md)). `species_actual` is the species the Predictor (model) actually used to make the predictions. It can differ from `species_requested`, for example when the requested name is normalized by the Matcher, and it is `null` if the task could not be performed.

(tasks-cannot-perform)=
## Tasks the Predictor cannot perform

If a request contains multiple `prediction_tasks`, the Predictor should return predictions for every task it can perform. A task the Predictor cannot perform (for example, no cell type or assay matching the requested `cell_type` or `type` could be found, even after using the Matcher) must still be returned, with its metadata:

- `name` and all `*_requested` keys are returned as normal.
- Every `*_actual` key (`type_actual`, `cell_type_actual`, `species_actual` and `scale_prediction_actual`) is `null` (Python `None`), because no task was performed. Placeholder strings such as `"N/A"` should not be used.
- `predictions` is an error object that uses the error keys and message format from [Error messages](Error_messages.md): `{"error": [{"<error_key>": "<message>"}]}`.
- `aggregation` and `trim_upstream` are omitted.

A task the Predictor lacks the capability to perform, for example because the Matcher could not find a good match, uses the `prediction_request_failed` error key (the request was valid, but the model could not complete it). This may change as the Matcher improves.

The HTTP status of the response is 200 as long as the request itself was valid, even if every task failed. Request-level failures (a malformed request, server errors, or an unreachable Matcher) are still returned as HTTP errors as described in [Error messages](Error_messages.md).

Evaluators identify a failed task by the `"error"` key in `predictions`, should score only the tasks that succeeded, and record `"NaN"` for the failed ones in the [evaluation output file](Evaluator_requests.md).

Example of a task that could not be performed, returned alongside tasks that succeeded:

```json
{
   "name": "sample_unmatched_cell_type",
   "type_requested": "expression",
   "type_actual": null,
   "cell_type_requested": "made_up_cell_type_xyz",
   "cell_type_actual": null,
   "species_requested": "homo_sapiens",
   "species_actual": null,
   "scale_prediction_requested": "linear",
   "scale_prediction_actual": null,
   "predictions": {
      "error": [{"prediction_request_failed": "No tracks found for expression in cell type 'made_up_cell_type_xyz'"}]
   }
}
```

## Note on Binned Predictions and Sequence-Length Alignment

Predictors that return **binned predictions** often include **"N" bases** in flanking bins. These can skew results when performing **base-pair (bp)–level evaluation**.

When an Evaluator requests a track `readout` request:

- The **expanded bp-level prediction** (for binned outputs) **must match the length of the input sequence**.
- The start of a prediction should be aligned with the first bp of the sequence.
- By default, if no `trim_upstream` parameter is returned, the Evaluator should **crop the predictions only at the downstream end**.
- If a `trim_upstream` parameter *is* returned, the Evaluator should:
  1. **Crop upstream** by the amount specified in `trim_upstream`.
  2. **Crop the remaining required amount downstream** to ensure the final prediction length equals the sequence length.

This ensures consistent evaluation and avoids artifacts introduced by binned predictions.
