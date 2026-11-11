# Retirement recommendation: `apps/falcon/` and the 3-Pi systemd kit

**Status: recommendation only. Nothing has been deleted.** This document exists so
the repo owner can make the call with the inventory in front of him. See
[TradingAsBuddies/falcon-operator#2](https://github.com/TradingAsBuddies/falcon-operator/issues/2).

Date: 2026-09-10. Last commit to this repo: `13745e8`, 2026-02-05.

---

## 1. What is being proposed

Retire two things that are no longer wired into the running platform:

1. **`apps/falcon/`** — a vendored copy of the pre-split Falcon application:
   184 tracked files, 91 of them Python, plus 52 markdown design notes. It was
   split into `falcon-trader`, `falcon-core`, `falcon-screener`, and
   `falcon-strategies`; this copy has not been touched since February.
2. **The 3-Pi systemd deploy kit** — `deploy/`, `inventory/hosts.yaml`, and
   `scripts/discover.sh`, which push code by rsync to `192.168.1.106` and
   `192.168.1.162` and install root systemd units on them.

The specific hazard that prompted the issue: `deploy/services/falcon-canary.service`
runs `canary.py --daemon` **as root** with `Restart=always`, probing
`192.168.1.162:443` with TLS verification disabled (`apps/falcon/canary.py:369-376`)
and calling `sudo systemctl restart` on `falcon-trader` and `falcon-feedback-loop`
(`apps/falcon/canary.py:51-54`). The dashboard now lives at `192.168.1.17:5000`
behind Traefik. Wherever that unit is still enabled, a root daemon is retrying a
host that no longer answers and is authorized to restart trading services on the
strength of that failure.

**The replacement for the monitoring half already exists in this branch** — see
§4. What remains is the deletion decision.

## 2. What is superseded, and by what

Verified by matching filenames against the checkouts under
`~/Projects/Falcon` on 2026-09-10.

| `apps/falcon/` component | Superseded by |
|---|---|
| `dashboard_server.py`, `paper_trading_bot.py`, `active_strategy.py`, `strategy_{manager,executor,orchestrator,analytics}.py`, `run_orchestrator.py`, `youtube_strategies.py` | `falcon-trader/src/falcon_trader/` |
| `orchestrator/` engines, routers, validators, execution, monitors (`base_engine.py`, `rsi_engine.py`, `bollinger_engine.py`, `momentum_engine.py`, `strategy_router.py`, `stock_classifier.py`, `entry_validator.py`, `screener_parser.py`, `trade_executor.py`, `market_data_fetcher.py`, `performance_tracker.py`, `data_structures.py`) | `falcon-trader/src/falcon_trader/orchestrator/` |
| `config.py`, `db_manager.py`, `finviz_client.py` | `falcon-core/src/falcon_core/` |
| `*_strategy.py` (RSI, Bollinger, MACD, momentum breakout, MA crossover, hybrid, one-candle) | `falcon-strategies/trader/` |
| `www/*.html`, `dashboard.html` | `falcon-trader/src/falcon_trader/www/` |
| `canary.py` + `falcon-canary.{service,timer}` | `exporter/falcon_canary_exporter.py` + `quadlet/falcon-canary-exporter.container` (this branch) |
| `Dockerfile`, `docker-compose.yml`, `.github/workflows/` | Per-service build in each split repo |

The 91 Python files carry 82 distinct filenames; 33 of those match a filename in
a successor repo, and one of the 33 is `__init__.py`, which matches trivially.
A filename match is evidence of supersession, not proof of content equivalence —
diff before trusting it. The other 49 are the ones that need §3.

## 3. What must be confirmed before anything is deleted

Do not delete until every box is checked. These are the items this branch could
**not** verify from a read-only workstation.

- [ ] **Nothing is still running the old units.** On each Pi
      (`192.168.1.106`, `192.168.1.162`, and the current dashboard host):
      ```sh
      systemctl list-units --all 'falcon-*'
      systemctl is-enabled falcon-canary.service falcon-canary.timer
      systemctl list-timers --all | grep -i falcon
      crontab -l; sudo crontab -l
      ```
      Expect `falcon-canary.service` to be either gone or failing in a restart
      loop. **Stop and disable it first — that is worth doing before, and
      independently of, any deletion decision.**
- [ ] **No successor repo imports from the vendored copy.**
      `grep -rn 'apps/falcon\|falcon-operator' ~/Projects/Falcon --include='*.py' --include='*.toml' --include='*.yaml'`
      (issue #2 reports this already returns nothing across gateway, trader,
      and core).
- [ ] **The 49 Python files with no name match in a successor repo are
      accounted for.** They are the ones at real risk of being the only copy:
      `ai_stock_screener.py`, `multi_screener.py`, `profile_manager.py`,
      `profile_templates.py`, `finviz_csv_screener.py`, `screener_profiles.yaml`
      (→ expected in **falcon-screener**, which is not checked out locally, so
      this was **not verified**); `feedback_loop.py`, `stop_loss_monitor.py`,
      `five_minute_scanner.py`, `daily_report.py`, `strategy_optimizer.py`,
      `strategy_parser.py`, `yaml_serializer.py`, `account_balance_updater.py`;
      the `migrate_*.py` / `init_strategy_tables.py` / `fix_*.py` /
      `backfill_pnl.py` one-shot database scripts; the `backtest_*.py` and
      `download_*_data.py` research scripts; and 18 `test_*.py` files, including
      `test_security.py`.
      Full list:
      ```sh
      for f in $(git ls-files apps/falcon | grep '\.py$' | xargs -n1 basename | sort -u); do
        [ -z "$(find ~/Projects/Falcon -name "$f" -not -path '*/.git/*' | head -1)" ] && echo "$f"
      done
      ```
- [ ] **The 52 markdown design notes are captured.** `ADAPTIVE_FEEDBACK_SYSTEM_SPEC.md`,
      `ALPHABETICAL_BIAS_*.md`, `BACKTEST_RESULTS_*.md`, `EXIT_STRATEGY_COMPARISON.md`,
      `DATA_RETENTION_POLICY.md` and the rest are the written record of decisions
      the current code embodies but does not explain. Move what is still true
      into the successor repos' docs before deleting.
- [ ] **Secrets and state in the tree are handled.** `deploy/services/falcon.env.example`,
      `apps/falcon/paper_trading.pid`, and `apps/falcon/strategy_history/` should
      be reviewed; rotate anything that turns out to be a real credential rather
      than an example.
- [ ] **Backups do not depend on `deploy/backup-db.sh`.** If the Postgres backup
      on `192.168.1.106` is still driven by that script, replace it before the
      deploy kit goes.

## 4. What replaces the canary

Delivered on this branch (`fix/review-2026-09-10`), not yet built or deployed:

- `exporter/falcon_canary_exporter.py` — Prometheus exporter. Target is
  `FALCON_CANARY_TARGET` (default `http://falcon-trader:5000`); no hardcoded
  host. TLS verification is always on, with `FALCON_CANARY_CA_BUNDLE` for a
  private CA. Optional bearer auth via `FALCON_API_TOKEN`. Probes `/health`,
  `/api/account`, `/api/positions`, `/api/trades`, `/api/recommendations`,
  `/api/sentinels`, and asserts JSON **shape**, not just HTTP 200. Exports
  `falcon_probe_up`, `falcon_probe_latency_seconds`, `falcon_probe_shape_ok`,
  `falcon_sentinel_pass{name}`, `falcon_position_stale{symbol}`.
  It observes only: no `systemctl`, no root, no repair actions.
- `exporter/Containerfile`, `quadlet/falcon-canary-exporter.container` —
  rootless, read-only, `DropCapability=ALL`, port 9107.
- `tests/test_falcon_canary_exporter.py` — 40 tests, no network.

Still to do, outside this branch: build the image, add the Prometheus scrape
job, and write the Grafana alerts (any `falcon_sentinel_pass == 0`, any
`falcon_position_stale == 1` during market hours, `falcon_probe_shape_ok == 0`).

## 5. The commands, if the owner decides to proceed

Nothing below has been run. Do it in this order; stop at the first surprise.

**Step 1 — defuse the live hazard (do this regardless of the deletion decision):**

```sh
# On every Pi that ever had the kit installed:
sudo systemctl disable --now falcon-canary.service falcon-canary.timer falcon-canary-oneshot.service
sudo systemctl reset-failed 'falcon-canary*'
sudo rm -f /etc/systemd/system/falcon-canary.{service,timer} \
           /etc/systemd/system/falcon-canary-oneshot.service
sudo systemctl daemon-reload
```

**Step 2 — tag the last state of the vendored app, so deletion stays reversible:**

```sh
cd ~/Projects/Falcon/falcon-operator
git tag -a vendored-falcon-final -m "Last state of apps/falcon before retirement (issue #2)" 13745e8
git push origin vendored-falcon-final
```

**Step 3 — rescue anything from §3 that has no successor**, into whichever repo
should own it (`falcon-screener` for the screener scripts, `falcon-core` for the
migrations, the successor repos' `docs/` for the markdown).

**Step 4 — delete:**

```sh
cd ~/Projects/Falcon/falcon-operator
git checkout -b chore/retire-vendored-app
git rm -r apps/falcon deploy inventory scripts
git commit -m "Retire vendored pre-split app and 3-Pi systemd kit

Superseded by falcon-trader, falcon-core, falcon-screener, falcon-strategies.
Monitoring replaced by exporter/falcon_canary_exporter.py.
Prior state preserved at tag vendored-falcon-final.

Closes TradingAsBuddies/falcon-operator#2"
```

Then update `README.md`, whose architecture diagram and host table still
describe the 3-Pi layout with the dashboard on `192.168.1.162`.

**Alternative — archive the whole repo instead.** If `falcon-operator` has no
role left once the exporter moves to `falcon-gateway`, archiving is cleaner
than a repo that is 90% deletion. In that case, move `exporter/`, `quadlet/`,
and `tests/` to `falcon-gateway` first, then archive with the tag in place.

## 6. Recommendation

Do step 1 now — an enabled root daemon with restart authority pointed at a dead
host is the actual risk, and disabling it costs nothing and decides nothing.

Then do steps 2-4 once the §3 checklist is clear, with the screener files being
the one item that genuinely needs eyes on `falcon-screener` before the delete.
Keep the repo (do not archive) if `falcon-gateway` is not ready to own the
exporter; it is a reasonable home for cluster-level operational tooling even
after the vendored app is gone.
