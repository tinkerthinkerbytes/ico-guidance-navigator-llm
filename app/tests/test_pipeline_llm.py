import json
import os
import urllib.error
from unittest import TestCase, mock

from app.pipeline import NavigatorPipeline

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus")


def fake_response_body(text: str):
    return json.dumps({"output_text": text}).encode("utf-8")


class PipelineLLMTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = NavigatorPipeline(CORPUS_DIR)

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test"})
    def test_llm_success_replaces_summary(self):
        def fake_urlopen(req, timeout=10):
            class FakeResponse:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

                def read(self_inner, *args, **kwargs):
                    return fake_response_body("LLM paraphrase")

            return FakeResponse()

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            res = self.pipeline.run(
                "What does the guidance say about choosing and documenting a lawful basis before processing personal data?",
                use_llm=True,
            )
        self.assertEqual(res["summary"], "LLM paraphrase")
        self.assertFalse(any("LLM summary failed" in l for l in res["limitations"]))

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test"})
    def test_llm_failure_falls_back_and_preserves_confidence(self):
        question = "How should we record processing activities?"
        baseline = self.pipeline.run(question, use_llm=False)
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            llm_res = self.pipeline.run(question, use_llm=True)
        self.assertEqual(llm_res["summary"], baseline["summary"])
        self.assertEqual(llm_res["confidence"], baseline["confidence"])
        self.assertTrue(any("LLM summary failed" in l for l in llm_res["limitations"]))

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test", "OPENAI_MODEL": "gpt-5-mini"})
    def test_llm_fallback_appends_note(self):
        calls = {"count": 0}

        def fake_urlopen(req, timeout=10):
            calls["count"] += 1
            if calls["count"] == 1:
                raise urllib.error.HTTPError(req.full_url, 404, "model not found", hdrs=None, fp=None)

            class FakeResponse:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

                def read(self_inner, *args, **kwargs):
                    return fake_response_body("LLM fallback summary")

            return FakeResponse()

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            res = self.pipeline.run(
                "What does the guidance say about choosing and documenting a lawful basis before processing personal data?",
                use_llm=True,
            )
        self.assertEqual(res["summary"], "LLM fallback summary")
        self.assertTrue(any("LLM fallback used" in l for l in res["limitations"]))

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test"})
    def test_refusal_does_not_invoke_llm(self):
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("LLM should not be called")):
            res = self.pipeline.run("Is this lawful?", use_llm=True)
        self.assertEqual(res["confidence"], "very_low")
        self.assertEqual(res["relevant_sections"], [])
        self.assertIn("legal advice", res["summary"])
