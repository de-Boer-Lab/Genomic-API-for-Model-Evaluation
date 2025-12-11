# REST API Methods

GAME’s modules communicate via REST APIs over HTTP. The main functionalities include:

1. **Requesting formats from Predictors** (`GET /formats`)  
2. **Requesting help files** (`GET /help`)  
3. **Requesting predictions** (`POST /predict`)  

---

| Method | Endpoint        | Description                                                                 | Request Type |
|--------|----------------|-----------------------------------------------------------------------------|--------------|
| Get Formats | `/formats`     | Evaluators request available data formats from the Predictors.             | GET          |
| Get Help    | `/help`        | Retrieve help or documentation files for a module.                         | GET          |
| Get Predictions | `/predict` | Evaluators request predictions from the Predictors using input data.       | POST         |

## Example `curl` Requests to access information

**Get available formats**

```bash
curl -X GET http://HOST:PORT/formats
curl -X GET http://HOST:PORT/help
```