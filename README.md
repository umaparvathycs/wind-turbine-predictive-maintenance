# Real-Time Predictive Maintenance of Wind Turbines Using Big Data Streaming Architecture

## 1. Project Overview

This project implements a real-time predictive maintenance pipeline for wind turbines using Big Data technologies and Machine Learning.

It processes real SCADA sensor records from the CARE dataset, publishes them through Apache Kafka, processes streaming data using PySpark Structured Streaming, and predicts abnormal turbine conditions using a trained Random Forest model.

The system also maintains consecutive-anomaly alarm information and provides a Streamlit dashboard for monitoring predictions.

## 2. System Architecture

CARE SCADA Dataset ZIP  
↓  
SCADA Data Generator  
↓  
Schema Validation (238 Sensor Features)  
↓  
Apache Kafka Producer  
↓  
Kafka Topic: `wind-turbine-scada`  
↓  
PySpark Structured Streaming  
↓  
Data Transformation and Validation  
↓  
Random Forest Prediction Model  
↓  
Anomaly Detection and Alarm Tracking  
↓  
Streamlit Monitoring Dashboard

## 3. Project Structure

```text
wind_turbine_kafka/
├── artifacts/
│   ├── model_avg.joblib
│   └── model_metadata_avg.json
├── config/
│   └── settings.py
├── consumer/
│   └── kafka_consumer.py
├── dashboard/
│   └── app.py
├── examples/
│   └── sample_message.json
├── generator/
│   └── scada_generator.py
├── producer/
│   └── kafka_producer.py
├── schemas/
│   └── message_schema.py
├── streaming/
│   ├── data_transformer.py
│   ├── prediction_client.py
│   └── spark_kafka_consumer.py
├── tests/
│   ├── test_generator.py
│   └── test_schema.py
├── wtpm/
│   ├── __init__.py
│   ├── config.py
│   ├── features.py
│   └── predict.py
├── requirements.txt
└── README.md
```

## 4. Technologies Used

- Python
- Apache Kafka 4.4.0
- PySpark Structured Streaming
- Apache Spark Kafka Connector
- Random Forest Classifier
- Scikit-learn
- Pandas and NumPy
- Streamlit
- Joblib
- Java 17

## 5. Requirements and Installation

Required software:

- Python 3.10 or later
- Java 17
- Apache Kafka 4.4.0
- Apache Spark / PySpark
- CARE dataset ZIP file

Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Activate your Python virtual environment before running the project.

## 6. Dataset Configuration

The project uses the CARE To Compare wind turbine SCADA dataset.

Place the original dataset ZIP in the parent `bigdata` directory:

```text
bigdata/
├── CARE_To_Compare.zip
└── wind_turbine_kafka/
```

The generator reads Farm C SCADA records directly from the ZIP archive using Python's ZIP handling and Pandas.

Dataset extraction is not required.

The original dataset is kept outside the project repository and is not included in GitHub.

## 7. Model Information

The project uses a trained Random Forest model for predictive maintenance.

Model artifact:

- Model file: `artifacts/model_avg.joblib`
- Metadata file: `artifacts/model_metadata_avg.json`
- Model version: `rf-farmC-avg-v1`
- Farm: C
- Feature set: Average (`avg`)
- Input features: 238
- Sampling interval: 10 minutes
- Anomaly threshold: 0.1775374057991335

The model predicts whether an incoming SCADA record represents normal or anomalous turbine behaviour.

Negative wind-speed sentinel values for the specified sensors are treated as missing values.

## 8. Kafka Configuration

Kafka settings are maintained in `config/settings.py`.

- Bootstrap server: `localhost:9092` for the Windows producer
- Topic: `wind-turbine-scada`
- Producer interval: 2 seconds
- Message limit: 100
- SCADA sampling interval: 10 minutes

The Spark consumer uses the Windows host gateway address to connect from Ubuntu/WSL.

## 9. Running the Project

### Step 1: Start Kafka

Start the Kafka server using the configured Kafka installation.

### Step 2: Create the Kafka topic

```powershell
& "C:\kafka\bin\windows\kafka-topics.bat" --create --topic wind-turbine-scada --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

If the topic already exists, it does not need to be recreated.

### Step 3: Start the SCADA producer

From the project root:

```bash
python -m producer.kafka_producer
```

The producer reads actual SCADA records, validates them, and publishes JSON messages to Kafka.

### Step 4: Start the Spark streaming consumer

In another Ubuntu/WSL terminal:

```bash
python -m streaming.spark_kafka_consumer
```

The Spark application reads Kafka messages, parses the SCADA features, applies the prediction model, and records the results.

### Step 5: Start the dashboard

In another terminal:

```bash
streamlit run dashboard/app.py
```

Open the displayed local URL, normally:

`http://localhost:8501`

The dashboard displays prediction statistics, anomaly probabilities, active alarms, and recent prediction records.

## 10. Prediction and Alarm Logic

Each incoming SCADA record is validated and passed to the Random Forest prediction model.

The prediction output includes:

- Turbine asset ID
- Timestamp
- Predicted status
- Anomaly probability
- Model threshold
- Model version
- Consecutive anomaly count
- Alarm status

The alarm tracker raises an alarm after six consecutive anomalous records spaced at 10-minute intervals, representing one continuous hour.

## 11. Testing

Run the complete test suite:

```bash
python -m pytest -v
```

The tests cover:

- SCADA data generation
- Reading records from the dataset ZIP
- Required sensor feature validation
- Message identifiers
- Timestamp validation
- Invalid sensor values
- Missing features
- Null sensor values

## 12. Implementation and Test Results

The following results have been verified during development:

- 100 SCADA messages previously published to Kafka.
- Kafka consumer successfully verified incoming messages.
- 238 model-compatible sensor features validated.
- 11 automated tests passed.
- Python syntax checks passed.
- Local Random Forest model loaded successfully.
- Actual SCADA record successfully processed by the local model.
- Prediction output successfully generated with anomaly probability and alarm information.
- Streamlit dashboard successfully displayed prediction statistics and charts.

Example prediction:

| Field | Result |
|---|---|
| Asset ID | 2 |
| Timestamp | 2022-06-27 00:00:00 |
| Prediction | Normal |
| Anomaly probability | 0.044679 |
| Threshold | 0.177537 |
| Alarm | False |

## 13. Important Notes

- The CARE dataset ZIP is not included in the repository.
- The trained model and metadata are included in the `artifacts` directory.
- The model prediction package is included locally in the `wtpm` directory.
- The project does not require Member 1's separate local repository to import the prediction model.
- The current generator streams real historical SCADA records and does not generate artificial failure events.
- The dashboard reads prediction results saved by the Spark streaming application.