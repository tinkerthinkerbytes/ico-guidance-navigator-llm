# Findings and Risks (Repo 2)

Date: March 5, 2026

## Scope of write-up

This write-up summarizes what was observed after implementing and testing the
bounded LLM path in Repo 2.

## Findings

1. Deterministic baseline remains intact.
   - Default runtime path is deterministic.
   - Retrieval, guardrails, refusal behavior, and confidence signaling remain unchanged.

2. LLM value is present but tightly limited.
   - `--use-llm` enables post-retrieval paraphrase/summarization only.
   - LLM output can improve readability while preserving source-bounded content.

3. Failure behavior is conservative.
   - Missing key, API/network failures, and unhelpful outputs fall back to deterministic summary.
   - Fallback adds limitation notes rather than silently masking failure.

4. Output contract stability is preserved.
   - Response schema remains `summary`, `relevant_sections`, `limitations`, `confidence`.
   - Confidence is still evidence-derived from retrieval signals, not LLM fluency.

## Residual risks

1. Paraphrase drift risk remains.
   - Even when bounded to retrieved passages, phrasing can over-compress nuance.

2. Trust inflation risk remains.
   - Fluent summaries may appear more authoritative than warranted by weak retrieval.

3. Fallback observability is partial in live checks.
   - Safe fallback behavior is confirmed.
   - Some model-unavailable paths can manifest as "unhelpful output discarded" rather than explicit fallback-note wording.

4. External dependency risk remains.
   - LLM mode depends on model availability, network reliability, and API access.

## Conclusion

Repo 2 is complete for its stated learning objective. It demonstrates bounded
LLM utility while preserving deterministic safety boundaries and documents the
main residual risks. Further feature development is not required unless scope is
explicitly reopened.
