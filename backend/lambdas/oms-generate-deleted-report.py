import json
import os
import boto3

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('ARCHIVE_BUCKET_NAME', '').strip()

def lambda_handler(event, context):
    print(f"Generating deleted orders report from bucket: {BUCKET_NAME}")
    
    if not BUCKET_NAME:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'ARCHIVE_BUCKET_NAME environment variable is missing'})
        }
    
    try:
        # List all archived order files under the deleted-orders/ prefix
        response = s3.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix='deleted-orders/'
        )
        
        deleted_orders = []
        total_lost_revenue = 0.0
        
        contents = response.get('Contents', [])
        
        for item in contents:
            key = item.get('Key', '')
            
            # Skip the folder marker if present and ensure it's a JSON file
            if key.endswith('.json'):
                file_obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
                file_content = file_obj['Body'].read().decode('utf-8')
                order_data = json.loads(file_content)
                
                deleted_orders.append(order_data)
                
                # Accumulate price
                try:
                    price_val = float(order_data.get('price', 0))
                    total_lost_revenue += price_val
                except (ValueError, TypeError):
                    pass

        # Sort orders by deletedAt / createdAt descending (newest first)
        deleted_orders.sort(
            key=lambda x: x.get('deletedAt') or x.get('createdAt') or '',
            reverse=True
        )

        report_summary = {
            'totalDeletedOrders': len(deleted_orders),
            'totalLostRevenue': round(total_lost_revenue, 2),
            'orders': deleted_orders
        }

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps(report_summary)
        }

    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f"Failed to generate report: {str(e)}"})
        }
