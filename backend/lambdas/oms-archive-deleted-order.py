import json
import os
import boto3
from datetime import datetime

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('ARCHIVE_BUCKET_NAME', '').strip()

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
            
            try:
                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=s3_key,
                    Body=json.dumps(archive_payload, indent=2),
                    ContentType='application/json'
                )
                print(f"Successfully archived deleted order {order_id} to s3://{BUCKET_NAME}/{s3_key}")
            except Exception as e:
                print(f"Error archiving to S3 for order {order_id}: {str(e)}")
                raise e

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'S3 archiving processed successfully'})
    }