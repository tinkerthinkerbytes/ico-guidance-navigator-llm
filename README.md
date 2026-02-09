# ICO Guidance Navigator — LLM-Assisted Variant (WIP)

> **Status:** Work in progress

This repository is a continuation of the deterministic ICO guidance navigator built in Repo 1.

Repo 1 deliberately avoided using an LLM in order to make retrieval, refusal behaviour, and failure modes explicit and inspectable. That repo is now frozen.

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

---

## Behavioural modes

* **Deterministic mode**
  Identical to Repo 1. No LLM involvement. Serves as a baseline.

* **LLM-assisted mode**
  Retrieval and refusal logic remain deterministic.
  The LLM operates only on already-retrieved text.

---

## What this repo does not aim to do

* Build an agentic system
* Introduce autonomy or planning
* Add UI, authentication, or deployment
* Optimise for scale or performance
* Evolve into a product

This is an exploration repo, not a production system.
