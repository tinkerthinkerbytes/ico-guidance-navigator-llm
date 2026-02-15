# ICO Guidance Navigator — LLM-Assisted Variant (WIP)

> **Status:** Work in progress

This repository is a continuation of the deterministic ICO guidance navigator built in Repo 1.

Repo 1 deliberately avoided using an LLM in order to make retrieval, refusal behaviour, and failure modes explicit and inspectable. That repo is now frozen.

---

## Current implementation (today)

* Pipeline runs deterministically by default; retrieval, refusal, and confidence are identical to Repo 1.
* An **opt-in LLM paraphrase step** can be enabled via `--use-llm` (CLI) when `OPENAI_API_KEY` is set.
* LLM usage is strictly post-retrieval and bounded to the retrieved passages; if LLM fails or returns unhelpful text, the deterministic summary is used with a limitation note.
* Default model is `gpt-4o-mini`, with fallbacks (`gpt-5.1-codex-mini`, `gpt-5-mini`) if the primary is unavailable.
* Outputs follow the same structured JSON contract.

---

## What this repo is about

The goal here is simple:

> Understand where an LLM adds value in a regulated guidance-navigation system, and where it starts to introduce new risks or ambiguity.

The domain, corpus, and advisory posture are held constant.
Only the use of an LLM changes.

---

## Intended use of the LLM

If used, the LLM is **strictly downstream of retrieval** and may be used only for:

* paraphrasing retrieved guidance
* summarising retrieved text
* ordering or grouping retrieved passages
* improving readability or tone

The LLM is not used for:

* relevance determination
* scope expansion
* ambiguity or conflict resolution
* advice or recommendations
* compliance or legal judgement

## Out of scope for the LLM

* Deciding relevance or ranking sections
* Expanding or inferring user intent beyond the query
* Overriding deterministic refusal/guardrail outcomes
* Setting confidence levels independently of retrieval signals

---

## Behavioural modes

* **Deterministic mode**
  Identical to Repo 1. No LLM involvement. Serves as a baseline.

* **LLM-assisted mode (opt-in)**
  Retrieval and refusal logic remain deterministic.
  The LLM operates only on already-retrieved text; unhelpful LLM output is discarded in favor of the deterministic summary.
  Enable via `--use-llm` and `OPENAI_API_KEY` (optional `OPENAI_MODEL` override).

---

## Usage

Deterministic (default):
```
python3 -m app.cli "What does ICO say about documenting lawful basis?"
```

LLM-assisted (post-retrieval paraphrase):
```
export OPENAI_API_KEY=sk-...
# optionally: export OPENAI_MODEL=gpt-4o-mini
python3 -m app.cli "What does ICO say about documenting lawful basis?" --use-llm
```

If the selected model is unavailable or the LLM returns an unhelpful message, the pipeline falls back to the deterministic summary and adds a limitation note.

---

## What this repo does not aim to do

* Build an agentic system
* Introduce autonomy or planning
* Add UI, authentication, or deployment
* Optimise for scale or performance
* Evolve into a product

This is an exploration repo, not a production system.
