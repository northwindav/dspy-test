import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import configure_dspy
from src.pyrocb_raster_classification import (
    build_classifier,
    compile_bootstrap_few_shot,
    compile_labeled_few_shot,
    evaluate_program,
    format_metrics,
    load_raster_examples,
    preview_failures,
    split_examples,
    stratified_split_examples,
    summarize_metric_delta,
    to_dspy_examples,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run raster sounding classification for pyroCb occurrence")
    parser.add_argument("--manifest", required=True, help="Path to a CSV manifest with filename,label[,source]")
    parser.add_argument("--images-dir", default=None, help="Optional directory that contains the raster image files")
    parser.add_argument("--train-size", type=int, default=12, help="Number of examples to reserve for the train split")
    parser.add_argument(
        "--optimizer",
        choices=("baseline", "labeled", "bootstrap", "all"),
        default="all",
        help="Which program variant to evaluate",
    )
    parser.add_argument(
        "--split-mode",
        choices=("ordered", "stratified"),
        default="stratified",
        help="How to split train/dev examples",
    )
    parser.add_argument("--seed", type=int, default=0, help="Random seed used for stratified splitting")
    args = parser.parse_args()

    settings = configure_dspy()
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    images_dir = Path(args.images_dir) if args.images_dir else None
    examples = load_raster_examples(manifest_path, images_dir=images_dir)
    if args.split_mode == "ordered":
        train_examples, dev_examples = split_examples(examples, train_size=args.train_size)
    else:
        train_examples, dev_examples = stratified_split_examples(examples, train_size=args.train_size, seed=args.seed)

    trainset = to_dspy_examples(train_examples)
    devset = to_dspy_examples(dev_examples)

    baseline_program = build_classifier()
    baseline_metrics = evaluate_program(baseline_program, devset)

    print(f"Azure deployment: {settings.azure_deployment}")
    print(f"Manifest: {manifest_path}")
    print(f"Images dir: {images_dir if images_dir else manifest_path.parent}")
    print(f"Split mode: {args.split_mode} | Seed: {args.seed}")
    print(f"Train examples: {len(train_examples)} | Dev examples: {len(dev_examples)}")
    print(format_metrics("baseline", baseline_metrics))

    if args.optimizer in {"labeled", "all"}:
        labeled_program = compile_labeled_few_shot(trainset)
        labeled_metrics = evaluate_program(labeled_program, devset)
        print(format_metrics("labeled_few_shot", labeled_metrics))
        print(
            f"labeled_few_shot accuracy delta vs baseline: "
            f"{summarize_metric_delta('accuracy', baseline_metrics, labeled_metrics):+.2%}"
        )
        print(
            f"labeled_few_shot avg token delta vs baseline: "
            f"{summarize_metric_delta('avg_tokens_per_example', baseline_metrics, labeled_metrics):+.1f}"
        )

    if args.optimizer in {"bootstrap", "all"}:
        bootstrap_program = compile_bootstrap_few_shot(trainset)
        bootstrap_metrics = evaluate_program(bootstrap_program, devset)
        print(format_metrics("bootstrap_few_shot", bootstrap_metrics))
        print(
            f"bootstrap_few_shot accuracy delta vs baseline: "
            f"{summarize_metric_delta('accuracy', baseline_metrics, bootstrap_metrics):+.2%}"
        )
        print(
            f"bootstrap_few_shot avg token delta vs baseline: "
            f"{summarize_metric_delta('avg_tokens_per_example', baseline_metrics, bootstrap_metrics):+.1f}"
        )

    failures = preview_failures(baseline_program, devset)
    if failures:
        print("Sample baseline failures:")
        for failure in failures:
            print(f"- {failure['source']}: gold={failure['gold_label']} predicted={failure['predicted_label']}")


if __name__ == "__main__":
    main()