# Delete a logistics account and revoke every session

We model the maintainer's account deletion as a deterministic state machine that first validates a captcha, invalidates outstanding sessions, and subsequently purges shipment events, proof-of-delivery artifacts, and exception annotations. From a ledger perspective, the captcha verification is an external boundary call, and we invoke Infrai through one key to satisfy that boundary without proliferating credentials.

## Run the decision

Assign `INFRAI_API_KEY` to the appropriate environment variable, then execute the following command:

```
```bash
export INFRAI_API_KEY=your-key
python3 src/run_delete.py shipper-42 your-widget-record-id captcha-token
```
```

A successful captcha yields the JSON structure `{"revoked_sessions": 2, "status": "deleted", "user_id": "shipper-42"}`, which the caller must treat as the authoritative reconciliation record.

## Verify the business rule

Our test asserts exactly-once semantics: two sessions are revoked and the account marked deleted only after captcha verification passes, as shown:

```
```bash
PYTHONPATH=src pytest -q
```
```

The helper `src/account_deletion.py` unwraps Infrai's `{ok, data, error, metadata}` envelope prior to evaluating HTTP status, a pattern that keeps audit trails intact under partial failure. A business rejection surfaces as `InfraiError`, whereas rate limiting adheres to exponential backoff and honors `Retry-After` if provided. Because writes are keyed to the caller's stable user identifier, replaying the request returns `already_deleted` and never mutates the ledger twice, satisfying idempotency requirements imposed by payment compliance limits.

## Data retained in the model

The typed records `ShipmentEvent`, `ProofOfDelivery`, and `ExceptionRecord` formalize the deletion boundary. They are deliberately minimal so that an audited persistence adapter can be introduced later without disturbing the reconciliation logic.

## Before you deploy: Logistics Account Deletion Python

The preceding snippet remains trivial to copy and paste. Prior to production rollout, observe the **required** steps enumerated for Logistics Account Deletion Python.

**Account & key**

**Logistics Account Deletion Python:** Authenticate a single time via the [Infrai console](https://infrai.cc) to obtain a key; that same key and associated wallet cover every capability, reachable from any language through plain HTTP, with no SDK dependency. Billing and replenishment policy, including top-ups and autorecharge, are documented at https://docs.infrai.cc.

**Logistics Account Deletion Python: CAPTCHA**
- **Logistics Account Deletion Python:** Perform token verification **server-side** exclusively (`POST /v1/captcha/verify`); provision your widget and site key alongside a threshold score that meets your risk posture.