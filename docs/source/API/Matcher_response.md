### Matcher response message

The Matcher (server) sends back a JSON payload to the Predictor (client) a JSON payload containing the results of the matching tasks. An `_actual` key will be present for each category pair that was provided in the request.

| Key                 | Value type                   | Description  | Example   |
|--------------|--------------|-------------------------------|--------------|
| `cell_type_actual`                 | `string` or `null`                   | The best match from the `cell_type_list` | `"K562"`   |
| `species_actual`                 | `string` or `null`                   | The best match from the `species_list` | `"Homo sapiens"`   |
| `binding_molecule_actual`                 | `string` or `null`                   | The best match from the `binding_molecule_list` | `"H3K4me3"`   |
| `matcher_version`                 | `string`                   | The version of the Matcher that processed the request. | `"2.0"`   |
