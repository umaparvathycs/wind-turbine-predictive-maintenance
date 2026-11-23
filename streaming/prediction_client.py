
"""Connect the streaming project to Member 1's Random Forest model."""

import sys
from pathlib import Path

# Locate Member 1's repository
PROJECT_ROOT = Path(__file__).resolve().parents[1]

MEMBER1_REPO = (
    PROJECT_ROOT.parent
    / "wind-turbine-predictive-maintenance"
)

# Make Member 1's repository importable
if str(MEMBER1_REPO) not in sys.path:
    sys.path.insert(0, str(MEMBER1_REPO))

from wtpm.predict import predict_turbine_status, AlarmTracker

def predict_record(record):
    """Predict whether one wind turbine SCADA record is anomalous."""

    results = predict_turbine_status(
        record,
        feature_set="avg",
    )

    return results[0]

# Maintain alarm state for each turbine
alarm_tracker = AlarmTracker()

def process_prediction(record):
    """Generate a prediction and update the turbine alarm tracker."""

    result = predict_record(record)

    alarm = alarm_tracker.update(
        asset_id=result["asset_id"],
        time_stamp=result["time_stamp"],
        label=result["label"],
    )

    result["consecutive_anomalies"] = alarm[
        "consecutive_anomalies"
    ]

    result["alarm"] = alarm["alarm"]

    return result

if __name__ == "__main__":
    print("Prediction client module loaded successfully.")
    print("Member 1 prediction function:", predict_turbine_status.__name__)
    print("Alarm tracker:", type(alarm_tracker).__name__)