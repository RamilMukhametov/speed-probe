# speed-probe

![CI](https://github.com/RamilMukhametov/speed-probe/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

A command-line download throughput probe: N sequential HTTP requests to a given
URL, reporting average response time, total payload, and throughput in MB/s.

Test assignment for the Python Developer (AD Robot) position at Eto Legko.

## Features

- Sequential requests with a per-request timeout (10 by default, per the assignment)
- Failed requests are counted separately and never skew the statistics
- Configurable address family: auto / ipv4 / ipv6
- CI- and script-friendly exit codes: 0 on success, 1 if every request failed
- Pure, I/O-free statistics core covered by unit tests

## Quick start

Requires Python 3.10+.

    git clone https://github.com/RamilMukhametov/speed-probe.git && cd speed-probe
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements-dev.txt

    # heavy image per the assignment (stable against repeated probes)
    python -m speed_probe https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg

After `pip install .`, the short `speed-probe <url>` command is also available.

## Example output

    Target              : https://eoimages.gsfc.nasa.gov/.../world.topo.bathy.200412.3x5400x2700.jpg
    Address family      : auto
    Successful requests : 10 (failed: 0)
    Avg response time   : 8.238 s
    Total downloaded    : 24.48 MiB
    Throughput          : 0.30 MB/s

## CLI reference

| Argument | Default | Description |
|---|---|---|
| `url` | - | Address to probe (image, archive, any file) |
| `-n, --attempts` | 10 | Number of sequential requests |
| `-t, --timeout` | 15 | Per-request timeout in seconds |
| `--family` | auto | Address family: auto (system choice), ipv4, ipv6 |

Exit codes: 0 - at least one successful request; 1 - all requests failed;
2 - invalid arguments.

## Assignment checklist

| Requirement | Implementation |
|---|---|
| Accept a target address | positional `url` argument |
| 10 sequential requests | `probe(attempts=10)`, plain loop, no parallelism |
| Wait for each response | full body read (`response.content`) |
| Average request time | `avg_seconds` = total time / successful count |
| Downloaded volume | `total_bytes` = sum of payload lengths |
| Speed in MB/s | total bytes / total time / 1024 squared, printed as `Throughput` |
| GitHub repo with instructions | this repository, see Quick start and Development |

## How the measurement works

- Throughput = total payload / total download time (not the mean of per-request
  speeds), so short failed attempts cannot skew the metric.
- Only successful requests contribute to the statistics; failures are tracked
  by the `failed` counter.
- The tool measures single-stream throughput to a specific host, including
  per-request overhead (DNS, TCP, TLS) - the same pattern a backend uses when
  calling external APIs. It is not a multi-stream channel benchmark like
  speedtest.

## Project layout

    speed-probe/
    |-- speed_probe/
    |   |-- cli.py        # arguments, report rendering, exit codes
    |   |-- measure.py    # network layer: request and timing
    |   |-- stats.py      # I/O-free math
    |   `-- __main__.py   # python -m speed_probe entry point
    |-- tests/            # unit tests, network fully mocked
    |-- .github/workflows/ci.yml
    `-- pyproject.toml    # package + pytest and pylint config

## Development

    pip install -r requirements-dev.txt
    pytest -v                                  # unit tests
    pylint speed_probe tests --fail-under=10   # quality gate

CI (GitHub Actions) runs both commands on every push and pull request.

## Design decisions

- "Speed in MB/s": computed in MiB/s (1024 squared), the convention used by most
  utilities; the formula is fixed above.
- Failed requests are excluded from averages and throughput and counted
  separately - otherwise a single 500 would distort the report.
- "Heavy image": the tool accepts any URL; examples cover both images and
  archive files.
- IPv4/IPv6: auto by default (system resolution - works on IPv4-only,
  IPv6-only, and dual-stack hosts); explicit ipv4/ipv6 for diagnostics.
- 10 sequential requests: exactly per the assignment, no multithreading.
- Named probe, not speedtest: a speedtest is a multi-stream channel benchmark;
  a probe measures a single connection to a specific host.
- A browser-like User-Agent is sent by default: public CDNs reject the stock
  python-requests UA with HTTP 403, which would break the tool on arbitrary URLs.

## Author

Ramil Mukhametov | github.com/RamilMukhametov
