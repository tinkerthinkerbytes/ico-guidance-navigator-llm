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

# Models to fall back to if the primary model is unavailable.
FALLBACK_MODELS = ["gpt-5.1-codex-mini", "gpt-4o-mini"]

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


def _build_prompt(passage_block: str, question: str) -> str:
    return (
        "You are a cautious summariser working in a regulated domain. "
        "Only use the provided passages to paraphrase succinctly into 2-3 sentences. "
        "Do not add advice, recommendations, or new facts. "
        "If passages are empty, state that no passages were provided."
        "\n\nQuestion:\n"
        + question
        + "\n\nPassages:\n"
        + passage_block
    )


def summarise_with_llm(
    retrieved: List[RetrievedSection],
    deterministic_summary: str,
    question: str,
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

    primary_model = os.getenv(model_env_var, "gpt-4o-mini")
    passage_block = _format_retrieved_passages(retrieved)
    if not passage_block:
        return deterministic_summary, "LLM summary skipped: empty passages after retrieval"

    models = _candidate_models(primary_model)
    first_error: Optional[Tuple[str, str]] = None
    for model in models:
        # Responses API payload stays minimal: one user message with question + passages.
        payload = {
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": _build_prompt(passage_block, question)},
                    ],
                }
            ],
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
            summary = _extract_text_from_responses(data)
            if _is_unhelpful_summary(summary):
                summary = deterministic_summary
                note = "LLM summary discarded: unhelpful content"
                return summary, note
            summary = summary or deterministic_summary
            if first_error:
                failed_model, detail = first_error
                note = f"LLM fallback used; primary {failed_model} failed ({detail})"
                return summary, note
            return summary, None
        except urllib.error.HTTPError as exc:  # pragma: no cover - network may be unavailable in tests
            detail = _format_error_detail(exc)
            if first_error is None:
                first_error = (model, detail)
            if _is_model_error(exc, detail):
                # Try next fallback model.
                continue
            note = f"LLM summary failed; deterministic summary used ({detail})"
            return deterministic_summary, note
        except Exception as exc:  # pragma: no cover
            detail = _format_error_detail(exc)
            note = f"LLM summary failed; deterministic summary used ({detail})"
            return deterministic_summary, note

    # All models failed.
    if first_error:
        failed_model, detail = first_error
        note = f"LLM summary failed; deterministic summary used ({failed_model}: {detail})"
    else:
        note = "LLM summary failed; deterministic summary used (unknown error)"
    return deterministic_summary, note


def _extract_text_from_responses(payload: dict) -> Optional[str]:
    """Robustly pull text from the Responses API payload."""
    if not isinstance(payload, dict):
        return None
    # Shortcut: Responses API exposes output_text when present.
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


def _is_model_error(exc: urllib.error.HTTPError, detail: str) -> bool:
    """Return True if error likely due to model availability/access."""
    if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
        return True
    lowered = detail.lower()
    return "model" in lowered or "not exist" in lowered or "must be verified" in lowered


def _candidate_models(primary: str) -> List[str]:
    """Return de-duplicated primary + fallback list, preserving order."""
    seen = set()
    ordered: List[str] = []
    for m in [primary] + FALLBACK_MODELS:
        if m and m not in seen:
            seen.add(m)
            ordered.append(m)
    return ordered


def _is_unhelpful_summary(summary: Optional[str]) -> bool:
    """Treat empty or boilerplate refusals as unusable."""
    if not summary:
        return True
    lower = summary.strip().lower()
    fallback_phrases = {
        "the provided passages do not contain an answer.",
        "no passages were provided.",
        "no answer provided.",
    }
    return lower in fallback_phrases


def _format_error_detail(exc: Exception) -> str:
    """Return short error detail for limitations notes."""
    if hasattr(exc, "read"):
        try:
            body = exc.read().decode("utf-8", errors="ignore")
            body = (body or "").strip()
            if len(body) > 180:
                body = body[:177] + "..."
            return f"{exc.__class__.__name__} {getattr(exc, 'code', '')} {body}".strip()
        except Exception:
            pass
    return exc.__class__.__name__
