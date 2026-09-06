# AWS Final Project — Master Architecture Document

**Event-Driven Serverless Order Management System (OMS)**  
Region: `us-east-1` · Learner Lab · All Lambdas use existing IAM role `LabRole`  
Client: React + Vite, hosted on AWS Amplify  
Freestyle service: Amazon Comprehend

This file is the single English source of truth: architecture, data model, flows, API table with sample input/output, and AWS CLI commands to inspect every service. After you deploy, replace `ACCOUNT_ID` and `API_ID` using the bootstrap commands in section 5. Until then, names (`orders`, `oms-api`, `oms-delete-order`, …) are the real resource names we will create.

The short HTTP contract for the React client is [API_CONTRACT.md](API_CONTRACT.md).

---

## 1. High-level architecture

The system is fully serverless. The browser never talks to DynamoDB, SNS, or S3. It only calls REST APIs. Business logic lives in Lambda.

```
Browser (Amplify — React + Vite dist/)
        |
        | HTTPS + CORS
        v
API Gateway REST API  oms-api  / stage prod
        |
        +--> oms-create-order
        +--> oms-get-orders
        +--> oms-get-order
        +--> oms-update-order
        +--> oms-delete-order          (DeleteItem only, returns 200 immediately)
        +--> oms-subscribe
        +--> oms-unsubscribe
        +--> oms-generate-report       (reads S3 TXT, writes PDF, returns URL in body)
        +--> oms-analyze-order         (Comprehend, writes result back to the order)
                |
                v
        DynamoDB table  orders
        (+ GSI createdAt-index)
                |
                | Stream event REMOVE (async, after delete)
                v
        oms-deleted-order-stream
                |
                | sns.publish  (not on the HTTP delete path)
                v
        SNS topic  oms-order-deleted
                |
                +-- email protocol --> confirmed subscriber inboxes
                +-- lambda protocol --> oms-backup-deleted-order --> S3 deleted/*.txt

        oms-generate-report --> S3 reports/*.pdf  (presigned URL in API JSON)
        oms-analyze-order   --> Amazon Comprehend
```

### How the services fit together

1. **API Gateway** is the only public HTTP front door. Every required action is a REST method with Lambda proxy integration and CORS.
2. **Lambda** implements create / read / update / delete, subscribe / unsubscribe, PDF report, sentiment analysis, stream handling, and S3 backup. One function per responsibility so each can be shown in the service table and in `aws lambda get-function`.
3. **DynamoDB** is the durable store for live orders. A GSI supports “get all orders sorted by creation date” without a table Scan.
4. **DynamoDB Streams** is the event source for deletion side effects. The delete API does not wait for email or backup.
5. **SNS** owns notification subscriptions and fans one delete message out to email *and* the backup Lambda independently.
6. **S3** stores deleted-order `.txt` files and generated PDF reports. Objects are private; download uses a presigned URL returned in the API body.
7. **Comprehend** is the graded extra feature: analyze an order description from the UI.
8. **Amplify Hosting** serves the React production build, as required for the web client option.

### Why delete is designed this way

`oms-delete-order` only runs `DeleteItem` and returns HTTP 200. It does **not** call `sns.publish()` and does **not** write to S3. If it published to SNS inside the request, the user’s HTTP call would wait for that network round-trip, which breaks “must not wait / must not delay in any way.”

After the item is gone, Streams emits `REMOVE` with `OldImage`. `oms-deleted-order-stream` publishes once to SNS. SNS then:

- emails every confirmed subscriber with the deleted order details (automatic; no extra user action);
- invokes `oms-backup-deleted-order`, which writes `deleted/{orderId}.txt`.

Email and backup cannot block each other or the delete response.

---

## 2. Data model — table `orders`

Attributes are **not** declared as columns when the table is created. The create-order Lambda writes them on `POST /orders`.

| Attribute | Type | Set by | Purpose |
|---|---|---|---|
| `orderId` | String (UUIDv4) | Create Lambda | Partition key; unique order identity |
| `createdAt` | String (ISO-8601 UTC) | Create Lambda | Creation date; GSI sort key |
| `lastModified` | String (ISO-8601 UTC) | Create and update | Last modified date |
| `price` | Number | Create / update | Order price |
| `description` | String | Create / update | Order description |
| `entityType` | String, always `ORDER` | Create Lambda | GSI partition key so all orders sit in one queryable partition |
| `sentiment` | String | Analyze Lambda | Comprehend label (e.g. POSITIVE) |
| `sentimentScore` | Map/Number | Analyze Lambda | Confidence |
| `keyPhrases` | List | Analyze Lambda | Comprehend key phrases |

**Billing:** on-demand.  
**Stream:** `StreamViewType = NEW_AND_OLD_IMAGES` (required so delete side effects see the old item).

### Primary key and sort key justification

**Table partition key:** `orderId` (String).

Get / update / delete receive only the order id. A single-attribute key allows `GetItem`, `UpdateItem`, and `DeleteItem` with no extra parameters and no Scan. UUIDv4 spreads writes across partitions (unlike a sequential counter).

**Sort key for “get all orders sorted by creation date”:** not on the base table (a composite base key would force every Get/Delete to supply a sort key the client does not have). Instead a **GSI** named `createdAt-index`:

- GSI partition key: `entityType` (`ORDER`)
- GSI sort key: `createdAt`

`GET /orders` is a **Query** on that GSI (`ScanIndexForward` false = newest first). That meets the assignment’s primary + sort key requirement and avoids Scan-then-sort-in-Lambda.

---

## 3. AWS resources to create

| Resource | Name |
|---|---|
| DynamoDB table | `orders` + GSI `createdAt-index` + streams |
| SNS topic | `oms-order-deleted` |
| S3 bucket | `oms-orders-ACCOUNT_ID` (must be globally unique) |
| S3 prefixes | `deleted/`, `reports/` |
| REST API | `oms-api`, stage `prod` |
| Lambda (Python 3.12) | `oms-create-order`, `oms-get-orders`, `oms-get-order`, `oms-update-order`, `oms-delete-order`, `oms-subscribe`, `oms-unsubscribe`, `oms-generate-report`, `oms-analyze-order`, `oms-deleted-order-stream`, `oms-backup-deleted-order` |
| Lambda layer | `oms-pdf-layer` (`fpdf2`) |
| Amplify app | `oms-client` |
| IAM | attach existing `LabRole` only — do not create or edit roles in Learner Lab |
| Comprehend | no stack resource; called from `oms-analyze-order` |

S3 block public access stays **ON**. The PDF API returns a presigned URL, not a public object.

---

## 4. Setup per service (assignment table)

CLI commands below are complete. After deploy, first resolve IDs (section 5), then run each command in the Learner Lab CloudShell / AWS CLI. They must succeed for the grader.

### Amazon API Gateway

**Why:** Public REST interface for every operation. Only HTTP surface the client is allowed to use.

**Relation to functionality:** Maps paths/methods to Lambdas; CORS so the Amplify origin can call the API; stage `prod` is the URL we put in the Word deliverable.

**CLI:**

```bash
aws apigateway get-rest-apis --region us-east-1
aws apigateway get-rest-api --rest-api-id API_ID --region us-east-1
aws apigateway get-resources --rest-api-id API_ID --region us-east-1
aws apigateway get-stage --rest-api-id API_ID --stage-name prod --region us-east-1
```

### AWS Lambda (all functions)

**Why:** Run business logic without servers; scale per request; isolate delete from notifications.

**Relation to functionality:** Each API and each async worker is its own function (see names in section 3).

**CLI (repeat per function name):**

```bash
aws lambda get-function --function-name oms-create-order --region us-east-1
aws lambda get-function --function-name oms-get-orders --region us-east-1
aws lambda get-function --function-name oms-get-order --region us-east-1
aws lambda get-function --function-name oms-update-order --region us-east-1
aws lambda get-function --function-name oms-delete-order --region us-east-1
aws lambda get-function --function-name oms-subscribe --region us-east-1
aws lambda get-function --function-name oms-unsubscribe --region us-east-1
aws lambda get-function --function-name oms-generate-report --region us-east-1
aws lambda get-function --function-name oms-analyze-order --region us-east-1
aws lambda get-function --function-name oms-deleted-order-stream --region us-east-1
aws lambda get-function --function-name oms-backup-deleted-order --region us-east-1
aws lambda list-functions --region us-east-1 --query "Functions[?starts_with(FunctionName, 'oms-')].[FunctionName,Runtime,Role]" --output table
```

### Lambda layer `oms-pdf-layer`

**Why:** `fpdf2` is pure Python (zips cleanly on Windows). ReportLab ships native extensions that are painful to package for Lambda from Windows.

**Relation to functionality:** Used only by `oms-generate-report` to build the deleted-orders PDF.

**CLI:**

```bash
aws lambda list-layers --region us-east-1
aws lambda list-layer-versions --layer-name oms-pdf-layer --region us-east-1
aws lambda get-layer-version --layer-name oms-pdf-layer --version-number 1 --region us-east-1
```

### Amazon DynamoDB

**Why:** Persistent, serverless table; Streams for event-driven delete; GSI for sorted list.

**Relation to functionality:** Source of truth for live orders; stream `REMOVE` starts notification + backup.

**CLI:**

```bash
aws dynamodb describe-table --table-name orders --region us-east-1
aws dynamodb describe-table --table-name orders --region us-east-1 --query "Table.{KeySchema:KeySchema,GSIs:GlobalSecondaryIndexes,Stream:LatestStreamArn,Billing:BillingModeSummary}"
aws dynamodb scan --table-name orders --region us-east-1 --max-items 5
```

### Amazon SNS

**Why:** Built-in email protocol, confirmation flow, and fan-out to many subscribers plus a Lambda — without a custom email table.

**Relation to functionality:** Subscribe / unsubscribe APIs; after delete, one publish delivers emails and triggers backup.

**CLI:**

```bash
aws sns list-topics --region us-east-1
aws sns get-topic-attributes --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:oms-order-deleted --region us-east-1
aws sns list-subscriptions-by-topic --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:oms-order-deleted --region us-east-1
```

### Amazon S3

**Why:** Object storage required for deleted-order TXT backups and the summary PDF.

**Relation to functionality:** Async backup writes `deleted/*.txt`. Report API reads them, writes `reports/*.pdf`, returns a presigned GET URL in the JSON body.

**CLI:**

```bash
aws s3api head-bucket --bucket oms-orders-ACCOUNT_ID
aws s3api get-bucket-location --bucket oms-orders-ACCOUNT_ID
aws s3api get-public-access-block --bucket oms-orders-ACCOUNT_ID
aws s3 ls s3://oms-orders-ACCOUNT_ID/deleted/
aws s3 ls s3://oms-orders-ACCOUNT_ID/reports/
```

### Amazon Comprehend

**Why:** Graded freestyle service; clear UI (Analyze button + sentiment badge); real NLP on order text.

**Relation to functionality:** `POST /orders/{orderId}/analyze` calls `DetectSentiment` and `DetectKeyPhrases`, stores the result on the item.

**CLI (invokes the service; confirms LabRole is allowed):**

```bash
aws comprehend detect-sentiment --language-code en --text "The order arrived damaged and late" --region us-east-1
aws comprehend detect-key-phrases --language-code en --text "The order arrived damaged and late" --region us-east-1
```

### AWS Amplify Hosting

**Why:** Assignment requires a working web URL hosted on Amplify (not localhost).

**Relation to functionality:** Serves the React + Vite `dist/` build that calls every API.

**CLI:**

```bash
aws amplify list-apps --region us-east-1
aws amplify get-app --app-id AMPLIFY_APP_ID --region us-east-1
```

### IAM `LabRole` (not created by us)

**Why:** Learner Lab blocks creating roles. Every Lambda must use this role.

**CLI:**

```bash
aws iam get-role --role-name LabRole
aws iam list-attached-role-policies --role-name LabRole
```

---

## 5. Bootstrap commands (fill ACCOUNT_ID and API_ID)

Run in Learner Lab after resources exist:

```bash
aws sts get-caller-identity --query Account --output text --region us-east-1
aws apigateway get-rest-apis --region us-east-1 --query "items[?name=='oms-api'].id" --output text
aws amplify list-apps --region us-east-1 --query "apps[?name=='oms-client'].appId" --output text
```

Base URL for all APIs:

```text
https://API_ID.execute-api.us-east-1.amazonaws.com/prod
```

Example with placeholders used in the API table:

```text
https://abcd1234.execute-api.us-east-1.amazonaws.com/prod
```

Replace `abcd1234` with the real `API_ID` from the command above. Sample JSON below is otherwise exact.

---

## 6. API list (assignment table)

All responses include CORS headers. Error shape: `{"error": "message"}` with 4xx/5xx.

### Create order

| | |
|---|---|
| **API name** | Create order |
| **HTTP method** | POST |
| **API URL** | `https://API_ID.execute-api.us-east-1.amazonaws.com/prod/orders` |
| **Sample input** | Body: `{"description": "Office chairs x4", "price": 199.90}` |
| **Sample output** | `{"orderId":"a3c1e8f2-9b44-4d21-8f0a-11b22c33d44e","createdAt":"2026-08-31T14:22:01Z","lastModified":"2026-08-31T14:22:01Z","price":199.9,"description":"Office chairs x4","entityType":"ORDER"}` |

### Get all orders (sorted by creation date)

| | |
|---|---|
| **API name** | Get all orders |
| **HTTP method** | GET |
| **API URL** | `https://API_ID.execute-api.us-east-1.amazonaws.com/prod/orders` |
| **Sample input** | None (URL only) |
| **Sample output** | `{"orders":[{"orderId":"...","createdAt":"2026-08-31T14:22:01Z","lastModified":"2026-08-31T14:22:01Z","price":199.9,"description":"Office chairs x4","entityType":"ORDER"}]}` — newest `createdAt` first (GSI Query). |

### Get a specific order

| | |
|---|---|
| **API name** | Get a specific order |
| **HTTP method** | GET |
| **API URL** | `https://API_ID.execute-api.us-east-1.amazonaws.com/prod/orders/{orderId}` |
| **Sample input** | URL: `.../orders/a3c1e8f2-9b44-4d21-8f0a-11b22c33d44e` |
| **Sample output** | Same object as create (plus `sentiment` / `keyPhrases` if analyzed). `404` if missing. |

### Update order details

| | |
|---|---|
| **API name** | Update order details |
| **HTTP method** | PUT |
| **API URL** | `https://API_ID.execute-api.us-east-1.amazonaws.com/prod/orders/{orderId}` |
| **Sample input** | URL id + body `{"description": "Office chairs x4 — rush", "price": 219.90}` |
| **Sample output** | Updated item; `lastModified` is a new UTC timestamp; `createdAt` unchanged. |

### Delete order

| | |
|---|---|
| **API name** | Delete order |
| **HTTP method** | DELETE |
| **API URL** | `https://API_ID.execute-api.us-east-1.amazonaws.com/prod/orders/{orderId}` |
| **Sample input** | URL: `.../orders/a3c1e8f2-9b44-4d21-8f0a-11b22c33d44e` |
| **Sample output** | `{"ok":true,"orderId":"a3c1e8f2-9b44-4d21-8f0a-11b22c33d44e","message":"Order deleted"}` — returned as soon as DynamoDB delete succeeds. Email and TXT backup happen afterward (Streams + SNS). |

### Register email for delete notifications

| | |
|---|---|
| **API name** | Subscribe to notifications |
| **HTTP method** | POST |
| **API URL** | `https://API_ID.execute-api.us-east-1.amazonaws.com/prod/notifications/subscribe` |
| **Sample input** | `{"email":"student@example.com"}` |
| **Sample output** | `{"ok":true,"email":"student@example.com","subscriptionArn":"pending confirmation","message":"Check your inbox and confirm the SNS subscription. Notifications start only after you click the AWS confirmation link."}` |

Lambda calls:

```text
sns.subscribe(TopicArn=OMS_TOPIC_ARN, Protocol="email", Endpoint=email)
```

Pending until the user confirms. That is normal SNS behavior.

### Unsubscribe from notifications

| | |
|---|---|
| **API name** | Unsubscribe from notifications |
| **HTTP method** | POST |
| **API URL** | `https://API_ID.execute-api.us-east-1.amazonaws.com/prod/notifications/unsubscribe` |
| **Sample input** | `{"email":"student@example.com"}` |
| **Sample output** | `{"ok":true,"email":"student@example.com","message":"Unsubscribed"}` |

SNS cannot unsubscribe by email string. Lambda: `list_subscriptions_by_topic` → match `Endpoint` → `unsubscribe(SubscriptionArn=...)`. A still-pending subscription may not be removable by ARN; the UI tells the user to confirm first or ignore the confirmation email.

### PDF summary of all deleted orders

| | |
|---|---|
| **API name** | Download deleted-orders PDF |
| **HTTP method** | GET |
| **API URL** | `https://API_ID.execute-api.us-east-1.amazonaws.com/prod/reports/deleted-orders` |
| **Sample input** | None (URL only). Do **not** use `/orders/deleted/report` — `{orderId}` would capture `deleted`. |
| **Sample output** | `{"url":"https://oms-orders-ACCOUNT_ID.s3.amazonaws.com/reports/deleted-orders-20260831T142501Z.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&..."}` — URL is in the **response body** for the client to open. |

Lambda steps: list `deleted/*.txt` → read all → build one PDF (`fpdf2` layer) → put object under `reports/` → presign → return `{"url": "..."}`.

### Analyze order description (freestyle)

| | |
|---|---|
| **API name** | Analyze order (Comprehend) |
| **HTTP method** | POST |
| **API URL** | `https://API_ID.execute-api.us-east-1.amazonaws.com/prod/orders/{orderId}/analyze` |
| **Sample input** | URL id; empty body |
| **Sample output** | `{"orderId":"...","sentiment":"NEGATIVE","sentimentScore":{"Negative":0.91,"Positive":0.02,"Neutral":0.06,"Mixed":0.01},"keyPhrases":["damaged packaging","late delivery"]}` |

---

## 7. Notification subscribe flow (UI)

User types an email and clicks Subscribe → `POST /notifications/subscribe`. All addresses live in SNS (no extra DynamoDB table). User must click the AWS confirmation mail. Then a later delete emails them automatically with the deleted order details.

---

## 8. Delete process (notification + backup)

**Function 1 — `oms-delete-order` (API Gateway):** DynamoDB `DeleteItem` → HTTP 200 to that user only. No email, no S3, no `sns.publish`.

**After that (not part of the HTTP response):**

1. DynamoDB Streams `REMOVE` + `OldImage`.
2. `oms-deleted-order-stream` publishes one message to `oms-order-deleted`.
3. SNS emails confirmed subscribers.
4. SNS invokes `oms-backup-deleted-order` → `s3://oms-orders-ACCOUNT_ID/deleted/{orderId}.txt`.

---

## 9. Freestyle — Amazon Comprehend

Same UX idea as a per-order button (the original draft used Polly). We use Comprehend: sentiment + key phrases on `description`, stored on the item, shown as a badge and tags on every later load. Value: spot complaint-toned orders.

Do not create IAM roles. If `LabRole` lacks `comprehend:DetectSentiment` and `comprehend:DetectKeyPhrases`, the demo fails — verify with the CLI in section 4 before relying on it.

---

## 10. Client — React + Vite on Amplify

The assignment asks for a web client in HTML/CSS/JS that performs real REST calls and is hosted on Amplify. Vite build output **is** static HTML/JS/CSS. No Node server in production.

Rules:

- Client only `fetch`es API Gateway and displays JSON. No DynamoDB/SNS/S3 from the browser. No “sort all orders in React” instead of the API.
- CORS on API Gateway must allow the Amplify origin.
- Word document gets the **Amplify URL**, not localhost.

Suggested layout: `src/api.ts` wraps all nine endpoints; React hooks for UI state; Tailwind optional.

Must cover: create, list, get, update, delete, subscribe, unsubscribe, open PDF from returned `url`, Analyze button per order.

Deploy: `npm run build` → upload `dist/` to Amplify app `oms-client`.

---

## 11. Tested flows (to screenshot after deploy)

1. Create order → GET all → GET by id (sorted list, fields present).
2. Update order → `lastModified` changes, `createdAt` does not.
3. Subscribe email → confirm SNS mail → delete order → HTTP 200 immediately → email arrives with order details → `.txt` appears under `deleted/`.
4. Unsubscribe → delete another order → no email to that address.
5. GET report → JSON contains `url` → browser downloads PDF listing deleted orders.
6. Analyze → badge + key phrases in UI; GET order still shows them.
7. Delete still fast when backup/email are slow (prove async).

---

## 12. Delete-order Lambda (contract for the Word appendix)

The submitted Python will implement only:

- parse `orderId` from the path;
- `DeleteItem` on table `orders`;
- return 200 JSON immediately;
- CORS headers.

No SNS and no S3 in this file. That is intentional.

---

## 13. What changed vs the earlier Hebrew/student draft

| Earlier draft | Problem | This design |
|---|---|---|
| Partition key only + Scan + sort in Lambda | Assignment asks for sort keys; Scan does not scale | GSI `createdAt-index` + Query |
| Delete Lambda calls `sns.publish()` then 200 | HTTP waits on publish | Delete = `DeleteItem` only; Stream → SNS |
| `GET /orders/deleted/report` | Collides with `/orders/{orderId}` | `GET /reports/deleted-orders` |
| Edit IAM in console for extra service | Learner Lab usually cannot create/edit roles | `LabRole` only |
| React without Amplify / localhost only | Grader needs a working URL | `vite build` + Amplify |
| Subscribe section had no command | Incomplete | `sns.subscribe` documented |
| Freestyle Polly | Valid, but we already chose Comprehend | Comprehend + per-order button |

---

## 14. Build order

1. Create `lambdas/`, `client/`, `layer/`, `scripts/`, `docs/`.
2. Provision DynamoDB `orders` (GSI + streams), S3 bucket, SNS topic.
3. Deploy five CRUD Lambdas; create `oms-api`; CORS; stage `prod`.
4. Subscribe / unsubscribe Lambdas; confirm email flow.
5. Stream Lambda + backup Lambda; prove delete does not wait.
6. `fpdf2` layer + report Lambda (URL in body).
7. Analyze Lambda (Comprehend).
8. React + Vite client; Amplify `dist/`.
9. Fill real `API_ID` / Amplify URL / CLI output into the Word submission; screenshots of section 11; paste delete Lambda source.
