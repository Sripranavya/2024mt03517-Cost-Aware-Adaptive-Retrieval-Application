# Messaging module

Provisions async orchestration primitives (full environment only):

- An **SQS queue** with server-side encryption and a **dead-letter queue**
  (redrive after `max_receive_count` failures).
- An **SNS topic** (KMS-encrypted) for fan-out notifications.

The `lab-budget` environment omits this module and uses direct in-process calls.

## Cost notes

SQS and SNS are pay-per-request with a generous free tier — effectively **US$0**
at demo volume.
