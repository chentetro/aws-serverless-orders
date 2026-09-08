"""Shared helpers copied into every Lambda zip.

CORS on every response so Amplify can call API Gateway.
Decimal-safe JSON because DynamoDB numbers come back as Decimal
and json.dumps crashes on Decimal without a converter.
"""

import json
from decimal import Decimal

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
}


class DecimalEncoder(json.JSONEncoder):
    """Turn DynamoDB Decimal into int or float for JSON."""

    def default(self, value):
        if isinstance(value, Decimal):
            if value % 1 == 0:
                return int(value)
            return float(value)
        return super().default(value)


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def ok(body, status_code=200):
    return response(status_code, body)


def error(status_code, message):
    return response(status_code, {"error": message})


def parse_json_body(event):
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    if not raw.strip():
        return {}
    return json.loads(raw)


def path_param(event, name):
    params = event.get("pathParameters") or {}
    return params.get(name)
