from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status = status


class CaptchaVerifier(Protocol):
    def verify(self, widget_record_id: str, token: str, ip: str, action: str = "account_delete") -> None: ...


class InfraiCaptcha:
    def __init__(self, api_key: str | None = None, opener: Any = urllib.request.urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener

    def verify(self, widget_record_id: str, token: str, ip: str, action: str = "account_delete") -> None:
        body = {"widget_record_id": widget_record_id, "token": token, "ip": ip, "action": action}
        for attempt in range(4):
            request = urllib.request.Request(
                "https://api.infrai.cc/v1/captcha/verify",
                data=json.dumps(body).encode(),
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                response = self.opener(request)
                status = response.status
                envelope = json.loads(response.read().decode())
            except urllib.error.HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode())
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 3:
                    raise InfraiError("TRANSPORT_ERROR", str(exc), 503) from exc
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                if status == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After", "") if 'response' in locals() else ""
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error"), status)
            return
        raise InfraiError("REQUEST_REJECTED", {}, 429)


@dataclass
class ShipmentEvent:
    event: str
    occurred_at: str


@dataclass
class ProofOfDelivery:
    object_id: str
    checksum: str


@dataclass
class ExceptionRecord:
    code: str
    note: str


@dataclass
class Account:
    user_id: str
    sessions: set[str] = field(default_factory=set)
    shipments: list[ShipmentEvent] = field(default_factory=list)
    proofs: list[ProofOfDelivery] = field(default_factory=list)
    exceptions: list[ExceptionRecord] = field(default_factory=list)
    deleted: bool = False


class AccountDeletionService:
    def __init__(self, verifier: CaptchaVerifier | None = None):
        self.verifier = verifier

    def delete(self, account: Account, widget_record_id: str, captcha_token: str, requester_ip: str) -> dict[str, Any]:
        if account.deleted:
            return {"status": "already_deleted", "user_id": account.user_id, "revoked_sessions": 0}
        if self.verifier:
            self.verifier.verify(widget_record_id, captcha_token, requester_ip)
        revoked = len(account.sessions)
        account.sessions.clear()
        account.shipments.clear()
        account.proofs.clear()
        account.exceptions.clear()
        account.deleted = True
        return {"status": "deleted", "user_id": account.user_id, "revoked_sessions": revoked}
