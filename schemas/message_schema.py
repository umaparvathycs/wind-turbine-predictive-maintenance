
"""Schema definition and validation for wind turbine SCADA messages."""

from datetime import datetime
from pathlib import Path
import json
import math


PROJECT_ROOT = Path(__file__).resolve().parents[1]

METADATA_PATH = (
    PROJECT_ROOT.parent
    / "wind-turbine-predictive-maintenance"
    / "artifacts"
    / "model_metadata_avg.json"
)

IDENTIFIER_FIELDS = ["asset_id", "time_stamp"]


def load_feature_names():
    """Load the exact feature names and order from Member 1's metadata."""

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Member 1 metadata not found: {METADATA_PATH}"
        )

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    features = metadata["features"]

    if len(features) != 238:
        raise ValueError(
            f"Expected 238 features, found {len(features)}"
        )

    return features


def validate_message(message):
    """Validate one incoming SCADA message."""

    features = load_feature_names()
    required_fields = IDENTIFIER_FIELDS + features

    missing = [
        field for field in required_fields
        if field not in message
    ]

    if missing:
        raise ValueError(
            f"Missing required fields: {missing[:10]}"
        )

    asset_id = message["asset_id"]

    if isinstance(asset_id, bool) or not isinstance(asset_id, int) or asset_id <= 0:
        raise ValueError("asset_id must be a positive integer")

    try:
        datetime.strptime(
            message["time_stamp"],
            "%Y-%m-%d %H:%M:%S"
        )
    except (ValueError, TypeError):
        raise ValueError(
            "Invalid time_stamp. Expected YYYY-MM-DD HH:MM:SS"
        )

    for feature in features:
        value = message[feature]

        if value is None:
            continue

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"{feature} must be numeric or null"
            )

        if not math.isfinite(value):
            raise ValueError(
                f"{feature} cannot contain infinite or NaN values; use null"
            )

    return True
