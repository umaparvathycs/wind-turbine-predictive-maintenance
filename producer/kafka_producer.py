
"""Publish SCADA messages to a Kafka topic."""

import json
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError

from config.settings import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    PRODUCER_INTERVAL_SECONDS,
    PRODUCER_MESSAGE_LIMIT,
)
from generator.scada_generator import generate_messages


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda key: str(key).encode("utf-8"),
        acks="all",
        retries=5,
    )


def run_producer():
    messages = generate_messages(PRODUCER_MESSAGE_LIMIT)
    producer = create_producer()

    try:
        for index, message in enumerate(messages, start=1):
            future = producer.send(
                KAFKA_TOPIC,
                key=message["asset_id"],
                value=message,
            )

            metadata = future.get(timeout=10)

            print(
                f"Sent {index}/{len(messages)} | "
                f"Topic: {metadata.topic} | "
                f"Partition: {metadata.partition} | "
                f"Offset: {metadata.offset} | "
                f"Asset: {message['asset_id']}"
            )

            time.sleep(PRODUCER_INTERVAL_SECONDS)

    except KafkaError as error:
        print(f"Kafka publishing error: {error}")
        raise

    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    run_producer()
