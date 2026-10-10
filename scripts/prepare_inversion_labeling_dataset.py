import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a stability-only inversion labeling dataset")
    parser.add_argument("--input", required=True, help="Path to the converter-generated profile dataset")
    parser.add_argument("--output", required=True, help="Path to write the stability-only labeling dataset")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    profiles = json.loads(input_path.read_text(encoding="utf-8"))

    labeling_records = []
    for profile in profiles:
        if profile.get("profile_type") != "stability":
            continue
        labeling_records.append(
            {
                "case_name": profile["case_name"],
                "source": profile["source"],
                "input_file": profile["input_file"],
                "station": profile["station"],
                "validUTC": profile["validUTC"],
                "profile_type": profile["profile_type"],
                "label": profile.get("label", "unknown"),
                "sounding_text": profile["sounding_text"],
                "levels": profile["levels"],
                "top_pressure_mb": profile.get("top_pressure_mb"),
            }
        )

    if not labeling_records:
        raise ValueError(
            "No stability profiles were found in the input JSON. Re-run conversion and ensure the converter emits profile_type values."
        )

    output_path.write_text(json.dumps(labeling_records, indent=2), encoding="utf-8")
    print(output_path)
    print(f"stability_profiles={len(labeling_records)}")


if __name__ == "__main__":
    main()