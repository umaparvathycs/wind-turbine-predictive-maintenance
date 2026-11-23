
"""Unit tests for the SCADA data generator."""

import unittest

from generator.scada_generator import (
    generate_messages,
    load_source_data,
)
from schemas.message_schema import load_feature_names, validate_message


class TestSCADAGenerator(unittest.TestCase):

    def test_source_data_loads_from_zip(self):
        data = load_source_data(number_of_rows=3)

        self.assertEqual(len(data), 3)
        self.assertIn("asset_id", data.columns)
        self.assertIn("time_stamp", data.columns)

    def test_generate_requested_number_of_messages(self):
        messages = generate_messages(number_of_messages=3)

        self.assertEqual(len(messages), 3)

    def test_each_message_contains_all_features(self):
        messages = generate_messages(number_of_messages=2)
        features = load_feature_names()

        for message in messages:
            for feature in features:
                self.assertIn(feature, message)

    def test_messages_pass_schema_validation(self):
        messages = generate_messages(number_of_messages=3)

        for message in messages:
            self.assertTrue(validate_message(message))

    def test_message_identifiers_are_present(self):
        messages = generate_messages(number_of_messages=2)

        for message in messages:
            self.assertIsInstance(message["asset_id"], int)
            self.assertIsInstance(message["time_stamp"], str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
