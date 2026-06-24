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
| `game_schema_version`               | `string`- Optional  | The version of the GAME API schema that this Predictor implements. This is distinct from module-level versioning, which is handled automatically by the container build timestamp appended to `predictor_name` (see [Versioning](../versioning.md)).                                                                                 | "game_schema_version": "1.0"|
| `publication`               | `string`- Optional  | Citation for original paper.                                                                                | "publication": "Luthra et. al, 2024"|
| `features`              | `array of strings`- Optional   | List of features that the model predicts for each of the cells in `cell_types`.                                                 | "features": ["accessibility", "accessibility", "binding_h3K4me3","binding_ctcf","expression", "expression", "expression"] |
| `cell_types`              | `array of strings`- Optional   | Cell types that correspond to predicted features in `features`. Length of "cell_types" should be the same as "features" or length 1.                                              | "cell_types": ["iPSC", "Hepg2", "iPSC", "iPSC", "iPSC", "HepG2",  "K562"] |
| `species`               | `array of strings`- Optional  | Species that correspond to predicted features in `features`. Length of "species" should be the same as "features" or length 1.                                               | "species": ["homo_sapiens"]|
| `container_authors`                | `string`- Optional  | Author/authors of container builders.                                                                 |  "container_authors": "Ishika Luthra" |
| `model_authors`                | `string`- Optional  | Paper author/authors.                                                                  |  "model_authors": "Ishika Luthra" |
| `input_size`            | `Integer`- Optional | Number of base pairs of sequence that the model takes as input.                                                  | "input_size" : 500500 |
| `bin_size`            | `Integer`- Optional | For models that predict across genomic tracks what is the base pair resolution.                                     | "bin_size": 10|
| `expression_strand_specific` | `Boolean`- Optional | For models that predict expression, is the expression prediction strand specific or not. | "expression_strand_specific": true|

For details on API schema versioning and module-level versioning, see [Versioning](../versioning.md).
