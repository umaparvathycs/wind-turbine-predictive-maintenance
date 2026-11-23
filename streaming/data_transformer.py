
"""Validate and prepare SCADA records for wind turbine prediction."""

import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

METADATA_PATH = (
    PROJECT_ROOT.parent
    / "wind-turbine-predictive-maintenance"
    / "artifacts"
    / "model_metadata_avg.json"
)


def load_feature_names():
    """Load the exact feature list used by Member 1's model."""

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    features = metadata["features"]

    if len(features) != 238:
        raise ValueError(
            f"Expected 238 features, found {len(features)}"
        )

    return features


def prepare_record(record):
    """Validate and prepare one SCADA record for prediction."""

    features = load_feature_names()

    required_fields = ["asset_id", "time_stamp"] + features

    missing_fields = [
        field for field in required_fields
        if field not in record
    ]

    if missing_fields:
        raise ValueError(
            f"Missing required fields: {missing_fields}"
        )

    asset_id = record["asset_id"]

    if (
        isinstance(asset_id, bool)
        or not isinstance(asset_id, int)
        or asset_id <= 0
    ):
        raise ValueError("Invalid asset_id")

    prepared_record = {
        "asset_id": asset_id,
        "time_stamp": record["time_stamp"],
    }

    for feature in features:
        value = record[feature]

        if value is None:
            prepared_record[feature] = None
            continue

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"Invalid value for feature: {feature}"
            )

        if not math.isfinite(value):
            raise ValueError(
                f"Non-finite value for feature: {feature}"
            )

        # Match Member 1's negative wind-speed sentinel handling.
        if (
            feature in {
                "wind_speed_235_avg",
                "wind_speed_236_avg",
                "wind_speed_237_avg",
            }
            and value < 0
        ):
            prepared_record[feature] = None
        else:
            prepared_record[feature] = float(value)

    return prepared_record
