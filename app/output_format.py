from typing import Dict, List

from .models import RetrievedSection
from .synthesis import build_summary, build_relevant_sections, build_limitations
from .confidence import determine_confidence
from .llm import summarise_with_llm


def build_response(
    retrieved: List[RetrievedSection],
    refusal: bool,
    refusal_reason: str = "",
    use_llm: bool = False,
    question: str = "",
) -> Dict:
    if refusal:
        return {
            "summary": refusal_reason,
            "relevant_sections": [],
            "limitations": [refusal_reason],
            "confidence": "very_low",
        }

    summary = build_summary(retrieved)
    relevant_sections = build_relevant_sections(retrieved)
    limitations = build_limitations(retrieved, refusal=False)
    confidence = determine_confidence(retrieved, refusal=False)

    # Optional, bounded LLM paraphrase of the deterministic summary.
    if use_llm:
        summary, note = summarise_with_llm(retrieved, summary, question)
        if note:
            limitations.append(note)

    return {
        "summary": summary,
        "relevant_sections": relevant_sections,
        "limitations": limitations,
        "confidence": confidence,
    }
