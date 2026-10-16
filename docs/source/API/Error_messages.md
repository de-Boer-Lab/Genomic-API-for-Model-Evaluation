# Error messages

Error messages that should be returned by the predictors in .json format. Values can follow the format described below (any type) or other/additional ones can be added by the Predictor builders.

We encourage Predictor builders to return error messages in the format show below using the appropriate HTTP error codes. 

---

| Error Key                 | Type            | Status Code | Description                                                          | Examples of Messages |
|----------------------------|----------------|-------------|----------------------------------------------------------------------|--------------------|
| `bad_prediction_request`    | array of strings | 400         | The request was unacceptable; the model did not run.               | • JSON file is formatted incorrectly.<br>• Mandatory key missing (e.g., `readout`, `sequences`).<br>• Invalid `type` or `readout` value.<br>• Duplicate sequence ID keys.<br>• `prediction_ranges` not integers, `start >= end`, or mismatched with `sequences`. |
| `prediction_request_failed` | array of strings | 422         | The request was valid, but the model could not complete the prediction. | • Sequence contains invalid characters.<br>• Model cannot handle sequence lengths this large.<br>• No matching cell type or assay could be found for a requested task (returned per task inside `predictions`, see {ref}`Predictor API Schema <tasks-cannot-perform>`). |
| `server_error`              | array of strings | 500         | Backend/server issue that prevented prediction.                     | • Socket communication failed.<br>• Memory error (e.g., large batch or JSON file).<br>• Wifi/network error. |

---

## Notes

- Each **error key** corresponds to a Python exception class in the Predictor:
  - `bad_prediction_request` &rarr; `BadRequestError` (HTTP 400)  
  - `prediction_request_failed` &rarr; `PredictionFailedError` (HTTP 422)  
  - `server_error` &rarr; `ServerError` (HTTP 500)  

- Errors for a single prediction task are returned inside that task's `predictions` object (HTTP 200) using the same error keys and messages, rather than as an HTTP error response. See {ref}`Tasks the Predictor cannot perform <tasks-cannot-perform>`. Tasks that could not be performed because no match was found currently use `prediction_request_failed`; this may change as the Matcher improves.
