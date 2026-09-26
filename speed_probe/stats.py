"""Pure statistics core: no I/O, no network, trivially unit-testable."""

from __future__ import annotations

from dataclasses import dataclass

BYTES_IN_MIB = 1024 * 1024


@dataclass(frozen=True)
class Sample:
    """One successful download measurement."""

    bytes_downloaded: int
    seconds_elapsed: float


@dataclass(frozen=True)
class Summary:
    """Aggregated result of a probe run."""

    samples: tuple[Sample, ...]
    failed: int
    last_error: str | None = None

    @property
    def total_bytes(self) -> int:
        """Sum of payload bytes over successful samples."""
        return sum(s.bytes_downloaded for s in self.samples)

    @property
    def total_seconds(self) -> float:
        """Sum of download times over successful samples."""
        return sum(s.seconds_elapsed for s in self.samples)

    @property
    def avg_seconds(self) -> float:
        """Mean response time; 0.0 when nothing succeeded."""
        if not self.samples:
            return 0.0
        return self.total_seconds / len(self.samples)

    @property
    def throughput_mib_per_sec(self) -> float:
        """Throughput = total payload / total download time, in MiB/s."""
        if self.total_seconds <= 0:
            return 0.0
        return self.total_bytes / self.total_seconds / BYTES_IN_MIB
