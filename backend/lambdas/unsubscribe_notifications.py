import json
import os
import boto3

sns = boto3.client('sns')
TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,DELETE'
    }

    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip().lower()

        if not email:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Email is required.'})
            }

        # חיפוש ה-SubscriptionArn המתאים למייל שהוזן
        paginator = sns.get_paginator('list_subscriptions_by_topic')
        subscription_arn = None

        for page in paginator.paginate(TopicArn=TOPIC_ARN):
            for sub in page.get('Subscriptions', []):
                if sub.get('Endpoint', '').lower() == email:
                    subscription_arn = sub.get('SubscriptionArn')
                    break
            if subscription_arn:
                break

        if not subscription_arn or subscription_arn == 'PendingConfirmation':
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'message': 'Active subscription not found for this email.'})
            }

        # ביטול ההרשמה ב-SNS
        sns.unsubscribe(SubscriptionArn=subscription_arn)

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'Successfully unsubscribed from notifications.'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'message': str(e)})
        }
