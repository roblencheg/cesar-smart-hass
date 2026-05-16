#!/usr/bin/env python3
"""OAuth probe script — mirrors integration's token request for debugging.

Usage:
    CESAR_SMART_USERNAME="+7..." CESAR_SMART_PASSWORD="..." python scripts/oauth_probe.py

Environment:
    CESAR_SMART_USERNAME  — Cesar Smart account phone/email
    CESAR_SMART_PASSWORD  — Cesar Smart account password

Output (sanitized — no tokens, passwords, or Basic header):
    status: 200
    ok: true
    has_access_token: true
    has_refresh_token: true
    expires_in: 119
    error: null
    error_description: null
"""

import asyncio
import base64
import os
import sys

# Public OAuth mobile client credentials — same as const.py
CLIENT_ID = "ma_cesar_key"
CLIENT_SECRET = "Kkl3Vh76Bn4sT98p"
OAUTH_API_URL = "https://tw-sso-authorization-server.csat.ru/tw-sso-authorization-server/"

GRANT_DATA = {
    "grant_type": "password",
    "device_id": "oauth_probe",
    "scope": "all",
}


async def probe() -> None:
    username = os.environ.get("CESAR_SMART_USERNAME")
    password = os.environ.get("CESAR_SMART_PASSWORD")

    if not username or not password:
        print("Usage: CESAR_SMART_USERNAME='...' CESAR_SMART_PASSWORD='...' python scripts/oauth_probe.py")
        sys.exit(1)

    basic = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")).decode("ascii")
    headers = {
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json;charset=UTF-8",
        "User-Agent": "CesarSmart/3.9 HomeAssistant",
    }
    data = {
        **GRANT_DATA,
        "username": username,
        "password": password,
    }

    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.post(
            OAUTH_API_URL.rstrip("/") + "/oauth/token",
            data=data,
            headers=headers,
        ) as resp:
            status = resp.status
            body = await resp.json()

    print(f"status: {status}")
    print(f"ok: {status == 200}")
    if status == 200:
        print(f"has_access_token: {bool(body.get('access_token'))}")
        print(f"has_refresh_token: {bool(body.get('refresh_token'))}")
        print(f"expires_in: {body.get('expires_in')}")
    print(f"error: {body.get('error')}")
    print(f"error_description: {body.get('error_description')}")


if __name__ == "__main__":
    asyncio.run(probe())
