import os
import boto3
from datetime import datetime, timezone

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('ARCHIVE_BUCKET_NAME', '').strip()
DELETED_PREFIX = 'deleted-orders/'


def build_backup_text(order_id, description, price, created_at, last_modified, deleted_at):
    """One label per line so oms-generate-deleted-report can read the values back."""
    try:
        formatted_price = f"{float(price):.2f}"
    except (TypeError, ValueError):
        formatted_price = str(price)

    return "\n".join([
        "Deleted Order Backup",
        "====================",
        f"Order ID: {order_id}",
        f"Description: {description}",
        f"Price: {formatted_price}",
        f"Created At: {created_at}",
        f"Last Modified: {last_modified}",
        f"Deleted At: {deleted_at}",
        "",
        "Written automatically by oms-archive-deleted-order from the DynamoDB stream.",
    ]) + "\n"


def lambda_handler(event, context):
    records = event.get('Records', [])
    print(f"Received {len(records)} stream record(s) for S3 archiving")

    for record in records:
        event_name = record.get('eventName')  # 'INSERT', 'MODIFY', 'REMOVE'

        # Archive only on item deletion
        if event_name == 'REMOVE':
            dynamodb_data = record.get('dynamodb', {})
            old_image = dynamodb_data.get('OldImage', {})

            if not old_image:
                print("Skipping record: OldImage is missing.")
                continue

            # Extract fields according to your schema
            order_id = old_image.get('orderId', {}).get('S', 'unknown_id')
            description = old_image.get('description', {}).get('S', 'No description')
            price = old_image.get('price', {}).get('N', '0')
            created_at = old_image.get('createdAt', {}).get('S', '')
            last_modified = old_image.get('lastModified', {}).get('S', '')
            deleted_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            backup_text = build_backup_text(
                order_id, description, price, created_at, last_modified, deleted_at
            )

            # The assignment requires the deleted order to be kept as a TXT file.
            s3_key = f"{DELETED_PREFIX}{order_id}.txt"

            try:
                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=s3_key,
                    Body=backup_text.encode('utf-8'),
                    ContentType='text/plain; charset=utf-8'
                )
                print(f"Successfully archived deleted order {order_id} to s3://{BUCKET_NAME}/{s3_key}")
            except Exception as e:
                print(f"Error archiving to S3 for order {order_id}: {str(e)}")
                raise e

    return {
        'statusCode': 200,
        'body': '{"message": "S3 archiving processed successfully"}'
    }
