
"""Central configuration for the Kafka streaming project."""

# Kafka connection
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

# Kafka topic
KAFKA_TOPIC = "wind-turbine-scada"

# Producer settings
PRODUCER_INTERVAL_SECONDS = 2
PRODUCER_MESSAGE_LIMIT = 100

# SCADA settings
SCADA_INTERVAL_MINUTES = 10

# Model details
MODEL_VERSION = "rf-farmC-avg-v1"
MODEL_FEATURE_COUNT = 238

SUPPORTED_TURBINES = [
    2, 5, 12, 14, 15, 16, 21, 32, 35,
    38, 42, 43, 50, 52, 53, 55, 56
]
