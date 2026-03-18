# Evaluator API Schema

## Evaluator request 

| Key | Value type - Required/Optional | Description: Value options | Example |
|---|---|---|---|
| `readout` | `string` - Required | Type of readout that is requested from the Predictor: ["point","track", "interaction_matrix"]. | "readout": "track" |
| `prediction_tasks`  | `array of objects` - Required        | Each object must contain the following keys: `name`, `type`, `cell_type`, `species`, `scale`(optional).| "prediction_tasks": [<br> {<br>   "name": "task1",<br>   "type": "expression",<br>  "cell_type": "iPSC",<br>  "scale": "linear",<br>  "species": "homo_sapiens" <br> }<br>]                                                                                                                                          |
| `name`  | `string` - Required        | Unique identifier for each prediction task object.                                                                                                                                                                                          | "name": "model_prediction"                                                                                                                                          |
| `type`  | `string` - Required        | Prediction type you want predicted: ["`accessibility`", "`binding_{molecule}`" , "`expression`", "`conformation_{isoform}`"]. "`binding_{molecule}`" can be for any type of binding assay (e.g. CHIP-Seq, H3k27ac) and the text trailing the `_` should be all lower case and without any special characters. `expression` by default refers to mRNA production [`expression_mRNA`] e.g. RNA-seq. The other valid types are ["`expression_pol1`", "`expression_pol2`", "`expression_pol3`", "`expression_splicing_acceptor`", "`expression_splicing_donor`"]. "`conformation_{isoform}`" can represent the conformation of any isoform e.g. "`conformation_chromatin`".                                                                                                                                                                                         | "type": "expression"                                                                                                                                         |
| `cell_type`        | `string` - Required       | What cell type you want predicted for `type`.                                                                                                                                                                                | "cell_type": "K562"                                                                                                                                                            |
| `species`        | `string` - Required       | What species you want predicted for `type`. Species names should be all lower case with words separated by a "_".                                                                    | "species": "homo_sapiens"                                                                                                                                                                |
| `scale`             | `string` - Optional                 | How would you like the predictions scaled upon return (if at all): ["linear", "log"].                                                                                                                                                                                                                                                                         | "scale" : "linear"                                                                                                                                                                                         |
| `upstream_seq`      | `string`- Optional                  | Upstream flanking sequences to add to each sequence in `sequences`.                                                                                                                                                                                                                                                                                       | "upstream_seq": "AATTA"                                                                                                                                                                                |
| `downstream_seq`    | `string`- Optional                  | Downstream flanking sequences to add to each sequence in `sequences`.                                                                                                                                                                                                                                                                                    | "downstream_seq": "CCCAAAA"                                                                                                                                                                            |
| `sequences`         | `object` - Required       | A collection of key-value pairs (strings). Keys are unique sequence ID keys - any characters [A-Z][a-z][0-9][-.\_\~#\@%^&\*()]. The sequence ID keys are matched to the Predictor sequence ID keys automatically by Predictor.                                                                                                                             | "sequences": {<br>   "seq1": "ATGC...",<br>   "seq2": "ATGC...",<br>  "random_seq": "ATGC...",<br>  "enhancer": "ATGC...",<br>  "control": "ATGC..." <br> }                                  |
| `prediction_ranges` | `object` - Optional | A collection of key-value pairs, where the keys should be identical to sequence ID keys and values are arrays with the start and end region you want predictions for, within the provided sequence context. Start and end are 0 indexed and inclusive, respectively (e.g. [0,1] is the first two bases).| "prediction_ranges": {<br>   "seq1": [0,1000],<br>   "seq2": [100,110],<br>  "random_seq": [],<br>  "enhancer": [210,500],<br>  "control": [] <br> } |

## Notes

1. keys in `sequences` must be unique or will be overwritten during the reading in
2. all indexing is 0 based
3. to minimize any bias from the predictors we suggested randomizing your sequences so that there is no dependency on the order

## Evaluator Output file specifications

Our evaluation framework is modular. While most evaluators provide a standard **Correlation Summary**, specialized evaluators (like `agarwal_2025_joint_lib_56k`) may provide additional (optional) granular metrics such as **Cell-Type Specificity**.

The codebase for the Agarwal MPRA Joint Library Evaluator can be found [here](https://github.com/de-Boer-Lab/GAME-Agarwal-MPRA-joint-library-evaluator) and serves as a reference for implementing custom metric calculations.

1. **Correlation Summary File (`evaluation_summary_[evaluator_name].csv`)**

    | `evaluator_name` | `description` | `predictor_name` | `time_stamp` | `metric` | `value` | `prediction_task(s)_data` |
    |---|---|---|---|---|---|---|
    | The unique identifier for the evaluator module | Description of the evaluation task | Returned `predictor_name` of the model being evaluated | UTC timestamp in `YYYYMMDD-HHMMSS.f` format to ensure unique entries | Evaluation metric used (typically `pearson_r`) | Evaluation metric value | Prediction task metadata used to calculate the metric as a dictionary |

2. **Cell-Type Specific Expression File (`cell_type_specific_expression_[evaluator_name].csv`)**

    *Optional: Only generated by joint library Evaluators that have data measured across multiple cell types*

    | `evaluator_name` | `description` | `predictor_name` | `metric` | `value` | `prediction_task(s)_data` |
    |---|---|---|---|---|---|
    | The unique identifier for the evaluator module | Identifies the pair being compared (e.g. `Cell type specific expression (HepG2 - K562)`). | Returned `predictor_name` of the model being evaluated | Evaluation metric used (typically `pearson_r` of the differential values) | Specificity correlation value | Prediction task metadata for both cell types used in the differential calculation |
