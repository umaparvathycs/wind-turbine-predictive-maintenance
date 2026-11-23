
"""Unit tests for SCADA message schema validation."""

import unittest

from schemas.message_schema import load_feature_names, validate_message


def create_valid_message():
    """Create a valid message using the model's 238 features."""
    features = load_feature_names()

    message = {
        "asset_id": 2,
        "time_stamp": "2022-06-27 00:00:00",
    }

    for feature in features:
        message[feature] = 1.0

    return message


class TestMessageSchema(unittest.TestCase):

    def test_valid_message(self):
        message = create_valid_message()
        self.assertTrue(validate_message(message))

    def test_missing_feature(self):
        message = create_valid_message()
        message.pop(load_feature_names()[0])

        with self.assertRaises(ValueError):
            validate_message(message)

    def test_invalid_asset_id(self):
        message = create_valid_message()
        message["asset_id"] = -1

        with self.assertRaises(ValueError):
            validate_message(message)

    def test_invalid_timestamp(self):
        message = create_valid_message()
        message["time_stamp"] = "invalid-date"

        with self.assertRaises(ValueError):
            validate_message(message)

    def test_invalid_sensor_value(self):
        message = create_valid_message()
        message[load_feature_names()[0]] = "not-a-number"

        with self.assertRaises(ValueError):
            validate_message(message)

    def test_nan_sensor_value(self):
        message = create_valid_message()
        message[load_feature_names()[0]] = None

        self.assertTrue(validate_message(message))


if __name__ == "__main__":
    unittest.main(verbosity=2)
