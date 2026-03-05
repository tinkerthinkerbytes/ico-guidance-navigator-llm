# Product Requirements Specification (PRS)

## Project
ICO Guidance Navigator — LLM-Assisted Variant (Repo 2)

## Status
Frozen (completed)

## Purpose

This repository exists to explore a single, tightly bounded question:

> Where does a Large Language Model (LLM) add value in a regulated-domain guidance navigation system — and where does it begin to erode safety, clarity, or failure legibility?

This is a controlled continuation of the deterministic ICO Guidance Navigator (Repo 1), which is intentionally frozen.

---

## Scope

Repo 2 introduces an LLM only as a **post-retrieval transformation layer**.

The LLM may be used for:
- paraphrasing retrieved guidance
- summarising retrieved text
- ordering or grouping retrieved passages
- tone or readability transformation

The LLM must not be used to:
- determine relevance
- expand scope
- infer intent
- resolve ambiguity or conflict
- provide advice or recommendations
- make compliance or legal judgements
- override deterministic refusal logic

---

## Inherited Constraints (Non-Negotiable)

The following constraints are carried forward unchanged from Repo 1:

- Same (or near-identical) ICO guidance corpus
- Deterministic retrieval and guardrails
- Conservative refusal logic
- Failure-aware degradation behaviour
- Advisory-only framing
- No compliance decisions or action recommendations
- Structured JSON output contract
- Confidence treated as communicative, not probabilistic
- Inspectable, stoppable system design

---

## System Behaviour

The system operates in two explicit modes:

### Mode A — Deterministic
- Behaviour identical to Repo 1
- No LLM involvement
- Serves as baseline and safety anchor

### Mode B — LLM-Assisted
- Identical retrieval and refusal logic
- LLM operates only on already-retrieved text
- Deterministic mode remains available and complete

The LLM is downstream of correctness, not upstream of truth.

### Current implementation state
- Mode A (deterministic) remains the default runtime behaviour.
- Mode B is implemented as an opt-in post-retrieval transformer (`--use-llm`) and remains bounded to paraphrase/summarise retrieved text only.
- LLM failures or unhelpful outputs degrade safely to deterministic summary plus limitation note.

---

## Risks Under Examination

Repo 2 intentionally surfaces new risks introduced by LLM use, including:

- Soft hallucination via paraphrase drift
- False coherence from summarisation
- Trust inflation due to fluent language
- Boundary erosion (answering instead of restating)

Mitigation is optional; recognition and documentation are mandatory.
These risks have now been exercised and documented in `FINDINGS_AND_RISKS.md`.

---

## Explicit Non-Goals

This repository does not aim to:
- build an agentic system
- introduce autonomy or tool-planning
- optimise performance or scale
- add UI, authentication, or deployment
- evolve into a product or service

---

## Stopping Condition

This repository is considered complete when:

- Deterministic behaviour remains intact
- LLM value is demonstrable but bounded
- New risks are clearly articulated in writing
- The learning objective is fully answered

No further features are required beyond this point.

### Completion decision

As of March 5, 2026, the stopping condition is satisfied:
- deterministic behaviour remains intact
- bounded LLM value is demonstrable via opt-in mode
- risks are explicitly documented

Further development is out of scope unless the PRS is re-opened by human decision.
