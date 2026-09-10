<<<<<<< HEAD
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

=======
import json
import os
import boto3
from datetime import datetime

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('ARCHIVE_BUCKET_NAME', '').strip()
>>>>>>> 5a3ce70bb17a99401fa4e2f7ffb2303ead13b2b2

def lambda_handler(event, context):
    records = event.get('Records', [])
    print(f"Received {len(records)} stream record(s) for S3 archiving")
<<<<<<< HEAD

    for record in records:
        event_name = record.get('eventName')  # 'INSERT', 'MODIFY', 'REMOVE'

=======
    
    for record in records:
        event_name = record.get('eventName')  # 'INSERT', 'MODIFY', 'REMOVE'
        
>>>>>>> 5a3ce70bb17a99401fa4e2f7ffb2303ead13b2b2
        # Archive only on item deletion
        if event_name == 'REMOVE':
            dynamodb_data = record.get('dynamodb', {})
            old_image = dynamodb_data.get('OldImage', {})
<<<<<<< HEAD

            if not old_image:
                print("Skipping record: OldImage is missing.")
                continue

=======
            
            if not old_image:
                print("Skipping record: OldImage is missing.")
                continue
            
>>>>>>> 5a3ce70bb17a99401fa4e2f7ffb2303ead13b2b2
            # Extract fields according to your schema
            order_id = old_image.get('orderId', {}).get('S', 'unknown_id')
            description = old_image.get('description', {}).get('S', 'No description')
            price = old_image.get('price', {}).get('N', '0')
            created_at = old_image.get('createdAt', {}).get('S', '')
            last_modified = old_image.get('lastModified', {}).get('S', '')
<<<<<<< HEAD
            deleted_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            backup_text = build_backup_text(
                order_id, description, price, created_at, last_modified, deleted_at
            )

            # The assignment requires the deleted order to be kept as a TXT file.
            s3_key = f"{DELETED_PREFIX}{order_id}.txt"

=======
            
            archive_payload = {
                "orderId": order_id,
                "description": description,
                "price": float(price),
                "createdAt": created_at,
                "lastModified": last_modified,
                "deletedAt": datetime.utcnow().isoformat() + "Z",
                "archivedBy": "DynamoDB Stream Archiver"
            }
            
            s3_key = f"deleted-orders/{order_id}.json"
            
>>>>>>> 5a3ce70bb17a99401fa4e2f7ffb2303ead13b2b2
            try:
                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=s3_key,
<<<<<<< HEAD
                    Body=backup_text.encode('utf-8'),
                    ContentType='text/plain; charset=utf-8'
=======
                    Body=json.dumps(archive_payload, indent=2),
                    ContentType='application/json'
>>>>>>> 5a3ce70bb17a99401fa4e2f7ffb2303ead13b2b2
                )
                print(f"Successfully archived deleted order {order_id} to s3://{BUCKET_NAME}/{s3_key}")
            except Exception as e:
                print(f"Error archiving to S3 for order {order_id}: {str(e)}")
                raise e

    return {
        'statusCode': 200,
<<<<<<< HEAD
        'body': '{"message": "S3 archiving processed successfully"}'
    }
=======
        'body': json.dumps({'message': 'S3 archiving processed successfully'})
    }
>>>>>>> 5a3ce70bb17a99401fa4e2f7ffb2303ead13b2b2
