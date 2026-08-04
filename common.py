from __future__ import annotations

import requests
from settings import REQUEST_TIMEOUT_SECONDS, USER_AGENT


def get_json(url: str, params: dict | None = None) -> dict:
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.json()


def get_text(url: str, params: dict | None = None) -> str:
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.text
