# GAME — Spec & Documentation Repo

## Project

GAME (Genomic API for Model Evaluation) standardizes benchmarking of genomic ML models. Two module types talk over a common REST protocol: Evaluators (dataset APIs) send structured prediction requests to Predictors (model APIs), which return predictions in a standard format; Evaluators then score against ground truth (Pearson r). Modules are containerized with Apptainer.

This repo (`Genomic-API-for-Model-Evaluation`) is the **source of truth for the spec and its documentation** — it is not a module implementation. Community module implementations (Evaluators/Predictors) live in a separate repo, `GAME_modules`, which is updated in a later, separate step once spec changes here are reviewed and pushed.

## Repo layout

- `docs/` — Sphinx/ReadTheDocs project (genomic-api-for-model-evaluation-documentation.readthedocs.io). All source lives in `docs/source/` and is **Markdown parsed by `myst_parser`**; only the `index.rst` toctree files are `.rst`. `docs/build/` is generated output (gitignored) — never edit or search it. Key structure:
  - `docs/source/API/` — the spec itself: `docs/source/API/RESTAPI_methods.md`, `docs/source/API/Evaluator_requests.md` (Evaluator API schema), `docs/source/API/Predictor_responses.md` (Predictor API schema), `docs/source/API/help.md` (help endpoint), `docs/source/API/Error_messages.md`, `docs/source/API/Matcher_schema.md`, `docs/source/API/index.rst`
  - `docs/source/Building_Modules/` — guidance for third parties building Evaluators/Predictors: `docs/source/Building_Modules/Build_test_modules.md`, `docs/source/Building_Modules/Contributing_modules.md`, `docs/source/Building_Modules/helpful_tips_notes.md`, `docs/source/Building_Modules/index.rst`
  - Root-level pages: `docs/source/main_page.md`, `docs/source/Using_prebuilt_containers.md`, `docs/source/Matcher.md`, `docs/source/Submitting_jobs.md`, `docs/source/Predictor_distributor.md`, `docs/source/versioning.md`, `docs/source/FAQ.md`, `docs/source/Troubleshooting.md`, `docs/source/External_Routing.md`, `docs/source/Contributors.md`
  - `docs/source/index.rst` (root toctree), `docs/source/conf.py` (Sphinx config), `docs/source/images/`
- `example_JSON_files/` — example request/response payloads referenced by the spec docs. **Must stay in sync** with any schema change made in `docs/source/API/`. Layout:
  - `example_JSON_files/sampleRequest1/` — `example_JSON_files/sampleRequest1/evaluator_request_simple.json`, `example_JSON_files/sampleRequest1/predictor_response_simple.json`, `example_JSON_files/sampleRequest1/mpra_evaluator_test_sequences.txt`
  - `example_JSON_files/sampleRequest2/` — fuller `example_JSON_files/sampleRequest2/evaluator_request.json` / `example_JSON_files/sampleRequest2/predictor_response.json` pair
  - `example_JSON_files/helpExample/predictor_help_message.json` — example `GET /help` response
  - `example_JSON_files/error_message_sample.json`
- `src/` — diagrams (`src/module-comms-white-bg.png`, `src/api-outline-white-bg.png`, plus the non-white-bg `src/api-outline.png` and `src/module-comms.png`, and `src/communication_protocol.png`), job scripts, and reference modules:
  - `src/job-submission-scripts/` — SLURM + Apptainer launch scripts for running full GAME pipelines (Matcher, Predictors, PD, Evaluator); has its own `src/job-submission-scripts/README.md`.
  - `src/Test_Modules/Test_Predictor/` — model-free reference Predictor used to validate new Evaluators against the spec (handles all task types — expression, accessibility, interaction matrix — and ignores cell-type/species checks).
  - `src/Test_Modules/Test_Evaluator/` — its counterpart: a reference Evaluator used to validate new Predictors against the spec. Ships with its own small synthetic test data in `src/Test_Modules/Test_Evaluator/evaluator_data/test_evaluator_request.json` (short synthetic sequences, mixed species/cell-type/task-type `prediction_tasks`, and edge-case `prediction_ranges` such as start-of-sequence, end-of-sequence, full-length, boundary and empty `[]` ranges) rather than requiring a real dataset.
- `readthedocs.yaml` — RTD build config.
- `README.md` — top-level overview and points of contact.

## What this agent is for

This work happens in two phases: (1) update the spec and documentation in this repo, reviewed and pushed here first; (2) only afterward, update module implementations in `GAME_modules` to match. **This agent is scoped to phase (1) only.**

Primary job: propose spec and documentation changes in this repo — editing the Markdown spec files under `docs/source/API/`, keeping `example_JSON_files/` consistent with schema edits, and fixing/improving documentation elsewhere under `docs/source/`.

Out of scope unless explicitly asked:

- Don't edit anything in `GAME_modules` or any other module-implementation repo — that's phase (2), handled by a different agent/session, only after spec changes here are reviewed and pushed.
- Don't modify `src/Test_Modules/Test_Predictor`, `src/Test_Modules/Test_Evaluator`, or other reference module code as part of a documentation fix — flag it instead if a spec change would require a reference implementation to change too.
- Don't touch `Genomic-Model-Evaluation-API.Rproj`, CI, or build config unless asked.

## Workflow

1. The developer describes the spec/doc change needed.
2. **Present the proposed changes first, before making them** — state which files will change and show the exact before/after wording (or a clear summary for large edits). Wait for the developer's go-ahead before editing. The only exception is when the developer has explicitly told you to make a specific edit; even then, show the resulting diff afterward.
3. Make sure you are on a dedicated branch (not `main`) before editing; if the developer asks for a new branch, create it before making any changes.
4. Edit the relevant `.md` / JSON files directly in the working tree.
5. Do **not** run `git add`, `git commit`, or `git push` unless explicitly asked — changes are reviewed via `git diff` and committed/pushed by the developer on their own schedule.
6. When a change to `docs/source/API/*` alters request/response shape, required fields, or error codes, call it out explicitly and check whether:
   - `example_JSON_files/` needs a matching update,
   - `docs/source/API/Error_messages.md` needs a new or changed error code,
   - `docs/source/versioning.md` needs a note — `game_schema_version` is `MAJOR.MINOR`: optional-key additions are a minor bump, while adding/removing/renaming required keys is a major bump,
   - `docs/source/API/Matcher_schema.md` and the Predictor Distributor may be affected (the Matcher is covered by the same schema version; the PD depends on `sequences`, `prediction_ranges`, `prediction_tasks`, `predictions`),
   - `game_schema_version` examples in `docs/source/API/help.md` and `example_JSON_files/helpExample/` are still correct,
   - `GAME_modules` will eventually need corresponding implementation changes (flag this — don't act on it here).
7. Keep changes scoped and minimal — don't reformat unrelated prose while fixing one section.

## Documentation conventions

- Markdown (MyST) under `docs/source/`; only the `index.rst` toctree files are reStructuredText. Tables are pipe tables, and HTML entities like `&rarr;` are used in places — match the surrounding file.
- Follow the existing heading hierarchy and cross-reference style already used in each file; check neighboring `.md` files for the pattern before introducing a new one.
- Spec pages should stay precise and implementation-agnostic — describe the contract (fields, types, required/optional, valid values), not any one predictor's or evaluator's internal behavior.

## Verification before handing back a change

Check your work in detail — don't assume an edit is correct. Re-read the full diff, and verify every claim you wrote against the repo (file paths exist, field names and counts match the source files, nothing existing was dropped unintentionally).

- Re-read edited `.md` for MyST/Sphinx problems (malformed pipe tables, unclosed code fences, broken relative links or toctree entries in `index.rst`).
- If `example_JSON_files/` changed, confirm the JSON is syntactically valid.
- If `sphinx-build` is available locally, offer to build (`sphinx-build docs/source docs/build/html`, deps in `docs/requirements.txt`) and check for warnings before handing back.
- Summarize exactly which files changed and why, so review is fast.
