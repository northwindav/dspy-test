import json
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

import dspy

dspy.configure(provide_traceback=True)

INVERSION_LABELS = ("none", "weak", "moderate", "strong")


class ClassifyInversionStrength(dspy.Signature):
    """Determine presence of an inversion in the lower atmopshere and classify its strength based on a combination of magnitude and depth."""

    sounding_text: str = dspy.InputField(desc="Text-only vertical profile (sounding) data.")
    label: str = dspy.OutputField(desc="One of: none, weak, moderate, strong")


@dataclass(frozen=True)
class DatasetExample:
    sounding_text: str
    label: str
    source: str


def load_examples(dataset_path: Path, profile_type: str = "stability") -> list[DatasetExample]:
    raw_examples = json.loads(dataset_path.read_text(encoding="utf-8"))
    examples: list[DatasetExample] = []

    for index, raw_example in enumerate(raw_examples, start=1):
        if raw_example.get("profile_type", profile_type) != profile_type:
            continue

        label = raw_example["label"].strip().lower()
        if label not in INVERSION_LABELS:
            raise ValueError(
                f"Invalid label '{label}' for example {index}. Expected one of: {', '.join(INVERSION_LABELS)}"
            )

        examples.append(
            DatasetExample(
                sounding_text=raw_example["sounding_text"].strip(),
                label=label,
                source=raw_example.get("source", f"example-{index}"),
            )
        )

    return examples


def to_dspy_examples(examples: list[DatasetExample]) -> list[dspy.Example]:
    return [
        dspy.Example(
            sounding_text=example.sounding_text,
            label=example.label,
            source=example.source,
        ).with_inputs("sounding_text")
        for example in examples
    ]


def split_examples(examples: list[DatasetExample], train_size: int) -> tuple[list[DatasetExample], list[DatasetExample]]:
    if train_size <= 0 or train_size >= len(examples):
        raise ValueError("train_size must be greater than 0 and smaller than the dataset size")

    return examples[:train_size], examples[train_size:]


def stratified_split_examples(
    examples: list[DatasetExample],
    train_size: int,
    seed: int = 0,
) -> tuple[list[DatasetExample], list[DatasetExample]]:
    if train_size <= 0 or train_size >= len(examples):
        raise ValueError("train_size must be greater than 0 and smaller than the dataset size")

    grouped: dict[str, list[DatasetExample]] = {}
    for example in examples:
        grouped.setdefault(example.label, []).append(example)

    if train_size < len(grouped):
        raise ValueError(
            f"train_size={train_size} is too small for stratified splitting across {len(grouped)} labels"
        )

    rng = random.Random(seed)
    train_examples: list[DatasetExample] = []
    remaining_examples: list[DatasetExample] = []

    for label_group in grouped.values():
        shuffled = label_group[:]
        rng.shuffle(shuffled)
        train_examples.append(shuffled[0])
        remaining_examples.extend(shuffled[1:])

    extra_needed = train_size - len(train_examples)
    rng.shuffle(remaining_examples)
    train_examples.extend(remaining_examples[:extra_needed])
    dev_examples = remaining_examples[extra_needed:]

    rng.shuffle(train_examples)
    rng.shuffle(dev_examples)
    return train_examples, dev_examples


def label_exact_match(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> bool:
    return example.label.strip().lower() == prediction.label.strip().lower()


def build_classifier() -> dspy.Module:
    return dspy.Predict(ClassifyInversionStrength)


def sum_total_tokens(history_entries: list[dict]) -> int:
    total_tokens = 0
    for entry in history_entries:
        usage = entry.get("usage") or {}
        total_tokens += int(usage.get("total_tokens") or 0)
    return total_tokens


def evaluate_program(program: dspy.Module, devset: list[dspy.Example]) -> dict[str, float]:
    evaluate = dspy.Evaluate(devset=devset, metric=label_exact_match, display_progress=False, display_table=False)
    original_cache = dspy.settings.lm.cache
    dspy.settings.lm.cache = False
    history_start = len(dspy.settings.lm.history)

    try:
        score = float(evaluate(program))
    finally:
        dspy.settings.lm.cache = original_cache

    history_slice = dspy.settings.lm.history[history_start:]
    total_tokens = sum_total_tokens(history_slice)
    examples_evaluated = len(devset)
    accuracy = score / 100.0 if score > 1.0 else score

    return {
        "accuracy": accuracy,
        "examples": float(examples_evaluated),
        "total_tokens": float(total_tokens),
        "avg_tokens_per_example": total_tokens / examples_evaluated if examples_evaluated else 0.0,
    }


def compile_labeled_few_shot(trainset: list[dspy.Example], k: int = 4) -> dspy.Module:
    optimizer = dspy.LabeledFewShot(k=min(k, len(trainset)))
    return optimizer.compile(student=build_classifier(), trainset=trainset)


def compile_bootstrap_few_shot(trainset: list[dspy.Example]) -> dspy.Module:
    optimizer = dspy.BootstrapFewShot(metric=label_exact_match, max_bootstrapped_demos=4, max_labeled_demos=4)
    return optimizer.compile(student=build_classifier(), trainset=trainset)


def preview_failures(program: dspy.Module, devset: list[dspy.Example], limit: int = 3) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for example in devset:
        prediction = program(sounding_text=example.sounding_text)
        predicted_label = prediction.label.strip().lower()
        gold_label = example.label.strip().lower()
        if predicted_label != gold_label:
            failures.append(
                {
                    "source": example.source,
                    "gold_label": gold_label,
                    "predicted_label": predicted_label,
                    "sounding_text": example.sounding_text,
                }
            )
        if len(failures) >= limit:
            break
    return failures


def format_metrics(name: str, metrics: dict[str, float]) -> str:
    return (
        f"{name}: accuracy={metrics['accuracy']:.2%}, "
        f"examples={int(metrics['examples'])}, "
        f"total_tokens={int(metrics['total_tokens'])}, "
        f"avg_tokens_per_example={metrics['avg_tokens_per_example']:.1f}"
    )


def summarize_metric_delta(metric_name: str, baseline: dict[str, float], candidate: dict[str, float]) -> float:
    return candidate[metric_name] - baseline[metric_name]


def average_text_length(examples: list[DatasetExample]) -> float:
    return mean(len(example.sounding_text) for example in examples)