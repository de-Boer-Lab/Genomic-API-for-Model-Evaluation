# GAME — Spec & Documentation Repo

## Project

GAME (Genomic API for Model Evaluation) standardizes benchmarking of genomic ML models. Two module types talk over a common REST protocol: Evaluators (dataset APIs) send structured prediction requests to Predictors (model APIs), which return predictions in a standard format; Evaluators then score against ground truth (Pearson r). Modules are containerized with Apptainer.

This repo (`Genomic-API-for-Model-Evaluation`) is the **source of truth for the spec and its documentation** — it is not a module implementation. Community module implementations (Evaluators/Predictors) live in a separate repo, `GAME_modules`, which is updated in a later, separate step once spec changes here are reviewed and pushed.

## Repo layout

- `docs/` — Sphinx/ReadTheDocs source (`.rst`). Builds the public docs site (genomic-api-for-model-evaluation-documentation.readthedocs.io). Key structure:
  - `docs/API/` — the spec itself: `RESTAPI_methods.rst`, `Evaluator_requests.rst` (Evaluator API schema), `Predictor_responses.rst` (Predictor API schema), `help.rst` (help endpoint), `Error_messages.rst`, `Matcher_schema.rst`
  - `docs/Building_Modules/` — guidance for third parties building Evaluators/Predictors: `Build_test_modules.rst`, `Contributing_modules.rst`, `helpful_tips_notes.rst`
  - Root-level docs pages: `Using_prebuilt_containers.rst`, `Matcher.rst`, `Submitting_jobs.rst`, `Predictor_distributor.rst`, `versioning.rst`, `FAQ.rst`, `External_Routing.rst`, `Contributors.rst`
- `example_JSON_files/` — example request/response payloads referenced by the spec docs. **Must stay in sync** with any schema change made in `docs/API/`.
- `src/` — diagrams (`module-comms-white-bg.png`, `api-outline-white-bg.png`) and reference modules under `src/Test_Modules/`:
  - `Test_Predictor` — model-free reference Predictor used to validate new Evaluators against the spec (handles all task types — expression, accessibility, interaction matrix — and ignores cell-type/species checks).
  - `Test_Evaluator` — its counterpart: a reference Evaluator used to validate new Predictors against the spec. Ships with its own small synthetic test data under `Test_Evaluator/evaluator_data/` (e.g. `test_evaluator_request.json` — short synthetic sequences, mixed species/cell-type/task-type prediction_tasks, and edge-case `prediction_ranges` like boundary and empty ranges) rather than requiring a real dataset.
- `readthedocs.yaml` — RTD build config.
- `README.md` — top-level overview and points of contact.

## What this agent is for

This work happens in two phases: (1) update the spec and documentation in this repo, reviewed and pushed here first; (2) only afterward, update module implementations in `GAME_modules` to match. **This agent is scoped to phase (1) only.**

Primary job: propose spec and documentation changes in this repo — editing `.rst` spec files under `docs/API/`, keeping `example_JSON_files/` consistent with schema edits, and fixing/improving documentation elsewhere under `docs/`.

Out of scope unless explicitly asked:

- Don't edit anything in `GAME_modules` or any other module-implementation repo — that's phase (2), handled by a different agent/session, only after spec changes here are reviewed and pushed.
- Don't modify `src/Test_Modules/Test_Predictor`, `src/Test_Modules/Test_Evaluator`, or other reference module code as part of a documentation fix — flag it instead if a spec change would require a reference implementation to change too.
- Don't touch `Genomic-Model-Evaluation-API.Rproj`, CI, or build config unless asked.

## Workflow

1. The developer describes the spec/doc change needed.
2. Edit the relevant `.rst` / JSON files directly in the working tree.
3. Do **not** run `git add`, `git commit`, or `git push` unless explicitly asked — changes are reviewed via `git diff` and committed/pushed by the developer on their own schedule.
4. When a change to `docs/API/*` alters request/response shape, required fields, or error codes, call it out explicitly and check whether:
   - `example_JSON_files/` needs a matching update,
   - `docs/API/Error_messages.rst` needs a new or changed error code,
   - `docs/versioning.rst` needs a note — this is a versioned spec, so breaking changes need a documented version bump,
   - `GAME_modules` will eventually need corresponding implementation changes (flag this — don't act on it here).
5. Keep changes scoped and minimal — don't reformat unrelated prose while fixing one section.

## Documentation conventions

- Sphinx reStructuredText (`.rst`) under `docs/` — the root `README.md` is the one Markdown exception.
- Follow the existing heading hierarchy and cross-reference style already used in each file; check neighboring `.rst` files for the pattern before introducing a new one.
- Spec pages should stay precise and implementation-agnostic — describe the contract (fields, types, required/optional, valid values), not any one predictor's or evaluator's internal behavior.

## Verification before handing back a change

- Re-read edited `.rst` for Sphinx syntax errors (unclosed directives, bad indentation, broken `:ref:`/`:doc:` links).
- If `example_JSON_files/` changed, confirm the JSON is syntactically valid.
- If `sphinx-build` is available locally, offer to build `docs/` and check for warnings before handing back.
- Summarize exactly which files changed and why, so review is fast.
