"""POST /orders — create one order in DynamoDB."""

import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3

from common import error, ok, parse_json_body

TABLE_NAME = os.environ.get("TABLE_NAME", "orders")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lambda_handler(event, context):
    try:
        body = parse_json_body(event)
    except (TypeError, ValueError):
        return error(400, "Body must be JSON")

    description = body.get("description")
    price = body.get("price")

    if not isinstance(description, str) or not description.strip():
        return error(400, "description must be a non-empty string")

    if not isinstance(price, (int, float)) or isinstance(price, bool) or price <= 0:
        return error(400, "price must be a number greater than 0")

    now = utc_now()
    item = {
        "orderId": str(uuid.uuid4()),
        "createdAt": now,
        "lastModified": now,
        "price": Decimal(str(price)),
        "description": description.strip(),
        "entityType": "ORDER",
    }

    table.put_item(Item=item)
    return ok(item, 201)
