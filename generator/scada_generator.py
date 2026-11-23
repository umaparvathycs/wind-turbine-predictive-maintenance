
"""Generate model-compatible SCADA messages from real Farm C data in a ZIP."""

import json
import zipfile
from pathlib import Path

import pandas as pd

from schemas.message_schema import load_feature_names, validate_message

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = PROJECT_ROOT.parent / "CARE_To_Compare.zip"

SOURCE_CSV = "CARE_To_Compare/Wind Farm C/datasets/12.csv"
METADATA_PATH = (
    PROJECT_ROOT.parent
    / "wind-turbine-predictive-maintenance"
    / "artifacts"
    / "model_metadata_avg.json"
)


def load_source_data(number_of_rows=100):
    """Read a small sample directly from the ZIP without extracting it."""
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Dataset ZIP not found: {ZIP_PATH}")

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        with archive.open(SOURCE_CSV) as csv_file:
            return pd.read_csv(csv_file, sep=";", nrows=number_of_rows)


def generate_messages(number_of_messages=20):
    """Return model-compatible messages based on actual SCADA records."""
    features = load_feature_names()
    source = load_source_data(number_of_messages)

    messages = []

    for _, row in source.iterrows():
        message = {
            "asset_id": int(row["asset_id"]),
            "time_stamp": str(row["time_stamp"]),
        }

        for feature in features:
            value = row[feature]
            message[feature] = None if pd.isna(value) else float(value)

        validate_message(message)
        messages.append(message)

    return messages


if __name__ == "__main__":
    records = generate_messages(5)

    print(f"Generated messages: {len(records)}")
    print(f"Features per message: {len(load_feature_names())}")
    print("\nFirst message preview:")

    preview = {
        key: records[0][key]
        for key in list(records[0])[:10]
    }
    print(json.dumps(preview, indent=2))
