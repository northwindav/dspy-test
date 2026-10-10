import csv
import random
from dataclasses import dataclass
from pathlib import Path

import dspy


PYROCB_LABELS = ("pyrocb", "no_pyrocb")


class ClassifyPyroCbLikelihood(dspy.Signature):
    """Classify whether an upper-air sounding raster is supportive of nearby pyrocumulonimbus development.

    Use only the sounding image. Do not explain your reasoning. Return exactly one label and nothing else:
    `pyrocb` or `no_pyrocb`.
    """

    sounding_raster: dspy.Image = dspy.InputField(desc="Raster image of an upper-air sounding")
    label: str = dspy.OutputField(desc="Return exactly one label: pyrocb or no_pyrocb. No explanation.")


@dataclass(frozen=True)
class RasterExample:
    image_path: Path
    label: str
    source: str


def _read_manifest_text(manifest_path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return manifest_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Could not decode manifest file: {manifest_path}")


def _normalize_label(label: str) -> str:
    normalized = label.strip().lower()
    if normalized == "y":
        normalized = "pyrocb"
    elif normalized == "n":
        normalized = "no_pyrocb"
    if normalized not in PYROCB_LABELS:
        raise ValueError(f"Invalid label '{label}'. Expected one of: {', '.join(PYROCB_LABELS)}")
    return normalized


def load_raster_examples(manifest_path: Path, images_dir: Path | None = None) -> list[RasterExample]:
    rows = list(csv.DictReader(_read_manifest_text(manifest_path).splitlines()))
    examples: list[RasterExample] = []

    for index, row in enumerate(rows, start=1):
        case_name = (row.get("case-name") or row.get("case_name") or "").strip()
        filename = (row.get("filename") or row.get("image") or "").strip()
        if not filename and case_name:
            filename = f"{case_name}.png"
        if not filename:
            raise ValueError(f"Missing filename/image field for manifest row {index}")

        raw_label = (row.get("label") or row.get("pyrocb-classification") or "").strip()
        if not raw_label:
            continue

        base_dir = images_dir if images_dir is not None else manifest_path.parent
        image_path = (base_dir / filename).resolve()
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found for manifest row {index}: {image_path}")

        label = _normalize_label(raw_label)
        source = (case_name or Path(filename).stem).strip()
        examples.append(RasterExample(image_path=image_path, label=label, source=source))

    return examples


def to_dspy_examples(examples: list[RasterExample]) -> list[dspy.Example]:
    return [
        dspy.Example(
            sounding_raster=dspy.Image.from_file(str(example.image_path)),
            label=example.label,
            source=example.source,
        ).with_inputs("sounding_raster")
        for example in examples
    ]


def split_examples(examples: list[RasterExample], train_size: int) -> tuple[list[RasterExample], list[RasterExample]]:
    if train_size <= 0 or train_size >= len(examples):
        raise ValueError("train_size must be greater than 0 and smaller than the dataset size")
    return examples[:train_size], examples[train_size:]


def stratified_split_examples(
    examples: list[RasterExample],
    train_size: int,
    seed: int = 0,
) -> tuple[list[RasterExample], list[RasterExample]]:
    if train_size <= 0 or train_size >= len(examples):
        raise ValueError("train_size must be greater than 0 and smaller than the dataset size")

    grouped: dict[str, list[RasterExample]] = {}
    for example in examples:
        grouped.setdefault(example.label, []).append(example)

    if train_size < len(grouped):
        raise ValueError(
            f"train_size={train_size} is too small for stratified splitting across {len(grouped)} labels"
        )

    rng = random.Random(seed)
    train_examples: list[RasterExample] = []
    remaining_examples: list[RasterExample] = []

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
    predicted_label = getattr(prediction, "label", None)
    if not isinstance(predicted_label, str):
        return False
    return example.label.strip().lower() == predicted_label.strip().lower()


def build_classifier() -> dspy.Module:
    return dspy.Predict(ClassifyPyroCbLikelihood)


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
        prediction = program(sounding_raster=example.sounding_raster)
        raw_predicted_label = getattr(prediction, "label", None)
        predicted_label = raw_predicted_label.strip().lower() if isinstance(raw_predicted_label, str) else "<missing>"
        gold_label = example.label.strip().lower()
        if predicted_label != gold_label:
            failures.append(
                {
                    "source": example.source,
                    "gold_label": gold_label,
                    "predicted_label": predicted_label,
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