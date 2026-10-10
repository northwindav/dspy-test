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


def _has_value(value: str) -> bool:
    stripped = value.strip()
    return bool(stripped) and stripped != "M"


def _profile_source(case_name: str, profile_type: str) -> str:
    return f"{case_name}_{profile_type}"


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
        stability_lines = [f"Station {station} valid at {timestamp}"]
        stability_levels: list[dict[str, str]] = []
        wind_lines = [f"Station {station} valid at {timestamp}"]
        wind_levels: list[dict[str, str]] = []

        for row in case_rows:
            pressure = row.get("pressure_mb", "").strip()
            pressure_value = _pressure_value(pressure)
            height_m = row.get("height_m", "").strip()
            if not _has_value(pressure) and not _has_value(height_m):
                continue

            temp = row.get("tmpc", "").strip()
            dew = row.get("dwpc", "").strip()
            wind = row.get("speed_kts", "").strip()
            level = {
                "pressure_mb": pressure,
                "height_m": height_m,
                "tmpc": temp,
                "dwpc": dew,
                "drct": row.get("drct", "").strip(),
                "speed_kts": wind,
            }

            if _has_value(pressure):
                if top_pressure_mb is not None and pressure_value is not None and pressure_value < top_pressure_mb:
                    continue
                stability_levels.append(level)
                stability_lines.append(
                    f"pressure {pressure} hPa, temp {temp} C, dewpoint {dew} C, wind {wind} kt"
                )
                continue

            wind_levels.append(level)
            wind_lines.append(f"height {height_m} m, wind {level['drct']} deg at {wind} kt")

        if stability_levels:
            cases.append(
                {
                    "case_name": case_name,
                    "station": station,
                    "validUTC": timestamp,
                    "profile_type": "stability",
                    "sounding_text": "\n".join(stability_lines),
                    "source": _profile_source(case_name, "stability"),
                    "input_file": path.name,
                    "levels": stability_levels,
                    "top_pressure_mb": top_pressure_mb,
                }
            )

        if wind_levels:
            cases.append(
                {
                    "case_name": case_name,
                    "station": station,
                    "validUTC": timestamp,
                    "profile_type": "wind",
                    "sounding_text": "\n".join(wind_lines),
                    "source": _profile_source(case_name, "wind"),
                    "input_file": path.name,
                    "levels": wind_levels,
                    "top_pressure_mb": top_pressure_mb,
                }
            )

    return sorted(cases, key=lambda item: (item["validUTC"], item["profile_type"]))


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
            "profile_type": case["profile_type"],
            "label": "unknown",
            "sounding_text": case["sounding_text"],
            "levels": case["levels"],
            "top_pressure_mb": case["top_pressure_mb"],
        }
        for case in cases
    ]
    output.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    return output
