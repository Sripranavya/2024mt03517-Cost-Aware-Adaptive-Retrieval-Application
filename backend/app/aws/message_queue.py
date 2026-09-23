"""Message queues: an in-process queue (local) and Amazon SQS (cloud).

Used for optional async orchestration hand-off. The in-process queue keeps
messages in a deque so local mode and CI need no broker; the SQS queue uses the
default credential chain with the queue URL injected from settings.
"""

from __future__ import annotations

from collections import deque

from app.aws.interfaces import MessageQueue


class InProcessMessageQueue(MessageQueue):
    """Simple FIFO in-memory queue for local mode and tests."""

    def __init__(self) -> None:
        self._queue: deque[dict] = deque()

    def send(self, message: dict) -> None:
        self._queue.append(message)

    def receive(self, max_messages: int = 1) -> list[dict]:
        if max_messages < 1:
            raise ValueError("max_messages must be >= 1")
        out: list[dict] = []
        while self._queue and len(out) < max_messages:
            out.append(self._queue.popleft())
        return out


class SQSMessageQueue(MessageQueue):
    """Amazon SQS message queue (cloud mode)."""

    def __init__(self, queue_url: str, region: str) -> None:
        if not queue_url:
            raise ValueError("SQS queue url is required in cloud mode")
        import boto3  # lazy import

        self.queue_url = queue_url
        self._client = boto3.client("sqs", region_name=region)

    def send(self, message: dict) -> None:
        import json

        self._client.send_message(
            QueueUrl=self.queue_url, MessageBody=json.dumps(message)
        )

    def receive(self, max_messages: int = 1) -> list[dict]:
        import json

        response = self._client.receive_message(
            QueueUrl=self.queue_url, MaxNumberOfMessages=min(max_messages, 10)
        )
        messages = response.get("Messages", [])
        out: list[dict] = []
        for msg in messages:
            out.append(json.loads(msg["Body"]))
            self._client.delete_message(
                QueueUrl=self.queue_url, ReceiptHandle=msg["ReceiptHandle"]
            )
        return out
