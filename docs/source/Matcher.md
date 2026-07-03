# Matcher

GAME introduces a module called “Matcher”, which automatically maps the Evaluator's requested cell type, measured molecule (TF binding molecule/ protein and histone markers), and species with what a Predictor can provide. The Matcher uses a local LLM model and is designed to perform this task by interpreting the relationship between terms through lexical, syntactic, and semantic matching. The use of Matcher with Predictor modules is optional and up to the model developer. Most Predictor modules will first check for exact matches between the request and what they can complete before asking Matcher for help.

The Matcher communicates via a standardized REST API over HTTP, with a single endpoint, `/match`, which accepts POST requests containing a JSON payload. For the full request and response schema, see the [Matcher API Schema](API/Matcher_schema.md).

For more information about the implementation, refer to the [Matcher GitHub Repository](https://github.com/de-Boer-Lab/GAME_matcher).

## How it works

The Matcher is implemented as a FastAPI server running a local [Gemma 3](https://deepmind.google/models/gemma/gemma-3/) 12B model via [Ollama](https://ollama.com/), both packaged inside a single Apptainer container. The LLM is configured with `temperature=0` to ensure deterministic output &mdash; the same input will produce the same match.

For each matching category (cell type, species, or binding molecule), the Matcher uses domain-specific prompt templates with worked examples and explicit instructions to return `NULL` when no suitable match exists. The LLM output is validated against the input choices to guard against hallucinated responses &mdash; if the LLM returns a value that was not in the provided list, it is discarded.

When the choice list is large (e.g. models with hundreds of cell types), the Matcher uses a **chunked tournament approach**: the list is split into chunks of up to 20 items, the LLM picks the best match from each chunk, and the winners compete in subsequent rounds until a single best match is determined.

The Matcher follows the same two-tier versioning convention as Predictor and Evaluator modules. The `matcher_version` returned in every response is the build-timestamped Matcher name (e.g. `Matcher_20260414-171101_PDT`), constructed automatically from Apptainer's build-date label. The API schema version (`SCHEMA_VERSION`) is stored in the Matcher's `config.py` and exposed via the FastAPI application metadata.

## Usage

The Matcher container can be downloaded from [HF](https://huggingface.co/datasets/deBoerLab/Matcher_GAME).

Please visit the [Matcher Github Repo](https://github.com/de-Boer-Lab/GAME_matcher) for the code and more details.

1. **Download the Matcher Container**

    ```bash
    wget -O matcher.sif https://huggingface.co/datasets/deBoerLab/Matcher_GAME/resolve/main/matcher.sif
    ```

2. **Run the Matcher Server**
    This single command starts the container, launches a private Ollama server inside it, and starts the FastAPI server listening for HTTP requests.

    ```bash
    # General Usage:
    # apptainer run --nv --containall <sif_file> <IP_TO_LISTEN_ON> <PORT>

    # Example: Run the matcher, listening on all network interfaces on port 8080
    apptainer run --nv --containall matcher.sif 0.0.0.0 8080
    ```

    **Note:** The `--nv` flag is required to expose the host's NVIDIA GPU drivers to the container for LLM inference.

3. **Verify the Matcher is running**

    Test with curl:

    ```bash
    curl -X POST http://HOST:PORT/match \
         -H "Content-Type: application/json" \
         -d '{"cell_type_requested": "Leukemia cell line", "cell_type_list": ["K562", "A549", "HepG2"]}'
    ```
