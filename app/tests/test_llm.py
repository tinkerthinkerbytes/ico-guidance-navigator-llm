import json
import os
import urllib.error
from types import SimpleNamespace
from unittest import TestCase, mock

from app import llm
from app.models import RetrievedSection, Section


def make_retrieved(title="T", paragraph="P", matched_idx=0):
    section = Section(
        section_id="s1",
        title=title,
        paragraphs=[paragraph],
        paragraph_ids=["s1#p1"],
        topic="t",
    )
    return RetrievedSection(
        section=section,
        rank=1,
        lexical_score=1.0,
        embedding_score=0.0,
        coverage_weak=False,
        conflict_flag=False,
        matched_paragraphs=[matched_idx],
    )


class ExtractTextTests(TestCase):
    def test_output_text_shortcut(self):
        payload = {"output_text": " hello "}
        self.assertEqual(llm._extract_text_from_responses(payload), "hello")

    def test_nested_output_content(self):
        payload = {"output": [{"content": [{"text": " hi there "}] }]}
        self.assertEqual(llm._extract_text_from_responses(payload), "hi there")

    def test_malformed_returns_none(self):
        self.assertIsNone(llm._extract_text_from_responses({"output": [{}]}))
        self.assertIsNone(llm._extract_text_from_responses("not a dict"))


class SummariseWithLLMTests(TestCase):
    def test_missing_api_key_returns_note(self):
        summary, note = llm.summarise_with_llm([make_retrieved()], "deterministic", "Q")
        self.assertEqual(summary, "deterministic")
        self.assertIn("missing OPENAI_API_KEY", note)

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test"})
    def test_empty_retrieved_no_note(self):
        summary, note = llm.summarise_with_llm([], "deterministic", "Q")
        self.assertEqual(summary, "deterministic")
        self.assertIsNone(note)

    @mock.patch.dict(os.environ, {"KEY": "present"})
    def test_empty_passages_returns_note(self):
        section = Section(
            section_id="s2",
            title="Empty",
            paragraphs=[],
            paragraph_ids=[],
            topic="t",
        )
        retrieved = RetrievedSection(
            section=section,
            rank=1,
            lexical_score=1.0,
            embedding_score=0.0,
            coverage_weak=False,
            conflict_flag=False,
            matched_paragraphs=[],
        )
        summary, note = llm.summarise_with_llm([retrieved], "deterministic", "Q", api_key_env_var="KEY")
        self.assertEqual(summary, "deterministic")
        self.assertIn("empty passages", note)

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test", "OPENAI_MODEL": "gpt-5.1-chat-latest"})
    def test_payload_and_model_override(self):
        captured = {}

        def fake_urlopen(req, timeout=10):
            captured["req"] = req
            captured["payload"] = json.loads(req.data.decode("utf-8"))
            resp_payload = json.dumps({"output_text": "LLM summary"}).encode("utf-8")

            class FakeResponse:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

                def read(self_inner, *args, **kwargs):
                    return resp_payload

            return FakeResponse()

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            summary, note = llm.summarise_with_llm([make_retrieved()], "deterministic", "Q")
        self.assertEqual(summary, "LLM summary")
        self.assertIsNone(note)
        req = captured["req"]
        payload = captured["payload"]
        self.assertEqual(req.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(req.headers.get("Content-type"), "application/json")
        self.assertIn("Bearer test", req.headers.get("Authorization", ""))
        self.assertEqual(payload["model"], "gpt-5.1-chat-latest")
        self.assertIn("input", payload)
        self.assertEqual(
            payload["input"],
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": mock.ANY},
                    ],
                }
            ],
        )
        self.assertEqual(payload["max_output_tokens"], 200)

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test", "OPENAI_MODEL": "gpt-5-mini"})
    def test_model_fallback_on_404(self):
        calls = {"count": 0, "models": []}

        def fake_urlopen(req, timeout=10):
            calls["count"] += 1
            payload = json.loads(req.data.decode("utf-8"))
            calls["models"].append(payload["model"])
            if calls["count"] == 1:
                raise urllib.error.HTTPError(req.full_url, 404, "model not found", hdrs=None, fp=None)
            resp_payload = json.dumps({"output_text": "Fallback summary"}).encode("utf-8")

            class FakeResponse:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

                def read(self_inner, *args, **kwargs):
                    return resp_payload

            return FakeResponse()

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            summary, note = llm.summarise_with_llm([make_retrieved()], "deterministic", "Q")
        self.assertEqual(summary, "Fallback summary")
        self.assertIn("LLM fallback used", note)
        # First attempt primary, second attempt fallback.
        self.assertEqual(calls["models"][0], "gpt-5-mini")
        self.assertEqual(calls["models"][1], llm.FALLBACK_MODELS[0])

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test"})
    def test_unhelpful_summary_discards_to_deterministic(self):
        def fake_urlopen(req, timeout=10):
            resp_payload = json.dumps({"output_text": "The provided passages do not contain an answer."}).encode("utf-8")

            class FakeResponse:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

                def read(self_inner, *args, **kwargs):
                    return resp_payload

            return FakeResponse()

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            summary, note = llm.summarise_with_llm([make_retrieved()], "deterministic", "Q")
        self.assertEqual(summary, "deterministic")
        self.assertEqual(note, "LLM summary discarded: unhelpful content")

    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test"})
    def test_network_error_falls_back(self):
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            summary, note = llm.summarise_with_llm([make_retrieved()], "deterministic", "Q")
        self.assertEqual(summary, "deterministic")
        self.assertIn("LLM summary failed", note)
