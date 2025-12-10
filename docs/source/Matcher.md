# Matcher
GAME introduces a module called “Matcher”, which automatically maps the Evaluator's requested cell type, measured molecule (TF binding molecule/ protein and histone markers), and species with what a Predictor can provide. The Matcher uses a local LLM model and is designed to perform this task by interpreting the relationship between terms through lexical, syntactic, and semantic matching. The use of Matcher with Predictor modules is optional and up to the model developer. Most Predictor modules will first check for exact matches between the request and what they can complete before asking Matcher for help.

The Matcher communicates via a standardized REST API over HTTP, with a single endpoint, `/match`, which accepts POST requests containing a JSON file.

### **Matcher Request Payload**
The request payload must be a JSON object conforming to the schema below. The API enforces strict validation logic using the `pydantic` library to ensure data integrity.

**Validation Rules:**

1. **Paired Fields:** If you provide a requested term (e.g. `cell_type_requested`), you must also provide the corresponding list (e.g. `cell_type_list`).
2. **Minimum Requirement:** The request must contain at least one valid category pair to process. Empty requests will be rejected with a `422 Unprocessable Entity` error.

| Key                 | Value type - Required/Optional                   | Description  | Example   |
|--------------|--------------|-------------------------------|--------------|
| `cell_type_requested`                 | `string` - Optional (Paired)                   | The fuzzy input term for the cell type requested by the Evaluator | `"Leukemia cell line"`   |
| `cell_type_list`                 | `array of strings` - Optional (Paired)                   | The list of choices the Predictor can support to match against | `["K562", "A549", "HepG2"]`   |
| `species_requested`                 | `string` - Optional (Paired)                   | The fuzzy input term for the species requested by the Evaluator | `"h_sap"`   |
| `species_list`                 | `array of strings` - Optional (Paired)                   | The list of choices the Predictor can support to match against | `["Homo sapiens", "Mus musculus"]`   |
| `binding_molecule_requested`                 | `string` - Optional (Paired)                   | The fuzzy input term for the binding molecule requested by the Evaluator | `"H3K4_trimethylation"`   |
| `binding_molecule_list`                 | `array of strings` - Optional (Paired)                   | The list of choices the Predictor can support to match against | `["CTCF", "H3K4me3", "POLR2A"]`   |

### **Matcher Response Payload**

The Matcher (server) sends back a JSON payload to the Predictor (client), containing the results of the matching tasks. An `_actual` key will be present for each category pair that was provided in the request.

| Key                 | Value type                   | Description  | Example   |
|--------------|--------------|-------------------------------|--------------|
| `cell_type_actual`                 | `string` or `null`                   | The best match from the `cell_type_list` | `"K562"`   |
| `species_actual`                 | `string` or `null`                   | The best match from the `species_list` | `"Homo sapiens"`   |
| `binding_molecule_actual`                 | `string` or `null`                   | The best match from the `binding_molecule_list` | `"H3K4me3"`   |
| `matcher_version`                 | `string`                   | The version of the Matcher that processed the request. | `"2.0"`   |

Please visit the Matcher Github Repo for the code and more details.

### Usage
The Matcher container can be downloaded from Zenodo: [[ADD LINK HERE]].

1. **Download the Matcher Container**

    ```bash
    wget -O matcher.sif [LINK]
    ```
2. **Run the Matcher Server**
    This single command starts the container, launches a private Ollama server inside it, and starts the FastAPI server listening for HTTP requests.

    ```bash
    # General Usage:
    # apptainer run --nv --containall <sif_file> <IP_TO_LISTEN_ON> <PORT>

    # Example: Run the matcher, listening on all network interfaces on port 8080
    apptainer run --nv --containall matcher.sif 0.0.0.0 8080
    ```