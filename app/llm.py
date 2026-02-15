"""Bounded post-retrieval LLM hook.

This module keeps the LLM downstream of retrieval. It never influences
relevance, guardrails, or confidence; it only paraphrases/summarises
already-retrieved text when explicitly enabled.
"""

import json
import os
import urllib.request
from typing import List, Optional, Tuple

from .models import RetrievedSection


def _format_retrieved_passages(retrieved: List[RetrievedSection], max_items: int = 5) -> str:
    """Join a small set of retrieved passages to feed the LLM.

    We include only top-ranked items and their first matched paragraph to keep
    prompts bounded and avoid scope creep.
    """

    blocks = []
    for item in retrieved[:max_items]:
        if not item.section.paragraphs:
            continue
        para_idx = item.matched_paragraphs[0] if item.matched_paragraphs else 0
        paragraph = item.section.paragraphs[para_idx]
        blocks.append(f"Title: {item.section.title}\nParagraph: {paragraph}")
    return "\n\n".join(blocks)


def _build_prompt(passage_block: str) -> str:
    return (
        "You are a cautious summariser working in a regulated domain. "
        "Only use the provided passages to paraphrase succinctly. "
        "Do not add advice, recommendations, or new facts. If the passages do "
        "not answer the question, state that the provided passages do not "
        "contain an answer."
        "\n\nPassages:\n" + passage_block
    )


def summarise_with_llm(
    retrieved: List[RetrievedSection],
    deterministic_summary: str,
    model_env_var: str = "OPENAI_MODEL",
    api_key_env_var: str = "OPENAI_API_KEY",
) -> Tuple[str, str | None]:
    """Attempt an LLM paraphrase of retrieved text.

    Returns (summary, note). On any failure or missing key, the deterministic
    summary is returned along with a note explaining the fallback.
    """

    api_key = os.getenv(api_key_env_var)
    if not api_key:
        return deterministic_summary, "LLM summary skipped: missing OPENAI_API_KEY"

    if not retrieved:
        return deterministic_summary, None

    # Default to cost/latency-efficient model; callers can override via env.
    model = os.getenv(model_env_var, "gpt-5.1-mini")
    passage_block = _format_retrieved_passages(retrieved)
    if not passage_block:
        return deterministic_summary, "LLM summary skipped: empty passages after retrieval"

    payload = {
        # Responses API (preferred going forward)
        "model": model,
        "input": _build_prompt(passage_block),
        "max_output_tokens": 200,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
        summary = _extract_text_from_responses(data) or deterministic_summary
        return summary, None
    except Exception as exc:  # pragma: no cover - network may be unavailable in tests
        note = f"LLM summary failed; deterministic summary used ({exc.__class__.__name__})"
        return deterministic_summary, note


def _extract_text_from_responses(payload: dict) -> Optional[str]:
    """Robustly pull text from the Responses API payload."""
    if not isinstance(payload, dict):
        return None
    # Convenient shortcut exposed by the API/SDK when present.
    txt = payload.get("output_text")
    if isinstance(txt, str) and txt.strip():
        return txt.strip()
    output = payload.get("output")
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, dict):
            content = first.get("content")
            if isinstance(content, list) and content:
                piece = content[0]
                if isinstance(piece, dict):
                    text_val = piece.get("text")
                    if isinstance(text_val, str) and text_val.strip():
                        return text_val.strip()
    return None
