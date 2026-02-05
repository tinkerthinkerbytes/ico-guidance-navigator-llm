# ICO Guidance Navigator (Bounded RAG Demo)

## Lineage

This repository is a direct continuation of `ico-guidance-navigator`.

Repo 1 is intentionally frozen.
This repository explores a single, controlled change: the reintroduction of a Large Language Model strictly as a transformation layer, while preserving deterministic behaviour, safety guardrails, and failure-aware design.

## Description
Small, local, **bounded RAG** demo to help internal teams **navigate** (not interpret) ICO-style guidance by:

- retrieving relevant guidance sections from a **static local corpus**
- producing a **grounded, advisory-only** summary
- refusing inputs that ask for legal/compliance judgement or “what should we do” actions

## Non-goals (hard constraints)

This project is **not**:

- legal advice
- a compliance decision engine
- a policy interpretation engine
- a production platform (no UI, auth, telemetry, scaling, etc.)

## Safety posture (high level)

- **Retrieval-first:** synthesis is grounded in retrieved sections only.
- **Deterministic refusal:** questions that require legal interpretation, compliance judgement, or action recommendations are refused.
- **Explicit limitations:** every response includes limitations; refusal returns `confidence="very_low"` and `relevant_sections=[]`.
- **No network fetch:** the corpus is local and static for this demo.

## Corpus (important)

The corpus in `app/corpus/` is:

- **static** (checked into the repo; no live fetching/scraping)
- **partial and illustrative** (intentionally small; not complete)
- written to resemble real guidance language for retrieval/synthesis evaluation

Do not treat the corpus as authoritative source text for real decisions.

## Run

```bash
python3 -m app.cli "your question"
```

## Output contract

All outputs conform to the PRS JSON shape:

```json
{
  "summary": "string",
  "relevant_sections": [{"title": "string", "why_relevant": "string"}],
  "limitations": ["string"],
  "confidence": "very_low | low | medium | high"
}
```
