import argparse
import sys
from pathlib import Path

import dspy

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import configure_dspy


class ExplainTerm(dspy.Signature):
    """Explain a concept in one short paragraph."""

    term = dspy.InputField(desc="Term or concept to explain")
    explanation = dspy.OutputField(desc="Clear, concise explanation")


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal DSPy smoke test")
    parser.add_argument("--term", default="retrieval augmented generation", help="Concept to explain")
    args = parser.parse_args()

    settings = configure_dspy()
    program = dspy.Predict(ExplainTerm)
    result = program(term=args.term)

    print(f"Azure deployment: {settings.azure_deployment}")
    print(f"Input: {args.term}")
    print("Output:")
    print(result.explanation)


if __name__ == "__main__":
    main()
