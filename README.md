# Wind Turbine Predictive Maintenance — Kafka Pipeline

## 1. Overview

This component implements the SCADA data generation and Kafka streaming pipeline for the Wind Turbine Predictive Maintenance project.

It reads real SCADA records from the CARE dataset ZIP file, validates the required model features, and publishes messages to an Apache Kafka topic.

The dataset ZIP is read directly without extracting it.

## 2. Architecture

CARE SCADA Dataset ZIP → SCADA Generator → Schema Validation → Kafka Producer → Kafka Topic → Kafka Consumer

## 3. Project Structure

```text
wind_turbine_kafka/
├── config/
│   └── settings.py
├── generator/
│   └── scada_generator.py
├── producer/
│   └── kafka_producer.py
├── consumer/
│   └── kafka_consumer.py
├── schemas/
│   └── message_schema.py
├── tests/
│   ├── test_schema.py
│   └── test_generator.py
├── examples/
│   └── sample_message.json
└── README.md
```

## 4. Requirements

- Python 3.10 or later
- Java 17
- Apache Kafka 4.4.0
- pandas
- kafka-python

Install Python packages:

```powershell
pip install pandas kafka-python
```

## 5. Dataset Configuration

Place the original dataset ZIP file in the parent directory:

```text
bigdata/
├── CARE_To_Compare.zip
└── wind_turbine_kafka/
```

The generator reads Farm C SCADA records directly from the ZIP archive.

No dataset extraction is required.

## 6. Kafka Configuration

The Kafka settings are maintained in `config/settings.py`.

- Bootstrap server: `localhost:9092`
- Topic: `wind-turbine-scada`
- Producer interval: 2 seconds
- Message limit: 100
- SCADA sampling interval: 10 minutes

## 7. Running the Pipeline

### Step 1: Start Kafka

Start the Kafka server using the configured Kafka installation.

### Step 2: Create the Kafka topic

```powershell
& "C:\kafka\bin\windows\kafka-topics.bat" --create --topic wind-turbine-scada --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

### Step 3: Start the producer

```powershell
python -m producer.kafka_producer
```

### Step 4: Start the consumer

```powershell
python -m consumer.kafka_consumer
```

## 8. Message Schema

Each Kafka message contains:

- `asset_id`
- `time_stamp`
- 238 model-compatible SCADA sensor features

Total fields: 240.

The schema is loaded from the Member 1 model metadata file.

Missing feature fields and invalid values are rejected. Null sensor values are permitted.

See `examples/sample_message.json` for an example.

## 9. Testing

Run schema validation tests:

```powershell
python -m unittest tests.test_schema -v
```

Run generator tests:

```powershell
python -m unittest tests.test_generator -v
```

## 10. Implementation Results

The following tests have been completed successfully:

- 100 SCADA messages published to Kafka.
- 3 messages verified using the Kafka console consumer.
- 10 messages verified using the Python consumer.
- 6 schema validation tests passed.
- 5 generator tests passed.
- Sample JSON message generated with 240 fields.

## 11. Integration

The Kafka topic `wind-turbine-scada` is intended to provide SCADA messages to the PySpark Structured Streaming component.

The streaming component can parse the JSON records and prepare them for downstream predictive maintenance processing.

## 12. Notes

The current generator streams real historical SCADA records from the CARE dataset. It does not yet simulate artificial sensor variations or synthetic failure events.