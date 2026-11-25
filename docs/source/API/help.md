# Help Endpoint

## Retrieve information about Predictor classes

We highly encourage detailed `help` responses to organize and document Predictor containers.

Once a Predictor server is up and running, its help information can be retrieved with:

```bash
curl -X GET http://HOST:PORT/help
```

### Predictor Response

| Key  | Value type     | Description       | Example Values |
|------|---------------|-------------------------------------------|-------------------|
| `model`                 | `string`- Optional  | Model name.                                                                                                         | "model": "deBoer Lab test" |
| `description`                 | `string`- Optional  | Short summary of the model.                                                                                         | "description": "DNA Language model" |
| `game_schema_version`               | `string`- Required  | The version of the GAME API schema that this Predictor implements. This is distinct from module-level versioning, which is handled automatically by the container build timestamp appended to `predictor_name` (see [Versioning](../versioning.md)).                                                                                 | "game_schema_version": "1.0"|
| `publication`               | `string`- Optional  | Citation for original paper.                                                                                | "publication": "Luthra et. al, 2024"|
| `features` | `array of strings`- Optional | What the model can predict, one entry per prediction. | "features": ["accessibility", "accessibility", "binding_h3k4me3", "binding_ctcf", "expression", "expression", "expression"] |
| `cell_types` | `array of strings`- Optional | The cell type for each entry in `features`. Must be the same length as `features`, or length 1 if one cell type applies to all of them. | "cell_types": ["iPSC", "HepG2", "iPSC", "iPSC", "iPSC", "HepG2", "K562"] |
| `species` | `array of strings`- Optional | The species for each entry in `features`, i.e. the species of the cells in which that feature was measured. Must be the same length as `features`, or length 1 if one species applies to all of them. | "species": ["homo_sapiens"] |

| `container_authors`                | `string`- Optional  | Author/authors of container builders.                                                                 |  "container_authors": "Ishika Luthra" |
| `model_authors`                | `string`- Optional  | Paper author/authors.                                                                  |  "model_authors": "Ishika Luthra" |
| `input_size`            | `Integer`- Optional | Number of base pairs of sequence that the model takes as input.                                                  | "input_size" : 500500 |
| `bin_size`            | `Integer`- Optional | For models that predict across genomic tracks what is the base pair resolution.                                     | "bin_size": 10|
| `expression_strand_specific` | `Boolean`- Optional | For models that predict expression, is the expression prediction strand specific or not. | "expression_strand_specific": true|

For details on API schema versioning and module-level versioning, see [Versioning](../versioning.md).
