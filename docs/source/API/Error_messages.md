### Error messages

Error messages that should be returned by the predictors in .json format. Values can follow the format described below (any type) or other/additional ones can be added by the Predictor builders.

We encourage Predictor builders to return error messages in the format show below using the appropriate HTTP error codes. 

---

| Error Key                 | Type            | Status Code | Description                                                          | Examples of Messages |
|----------------------------|----------------|-------------|----------------------------------------------------------------------|--------------------|
| `bad_prediction_request`    | array of strings | 400         | The request was unacceptable; the model did not run.               | • JSON file is formatted incorrectly.<br>• Mandatory key missing (e.g., `readout`, `sequences`).<br>• Invalid `type` or `readout` value.<br>• Duplicate sequence ID keys.<br>• `prediction_ranges` not integers or mismatched with `sequences`.<br>• Invalid characters in sequence IDs. |
| `prediction_request_failed` | array of strings | 422         | The request was valid, but the model could not complete the prediction. | • Sequence contains invalid characters.<br>• Model cannot handle sequence lengths this large. |
| `server_error`              | array of strings | 500         | Backend/server issue that prevented prediction.                     | • Socket communication failed.<br>• Memory error (e.g., large batch or JSON file).<br>• Wifi/network error. |

---

### Notes

- Each **error key** corresponds to a Python exception class in the Predictor:
  - `bad_prediction_request` → `BadRequestError` (HTTP 400)  
  - `prediction_request_failed` → `PredictionFailedError` (HTTP 422)  
  - `server_error` → `ServerError` (HTTP 500)  


