from __future__ import annotations

from typing import Any

import requests

from settings import REQUEST_TIMEOUT_SECONDS, USER_AGENT


class CollectionRequestError(RuntimeError):
    """Raised when a collector cannot download or read a source."""


def _request_headers() -> dict[str, str]:
    return {
        "User-Agent": USER_AGENT,
        "Accept": (
            "application/json, application/xml, text/xml, "
            "text/html, application/rss+xml, */*"
        ),
    }


def get_response(
    url: str,
    *,
    params: dict[str, Any] | None = None,
) -> requests.Response:
    """
    Download a source safely and return the response.

    The timeout prevents the program from waiting indefinitely.
    The response is checked so HTTP errors are reported clearly.
    """

    try:
        response = requests.get(
            url,
            params=params,
            headers=_request_headers(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        response.raise_for_status()
        return response

    except requests.Timeout as exc:
        raise CollectionRequestError(
            f"Request timed out after {REQUEST_TIMEOUT_SECONDS} seconds: {url}"
        ) from exc

    except requests.ConnectionError as exc:
        raise CollectionRequestError(
            f"Could not connect to source: {url}"
        ) from exc

    except requests.HTTPError as exc:
        status_code = (
            exc.response.status_code
            if exc.response is not None
            else "unknown"
        )

        raise CollectionRequestError(
            f"Source returned HTTP {status_code}: {url}"
        ) from exc

    except requests.RequestException as exc:
        raise CollectionRequestError(
            f"Request failed for source: {url}. Error: {exc}"
        ) from exc


def get_text(
    url: str,
    *,
    params: dict[str, Any] | None = None,
) -> str:
    """
    Download a source and return its text content.
    """

    response = get_response(url, params=params)

    if not response.encoding:
        response.encoding = response.apparent_encoding or "utf-8"

    return response.text


def get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any] | list[Any]:
    """
    Download a source and return decoded JSON.
    """

    response = get_response(url, params=params)

    try:
        return response.json()

    except ValueError as exc:
        raise CollectionRequestError(
            f"Source did not return valid JSON: {url}"
        ) from exc