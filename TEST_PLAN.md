# Test plan for bounded LLM summariser and deterministic pipeline

Validate that the pipeline remains deterministic by default, the LLM path is strictly post-retrieval and opt-in, failures fall back safely, and outputs stay within the documented contract. Include human review to verify prompt/response safety and drift.

## Test structure
- **Unit tests (pure, fast)**
  - `llm._extract_text_from_responses` parses `output_text`, nested `output[].content[].text`, and returns `None` on malformed payloads.
  - `summarise_with_llm` behavior without API key returns deterministic summary + note.
  - `summarise_with_llm` with empty `retrieved` returns deterministic summary with no note.
  - `summarise_with_llm` when passages missing returns deterministic summary + note.
  - Payload shape: verify POST target, headers, and body keys (`model`, `input`, `max_output_tokens`) via a stubbed `urlopen`.
- **Integration tests (network mocked)**
  - Pipeline `run(..., use_llm=True)` with successful mock response replaces summary, appends no extra limitation.
  - Pipeline with mocked failure (timeout/HTTP error) returns deterministic summary and adds limitation note, confidence unchanged.
  - Refusal path: `use_llm=True` still yields refusal payload; LLM is never called (stub asserts no requests).
- **Contract/compat tests**
  - JSON schema remains `summary`, `relevant_sections`, `limitations`, `confidence`.
  - `--use-llm` CLI flag passes through to pipeline; default remains deterministic.
  - Model default is `gpt-4o-mini`; fallbacks include `gpt-5.1-codex-mini` and `gpt-5-mini`; env override respected.
- **Non-regression on deterministic path**
  - Re-run existing `app/tests/test_pipeline.py` suite with `use_llm=False` (default).
- **Manual tests (human-in-loop)**
  - With real `OPENAI_API_KEY`, run `python -m app.cli "What does ICO say about documenting lawful basis?" --use-llm`; reviewer checks output contains only paraphrase of retrieved passages, no advice, and limitations intact.
  - Adversarial query: “Give me steps to become compliant” with `--use-llm`; reviewer confirms refusal still returned and LLM not invoked (no key check or LLM note).
  - Empty/weak query (e.g., `""`) with and without `--use-llm`; expect “no matches” deterministic response and LLM skipped.
  - Fallback exercise: set `OPENAI_MODEL=gpt-does-not-exist` and run the lawful-basis query with `--use-llm`; expect deterministic summary plus limitation note indicating primary model failure or unhelpful LLM content.

## Human reviewer checkpoints
- Approve prompt wording in `llm.py` for safety (no advice, no scope creep).
- Spot-check a few real responses for paraphrase drift or hallucination.
- Confirm limitation notes are present on LLM failure and absence of confidence inflation.
- Decide if `max_output_tokens` / model choice are appropriate for cost and tone.

## Acceptance criteria
- All automated tests pass locally with network mocked; deterministic suite unchanged.
- Enabling `--use-llm` does not alter confidence/refusal logic; only summary text may change.
- Failure modes (no key, empty passages, HTTP error) return deterministic summary + limitation note.
- Human review signs off that live responses stay within post-retrieval bounds and avoid recommendations.

## Assumptions
- Network will be mocked in CI; live-key tests are manual only.
- No new external dependencies beyond standard library and existing pytest vendoring.
