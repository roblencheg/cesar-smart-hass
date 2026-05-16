from __future__ import annotations

import asyncio
import json
import logging

import aiohttp

from .const import WS_RECONNECT_DELAYS, WS_URL

_LOGGER = logging.getLogger(__name__)

STOMP_CONNECT = "CONNECT\naccept-version:1.1,1.2\nheart-beat:10000,10000\n\n\x00"
STOMP_SUBSCRIBE_EVENT = "SUBSCRIBE\nid:sub-event\ndestination:/user/queue/event\nack:auto\n\n\x00"
STOMP_SUBSCRIBE_LOCATION = (
    "SUBSCRIBE\nid:sub-location\ndestination:/user/queue/location\nack:auto\n\n\x00"
)

LOCATION_UPPER_MAP = {
    "LATITUDE": "latitude",
    "LONGITUDE": "longitude",
    "COURSE": "course",
    "SPEED": "speedKm",
    "DATE_MILLI": "date",
    "DATE": "date",
    "UNIT_ID": "unitId",
    "SPEEDKM": "speedKm",
}

EVENT_PUSH_TYPES = {
    "STATUS_CHANGED",
    "LOCATION_CHANGED",
    "COMMAND_STATUS_CHANGED",
    "COMMAND_LOG_CHANGED",
    "SIM_STATUS_CHANGED",
    "SECURITY_OBJECT_BALANCE_CHANGED",
    "AUTOSTART_SCHEDULE_CHANGED",
}


class CesarSmartWebSocket:
    def __init__(self, hass, access_token: str, device_id: str, coordinator) -> None:
        self._hass = hass
        self._access_token = access_token
        self._device_id = device_id
        self._coordinator = coordinator
        self._session: aiohttp.ClientSession | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._task: asyncio.Task | None = None
        self._should_stop = False

    async def start(self):
        self._should_stop = False
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._should_stop = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._ws:
            await self._ws.close()
            self._ws = None
        if self._session:
            await self._session.close()
            self._session = None

    async def _run(self):
        attempt = 0
        while not self._should_stop:
            try:
                await self._connect()
                attempt = 0
                await self._listen()
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.warning("WebSocket error: %s", err)
                if not self._should_stop:
                    delay = WS_RECONNECT_DELAYS[min(attempt, len(WS_RECONNECT_DELAYS) - 1)]
                    _LOGGER.info("WebSocket reconnecting in %ss", delay)
                    attempt += 1
                    await asyncio.sleep(delay)

    async def _connect(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        url = f"{WS_URL}?access_token={self._access_token}&device_id={self._device_id}"
        self._ws = await self._session.ws_connect(url, heartbeat=30)
        await self._ws.send_str(STOMP_CONNECT)
        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if "CONNECTED" in msg.data:
                    _LOGGER.debug("STOMP connected")
                    await self._ws.send_str(STOMP_SUBSCRIBE_EVENT)
                    await self._ws.send_str(STOMP_SUBSCRIBE_LOCATION)
                    _LOGGER.debug("STOMP subscriptions sent")
                    break
                elif "ERROR" in msg.data:
                    _LOGGER.error("STOMP connect error: %s", msg.data)
                    raise ConnectionError("STOMP connection failed")
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                raise ConnectionError("WebSocket closed during connect")
            elif msg.type == aiohttp.WSMsgType.ERROR:
                raise ConnectionError("WebSocket error during connect")

    async def _listen(self):
        async for msg in self._ws:
            if self._should_stop:
                break
            if msg.type == aiohttp.WSMsgType.TEXT:
                await self._handle_message(msg.data)
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                _LOGGER.debug("WebSocket closed")
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                _LOGGER.error("WebSocket error: %s", self._ws.exception())
                break

    async def _handle_message(self, data: str):
        if data == "\x00":
            return
        if data.startswith("CONNECTED"):
            return
        if data.startswith("RECEIPT"):
            return
        if data.startswith("\n"):
            return

        headers_raw, _, body = data.partition("\n\n")
        body = body.rstrip("\x00")

        destination = ""
        for line in headers_raw.split("\n"):
            if line.lower().startswith("destination:"):
                destination = line.split(":", 1)[1].strip()
                break

        if not destination or not body:
            return

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            _LOGGER.warning("WS invalid JSON: %s", body[:200])
            return

        if destination == "/user/queue/event":
            await self._handle_event(payload)
        elif destination == "/user/queue/location":
            await self._handle_location(payload)

    async def _handle_event(self, payload: dict):
        push_type = payload.get("PUSH_TYPE")
        if not push_type:
            return
        _LOGGER.debug("WS event PUSH_TYPE=%s", push_type)

        if push_type == "STATUS_CHANGED":
            await self._coordinator.async_update_ws_statuses()

        elif push_type == "LOCATION_CHANGED":
            loc_data = _normalize_ws_location(payload)
            if loc_data:
                await self._coordinator.async_update_ws_location(loc_data)

        elif push_type == "SIM_STATUS_CHANGED":
            await self._coordinator.async_update_ws_statuses()

        elif push_type == "SECURITY_OBJECT_BALANCE_CHANGED":
            await self._coordinator.async_update_ws_statuses()

        elif push_type == "COMMAND_STATUS_CHANGED":
            _LOGGER.debug("Command status change ignored (read-only)")

        elif push_type == "COMMAND_LOG_CHANGED":
            _LOGGER.debug("Command log change ignored (read-only)")

        elif push_type == "AUTOSTART_SCHEDULE_CHANGED":
            _LOGGER.debug("Autostart schedule change ignored (read-only)")

    async def _handle_location(self, payload: dict):
        loc_data = payload.get("data") or payload.get("location") or payload
        if isinstance(loc_data, dict):
            loc_data = _normalize_ws_location(loc_data)
            if loc_data and "latitude" in loc_data:
                await self._coordinator.async_update_ws_location(loc_data)

    def update_token(self, access_token: str):
        self._access_token = access_token


def _normalize_ws_location(data: dict) -> dict:
    result = {}
    for key, val in data.items():
        upper = key.upper()
        if upper in LOCATION_UPPER_MAP:
            result[LOCATION_UPPER_MAP[upper]] = val
        elif key.isupper() or key[0].isupper():
            result[key.lower()] = val
        else:
            result[key] = val
    return result
