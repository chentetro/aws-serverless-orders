import boto3

REGION = "us-east-1"
TABLE_NAME = "orders"
GSI_NAME = "createdAt-index"
ENTITY_TYPE = "ORDER"
TOPIC_NAME = "oms-order-deleted"
API_NAME = "oms-api"
STAGE_NAME = "prod"
LAMBDA_RUNTIME = "python3.12"
LAB_ROLE_NAME = "LabRole"
PDF_LAYER_NAME = "oms-pdf-layer"
AMPLIFY_APP_NAME = "oms-client"
S3_DELETED_PREFIX = "deleted/"
S3_REPORTS_PREFIX = "reports/"

LAMBDA_NAMES = [
    "oms-create-order",
    "oms-get-orders",
    "oms-get-order",
    "oms-update-order",
    "oms-delete-order",
    "oms-subscribe",
    "oms-unsubscribe",
    "oms-generate-report",
    "oms-analyze-order",
    "oms-deleted-order-stream",
    "oms-backup-deleted-order",
]


def account_id():
    """Current Learner Lab account. Used in bucket name and ARNs."""
    return boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]


def bucket_name(acct=None):
    return f"oms-orders-{acct or account_id()}"


def topic_arn(acct=None):
    return f"arn:aws:sns:{REGION}:{acct or account_id()}:{TOPIC_NAME}"


def lab_role_arn(acct=None):
    return f"arn:aws:iam::{acct or account_id()}:role/{LAB_ROLE_NAME}"


if __name__ == "__main__":
    import sys

    print(f"region={REGION}")
    print(f"table={TABLE_NAME}  gsi={GSI_NAME}")
    print(f"topic={TOPIC_NAME}")
    print("lambdas:")
    for name in LAMBDA_NAMES:
        print(f"  {name}")
    if "--live" in sys.argv:
        acct = account_id()
        print(f"account={acct}")
        print(f"bucket={bucket_name(acct)}")
        print(f"role={lab_role_arn(acct)}")
        print(f"topic_arn={topic_arn(acct)}")
    else:
        print("Add --live (needs AWS credentials) to print account/bucket/role.")
