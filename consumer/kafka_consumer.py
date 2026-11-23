
"""Consume wind turbine SCADA messages from Kafka."""

import json

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from config.settings import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC


def create_consumer():
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="wind-turbine-scada-consumer",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )


def run_consumer(message_limit=None):
    consumer = create_consumer()
    count = 0

    print(f"Listening to topic: {KAFKA_TOPIC}")

    try:
        for record in consumer:
            message = record.value

            print(
                f"Received message {count + 1} | "
                f"Asset: {message.get('asset_id')} | "
                f"Timestamp: {message.get('time_stamp')} | "
                f"Partition: {record.partition} | "
                f"Offset: {record.offset}"
            )

            count += 1

            if message_limit is not None and count >= message_limit:
                break

    except KafkaError as error:
        print(f"Kafka consumer error: {error}")
        raise

    finally:
        consumer.close()
        print(f"Consumer stopped. Total messages received: {count}")


if __name__ == "__main__":
    run_consumer(message_limit=10)
