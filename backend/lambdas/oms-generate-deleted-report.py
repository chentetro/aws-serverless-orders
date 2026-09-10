<<<<<<< HEAD
"""GET /reports/deleted-orders

Reads every deleted-order backup in S3, builds one summary PDF, stores it back in
S3 under reports/, and returns a presigned download URL in the response body so
the client can download it.

The PDF is written by hand below. That keeps the function dependency free, so it
needs no Lambda layer and can be pasted straight into the console.
"""

import json
import os
import boto3
from datetime import datetime, timezone

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('ARCHIVE_BUCKET_NAME', '').strip()
DELETED_PREFIX = 'deleted-orders/'
REPORTS_PREFIX = 'reports/'
URL_TTL_SECONDS = 3600

CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
    'Access-Control-Allow-Methods': 'GET,OPTIONS'
}

# --- minimal PDF writer -----------------------------------------------------

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN_LEFT = 45
FIRST_BASELINE = 790
LINE_HEIGHT = 15
LINES_PER_PAGE = 48
FONT_SIZE = 10


def _escape_pdf_text(text):
    """PDF strings are latin-1 and must escape backslash and both parentheses."""
    safe = ''.join(char if 32 <= ord(char) < 127 else '?' for char in str(text))
    return safe.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')


def _content_stream(lines):
    parts = [
        'BT',
        f'/F1 {FONT_SIZE} Tf',
        f'{LINE_HEIGHT} TL',
        f'{MARGIN_LEFT} {FIRST_BASELINE} Td',
    ]
    for index, line in enumerate(lines):
        if index:
            parts.append('T*')
        parts.append(f'({_escape_pdf_text(line)}) Tj')
    parts.append('ET')
    return '\n'.join(parts).encode('latin-1', 'replace')


def build_pdf(lines):
    """Return the bytes of a simple multi-page PDF containing the given lines."""
    pages = [lines[i:i + LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)]
    if not pages:
        pages = [['No deleted orders found.']]

    font_id = 3 + 2 * len(pages)
    objects = {
        1: b'<< /Type /Catalog /Pages 2 0 R >>',
        font_id: b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
    }

    kids = []
    for index, page_lines in enumerate(pages):
        page_id = 3 + 2 * index
        content_id = page_id + 1
        kids.append(f'{page_id} 0 R')
        objects[page_id] = (
            f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] '
            f'/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>'
        ).encode('latin-1')
        stream = _content_stream(page_lines)
        objects[content_id] = (
            b'<< /Length ' + str(len(stream)).encode('ascii') + b' >>\nstream\n' + stream + b'\nendstream'
        )

    objects[2] = (
        '<< /Type /Pages /Kids [' + ' '.join(kids) + f'] /Count {len(pages)} >>'
    ).encode('latin-1')

    out = bytearray(b'%PDF-1.4\n')
    offsets = {}
    for object_id in sorted(objects):
        offsets[object_id] = len(out)
        out += f'{object_id} 0 obj\n'.encode('ascii') + objects[object_id] + b'\nendobj\n'

    xref_offset = len(out)
    highest_id = max(objects)
    out += f'xref\n0 {highest_id + 1}\n'.encode('ascii')
    out += b'0000000000 65535 f \n'
    for object_id in range(1, highest_id + 1):
        out += f'{offsets[object_id]:010d} 00000 n \n'.encode('ascii')
    out += (
        f'trailer\n<< /Size {highest_id + 1} /Root 1 0 R >>\n'
        f'startxref\n{xref_offset}\n%%EOF\n'
    ).encode('ascii')

    return bytes(out)


# --- backup file parsing ----------------------------------------------------

def parse_backup_text(text):
    """Read back the 'Label: value' lines written by oms-archive-deleted-order."""
    values = {}
    for raw_line in text.splitlines():
        if ':' not in raw_line:
            continue
        label, _, value = raw_line.partition(':')
        values[label.strip().lower()] = value.strip()

    if not values.get('order id'):
        return None

    try:
        price = float(values.get('price', '0') or 0)
    except ValueError:
        price = 0.0

    return {
        'orderId': values.get('order id', ''),
        'description': values.get('description', ''),
        'price': price,
        'createdAt': values.get('created at', ''),
        'lastModified': values.get('last modified', ''),
        'deletedAt': values.get('deleted at', ''),
    }


def parse_backup_json(text):
    """Older backups were written as JSON. Keep reading them so nothing is lost."""
    data = json.loads(text)
    try:
        price = float(data.get('price', 0) or 0)
    except (TypeError, ValueError):
        price = 0.0

    return {
        'orderId': data.get('orderId', ''),
        'description': data.get('description', ''),
        'price': price,
        'createdAt': data.get('createdAt', ''),
        'lastModified': data.get('lastModified', ''),
        'deletedAt': data.get('deletedAt', ''),
    }


def load_deleted_orders():
    orders = []
    paginator = s3.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=DELETED_PREFIX):
        for item in page.get('Contents', []):
            key = item.get('Key', '')
            if not (key.endswith('.txt') or key.endswith('.json')):
                continue

            body = s3.get_object(Bucket=BUCKET_NAME, Key=key)['Body'].read().decode('utf-8')
            try:
                order = parse_backup_json(body) if key.endswith('.json') else parse_backup_text(body)
            except (ValueError, TypeError) as parse_error:
                print(f"Skipping unreadable backup {key}: {parse_error}")
                continue

            if order:
                orders.append(order)

    orders.sort(key=lambda order: order.get('deletedAt') or order.get('createdAt') or '', reverse=True)
    return orders


# --- report -----------------------------------------------------------------

def build_report_lines(orders, total_lost_revenue, generated_at):
    lines = [
        'DELETED ORDERS SUMMARY REPORT',
        'Order Management System',
        f'Generated At: {generated_at}',
        '',
        f'Total deleted orders: {len(orders)}',
        f'Total lost revenue: ${total_lost_revenue:,.2f}',
        '',
        '-' * 92,
    ]

    if not orders:
        lines.append('No deleted orders were found in object storage.')
        return lines

    for position, order in enumerate(orders, start=1):
        lines.extend([
            f"{position}. Order ID: {order['orderId']}",
            f"   Description:   {order['description']}",
            f"   Price:         ${order['price']:,.2f}",
            f"   Created At:    {order['createdAt']}",
            f"   Deleted At:    {order['deletedAt']}",
            '',
        ])

    return lines


def respond(status_code, payload):
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(payload)
    }


def lambda_handler(event, context):
    print(f"Generating deleted orders report from bucket: {BUCKET_NAME}")

    if not BUCKET_NAME:
        return respond(500, {'error': 'ARCHIVE_BUCKET_NAME environment variable is missing'})

    try:
        orders = load_deleted_orders()
        total_lost_revenue = round(sum(order['price'] for order in orders), 2)

        now = datetime.now(timezone.utc)
        generated_at = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        report_key = f"{REPORTS_PREFIX}deleted-orders-{now.strftime('%Y%m%dT%H%M%SZ')}.pdf"

        pdf_bytes = build_pdf(build_report_lines(orders, total_lost_revenue, generated_at))

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=report_key,
            Body=pdf_bytes,
            ContentType='application/pdf',
            ContentDisposition=f'attachment; filename="{report_key.split("/")[-1]}"'
        )

        download_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': report_key},
            ExpiresIn=URL_TTL_SECONDS
        )

        print(f"Report written to s3://{BUCKET_NAME}/{report_key}")

        return respond(200, {
            'totalDeletedOrders': len(orders),
            'totalLostRevenue': total_lost_revenue,
            'orders': orders,
            'url': download_url,
            'generatedAt': generated_at
        })

    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return respond(500, {'error': f"Failed to generate report: {str(e)}"})
=======
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
>>>>>>> 5a3ce70bb17a99401fa4e2f7ffb2303ead13b2b2
