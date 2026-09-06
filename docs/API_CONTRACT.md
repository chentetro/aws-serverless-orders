# OMS API contract (frozen)

Source of truth for the React client and the Python Lambdas. Paths match `MASTER.md` (the graded Word API table). Do **not** prefix paths with `/api`.

Base URL (replace `API_ID` after the `prod` stage is deployed):

```text
https://API_ID.execute-api.us-east-1.amazonaws.com/prod
```

Set this as `VITE_API_BASE_URL` (no trailing slash). Client calls are `VITE_API_BASE_URL + path`, e.g. `.../prod/orders`.

Region: `us-east-1`. All responses include CORS headers. Errors use HTTP 4xx/5xx and:

```json
{"error": "message"}
```

Always show the JSON the backend returned. Do not sort `GET /orders` in the client — the list is already newest-first.

---

## Orders

### Create order

| | |
|---|---|
| Method | `POST` |
| Path | `/orders` |
| Body | `{"description": "Office chairs x4", "price": 199.90}` |
| Success | `201` — created item |

```json
{
  "orderId": "a3c1e8f2-9b44-4d21-8f0a-11b22c33d44e",
  "createdAt": "2026-08-31T14:22:01Z",
  "lastModified": "2026-08-31T14:22:01Z",
  "price": 199.9,
  "description": "Office chairs x4",
  "entityType": "ORDER"
}
```

`price` must be a number greater than 0. `description` must be a non-empty string.

### Get all orders

| | |
|---|---|
| Method | `GET` |
| Path | `/orders` |
| Body | none |
| Success | `200` — wrapper object, newest `createdAt` first |

```json
{
  "orders": [
    {
      "orderId": "a3c1e8f2-9b44-4d21-8f0a-11b22c33d44e",
      "createdAt": "2026-08-31T14:22:01Z",
      "lastModified": "2026-08-31T14:22:01Z",
      "price": 199.9,
      "description": "Office chairs x4",
      "entityType": "ORDER"
    }
  ]
}
```

Use `response.orders`. If an order was analyzed, items may also include `sentiment`, `sentimentScore`, and `keyPhrases`.

### Get one order

| | |
|---|---|
| Method | `GET` |
| Path | `/orders/{orderId}` |
| Body | none |
| Success | `200` — same object as create (plus analyze fields if present) |
| Missing | `404` `{"error": "Order not found"}` |

### Update order

| | |
|---|---|
| Method | `PUT` |
| Path | `/orders/{orderId}` |
| Body | `{"description": "Office chairs x4 — rush", "price": 219.90}` |
| Success | `200` — updated item; `lastModified` changes; `createdAt` does not |
| Missing | `404` |

### Delete order

| | |
|---|---|
| Method | `DELETE` |
| Path | `/orders/{orderId}` |
| Body | none |
| Success | `200` as soon as DynamoDB delete succeeds |

```json
{
  "ok": true,
  "orderId": "a3c1e8f2-9b44-4d21-8f0a-11b22c33d44e",
  "message": "Order deleted"
}
```

Email and S3 TXT backup happen **after** this response (Streams + SNS). Do not wait for them in the UI.

---

## Notifications

SNS emails **only on delete**, not on create or update. The user must click the AWS confirmation link once; until then they get no mail.

### Subscribe

| | |
|---|---|
| Method | `POST` |
| Path | `/notifications/subscribe` |
| Body | `{"email": "student@example.com"}` |
| Success | `200` |

```json
{
  "ok": true,
  "email": "student@example.com",
  "subscriptionArn": "pending confirmation",
  "message": "Check your inbox and confirm the SNS subscription. Notifications start only after you click the AWS confirmation link."
}
```

Show `message` as-is.

### Unsubscribe

| | |
|---|---|
| Method | `POST` |
| Path | `/notifications/unsubscribe` |
| Body | `{"email": "student@example.com"}` |
| Success | `200` `{"ok": true, "email": "...", "message": "Unsubscribed"}` |
| Pending SNS confirm | `409` — cannot unsubscribe until they confirm or ignore the mail |

This is **POST**, not DELETE.

---

## Report and analyze

### Deleted-orders PDF

| | |
|---|---|
| Method | `GET` |
| Path | `/reports/deleted-orders` |
| Body | none |
| Success | `200` `{"url": "<presigned S3 GET URL>"}` |

Open `url` in the browser / download. Do **not** use `/orders/deleted/report` — `{orderId}` would capture `deleted`.

### Analyze order (Comprehend)

| | |
|---|---|
| Method | `POST` |
| Path | `/orders/{orderId}/analyze` |
| Body | empty / omit |
| Success | `200` |

```json
{
  "orderId": "a3c1e8f2-9b44-4d21-8f0a-11b22c33d44e",
  "sentiment": "NEGATIVE",
  "sentimentScore": {
    "Negative": 0.91,
    "Positive": 0.02,
    "Neutral": 0.06,
    "Mixed": 0.01
  },
  "keyPhrases": ["damaged packaging", "late delivery"]
}
```

Must be a visible per-order button in the UI. Persist on the item, so later `GET` still shows the badge.

---

## Client checklist vs this contract

| Operation | Path | Frontend today |
|---|---|---|
| Create | `POST /orders` | calls `/api/orders` — drop `/api` |
| List | `GET /orders` | calls `/api/orders` — drop `/api`; render `response.orders` |
| Get one | `GET /orders/{id}` | not built yet |
| Update | `PUT /orders/{id}` | not built yet |
| Delete | `DELETE /orders/{id}` | service exists with `/api` prefix; no UI yet |
| Subscribe | `POST /notifications/subscribe` | drop `/api` |
| Unsubscribe | `POST /notifications/unsubscribe` | drop `/api`; change `DELETE` → `POST` |
| PDF | `GET /reports/deleted-orders` | not built yet |
| Analyze | `POST /orders/{id}/analyze` | not built yet |

Copy text: notification UI should say emails fire on **delete**, not on create/change.
