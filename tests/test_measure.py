# pylint: disable=missing-function-docstring,unused-argument  # test names are self-documenting
"""Tests for network probing and CLI, with the network fully mocked."""

import socket

import requests
import urllib3.util.connection as uc

from speed_probe import measure
from speed_probe.cli import main


class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, content: bytes, status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code
        self.ok = 200 <= status_code < 300


def test_probe_counts_success_and_failure(monkeypatch) -> None:
    payload = b"x" * 2048
    queue = [FakeResponse(payload)] * 3 + [FakeResponse(b"", status_code=500)]

    def fake_get(*_, **__):
        return queue.pop(0)

    monkeypatch.setattr(measure.requests, "get", fake_get)
    summary = measure.probe("http://example.invalid/file.bin", attempts=4)
    assert len(summary.samples) == 3
    assert summary.failed == 1
    assert summary.total_bytes == 6144


def test_probe_survives_network_errors(monkeypatch) -> None:
    def boom(*_, **__):
        raise requests.ConnectionError("no route to host")

    monkeypatch.setattr(measure.requests, "get", boom)
    summary = measure.probe("http://example.invalid/file.bin", attempts=2)
    assert not summary.samples
    assert summary.failed == 2
    assert summary.last_error == "no route to host"


def test_cli_prints_report_and_returns_zero(monkeypatch, capsys) -> None:
    payload = b"y" * (1024 * 1024)

    def fake_get(*_, **__):
        return FakeResponse(payload)

    monkeypatch.setattr(measure.requests, "get", fake_get)
    code = main(["http://example.invalid/1mb.bin", "--attempts", "2"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Throughput" in out
    assert "failed: 0" in out


def test_cli_returns_one_when_all_failed(monkeypatch, capsys) -> None:
    def boom(*_, **__):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(measure.requests, "get", boom)
    code = main(["http://example.invalid/1mb.bin", "--attempts", "2"])
    assert code == 1


def test_family_pin_and_restore(monkeypatch) -> None:
    original = uc.allowed_gai_family

    def fake_get(*_, **__):
        return FakeResponse(b"z")

    monkeypatch.setattr(measure.requests, "get", fake_get)
    measure.probe("http://example.invalid/f.bin", attempts=1, family="ipv4")
    assert uc.allowed_gai_family() == socket.AF_INET
    measure.probe("http://example.invalid/f.bin", attempts=1, family="auto")
    assert uc.allowed_gai_family is original
