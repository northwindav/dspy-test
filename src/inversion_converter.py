import csv
import json
import re
from pathlib import Path
from typing import Any


def _parse_timestamp(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", value):
        return value
    raise ValueError(f"Unsupported timestamp format: {value}")


def _case_name_from_row(row: dict[str, str]) -> str:
    station = row["station"].strip().upper()
    timestamp = _parse_timestamp(row["validUTC"])
    match = re.match(r"(\d{4})-(\d{2})-(\d{2}) (\d{2})", timestamp)
    if not match:
        raise ValueError(f"Could not parse case timestamp: {timestamp}")
    year, month, day, hour = match.groups()
    stamp = f"{year}{month}{day}{hour}"
    return f"{station}_{stamp}"


def _pressure_value(pressure: str) -> float | None:
    value = pressure.strip()
    if not value or value == "M":
        return None
    return float(value)


def build_case_records(input_path: str | Path, top_pressure_mb: float | None = None) -> list[dict[str, Any]]:
    path = Path(input_path)
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))

    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        if not row:
            continue
        case_name = _case_name_from_row(row)
        grouped.setdefault(case_name, []).append(row)

    cases: list[dict[str, Any]] = []
    for case_name, case_rows in grouped.items():
        station = case_rows[0]["station"].strip().upper()
        timestamp = case_rows[0]["validUTC"].strip()
        lines = [f"Station {station} valid at {timestamp}"]
        levels: list[dict[str, str]] = []
        for row in case_rows:
            pressure = row.get("pressure_mb", "").strip()
            pressure_value = _pressure_value(pressure)
            if top_pressure_mb is not None and pressure_value is not None and pressure_value < top_pressure_mb:
                continue
            temp = row.get("tmpc", "").strip()
            dew = row.get("dwpc", "").strip()
            wind = row.get("speed_kts", "").strip()
            level = {
                "levelcode": row.get("levelcode", "").strip(),
                "pressure_mb": pressure,
                "height_m": row.get("height_m", "").strip(),
                "tmpc": temp,
                "dwpc": dew,
                "drct": row.get("drct", "").strip(),
                "speed_kts": wind,
            }
            levels.append(level)
            if pressure and pressure != "M":
                lines.append(
                    f"pressure {pressure} hPa, temp {temp} C, dewpoint {dew} C, wind {wind} kt"
                )
        cases.append(
            {
                "case_name": case_name,
                "station": station,
                "validUTC": timestamp,
                "sounding_text": "\n".join(lines),
                "source": case_name,
                "input_file": path.name,
                "levels": levels,
                "top_pressure_mb": top_pressure_mb,
            }
        )

    return sorted(cases, key=lambda item: item["validUTC"])


def write_dataset_json(
    input_path: str | Path,
    output_path: str | Path,
    top_pressure_mb: float | None = None,
) -> Path:
    cases = build_case_records(input_path, top_pressure_mb=top_pressure_mb)
    output = Path(output_path)
    dataset = [
        {
            "case_name": case["case_name"],
            "source": case["source"],
            "input_file": case["input_file"],
            "station": case["station"],
            "validUTC": case["validUTC"],
            "label": "unknown",
            "sounding_text": case["sounding_text"],
            "levels": case["levels"],
            "top_pressure_mb": case["top_pressure_mb"],
        }
        for case in cases
    ]
    output.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    return output
