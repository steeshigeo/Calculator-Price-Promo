#!/usr/bin/env python3
"""Download Calculator Promo.xlsx from Google Drive using a service account.

GitHub Actions inputs (environment variables):
  GOOGLE_SERVICE_ACCOUNT_JSON_BASE64  Base64-encoded service-account JSON
  GOOGLE_DRIVE_FILE_ID                 Google Drive file ID for the XLSX
  DOWNLOAD_PATH                        Output path (default: Calculator Promo.xlsx)

The Google Drive file must be shared with the service account's email address
with at least Viewer permission.
"""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

DRIVE_API = "https://www.googleapis.com/drive/v3"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def load_service_account_credentials():
    raw_b64 = required("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64")
    try:
        raw_json = base64.b64decode(raw_b64).decode("utf-8")
        info = json.loads(raw_json)
    except Exception as exc:
        raise SystemExit(f"Invalid GOOGLE_SERVICE_ACCOUNT_JSON_BASE64: {exc}") from exc

    if info.get("type") != "service_account":
        raise SystemExit("The supplied Google credential is not a service-account JSON file.")

    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    creds.refresh(Request())
    return creds


def download() -> Path:
    file_id = required("GOOGLE_DRIVE_FILE_ID")
    output = Path(os.getenv("DOWNLOAD_PATH", "Calculator Promo.xlsx"))
    output.parent.mkdir(parents=True, exist_ok=True)

    creds = load_service_account_credentials()
    headers = {"Authorization": f"Bearer {creds.token}"}

    # First read metadata so errors are easier to diagnose.
    meta_url = f"{DRIVE_API}/files/{file_id}"
    meta = requests.get(
        meta_url,
        headers=headers,
        params={"fields": "id,name,mimeType,size,modifiedTime"},
        timeout=60,
    )
    if not meta.ok:
        raise SystemExit(
            f"Google Drive metadata request failed ({meta.status_code}): {meta.text[:1000]}"
        )

    metadata = meta.json()
    print(
        "Google Drive file:",
        metadata.get("name"),
        "| MIME:", metadata.get("mimeType"),
        "| modified:", metadata.get("modifiedTime"),
    )

    if metadata.get("mimeType") != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        raise SystemExit(
            "The Drive file is not an XLSX blob. Use an uploaded .xlsx file, not a native Google Sheets file."
        )

    content_url = f"{DRIVE_API}/files/{file_id}"
    resp = requests.get(
        content_url,
        headers=headers,
        params={"alt": "media"},
        timeout=180,
    )
    if not resp.ok:
        raise SystemExit(
            f"Google Drive download failed ({resp.status_code}): {resp.text[:1000]}"
        )

    content = resp.content
    if len(content) < 1000 or content[:2] != b"PK":
        raise SystemExit(
            "Downloaded content does not look like a valid .xlsx file. "
            f"content-type={resp.headers.get('content-type')!r}, size={len(content)} bytes"
        )

    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.write_bytes(content)
    tmp.replace(output)

    print(f"Downloaded: {output} ({len(content):,} bytes)")
    return output


if __name__ == "__main__":
    try:
        download()
    except requests.RequestException as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        raise SystemExit(2)
