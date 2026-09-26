"""HTTP download probing: the only module that touches the network."""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass

import requests
import urllib3.util.connection

from .stats import Sample, Summary

DEFAULT_TIMEOUT_SECONDS = 15.0
# Remember the platform default so we can restore it after a pinned run.
SYSTEM_GAI_FAMILY = urllib3.util.connection.allowed_gai_family

# Many public CDNs reject the default python-requests User-Agent with HTTP 403.
# A browser-like UA keeps the probe working against arbitrary public URLs.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 speed-probe/1.0"
    )
}


def apply_family(family: str) -> None:
    """Pin the address family for urllib3, or restore system behaviour."""
    if family == "ipv4":
        urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET
    elif family == "ipv6":
        urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET6
    else:
        urllib3.util.connection.allowed_gai_family = SYSTEM_GAI_FAMILY


@dataclass(frozen=True)
class FetchResult:
    """Outcome of a single download attempt."""

    ok: bool
    sample: Sample | None
    error: str | None


def fetch_once(
    url: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    family: str = "auto",
) -> FetchResult:
    """Download url once, measuring payload size and wall time."""
    apply_family(family)
    started = time.perf_counter()
    try:
        response = requests.get(url, timeout=timeout, headers=DEFAULT_HEADERS)
        payload = response.content
        elapsed = time.perf_counter() - started
    except requests.RequestException as exc:
        return FetchResult(ok=False, sample=None, error=str(exc))
    if not response.ok:
        return FetchResult(ok=False, sample=None, error=f"HTTP {response.status_code}")
    return FetchResult(ok=True, sample=Sample(len(payload), elapsed), error=None)


def probe(
    url: str,
    attempts: int = 10,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    family: str = "auto",
) -> Summary:
    """Run attempts sequential downloads and aggregate statistics."""
    samples: list[Sample] = []
    failed = 0
    last_error: str | None = None
    for _ in range(attempts):
        result = fetch_once(url, timeout, family)
        if result.ok and result.sample is not None:
            samples.append(result.sample)
        else:
            failed += 1
            last_error = result.error
    return Summary(samples=tuple(samples), failed=failed, last_error=last_error)
