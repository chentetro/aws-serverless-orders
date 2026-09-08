"""POST /orders/extract — Amazon Textract FORMS → description + price.

Same Analyze document + Forms view you used in the Textract console.
Zip this folder together with ../common.py (handler: lambda_function.lambda_handler).
Use LabRole. API Gateway: POST /orders/extract, Lambda proxy, CORS.
"""

import base64
import re

import boto3

from common import error, ok, parse_json_body

textract = boto3.client("textract")
PRICE_RE = re.compile(r"(\d+(?:\.\d+)?)")
MAX_BYTES = 4_500_000


def _block_text(block, block_map):
    parts = []
    for rel in block.get("Relationships") or []:
        if rel.get("Type") != "CHILD":
            continue
        for child_id in rel.get("Ids") or []:
            child = block_map.get(child_id) or {}
            if child.get("BlockType") == "WORD":
                parts.append(child.get("Text") or "")
            elif child.get("BlockType") == "SELECTION_ELEMENT":
                if child.get("SelectionStatus") == "SELECTED":
                    parts.append("[X]")
    return " ".join(p for p in parts if p).strip()


def _form_pairs(blocks):
    block_map = {b["Id"]: b for b in blocks if "Id" in b}
    pairs = []
    for block in blocks:
        if block.get("BlockType") != "KEY_VALUE_SET":
            continue
        if "KEY" not in (block.get("EntityTypes") or []):
            continue
        key = _block_text(block, block_map)
        value = ""
        for rel in block.get("Relationships") or []:
            if rel.get("Type") != "VALUE":
                continue
            for value_id in rel.get("Ids") or []:
                value_block = block_map.get(value_id)
                if value_block:
                    value = _block_text(value_block, block_map)
        if key or value:
            pairs.append({"key": key, "value": value})
    return pairs


def parse_order_from_blocks(blocks):
    """Turn Textract blocks into {description, price, forms, rawText}."""
    pairs = _form_pairs(blocks)
    lines = [
        b.get("Text") or ""
        for b in blocks
        if b.get("BlockType") == "LINE" and b.get("Text")
    ]
    raw_text = " ".join(lines).strip()

    price = None
    price_key = None
    for pair in pairs:
        blob = f"{pair['key']} {pair['value']}".lower()
        if "price" in blob or "$" in pair["key"] or "$" in pair["value"]:
            match = PRICE_RE.search(pair["value"] or pair["key"] or "")
            if match:
                price = float(match.group(1))
                price_key = pair["key"]
                break

    if price is None:
        match = PRICE_RE.search(raw_text.replace(",", ""))
        if match:
            price = float(match.group(1))

    desc_parts = []
    for pair in pairs:
        if pair["key"] == price_key:
            continue
        piece = " ".join(p for p in (pair["key"], pair["value"]) if p).strip()
        if piece and "price" not in piece.lower():
            desc_parts.append(piece)

    description = " ".join(desc_parts).strip() or re.sub(
        r"price\s*:?\s*\d+(?:\.\d+)?\.?",
        "",
        raw_text,
        flags=re.IGNORECASE,
    ).strip(" .")

    return {
        "description": description,
        "price": price,
        "forms": pairs,
        "rawText": raw_text,
        "service": "Amazon Textract",
    }


def _document_bytes(body):
    raw = body.get("imageBase64") or body.get("documentBase64") or ""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("imageBase64 is required")
    raw = raw.strip()
    if "," in raw and raw.lower().startswith("data:"):
        raw = raw.split(",", 1)[1]
    data = base64.b64decode(raw)
    if not data:
        raise ValueError("file is empty")
    if len(data) > MAX_BYTES:
        raise ValueError("file is too large (keep the PNG under about 4 MB)")
    return data


def lambda_handler(event, context):
    method = (event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method") or "").upper()
    if method == "OPTIONS":
        return ok({"ok": True})

    try:
        body = parse_json_body(event)
        document = _document_bytes(body)
    except (TypeError, ValueError) as exc:
        return error(400, str(exc) or "Body must be JSON with imageBase64")

    result = textract.analyze_document(
        Document={"Bytes": document},
        FeatureTypes=["FORMS"],
    )
    parsed = parse_order_from_blocks(result.get("Blocks") or [])

    if not parsed.get("description") and parsed.get("price") is None:
        return error(422, "Textract did not find a description or price in this file")

    return ok(parsed)
