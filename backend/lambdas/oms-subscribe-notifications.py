import os
import re

import boto3

from common import error, ok, parse_json_body

TOPIC_ARN = os.environ.get("TOPIC_ARN") or os.environ.get("OMS_TOPIC_ARN")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
sns = boto3.client("sns")


def lambda_handler(event, context):
    if not TOPIC_ARN:
        return error(500, "TOPIC_ARN is not configured")

    try:
        body = parse_json_body(event)
    except (TypeError, ValueError):
        return error(400, "Body must be JSON")

    email = body.get("email")
    if not isinstance(email, str) or not EMAIL_RE.match(email.strip()):
        return error(400, "email must be a valid address")

    email = email.strip()
    result = sns.subscribe(
        TopicArn=TOPIC_ARN,
        Protocol="email",
        Endpoint=email,
        ReturnSubscriptionArn=True,
    )
    arn = result.get("SubscriptionArn", "")
    pending = arn == "pending confirmation" or "PendingConfirmation" in arn

    return ok(
        {
            "ok": True,
            "email": email,
            "subscriptionArn": "pending confirmation" if pending else arn,
            "message": (
                "Check your inbox and confirm the SNS subscription. "
                "Notifications start only after you click the AWS confirmation link."
            ),
        }
    )