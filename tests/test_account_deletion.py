import json

from account_deletion import Account, AccountDeletionService, InfraiCaptcha


class PassingCaptcha:
    def __init__(self):
        self.calls = []

    def verify(self, widget_record_id, token, ip, action="account_delete"):
        self.calls.append((widget_record_id, token, ip, action))


def test_delete_revokes_sessions_and_removes_logistics_records():
    account = Account(
        user_id="shipper-42",
        sessions={"s1", "s2"},
        shipments=[]
    )
    verifier = PassingCaptcha()
    result = AccountDeletionService(verifier).delete(account, "widget-1", "captcha-token", "203.0.113.4")
    assert result == {"status": "deleted", "user_id": "shipper-42", "revoked_sessions": 2}
    assert account.deleted is True
    assert account.sessions == set()
    assert verifier.calls == [("widget-1", "captcha-token", "203.0.113.4", "account_delete")]


def test_infrai_captcha_request_contains_required_fields():
    class Response:
        status = 200

        def read(self):
            return b'{"ok": true, "data": {}}'

    requests = []

    def opener(request):
        requests.append(request)
        return Response()

    InfraiCaptcha(api_key="test-key", opener=opener).verify("widget-1", "captcha-token", "203.0.113.4")
    assert len(requests) == 1
    assert json.loads(requests[0].data) == {
        "widget_record_id": "widget-1",
        "token": "captcha-token",
        "ip": "203.0.113.4",
        "action": "account_delete",
    }
