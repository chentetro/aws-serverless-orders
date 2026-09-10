import json
import uuid
from datetime import datetime, timezone
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('orders')

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT,DELETE"
}

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        description = body.get('description')
        price = body.get('price')

        if not description or price is None:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Missing description or price"})
            }

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        order_id = str(uuid.uuid4())

        item = {
            "orderId": order_id,
            "createdAt": now_iso,
            "lastModified": now_iso,
            "entityType": "ORDER",
            "description": str(description),
            "price": Decimal(str(price))
        }

        table.put_item(Item=item)

        response_item = {**item, "price": float(item["price"])}
        return {
            "statusCode": 201,
            "headers": CORS_HEADERS,
            "body": json.dumps(response_item)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(e)})
        }

    