"""Unit tests for the Falcon canary exporter's pure layer.

No network, no server, no container. Every test feeds parsed JSON to a pure
function and asserts on the returned metric values or shape verdict.
"""

import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exporter"))

import falcon_canary_exporter as exporter  # noqa: E402


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def sample_value(samples, metric, **labels):
    """Value of the one sample matching metric name + labels."""
    wanted = tuple(sorted(labels.items()))
    matches = [s for s in samples if s.name == metric and tuple(sorted(s.labels)) == wanted]
    assert len(matches) == 1, f"expected exactly one {metric}{labels}, got {len(matches)}"
    return matches[0].value


def position(symbol="AAPL", avg=100.0, current=101.5, qty=10, stop=95.0):
    return {
        "symbol": symbol,
        "quantity": qty,
        "avgPrice": avg,
        "currentPrice": current,
        "stopLoss": stop,
    }


ACCOUNT_OK = {
    "cash": 4200.0,
    "initialBalance": 10000.0,
    "positionsValue": 6000.0,
    "totalValue": 10200.0,
}


# --------------------------------------------------------------------------
# the target is configuration, not a constant (the core bug)
# --------------------------------------------------------------------------


def test_default_target_is_the_service_name_not_the_retired_host():
    config = exporter.Config.from_env({})
    assert config.target == "http://falcon-trader:5000"
    assert "192.168.1.162" not in config.target


def test_target_comes_from_environment_and_trailing_slash_is_stripped():
    config = exporter.Config.from_env({"FALCON_CANARY_TARGET": "https://falcon.internal/"})
    assert config.target == "https://falcon.internal"


def test_retired_host_appears_only_in_the_explanatory_docstring():
    """canary.py hardcoded 192.168.1.162; the port may only mention it in prose."""
    import ast

    source = pathlib.Path(exporter.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    docstring = ast.get_docstring(tree) or ""
    body_without_docstring = source.replace(docstring, "", 1)
    assert "192.168.1.162" in docstring  # documented as the bug being fixed
    assert "192.168.1.162" not in body_without_docstring


def test_tls_verification_defaults_on_and_ca_bundle_is_the_only_override():
    assert exporter.Config.from_env({}).verify is True
    with_ca = exporter.Config.from_env({"FALCON_CANARY_CA_BUNDLE": "/etc/pki/falcon.pem"})
    assert with_ca.verify == "/etc/pki/falcon.pem"
    # No env value can produce verify=False.
    for value in ("0", "false", "no", ""):
        assert exporter.Config.from_env({"FALCON_CANARY_CA_BUNDLE": value}).verify is not False


def test_bearer_token_is_read_from_falcon_api_token():
    assert exporter.Config.from_env({"FALCON_API_TOKEN": "s3cr3t"}).token == "s3cr3t"
    assert exporter.Config.from_env({}).token is None


def test_all_six_endpoints_are_probed():
    assert exporter.ENDPOINTS == (
        "/health",
        "/api/account",
        "/api/positions",
        "/api/trades",
        "/api/recommendations",
        "/api/sentinels",
    )


# --------------------------------------------------------------------------
# account shape
# --------------------------------------------------------------------------


def test_valid_account_passes_shape_check():
    result = exporter.check_account_shape(ACCOUNT_OK)
    assert result.ok
    assert result.errors == ()


@pytest.mark.parametrize("missing", sorted(exporter.ACCOUNT_FIELDS))
def test_account_missing_any_required_field_fails(missing):
    payload = dict(ACCOUNT_OK)
    del payload[missing]
    result = exporter.check_account_shape(payload)
    assert not result.ok
    assert any(missing in err for err in result.errors)


def test_malformed_account_error_body_fails_shape_check_despite_http_200():
    """A dashboard answering 200 with {"error": ...} must not read as healthy."""
    result = exporter.check_account_shape({"error": "Bot not initialized"})
    assert not result.ok
    assert len(result.errors) == 4


def test_account_with_string_balances_fails():
    payload = dict(ACCOUNT_OK, cash="4200.00")
    result = exporter.check_account_shape(payload)
    assert not result.ok
    assert any("cash is not numeric" in err for err in result.errors)


def test_account_that_is_a_list_fails():
    assert not exporter.check_account_shape([ACCOUNT_OK]).ok


def test_boolean_is_not_accepted_as_a_balance():
    assert not exporter.check_account_shape(dict(ACCOUNT_OK, totalValue=True)).ok


# --------------------------------------------------------------------------
# positions shape and the stale-mark bug
# --------------------------------------------------------------------------


def test_valid_positions_list_passes():
    assert exporter.check_positions_shape([position(), position("MSFT")]).ok


def test_empty_positions_list_is_valid():
    assert exporter.check_positions_shape([]).ok


def test_positions_object_instead_of_list_fails():
    assert not exporter.check_positions_shape({"positions": []}).ok


def test_position_missing_stop_loss_key_fails():
    broken = position()
    del broken["stopLoss"]
    result = exporter.check_positions_shape([broken])
    assert not result.ok
    assert any("stopLoss" in err for err in result.errors)


def test_null_stop_loss_is_allowed():
    assert exporter.check_positions_shape([position(stop=None)]).ok


def test_stale_position_exports_falcon_position_stale_1():
    """currentPrice == avgPrice means the mark never updated."""
    samples = exporter.position_samples([position("TSLA", avg=250.0, current=250.0)])
    assert sample_value(samples, "falcon_position_stale", symbol="TSLA") == 1.0


def test_fresh_position_exports_falcon_position_stale_0():
    samples = exporter.position_samples([position("TSLA", avg=250.0, current=251.25)])
    assert sample_value(samples, "falcon_position_stale", symbol="TSLA") == 0.0


def test_stale_detection_across_int_float_and_below_the_mark():
    samples = exporter.position_samples(
        [
            position("AAPL", avg=100, current=100.0),   # int/float equal -> stale
            position("MSFT", avg=300.0, current=299.5), # below entry -> fresh
            position("NVDA", avg=0.0, current=0.0),     # zero-priced -> stale
        ]
    )
    assert sample_value(samples, "falcon_position_stale", symbol="AAPL") == 1.0
    assert sample_value(samples, "falcon_position_stale", symbol="MSFT") == 0.0
    assert sample_value(samples, "falcon_position_stale", symbol="NVDA") == 1.0
    assert sample_value(samples, "falcon_positions_count") == 3.0


def test_is_position_stale_ignores_non_numeric_prices():
    assert not exporter.is_position_stale({"avgPrice": None, "currentPrice": None})
    assert not exporter.is_position_stale({"avgPrice": "100", "currentPrice": "100"})
    assert not exporter.is_position_stale("not a position")


# --------------------------------------------------------------------------
# sentinels
# --------------------------------------------------------------------------


SENTINELS_LIST = {
    "passed": 2,
    "total": 3,
    "results": [
        {"name": "stop_loss_present", "passed": True},
        {"name": "cash_reconciles", "passed": True},
        {"name": "marks_fresh", "passed": False},
    ],
}


def test_sentinels_payload_parses_into_per_name_metrics():
    assert exporter.check_sentinels_shape(SENTINELS_LIST).ok
    samples = exporter.sentinel_samples(SENTINELS_LIST)
    assert sample_value(samples, "falcon_sentinel_pass", name="stop_loss_present") == 1.0
    assert sample_value(samples, "falcon_sentinel_pass", name="cash_reconciles") == 1.0
    assert sample_value(samples, "falcon_sentinel_pass", name="marks_fresh") == 0.0
    assert sample_value(samples, "falcon_sentinels_total") == 3.0
    assert sample_value(samples, "falcon_sentinels_passed") == 2.0


def test_sentinels_mapping_form_also_parses():
    payload = {
        "passed": 1,
        "total": 2,
        "results": {"db_reachable": True, "quotes_flowing": {"passed": False}},
    }
    samples = exporter.sentinel_samples(payload)
    assert sample_value(samples, "falcon_sentinel_pass", name="db_reachable") == 1.0
    assert sample_value(samples, "falcon_sentinel_pass", name="quotes_flowing") == 0.0


def test_sentinel_string_verdicts_are_understood():
    payload = {
        "passed": 1,
        "total": 2,
        "results": [{"name": "a", "status": "pass"}, {"name": "b", "status": "fail"}],
    }
    samples = exporter.sentinel_samples(payload)
    assert sample_value(samples, "falcon_sentinel_pass", name="a") == 1.0
    assert sample_value(samples, "falcon_sentinel_pass", name="b") == 0.0


def test_unreadable_sentinel_verdict_is_skipped_not_counted_as_passing():
    payload = {"passed": 0, "total": 1, "results": [{"name": "mystery"}]}
    names = [s.labels for s in exporter.sentinel_samples(payload) if s.name == "falcon_sentinel_pass"]
    assert names == []


def test_sentinels_missing_results_fails_shape_check():
    result = exporter.check_sentinels_shape({"passed": 1, "total": 1})
    assert not result.ok
    assert any("results" in err for err in result.errors)


def test_sentinels_with_scalar_results_fails_shape_check():
    assert not exporter.check_sentinels_shape({"passed": 1, "total": 1, "results": "ok"}).ok


# --------------------------------------------------------------------------
# probe samples and assembly
# --------------------------------------------------------------------------


def test_probe_samples_report_up_latency_and_shape():
    result = exporter.ProbeResult("/api/account", up=True, latency_seconds=0.042, status_code=200, payload=ACCOUNT_OK)
    samples = exporter.probe_samples(result)
    assert sample_value(samples, "falcon_probe_up", endpoint="/api/account") == 1.0
    assert sample_value(samples, "falcon_probe_latency_seconds", endpoint="/api/account") == 0.042
    assert sample_value(samples, "falcon_probe_shape_ok", endpoint="/api/account") == 1.0


def test_http_200_with_wrong_shape_is_up_but_shape_not_ok():
    """The whole point: canary.py would have called this healthy."""
    result = exporter.ProbeResult("/api/account", up=True, latency_seconds=0.01, status_code=200, payload={"error": "x"})
    samples = exporter.probe_samples(result)
    assert sample_value(samples, "falcon_probe_up", endpoint="/api/account") == 1.0
    assert sample_value(samples, "falcon_probe_shape_ok", endpoint="/api/account") == 0.0


def test_down_endpoint_reports_zero_for_up_and_shape():
    result = exporter.ProbeResult("/api/positions", up=False, latency_seconds=10.0, error="timeout")
    samples = exporter.probe_samples(result)
    assert sample_value(samples, "falcon_probe_up", endpoint="/api/positions") == 0.0
    assert sample_value(samples, "falcon_probe_shape_ok", endpoint="/api/positions") == 0.0


def test_endpoints_without_a_schema_are_shape_ok_when_json_parsed():
    for endpoint, payload in (("/health", {"status": "healthy"}), ("/api/trades", []), ("/api/recommendations", {})):
        result = exporter.ProbeResult(endpoint, up=True, latency_seconds=0.01, status_code=200, payload=payload)
        assert sample_value(exporter.probe_samples(result), "falcon_probe_shape_ok", endpoint=endpoint) == 1.0


def test_build_samples_emits_derived_metrics_only_for_valid_payloads():
    results = [
        exporter.ProbeResult("/api/positions", up=True, latency_seconds=0.01, status_code=200,
                             payload=[position("AAPL", avg=100.0, current=100.0)]),
        exporter.ProbeResult("/api/sentinels", up=True, latency_seconds=0.02, status_code=200, payload=SENTINELS_LIST),
        exporter.ProbeResult("/api/account", up=False, latency_seconds=5.0, error="connection refused"),
    ]
    samples = exporter.build_samples(results)
    assert sample_value(samples, "falcon_position_stale", symbol="AAPL") == 1.0
    assert sample_value(samples, "falcon_sentinel_pass", name="marks_fresh") == 0.0
    assert sample_value(samples, "falcon_probe_up", endpoint="/api/account") == 0.0


def test_build_samples_skips_derived_metrics_when_the_shape_is_wrong():
    results = [
        exporter.ProbeResult("/api/positions", up=True, latency_seconds=0.01, status_code=200,
                             payload={"error": "Bot not initialized"}),
    ]
    samples = exporter.build_samples(results)
    assert [s for s in samples if s.name == "falcon_position_stale"] == []
    assert sample_value(samples, "falcon_probe_shape_ok", endpoint="/api/positions") == 0.0


# --------------------------------------------------------------------------
# exposition rendering
# --------------------------------------------------------------------------


def test_exposition_groups_metrics_under_one_help_and_type_header():
    text = exporter.render_exposition(
        exporter.position_samples([position("AAPL", avg=1.0, current=1.0), position("MSFT")])
    )
    assert text.count("# TYPE falcon_position_stale gauge") == 1
    assert text.count("# HELP falcon_position_stale") == 1
    assert 'falcon_position_stale{symbol="AAPL"} 1' in text
    assert 'falcon_position_stale{symbol="MSFT"} 0' in text
    assert text.endswith("\n")


def test_exposition_renders_unlabelled_metrics_without_braces():
    text = exporter.render_exposition([exporter.Sample("falcon_sentinels_total", (), 3.0)])
    assert "falcon_sentinels_total 3\n" in text
    assert "falcon_sentinels_total{" not in text


def test_label_values_are_escaped():
    text = exporter.render_exposition(
        [exporter.Sample("falcon_sentinel_pass", (("name", 'weird"\\name'),), 1.0)]
    )
    assert 'name="weird\\"\\\\name"' in text


def test_latency_is_rendered_as_a_float():
    text = exporter.render_exposition(
        [exporter.Sample("falcon_probe_latency_seconds", (("endpoint", "/health"),), 0.125)]
    )
    assert 'falcon_probe_latency_seconds{endpoint="/health"} 0.125' in text
