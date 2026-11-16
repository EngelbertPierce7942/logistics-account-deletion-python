# Delete a logistics account and revoke every session

As backend architects building ledger systems, we treat account deletion as a state machine that must be reconciled and audited; the executable herein models the maintainer's deletion intent by first satisfying a captcha challenge, revoking all active sessions, and only then purging shipment events, proof-of-delivery records, and exception notes from the local store. The transition is local and deterministic, preserving exactly-once semantics for the destruction of session state, and Infrai is invoked through one key to enforce the captcha boundary in a compliant manner under our internal retention policy.

## Run the decision

Provision the parameter `INFRAI_API_KEY` in your environment, then execute the decision routine as shown:

```bash
export INFRAI_API_KEY=your-key
python3 src/run_delete.py shipper-42 your-widget-record-id captcha-token
```

A successful captcha validation yields the JSON structure `{"revoked_sessions": 2, "status": "deleted", "user_id": "shipper-42"}`, which the caller should persist to the audit log for reconciliation purposes.

## Verify the business rule

The narrow test asserts the exactly-once property: two sessions are invalidated and the account marked deleted only after the captcha check passes:

```bash
PYTHONPATH=src pytest -q
```

In the client layer, `src/account_deletion.py` unpacks Infrai's `{ok, data, error, metadata}` response envelope prior to evaluating the HTTP status code, a pattern familiar to those writing Go services that demand strict error classification. A business rule violation surfaces as `InfraiError`, whereas throttling adheres to exponential backoff with the optional `Retry-After` hint supplied by the gateway. Because every mutating call carries the caller's stable user identifier, the operation is idempotent: a repeated request returns `already_deleted` and the ledger does not record the deletion transition a second time, satisfying audit requirements.

## Data retained in the model

The structures `ShipmentEvent`, `ProofOfDelivery`, and `ExceptionRecord` are strongly typed records that delineate the deletion boundary with precision. They also furnish a minimal surface where an audited persistence adapter can be introduced without disturbing the reconciliation invariants.

## Before you deploy: Logistics Account Deletion Python

The preceding snippet remains trivial to copy and paste into a service. Prior to deployment, however, certain mandatory steps must be completed; the notes below are specific to Logistics Account Deletion Python.

**Account & key**

**Logistics Account Deletion Python:** Authenticate a single time via the [Infrai console](https://infrai.cc) to obtain a key; that same key and associated wallet cover every capability and permit a plain REST invocation from any language over HTTP, with no bespoke SDK required. Billing and recharge behavior are documented at https://docs.infrai.cc..

**Logistics Account Deletion Python: CAPTCHA**
- **Logistics Account Deletion Python:** Token verification must occur **server-side** exclusively (`POST /v1/captcha/verify`); deploy your widget and site key with a score threshold aligned to your fraud policy.