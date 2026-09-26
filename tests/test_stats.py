# pylint: disable=missing-function-docstring  # test names are self-documenting
"""Unit tests for the statistics core."""

from speed_probe.stats import Sample, Summary


def test_summary_aggregates_samples() -> None:
    summary = Summary(samples=(Sample(1000, 1.0), Sample(3000, 3.0)), failed=1)
    assert summary.total_bytes == 4000
    assert summary.total_seconds == 4.0
    assert summary.avg_seconds == 2.0


def test_throughput_in_mib_per_sec() -> None:
    summary = Summary(samples=(Sample(1024 * 1024, 2.0),), failed=0)
    assert summary.throughput_mib_per_sec == 0.5


def test_empty_summary_is_safe() -> None:
    summary = Summary(samples=(), failed=3)
    assert summary.avg_seconds == 0.0
    assert summary.throughput_mib_per_sec == 0.0
