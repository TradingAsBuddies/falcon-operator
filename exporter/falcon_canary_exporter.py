#!/usr/bin/env python3
"""
Falcon Canary Exporter - Prometheus exporter for the Falcon trading dashboard.

Successor to ``apps/falcon/canary.py``. Differences that matter:

* The target is configuration, not a constant. ``FALCON_CANARY_TARGET`` selects
  the dashboard base URL; it defaults to the service name inside the container
  network (``http://falcon-trader:5000``). The old canary hardcoded a retired
  host (192.168.1.162) and could never be pointed anywhere else.
* TLS verification is never disabled. ``canary.py`` set ``CERT_NONE``; here a
  private CA is handled by ``FALCON_CANARY_CA_BUNDLE``, not by trusting
  anything that answers.
* It observes, it does not act. No ``systemctl restart``, no root, no repairs.
  Prometheus scrapes the metrics and Grafana decides what is worth waking
  someone up for.
* HTTP 200 is not health. Every probe with a known schema also has its JSON
  shape asserted, so a dashboard serving ``200 {"error": ...}`` reads as down.

Endpoints probed: /health, /api/account, /api/positions, /api/trades,
/api/recommendations, /api/sentinels.

Metrics exported (all gauges):

    falcon_probe_up{endpoint}                 1 when the endpoint answered 200
    falcon_probe_latency_seconds{endpoint}    request duration in seconds
    falcon_probe_shape_ok{endpoint}           1 when the JSON matched the schema
    falcon_sentinel_pass{name}                1 per passing sentinel
    falcon_sentinels_total / _passed          sentinel run totals
    falcon_position_stale{symbol}             1 when currentPrice == avgPrice
    falcon_positions_count                    number of open positions
    falcon_canary_scrape_duration_seconds     time to collect one scrape

Environment:

    FALCON_CANARY_TARGET      base URL       (default http://falcon-trader:5000)
    FALCON_API_TOKEN          bearer token   (optional; sent as Authorization)
    FALCON_CANARY_TIMEOUT     per-request seconds (default 10)
    FALCON_CANARY_CA_BUNDLE   CA bundle path for a private CA (optional)
    FALCON_CANARY_PORT        listen port    (default 9107)
    FALCON_CANARY_BIND        listen address (default 0.0.0.0)

Usage:

    python3 falcon_canary_exporter.py             # serve /metrics
    python3 falcon_canary_exporter.py --once      # scrape once, print, exit

Design note: everything above the "I/O" banner is pure. The shape checks and
metric builders take already-parsed JSON and return values, so the whole
analysis layer is testable with no network and no HTTP server.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "ENDPOINTS",
    "DEFAULT_TARGET",
    "ShapeCheck",
    "ProbeResult",
    "Sample",
    "check_account_shape",
    "check_positions_shape",
    "check_sentinels_shape",
    "check_shape",
    "iter_sentinel_results",
    "is_position_stale",
    "position_samples",
    "sentinel_samples",
    "probe_samples",
    "build_samples",
    "render_exposition",
]

DEFAULT_TARGET = "http://falcon-trader:5000"
DEFAULT_PORT = 9107
DEFAULT_TIMEOUT = 10.0

HEALTH = "/health"
ACCOUNT = "/api/account"
POSITIONS = "/api/positions"
TRADES = "/api/trades"
RECOMMENDATIONS = "/api/recommendations"
SENTINELS = "/api/sentinels"

ENDPOINTS: Tuple[str, ...] = (
    HEALTH,
    ACCOUNT,
    POSITIONS,
    TRADES,
    RECOMMENDATIONS,
    SENTINELS,
)

ACCOUNT_FIELDS = ("cash", "initialBalance", "positionsValue", "totalValue")
POSITION_FIELDS = ("avgPrice", "currentPrice", "quantity", "stopLoss", "symbol")
SENTINEL_FIELDS = ("passed", "results", "total")

# Keys a sentinel result may use for its name and its pass/fail verdict. The
# /api/sentinels endpoint is being written in a parallel change; accept the
# plausible spellings rather than hard-failing on a synonym.
_SENTINEL_NAME_KEYS = ("name", "id", "check", "sentinel")
_SENTINEL_PASS_KEYS = ("passed", "pass", "ok", "success", "healthy")


# =============================================================================
# Pure analysis layer - no I/O below this point until the I/O banner
# =============================================================================


@dataclass(frozen=True)
class ShapeCheck:
    """Result of validating one parsed JSON payload against its schema."""

    ok: bool
    errors: Tuple[str, ...] = ()

    def __bool__(self) -> bool:  # pragma: no cover - convenience only
        return self.ok


@dataclass(frozen=True)
class Sample:
    """One Prometheus sample: metric name, ordered labels, value."""

    name: str
    labels: Tuple[Tuple[str, str], ...]
    value: float


@dataclass
class ProbeResult:
    """What one HTTP probe observed. Built by the I/O layer, consumed pure."""

    endpoint: str
    up: bool
    latency_seconds: float
    status_code: Optional[int] = None
    payload: Any = None
    error: Optional[str] = None


def _is_number(value: Any) -> bool:
    """True for JSON numbers. bool is a Python int but is not a price."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check_account_shape(payload: Any) -> ShapeCheck:
    """/api/account must be an object of four numeric balances."""
    if not isinstance(payload, dict):
        return ShapeCheck(False, (f"expected object, got {type(payload).__name__}",))

    errors: List[str] = []
    for key in ACCOUNT_FIELDS:
        if key not in payload:
            errors.append(f"missing field: {key}")
        elif not _is_number(payload[key]):
            errors.append(f"field {key} is not numeric: {payload[key]!r}")
    return ShapeCheck(not errors, tuple(errors))


def check_positions_shape(payload: Any) -> ShapeCheck:
    """/api/positions must be a list of position objects.

    An empty list is valid - flat is a legitimate state. ``stopLoss`` must be
    present but may be null, which is what the dashboard returns when no stop
    has been recorded for the symbol yet.
    """
    if not isinstance(payload, list):
        return ShapeCheck(False, (f"expected list, got {type(payload).__name__}",))

    errors: List[str] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            errors.append(f"position[{index}] is not an object")
            continue
        for key in POSITION_FIELDS:
            if key not in item:
                errors.append(f"position[{index}] missing field: {key}")
        symbol = item.get("symbol")
        if "symbol" in item and not isinstance(symbol, str):
            errors.append(f"position[{index}] symbol is not a string: {symbol!r}")
        for key in ("avgPrice", "currentPrice", "quantity"):
            if key in item and not _is_number(item[key]):
                errors.append(f"position[{index}] {key} is not numeric: {item[key]!r}")
        if "stopLoss" in item and item["stopLoss"] is not None:
            if not _is_number(item["stopLoss"]):
                errors.append(
                    f"position[{index}] stopLoss is neither null nor numeric: "
                    f"{item['stopLoss']!r}"
                )
    return ShapeCheck(not errors, tuple(errors))


def check_sentinels_shape(payload: Any) -> ShapeCheck:
    """/api/sentinels must be {passed, results, total} with numeric counters."""
    if not isinstance(payload, dict):
        return ShapeCheck(False, (f"expected object, got {type(payload).__name__}",))

    errors: List[str] = []
    for key in SENTINEL_FIELDS:
        if key not in payload:
            errors.append(f"missing field: {key}")
    for key in ("passed", "total"):
        if key in payload and not _is_number(payload[key]):
            errors.append(f"field {key} is not numeric: {payload[key]!r}")
    if "results" in payload and not isinstance(payload["results"], (list, dict)):
        errors.append(
            f"field results is neither list nor object: {type(payload['results']).__name__}"
        )
    return ShapeCheck(not errors, tuple(errors))


# Endpoints without an entry are probed for reachability and valid JSON only.
SHAPE_CHECKS: Dict[str, Callable[[Any], ShapeCheck]] = {
    ACCOUNT: check_account_shape,
    POSITIONS: check_positions_shape,
    SENTINELS: check_sentinels_shape,
}


def check_shape(endpoint: str, payload: Any) -> ShapeCheck:
    """Apply the schema registered for ``endpoint``, if any."""
    checker = SHAPE_CHECKS.get(endpoint)
    if checker is None:
        return ShapeCheck(True)
    return checker(payload)


def _coerce_pass(value: Any) -> Optional[bool]:
    """Read a sentinel verdict from bool, number, or the usual strings."""
    if isinstance(value, bool):
        return value
    if _is_number(value):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("pass", "passed", "true", "ok", "yes", "healthy"):
            return True
        if lowered in ("fail", "failed", "false", "error", "no", "unhealthy"):
            return False
    return None


def _result_verdict(entry: Any) -> Optional[bool]:
    if isinstance(entry, dict):
        for key in _SENTINEL_PASS_KEYS:
            if key in entry:
                verdict = _coerce_pass(entry[key])
                if verdict is not None:
                    return verdict
        if "status" in entry:
            return _coerce_pass(entry["status"])
        return None
    return _coerce_pass(entry)


def iter_sentinel_results(payload: Any) -> List[Tuple[str, bool]]:
    """Flatten ``results`` into ``[(name, passed)]``.

    Handles the list-of-objects form (``[{"name": "x", "passed": true}]``) and
    the mapping form (``{"x": true}`` or ``{"x": {"passed": true}}``). Entries
    whose verdict cannot be read are skipped rather than counted as passing.
    """
    if not isinstance(payload, dict):
        return []
    results = payload.get("results")

    pairs: List[Tuple[str, bool]] = []
    if isinstance(results, list):
        for index, entry in enumerate(results):
            name = None
            if isinstance(entry, dict):
                for key in _SENTINEL_NAME_KEYS:
                    if isinstance(entry.get(key), str):
                        name = entry[key]
                        break
            if name is None:
                name = f"unnamed_{index}"
            verdict = _result_verdict(entry)
            if verdict is not None:
                pairs.append((name, verdict))
    elif isinstance(results, dict):
        for name, entry in results.items():
            verdict = _result_verdict(entry)
            if verdict is not None:
                pairs.append((str(name), verdict))
    return pairs


def is_position_stale(position: Any) -> bool:
    """True when the mark equals the entry price exactly.

    That is the stale-mark bug: the dashboard falls back to ``average_price``
    when it has no live quote for the symbol, so the position silently shows a
    frozen price and a P&L of zero instead of an error.
    """
    if not isinstance(position, dict):
        return False
    current = position.get("currentPrice")
    average = position.get("avgPrice")
    if not (_is_number(current) and _is_number(average)):
        return False
    return float(current) == float(average)


def position_samples(payload: Any) -> List[Sample]:
    """falcon_position_stale{symbol} plus the open-position count."""
    if not isinstance(payload, list):
        return []

    samples: List[Sample] = []
    counted = 0
    for position in payload:
        if not isinstance(position, dict):
            continue
        symbol = position.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            continue
        counted += 1
        samples.append(
            Sample(
                "falcon_position_stale",
                (("symbol", symbol),),
                1.0 if is_position_stale(position) else 0.0,
            )
        )
    samples.append(Sample("falcon_positions_count", (), float(counted)))
    return samples


def sentinel_samples(payload: Any) -> List[Sample]:
    """falcon_sentinel_pass{name} plus the run totals."""
    samples: List[Sample] = [
        Sample("falcon_sentinel_pass", (("name", name),), 1.0 if passed else 0.0)
        for name, passed in iter_sentinel_results(payload)
    ]
    if isinstance(payload, dict):
        if _is_number(payload.get("total")):
            samples.append(Sample("falcon_sentinels_total", (), float(payload["total"])))
        if _is_number(payload.get("passed")):
            samples.append(Sample("falcon_sentinels_passed", (), float(payload["passed"])))
    return samples


def probe_samples(result: ProbeResult) -> List[Sample]:
    """Reachability, latency, and shape verdict for one endpoint."""
    labels = (("endpoint", result.endpoint),)
    shape = check_shape(result.endpoint, result.payload) if result.up else ShapeCheck(False)
    return [
        Sample("falcon_probe_up", labels, 1.0 if result.up else 0.0),
        Sample("falcon_probe_latency_seconds", labels, float(result.latency_seconds)),
        Sample("falcon_probe_shape_ok", labels, 1.0 if shape.ok else 0.0),
    ]


def build_samples(results: Sequence[ProbeResult]) -> List[Sample]:
    """Turn a full round of probes into every sample this exporter publishes."""
    samples: List[Sample] = []
    for result in results:
        samples.extend(probe_samples(result))
    for result in results:
        if not result.up:
            continue
        if result.endpoint == POSITIONS and check_positions_shape(result.payload).ok:
            samples.extend(position_samples(result.payload))
        elif result.endpoint == SENTINELS and check_sentinels_shape(result.payload).ok:
            samples.extend(sentinel_samples(result.payload))
    return samples


METRIC_HELP: Dict[str, str] = {
    "falcon_probe_up": "1 if the endpoint returned HTTP 200, 0 otherwise",
    "falcon_probe_latency_seconds": "Seconds taken by the probe request",
    "falcon_probe_shape_ok": "1 if the JSON response matched the expected schema",
    "falcon_sentinel_pass": "1 if the named sentinel passed, 0 if it failed",
    "falcon_sentinels_total": "Number of sentinels in the last run",
    "falcon_sentinels_passed": "Number of sentinels that passed in the last run",
    "falcon_position_stale": "1 if currentPrice equals avgPrice (stale mark)",
    "falcon_positions_count": "Number of open positions reported by the dashboard",
    "falcon_canary_scrape_duration_seconds": "Seconds taken to collect one scrape",
}


def escape_label_value(value: str) -> str:
    """Escape per the Prometheus text exposition format."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _format_value(value: float) -> str:
    if value != value:  # NaN
        return "NaN"
    if value == float("inf"):
        return "+Inf"
    if value == float("-inf"):
        return "-Inf"
    if float(value).is_integer() and abs(value) < 1e15:
        return str(int(value))
    return repr(float(value))


def render_exposition(samples: Iterable[Sample]) -> str:
    """Render samples as Prometheus text exposition format (all gauges).

    Samples of the same metric are grouped under a single HELP/TYPE header, in
    first-seen order, which is what the text format requires.
    """
    grouped: Dict[str, List[Sample]] = {}
    for sample in samples:
        grouped.setdefault(sample.name, []).append(sample)

    lines: List[str] = []
    for name, group in grouped.items():
        lines.append(f"# HELP {name} {METRIC_HELP.get(name, name)}")
        lines.append(f"# TYPE {name} gauge")
        for sample in group:
            if sample.labels:
                rendered = ",".join(
                    f'{key}="{escape_label_value(str(val))}"' for key, val in sample.labels
                )
                lines.append(f"{name}{{{rendered}}} {_format_value(sample.value)}")
            else:
                lines.append(f"{name} {_format_value(sample.value)}")
    return "\n".join(lines) + "\n"


# =============================================================================
# I/O layer - HTTP probing and the /metrics server
# =============================================================================


@dataclass
class Config:
    target: str = DEFAULT_TARGET
    token: Optional[str] = None
    timeout: float = DEFAULT_TIMEOUT
    verify: Any = True
    endpoints: Tuple[str, ...] = ENDPOINTS
    bind: str = "0.0.0.0"
    port: int = DEFAULT_PORT

    @classmethod
    def from_env(cls, env: Optional[Dict[str, str]] = None) -> "Config":
        env = os.environ if env is None else env
        target = (env.get("FALCON_CANARY_TARGET") or DEFAULT_TARGET).rstrip("/")
        token = env.get("FALCON_API_TOKEN") or None
        try:
            timeout = float(env.get("FALCON_CANARY_TIMEOUT") or DEFAULT_TIMEOUT)
        except ValueError:
            timeout = DEFAULT_TIMEOUT
        try:
            port = int(env.get("FALCON_CANARY_PORT") or DEFAULT_PORT)
        except ValueError:
            port = DEFAULT_PORT
        # A private CA is trusted by pointing at its bundle. Verification is
        # never turned off - that was the canary.py failure mode.
        ca_bundle = env.get("FALCON_CANARY_CA_BUNDLE") or None
        return cls(
            target=target,
            token=token,
            timeout=timeout,
            verify=ca_bundle if ca_bundle else True,
            bind=env.get("FALCON_CANARY_BIND") or "0.0.0.0",
            port=port,
        )


def _require_requests():
    try:
        import requests  # noqa: PLC0415 - optional at import time, required at probe time
    except ImportError as exc:  # pragma: no cover - environment problem
        raise SystemExit(
            "falcon_canary_exporter needs the 'requests' package to probe endpoints"
        ) from exc
    return requests


def build_session(config: Config):
    """A requests.Session carrying the bearer token, if one is configured."""
    requests = _require_requests()
    session = requests.Session()
    session.headers.update({"User-Agent": "falcon-canary-exporter/1.0", "Accept": "application/json"})
    if config.token:
        session.headers["Authorization"] = f"Bearer {config.token}"
    return session


def probe(session, config: Config, endpoint: str) -> ProbeResult:
    """Fetch one endpoint. Never raises; failures come back as up=False."""
    url = f"{config.target}{endpoint}"
    started = time.monotonic()
    try:
        response = session.get(url, timeout=config.timeout, verify=config.verify)
        elapsed = time.monotonic() - started
    except Exception as exc:  # noqa: BLE001 - any transport failure is "down"
        return ProbeResult(
            endpoint=endpoint,
            up=False,
            latency_seconds=time.monotonic() - started,
            error=f"{type(exc).__name__}: {exc}",
        )

    if response.status_code != 200:
        return ProbeResult(
            endpoint=endpoint,
            up=False,
            latency_seconds=elapsed,
            status_code=response.status_code,
            error=f"HTTP {response.status_code}",
        )

    try:
        payload = response.json()
    except ValueError as exc:
        return ProbeResult(
            endpoint=endpoint,
            up=False,
            latency_seconds=elapsed,
            status_code=response.status_code,
            error=f"invalid JSON: {exc}",
        )

    return ProbeResult(
        endpoint=endpoint,
        up=True,
        latency_seconds=elapsed,
        status_code=response.status_code,
        payload=payload,
    )


def collect(config: Config) -> List[Sample]:
    """One full scrape: probe every endpoint, build every sample."""
    started = time.monotonic()
    session = build_session(config)
    try:
        results = [probe(session, config, endpoint) for endpoint in config.endpoints]
    finally:
        session.close()

    samples = build_samples(results)
    samples.append(
        Sample("falcon_canary_scrape_duration_seconds", (), time.monotonic() - started)
    )
    for result in results:
        if result.error:
            print(
                f"[falcon-canary] {result.endpoint}: {result.error}",
                file=sys.stderr,
                flush=True,
            )
    return samples


def _make_handler(config: Config):
    from http.server import BaseHTTPRequestHandler

    class MetricsHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path.split("?")[0] not in ("/metrics", "/"):
                self.send_error(404, "only /metrics is served")
                return
            try:
                body = render_exposition(collect(config)).encode("utf-8")
            except Exception as exc:  # noqa: BLE001 - a scrape must not kill the server
                self.send_error(500, f"scrape failed: {type(exc).__name__}")
                print(f"[falcon-canary] scrape failed: {exc}", file=sys.stderr, flush=True)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args) -> None:  # noqa: A002
            print(f"[falcon-canary] {self.address_string()} {fmt % args}", file=sys.stderr)

    return MetricsHandler


def serve(config: Config) -> None:  # pragma: no cover - long-running
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer((config.bind, config.port), _make_handler(config))
    print(
        f"[falcon-canary] serving /metrics on {config.bind}:{config.port} "
        f"target={config.target} auth={'yes' if config.token else 'no'}",
        file=sys.stderr,
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Prometheus exporter for the Falcon dashboard")
    parser.add_argument("--once", action="store_true", help="scrape once, print metrics, exit")
    parser.add_argument("--target", help="override FALCON_CANARY_TARGET")
    parser.add_argument("--port", type=int, help="override FALCON_CANARY_PORT")
    parser.add_argument("--bind", help="override FALCON_CANARY_BIND")
    args = parser.parse_args(argv)

    config = Config.from_env()
    if args.target:
        config.target = args.target.rstrip("/")
    if args.port:
        config.port = args.port
    if args.bind:
        config.bind = args.bind

    if args.once:
        sys.stdout.write(render_exposition(collect(config)))
        return 0

    serve(config)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
