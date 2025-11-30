### Matcher response message

To perform a match for a specific category (e.g. cell_type), the Evaluator sends a **POST request** to the `/match` endpoint. 

The JSON payload must include paired keys for each category:

- `<category>_requested` → the fuzzy input term provided by the Evaluator  
- `<category>_list` → the list of possible values the Predictor can match against  

Multiple categories can be included in a single request.


| Key                 | Value type - Required/Optional                   | Description  | Example   |
|--------------|--------------|-------------------------------|--------------|
| `cell_type_requested`                 | `string` - Optional (Paired)                   | The fuzzy input term for the cell type requested by the Evaluator | `"Leukemia cell line"`   |
| `cell_type_list`                 | `array of strings` - Optional (Paired)                   | The list of choices the Predictor can support to match against | `["K562", "A549", "HepG2"]`   |
| `species_requested`                 | `string` - Optional (Paired)                   | The fuzzy input term for the species requested by the Evaluator | `"h_sap"`   |
| `species_list`                 | `array of strings` - Optional (Paired)                   | The list of choices the Predictor can support to match against | `["Homo sapiens", "Mus musculus"]`   |
| `binding_molecule_requested`                 | `string` - Optional (Paired)                   | The fuzzy input term for the binding molecule requested by the Evaluator | `"H3K4_trimethylation"`   |
| `binding_molecule_list`                 | `array of strings` - Optional (Paired)                   | The list of choices the Predictor can support to match against | `["CTCF", "H3K4me3", "POLR2A"]`   |

The Matcher (server) sends back a JSON payload to the Predictor (client) a JSON payload containing the results of the matching tasks. An `_actual` key will be present for each category pair that was provided in the request.

| Key                 | Value type                   | Description  | Example   |
|--------------|--------------|-------------------------------|--------------|
| `cell_type_actual`                 | `string` or `null`                   | The best match from the `cell_type_list` | `"K562"`   |
| `species_actual`                 | `string` or `null`                   | The best match from the `species_list` | `"Homo sapiens"`   |
| `binding_molecule_actual`                 | `string` or `null`                   | The best match from the `binding_molecule_list` | `"H3K4me3"`   |
| `matcher_version`                 | `string`                   | The version of the Matcher that processed the request. | `"2.0"`   |


```bash
curl -X POST http://localhost:8000/match \
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