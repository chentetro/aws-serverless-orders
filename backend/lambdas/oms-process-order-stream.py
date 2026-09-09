import json
import os
import boto3

sns = boto3.client('sns')
TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '').strip()

def lambda_handler(event, context):
    records = event.get('Records', [])
    print(f"Processing {len(records)} stream record(s)")
    
    for record in records:
        event_name = record.get('eventName')  # 'INSERT', 'MODIFY', 'REMOVE'
        
        # Only process deletions
        if event_name == 'REMOVE':
            dynamodb_data = record.get('dynamodb', {})
            old_image = dynamodb_data.get('OldImage', {})
            
            if not old_image:
                print("Skipping record: OldImage is missing.")
                continue
            
            # Extract fields according to your schema
            order_id = old_image.get('orderId', {}).get('S', 'N/A')
            description = old_image.get('description', {}).get('S', 'No description')
            price = old_image.get('price', {}).get('N', '0.00')
            created_at = old_image.get('createdAt', {}).get('S', 'N/A')
            last_modified = old_image.get('lastModified', {}).get('S', 'N/A')
            
            # Format currency presentation
            try:
                formatted_price = f"${float(price):,.2f}"
            except ValueError:
                formatted_price = f"${price}"

            # Compose notification email
            subject = f"⚠️ Order Deleted: #{order_id}"
            message = (
                f"Hello,\n\n"
                f"An order has been deleted from the Order Management System.\n\n"
                f"--- Deleted Order Details ---\n"
                f"• Order ID: {order_id}\n"
                f"• Item / Description: {description}\n"
                f"• Price: {formatted_price}\n"
                f"• Created At: {created_at}\n"
                f"• Last Modified: {last_modified}\n\n"
                f"This is an automated system notification."
            )
            
            try:
                response = sns.publish(
                    TopicArn=TOPIC_ARN,
                    Subject=subject,
                    Message=message
                )
                print(f"Successfully sent SNS notification for deleted order {order_id}. MessageId: {response.get('MessageId')}")
            except Exception as err:
                print(f"Error publishing to SNS for order {order_id}: {str(err)}")
                raise err

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Stream processed successfully'})
    }