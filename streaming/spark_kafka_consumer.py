
"""Read and transform wind turbine SCADA messages using PySpark Structured Streaming."""

import json
import csv
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    from_json,
    to_timestamp,
    current_timestamp,
    when,
)
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from config.settings import KAFKA_TOPIC
from streaming.data_transformer import load_feature_names
from streaming.prediction_client import process_prediction
# Project folders
PROJECT_ROOT = Path(__file__).resolve().parents[1]

METADATA_PATH = (
    PROJECT_ROOT.parent
    / "wind-turbine-predictive-maintenance"
    / "artifacts"
    / "model_metadata_avg.json"
)

# Kafka connection from Ubuntu (WSL) to Windows
KAFKA_BOOTSTRAP_SERVERS = "172.22.32.1:9092"

# Spark checkpoint in Ubuntu's Linux filesystem
CHECKPOINT_PATH = (
    "/home/uma_parvathy/spark_checkpoints/wind_turbine"
)
PREDICTIONS_FILE = PROJECT_ROOT / "dashboard" / "predictions.csv"

def load_message_schema():
    """Build a Spark schema using Member 1's model feature list."""

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    features = metadata["features"]

    if len(features) != 238:
        raise ValueError(
            f"Expected 238 model features, found {len(features)}"
        )

    fields = [
        StructField("asset_id", IntegerType(), False),
        StructField("time_stamp", StringType(), False),
    ]

    fields.extend(
        StructField(feature, DoubleType(), True)
        for feature in features
    )

    return StructType(fields)


def create_spark_session():
    """Create a Spark session with the Kafka connector."""

    return (
        SparkSession.builder
        .appName("WindTurbinePredictiveMaintenance")
        .master("local[2]")
        .config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.13:4.3.0",
        )
        .getOrCreate()
    )

def predict_batch(batch_df, batch_id):
    """Predict SCADA records and save results for the dashboard."""

    records = batch_df.collect()

    print(f"\nProcessing batch: {batch_id}")
    print(f"Records received: {len(records)}")

    prediction_results = []

    for row in records:
        record = row.asDict()

        model_record = {
            "asset_id": record["asset_id"],
            "time_stamp": record["time_stamp"],
        }

        for feature in load_feature_names():
            model_record[feature] = record[feature]

        try:
            result = process_prediction(model_record)
            prediction_results.append(result)

            print(
                f"Asset: {result['asset_id']} | "
                f"Time: {result['time_stamp']} | "
                f"Prediction: {result['prediction']} | "
                f"Probability: {result['anomaly_probability']} | "
                f"Alarm: {result['alarm']}"
            )

        except Exception as error:
            print(
                f"Prediction failed for asset "
                f"{record['asset_id']}: {error}"
            )

    if prediction_results:
        PREDICTIONS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fieldnames = [
            "asset_id",
            "time_stamp",
            "prediction",
            "anomaly_probability",
            "alarm",
            "consecutive_anomalies",
        ]

        file_exists = PREDICTIONS_FILE.exists()

        with open(
            PREDICTIONS_FILE,
            "a",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )

            if not file_exists or PREDICTIONS_FILE.stat().st_size == 0:
                writer.writeheader()

            writer.writerows(prediction_results)

        print(f"Saved {len(prediction_results)} predictions to dashboard CSV.")

def run_stream():
    """Read, parse, and transform SCADA messages from Kafka."""

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    message_schema = load_message_schema()

    # Read messages from Kafka
    kafka_stream = (
        spark.readStream
        .format("kafka")
        .option(
            "kafka.bootstrap.servers",
            KAFKA_BOOTSTRAP_SERVERS,
        )
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )

    # Parse JSON messages and apply transformations
    parsed_stream = (
        kafka_stream
        .select(
            from_json(
                col("value").cast("string"),
                message_schema,
            ).alias("scada")
        )
        .select("scada.*")
        .withColumn(
            "event_timestamp",
            to_timestamp(
                col("time_stamp"),
                "yyyy-MM-dd HH:mm:ss",
            ),
        )
        .withColumn(
            "processing_timestamp",
            current_timestamp(),
        )
        .withColumn(
            "available_sensor_count",
            sum(
                when(col(feature).isNotNull(), 1).otherwise(0)
                for feature in load_feature_names()
            ),
        )
    )

    # Display processed records
    query = (
    parsed_stream.writeStream
    .foreachBatch(predict_batch)
    .outputMode("append")
    .option(
        "checkpointLocation",
        CHECKPOINT_PATH,
    )
    .trigger(availableNow=True)
    .start()
)
    query.awaitTermination()
    spark.stop()


if __name__ == "__main__":
    run_stream()
