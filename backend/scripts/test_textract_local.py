"""Test Amazon Textract from your PC (needs Learner Lab keys).

1. In AWS Academy → AWS Details, copy Access key, Secret, Session token.
2. aws configure  (region us-east-1) and set AWS_SESSION_TOKEN if needed.
3. python backend/scripts/test_textract_local.py path\\to\\order.png

This is the same Analyze document + Forms call as the Lambda and the console.
"""

import json
import sys
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lambdas"))
sys.path.insert(0, str(ROOT / "lambdas" / "oms-extract-order-doc"))

from lambda_function import parse_order_from_blocks  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_textract_local.py <png-or-jpg>")
        sys.exit(1)

    path = Path(sys.argv[1])
    data = path.read_bytes()
    client = boto3.client("textract", region_name="us-east-1")
    result = client.analyze_document(
        Document={"Bytes": data},
        FeatureTypes=["FORMS"],
    )
    parsed = parse_order_from_blocks(result.get("Blocks") or [])
    print(json.dumps(parsed, indent=2))


if __name__ == "__main__":
    main()
