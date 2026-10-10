import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.inversion_converter import write_dataset_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a multi-sounding text file into a JSON dataset")
    parser.add_argument("--input", required=True, help="Path to the input sounding text file")
    parser.add_argument("--output", required=True, help="Path to the output JSON file")
    parser.add_argument(
        "--top-pressure-mb",
        type=float,
        default=None,
        help="Optional pressure cutoff. Rows with real pressure below this value are excluded.",
    )
    parser.add_argument(
        "--valid-utc",
        default=None,
        help="Optional exact validUTC timestamp to keep only one sounding after conversion, for example 2025-06-02 00:00:00",
    )
    args = parser.parse_args()

    output_path = write_dataset_json(
        input_path=Path(args.input),
        output_path=Path(args.output),
        top_pressure_mb=args.top_pressure_mb,
    )

    if args.valid_utc is not None:
        dataset = json.loads(output_path.read_text(encoding="utf-8"))
        filtered = [record for record in dataset if record.get("validUTC") == args.valid_utc]
        output_path.write_text(json.dumps(filtered, indent=2), encoding="utf-8")

    print(output_path)


if __name__ == "__main__":
    main()