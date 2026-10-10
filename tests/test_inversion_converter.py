import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.inversion_converter import build_case_records, write_dataset_json


class InversionConverterTests(unittest.TestCase):
    def test_build_case_records_groups_rows_by_validutc_and_creates_case_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "sample.txt"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["station", "validUTC", "levelcode", "pressure_mb", "height_m", "tmpc", "dwpc", "drct", "speed_kts"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "9", "937.0", "M", "14.8", "-4.2", "210.0", "9"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "4", "850.0", "1511.0", "4.6", "-6.4", "215.0", "19"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "5", "", "1200.0", "M", "M", "235.0", "17"])
                writer.writerow(["CYXY", "2025-06-02 12:00:00", "9", "939.0", "M", "3.8", "-2.2", "195.0", "1"])

            cases = build_case_records(input_path)

            self.assertEqual(len(cases), 3)
            self.assertEqual(cases[0]["case_name"], "CYXY_2025060200")
            self.assertEqual(cases[0]["profile_type"], "stability")
            self.assertEqual(cases[0]["station"], "CYXY")
            self.assertEqual(cases[0]["validUTC"], "2025-06-02 00:00:00")
            self.assertEqual(cases[0]["source"], "CYXY_2025060200_stability")
            self.assertEqual(len(cases[0]["levels"]), 2)
            self.assertNotIn("levelcode", cases[0]["levels"][0])
            self.assertIn("Station CYXY", cases[0]["sounding_text"])
            self.assertIn("pressure 937.0 hPa", cases[0]["sounding_text"])
            self.assertEqual(cases[1]["profile_type"], "wind")
            self.assertEqual(cases[1]["source"], "CYXY_2025060200_wind")
            self.assertIn("height 1200.0 m", cases[1]["sounding_text"])
            self.assertEqual(cases[2]["case_name"], "CYXY_2025060212")

    def test_build_case_records_applies_top_pressure_cutoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "sample.txt"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["station", "validUTC", "levelcode", "pressure_mb", "tmpc", "dwpc", "speed_kts"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "9", "937.0", "14.8", "-4.2", "9"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "4", "850.0", "4.6", "-6.4", "19"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "4", "700.0", "-8.9", "-14.9", "6"])

            cases = build_case_records(input_path, top_pressure_mb=850.0)

            self.assertEqual(len(cases), 1)
            self.assertEqual(cases[0]["profile_type"], "stability")
            self.assertEqual(len(cases[0]["levels"]), 2)
            self.assertIn("pressure 937.0 hPa", cases[0]["sounding_text"])
            self.assertIn("pressure 850.0 hPa", cases[0]["sounding_text"])
            self.assertNotIn("pressure 700.0 hPa", cases[0]["sounding_text"])
            self.assertEqual(cases[0]["top_pressure_mb"], 850.0)

    def test_write_dataset_json_emits_valid_json_with_levels(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "sample.txt"
            output_path = Path(tmpdir) / "dataset.json"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["station", "validUTC", "levelcode", "pressure_mb", "height_m", "tmpc", "dwpc", "drct", "speed_kts"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "9", "937.0", "M", "14.8", "-4.2", "210.0", "9"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "4", "850.0", "1511.0", "4.6", "-6.4", "215.0", "19"])

            write_dataset_json(input_path, output_path)
            dataset = json.loads(output_path.read_text(encoding="utf-8"))

            self.assertEqual(len(dataset), 1)
            self.assertEqual(dataset[0]["case_name"], "CYXY_2025060200")
            self.assertEqual(dataset[0]["source"], "CYXY_2025060200_stability")
            self.assertEqual(dataset[0]["profile_type"], "stability")
            self.assertEqual(dataset[0]["label"], "unknown")
            self.assertEqual(len(dataset[0]["levels"]), 2)

    def test_write_dataset_json_persists_top_pressure_cutoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "sample.txt"
            output_path = Path(tmpdir) / "dataset.json"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["station", "validUTC", "levelcode", "pressure_mb", "height_m", "tmpc", "dwpc", "drct", "speed_kts"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "9", "937.0", "M", "14.8", "-4.2", "210.0", "9"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "4", "700.0", "3051.0", "-8.9", "-14.9", "225.0", "6"])

            write_dataset_json(input_path, output_path, top_pressure_mb=850.0)
            dataset = json.loads(output_path.read_text(encoding="utf-8"))

            self.assertEqual(dataset[0]["top_pressure_mb"], 850.0)
            self.assertEqual(len(dataset[0]["levels"]), 1)

    def test_write_dataset_json_emits_stability_and_wind_profiles_for_same_valid_time(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "sample.txt"
            output_path = Path(tmpdir) / "dataset.json"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["station", "validUTC", "levelcode", "pressure_mb", "height_m", "tmpc", "dwpc", "drct", "speed_kts"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "9", "937.0", "M", "14.8", "-4.2", "210.0", "9"])
                writer.writerow(["CYXY", "2025-06-02 00:00:00", "5", "", "1200.0", "M", "M", "235.0", "17"])

            write_dataset_json(input_path, output_path)
            dataset = json.loads(output_path.read_text(encoding="utf-8"))

            self.assertEqual(len(dataset), 2)
            self.assertEqual(dataset[0]["profile_type"], "stability")
            self.assertEqual(dataset[1]["profile_type"], "wind")


if __name__ == "__main__":
    unittest.main()
