import argparse
import json
import os
import sys

from .pipeline import NavigatorPipeline


def main():
    parser = argparse.ArgumentParser(description="ICO Guidance Navigator")
    parser.add_argument("question", type=str, help="Natural-language question to answer")
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "corpus"),
        help="Path to corpus directory",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Enable bounded LLM paraphrase of the deterministic summary (requires OPENAI_API_KEY)",
    )
    args = parser.parse_args()

    pipeline = NavigatorPipeline(args.corpus_dir)
    result = pipeline.run(args.question, use_llm=args.use_llm)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
