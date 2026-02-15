from typing import Dict, List

from .corpus_loader import load_corpus
from .retrieval import BM25Retriever, tokenize
from .refusal import should_refuse
from .output_format import build_response
from .models import RetrievedSection


class NavigatorPipeline:
    def __init__(self, corpus_dir: str):
        self.sections = load_corpus(corpus_dir)
        self.retriever = BM25Retriever(self.sections)

    def _annotate_matches(self, retrieved: List[RetrievedSection], question: str) -> None:
        q_terms = set(tokenize(question))
        for item in retrieved:
            matches = []
            for idx, paragraph in enumerate(item.section.paragraphs):
                tokens = set(tokenize(paragraph))
                if q_terms & tokens:
                    matches.append(idx)
            if not matches and item.section.paragraphs:
                matches.append(0)
            item.matched_paragraphs = matches

    def run(self, question: str, top_k: int = 5, use_llm: bool = False) -> Dict:
        if should_refuse(question):
            reason = "Cannot provide legal advice, compliance decisions, or action recommendations."
            return build_response([], refusal=True, refusal_reason=reason)

        retrieved = self.retriever.retrieve(question, top_k=top_k)
        # Drop weak/coverage-failed hits rather than presenting loosely-related sections as "relevant".
        retrieved = [r for r in retrieved if not r.coverage_weak]
        self._annotate_matches(retrieved, question)
        # use_llm remains opt-in; default False keeps current deterministic behaviour.
        return build_response(retrieved, refusal=False, use_llm=use_llm)
