import json
import argparse

from account_deletion import Account, AccountDeletionService, InfraiCaptcha


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("user_id")
    parser.add_argument("widget_record_id")
    parser.add_argument("token")
    args = parser.parse_args()
    account = Account(user_id=args.user_id, sessions={"session-a", "session-b"})
    result = AccountDeletionService(InfraiCaptcha()).delete(account, args.widget_record_id, args.token, "198.51.100.10")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
