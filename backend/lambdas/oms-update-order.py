import json
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

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        path_params = event.get('pathParameters') or {}
        order_id = path_params.get('orderId')
        body = json.loads(event.get('body', '{}'))

        if not order_id:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Missing orderId in path"})
            }

        description = body.get('description')
        price = body.get('price')

        if not description or price is None:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Missing description or price"})
            }

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        response = table.update_item(
            Key={"orderId": order_id},
            UpdateExpression="SET description = :d, price = :p, lastModified = :m",
            ExpressionAttributeValues={
                ":d": str(description),
                ":p": Decimal(str(price)),
                ":m": now_iso
            },
            ReturnValues="ALL_NEW"
        )

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(response.get('Attributes'), default=decimal_default)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(e)})
        }