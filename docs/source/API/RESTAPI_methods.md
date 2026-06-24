# REST API Methods

GAME’s modules communicate via REST APIs over HTTP. The main functionalities include:

1. **Requesting formats from Predictors** (`GET /formats`)  
2. **Requesting help files** (`GET /help`)  
3. **Requesting predictions** (`POST /predict`)  

---

| Method | Endpoint        | Description                                                                 |
|--------|----------------|-----------------------------------------------------------------------------|
| GET | `/formats`     | Evaluators request available data formats from the Predictors.             |
| GET    | `/help`        | Retrieve help or documentation files for a module.                         |
| POST | `/predict` | Evaluators request predictions from the Predictors using input data.       |

## Ping and health checks (`curl`)

While the Predictor is designed for machine-to-machine communication, developers can manually verify that a Predictor container is alive and configured correctly by querying its metadata endpoints:

### Get available serialization formats

```bash
curl -X GET http://HOST:PORT/formats
```

### Get help

```bash
curl -X GET http://HOST:PORT/help
```

## Utilization of [Matcher](../Matcher.md) module

The Predictor module may utilize automated task alignment using the [Matcher](../Matcher.md) module by also using HTTP methods:

| Method | Endpoint        | Description                                                                 |
|--------|----------------|-----------------------------------------------------------------------------|
| POST | `/match`     | Predictors request the Matcher to map Evaluator tasks to the Predictor-specific capabilities.            |
