# Data module

Provisions the stateful data services, all **encrypted at rest**:

- **S3 bucket** for corpus artifacts and the persisted FAISS index. Public access
  fully blocked, versioning enabled, SSE-KMS (or SSE-S3/AES256 if no KMS key).
- **DynamoDB table** (`PAY_PER_REQUEST`) for per-request POMDP episode traces,
  with server-side encryption and point-in-time recovery.
- **Optional OpenSearch domain** (`enable_opensearch = true`, full env only) for
  managed vector search — encryption at rest, node-to-node encryption, and
  enforced HTTPS with TLS 1.2.

## Cost notes

- **S3**: pay per GB stored + requests. A small demo corpus is a few cents/month.
- **DynamoDB on-demand**: pay per request; effectively ~US$0 at demo volume.
- **OpenSearch** `t3.small.search` single node + 10 GB EBS:
  ~US$0.036/hour (~US$26/month) — the biggest line item, hence disabled in the
  `lab-budget` environment (FAISS-in-container is used instead).

Estimated cost: **~US$0–1/month** without OpenSearch, **~US$26+/month** with it.
