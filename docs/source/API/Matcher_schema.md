# Matcher API Schema

## Request to Matcher

To perform a match for a specific category (e.g. cell_type), the Predictor sends a **POST request** to the `/match` endpoint. The Evaluator does not communicate with the Matcher directly &mdash; the Predictor is the client to the Matcher service.

The JSON payload must include paired keys for each category:

- `<category>_requested` $\rightarrow$ the fuzzy input term provided by the Evaluator  
- `<category>_list` $\rightarrow$ the list of possible values the Predictor can match against.

**Validation Rules:**

1. **Paired Fields:** If you provide a requested term (e.g. `cell_type_requested`), you must also provide the corresponding list (e.g. `cell_type_list`).
2. **Minimum Requirement:** The request must contain at least one valid category pair to process. Empty requests will be rejected with a `422 Unprocessable Entity` error.

Multiple categories can be included in a single request.

| Key                 | Value type - Required/Optional                   | Description  | Example   |
|--------------|--------------|-------------------------------|--------------|
| `cell_type_requested`                 | `string` - Optional (Paired)                   | The fuzzy input term for the cell type requested by the Evaluator | `"Leukemia cell line"`   |
| `cell_type_list`                 | `array of strings` - Optional (Paired)                   | The list of choices the Predictor can support to match against | `["K562", "A549", "HepG2"]`   |
| `species_requested`                 | `string` - Optional (Paired)                   | The fuzzy input term for the species requested by the Evaluator | `"h_sap"`   |
| `species_list`                 | `array of strings` - Optional (Paired)                   | The list of choices the Predictor can support to match against | `["Homo sapiens", "Mus musculus"]`   |
| `binding_molecule_requested`                 | `string` - Optional (Paired)                   | The fuzzy input term for the binding molecule requested by the Evaluator | `"H3K4_trimethylation"`   |
| `binding_molecule_list`                 | `array of strings` - Optional (Paired)                   | The list of choices the Predictor can support to match against | `["CTCF", "H3K4me3", "POLR2A"]`   |

## Matcher response

The Matcher (server) sends back a JSON payload to the Predictor (client) a JSON payload containing the results of the matching tasks. An `_actual` key will be present for each category pair that was provided in the request.

A value of `null` indicates that the Matcher determined no suitable match exists in the provided list &mdash; this is a valid result, not an error.

| Key                 | Value type                   | Description  | Example   |
|--------------|--------------|-------------------------------|--------------|
| `cell_type_actual`                 | `string` or `null`                   | The best match from the `cell_type_list` | `"K562"`   |
| `species_actual`                 | `string` or `null`                   | The best match from the `species_list` | `"Homo sapiens"`   |
| `binding_molecule_actual`                 | `string` or `null`                   | The best match from the `binding_molecule_list` | `"H3K4me3"`   |
| `matcher_version`                 | `string`                   | The versioned name of the Matcher that processed the request. Constructed automatically using the same build-timestamp convention as `predictor_name` and `evaluator_name` (see [Help Endpoint](help.md)). | `"Matcher_20260414-171101_PDT"`   |

```bash
curl -X POST http://[HOST]:[PORT]/match \
     -H "Content-Type: application/json" \
     -d '{
           "cell_type_requested": "Leukemia cell line",
           "cell_type_list": ["K562", "A549", "HepG2"],
           "species_requested": "h_sap",
           "species_list": ["Homo sapiens", "Mus musculus"],
           "binding_molecule_requested": "H3K4_trimethylation",
           "binding_molecule_list": ["CTCF", "H3K4me3", "POLR2A"]
         }'
```
