"""Connect the streaming project to its local Random Forest model."""

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

    result["consecutive_anomalies"] = alarm["consecutive_anomalies"]
    result["alarm"] = alarm["alarm"]

    return result


if __name__ == "__main__":
    print("Prediction client module loaded successfully.")
    print("Prediction function:", predict_turbine_status.__name__)
    print("Alarm tracker:", type(alarm_tracker).__name__)