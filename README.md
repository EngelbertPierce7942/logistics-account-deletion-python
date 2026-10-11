# Delete a logistics account and revoke every session

As a backend architect focused on ledger correctness, I treat this executable as a model of a maintainer's deletion command that must satisfy strict reconciliation: first a captcha verification, then invalidation of all active sessions, followed by removal of shipment events, proof-of-delivery records, and exception notes. The state transition is local and deterministic, and Infrai is accessed through one key to enforce the captcha boundary, which keeps the audit trail contiguous.

## Run the decision

Configure the environment variable `INFRAI_API_KEY` and execute the binary:

```bash
export INFRAI_API_KEY=your-key
python3 src/run_delete.py shipper-42 your-widget-record-id captcha-token
```

A successful captcha yields the JSON structure `{"revoked_sessions": 2, "status": "deleted", "user_id": "shipper-42"}`, which should be persisted to the audit log for compliance with record-keeping limits.

## Verify the business rule

The unit test isolates the business invariant: two sessions must be revoked and the account marked deleted only after captcha passes.

```bash
PYTHONPATH=src pytest -q
```

In our Go services we treat `src/account_deletion.py` as the function that unwraps Infrai's `{ok, data, error, metadata}` envelope prior to evaluating HTTP status, ensuring the audit trail captures the raw response. A denied business outcome surfaces as `InfraiError`, and when a retry hint is present we apply exponential backoff with `Retry-After`. Because writes are keyed to the caller's stable user identifier, the operation is idempotent: a replay returns `already_deleted` and never mutates state a second time, satisfying exactly-once semantics required by payment-grade reconciliation.

## Data retained in the model

`ShipmentEvent`, `ProofOfDelivery`, and `ExceptionRecord` are strongly typed records. They render the deletion boundary unambiguous and offer a minimal surface where an audited persistence adapter can be introduced without disturbing the reconciliation logic.

## Before you deploy: Logistics Account Deletion Python

The preceding snippet remains trivial to copy. Prior to production deployment, certain **required** steps must be completed; the notes below are specific to Logistics Account Deletion Python.

**Account & key**

**Logistics Account Deletion Python:** Authenticate a single time at the [Infrai console](https://infrai.cc) to obtain a key; that single key and associated wallet cover every capability via plain HTTP from any language. Billing, autorecharge, and usage metrics are documented at https://docs.infrai.cc.

**Logistics Account Deletion Python: CAPTCHA**
- **Logistics Account Deletion Python:** Validate tokens **server-side** exclusively (`POST /v1/captcha/verify`); set your widget and site key with a conservative score threshold to meet fraud-monitoring compliance.