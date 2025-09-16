# Multi-Agent Trading System Architecture

## Overview
This document describes the modular architecture scaffold generated for the project. It is intentionally minimal yet production‑oriented so you can iteratively enhance components (agents, orchestration, data services, memory, execution) without rewrites.

## Layered Structure
| Layer | Purpose | Examples |
|-------|---------|----------|
| config | Environment & logging | `config/config.py`, `logging.yaml` |
| core | Cross-cutting primitives | events, bus, utils (future) |
| agents | Specialized reasoning units | research, strategy, risk, execution, supervisor |
| graphs | Orchestration / state machine | `trading_graph.py`, `state.py` |
| tools | External data & LLM adapters | yfinance, finnhub, tavily, vector store |
| services | Domain services | portfolio, risk engine, execution adapters |
| data | Persisted artifacts | raw, processed, cache |
| scripts | Operational tasks | ingest, backtest, build vector memory |
| tests | Quality / regression | basic smoke tests |

## Orchestration (LangGraph State Machine)
The original linear loop has been refactored into a LangGraph `StateGraph` with conditional routing:
```
 research -> strategy -> risk --(approved?)--> execution -> supervisor
										 \--(none)------> supervisor
 supervisor --(continue?)--> research | END
```
The supervisor sets `done=True` to terminate. This design allows future branching (e.g., alternative risk paths, portfolio rebalancing) without rewriting core loops.

## Implemented Enhancements
- LangGraph orchestration (`graphs/trading_graph.py`).
- Vector memory + research persistence (`tools/vectorstore.py`, `tools/memory.py`).
- Event bus + event models (`core/bus.py`, `core/events.py`).
- Risk engine (exposure + stop loss scaffolding) (`services/risk_engine.py`).
- Backtesting service with Sharpe & max drawdown (`services/backtest_service.py`).
- Typer CLI (`app/cli.py`) with run / research / backtest commands.
- Structured logging via YAML config + Rich (`config/logging.yaml`).
- Pydantic domain models (`core/models.py`).

## Updated Roadmap (Next Candidates)
1. Portfolio accounting (multi‑symbol positions & PnL attribution).
2. Order lifecycle simulation (partial fills, slippage, commissions).
3. Data caching layer (Redis/SQLite) + rate limit guards.
4. Async event-driven ingestion (websocket market data) feeding graph triggers.
5. Strategy module expansion (factor models, sentiment fusion, ML signals).
6. Observability: tracing (OpenTelemetry) + metrics (Prometheus) + structured event logs.
7. Deployment hardening: container health checks, graceful shutdown hooks.
8. Security & secrets management (Vault / AWS Secrets Manager integration).

### Execution Cost Modeling

The backtest engine (`services/backtest_service.py`) supports realistic execution frictions:

| Feature | Parameter | Description |
|---------|-----------|-------------|
| Commission | `commission_pct` | Percent of notional per fill (e.g. 0.0005 = 5 bps) |
| Slippage | `slippage_bps` | Basis point adjustment applied to execution price (directional) |
| Partial Fills | `participation_cap` | If set (0 < cap <= 1), max fraction of bar volume filled per bar |
| Spread Impact | `base_spread_bps` | Half-spread added/subtracted prior to slippage when partial fills enabled |

Trade records now contain `effective_price`, `commission`, `slippage_bps`, `remaining`, and `original_qty` for auditing.

`BacktestResult` aggregates:
- `total_commission`
- `total_slippage_cost`
- `total_notional`
- `total_trades`
- `average_cost_bps`
- `gross_exposure_peak`

### Tracing & LangSmith

Local lightweight spans: `core/tracing.py` provides `span()` for timing blocks.

LangSmith optional activation:
1. Set env vars:
	- `LANGCHAIN_API_KEY`
	- (optional) `LANGCHAIN_PROJECT`
2. Pass `--trace` to CLI commands (`run`, `backtest`) or call `init_langsmith()` manually.

When enabled, LangChain internals (if used within agents/tools with callbacks) will emit traces to LangSmith; otherwise only activation is recorded.

### CLI Enhancements

`python -m app.cli backtest --symbol AAPL --commission-pct 0.0005 --slippage-bps 5 --participation-cap 0.25 --trace`

Outputs extended metrics including total and average costs plus peak gross exposure.

### Future Extensions

- Impact model sensitive to order size vs ADV.
- Latency & queue position modeling.
- Dynamic spread estimation from intraday data.

### Market Impact Curve
Execution modeling now supports multiple market impact functional forms reflecting how slippage scales with participation.

Core parameters:
- `impact_coef` (float): Base coefficient applied to impact term.
- `impact_model` (str): One of `linear | sqrt | power` (default `linear`).
- `impact_power` (float): Exponent when `impact_model=power` (default 0.6 typical for empirical impact studies if unspecified at CLI level).

Definitions:
Let:
- `cum_participation` = cumulative filled quantity / cumulative encountered volume (bounded 0..1+).
- `P_ref` = pre-impact reference price (post spread + slippage adjustments).

Functional forms:
1. Linear:  impact_raw = impact_coef * cum_participation
2. Square-root: impact_raw = impact_coef * sqrt(cum_participation)
3. Power:  impact_raw = impact_coef * (cum_participation ** impact_power)

Applied price shift:

```
impact_price_delta = impact_raw * P_ref
effective_price = P_ref + direction * impact_price_delta
```

Where `direction` = +1 for BUY, -1 for SELL. Recorded per trade as `impact_applied` along with existing cost fields. This layering order ensures explicit visibility of spread, nominal slippage, and endogenous impact separately.

Rationale: Square-root (and general power) models align with microstructure literature indicating concave impact vs participation / volume fraction; linear retained for simplicity and regression baselines.

### JSON Metrics Export

`backtest` CLI supports `--json` and `--json-path` to emit machine-readable metrics for downstream analysis / dashboards.

Example:
```
python -m app.cli backtest --symbol AAPL --json --commission-pct 0.0005 --slippage-bps 5 --participation-cap 0.25 --impact-coef 0.01
```

### Risk Report Command

`risk-report` aggregates per-symbol backtests:
```
python -m app.cli risk-report --symbols AAPL MSFT GOOG --period 6mo --participation-cap 0.2 --impact-coef 0.01 --json
```
Outputs per-symbol stats plus aggregate averages and totals. Extended analytics now include (when benchmark provided):
- Beta (slope) and Alpha (annualized intercept approximation) vs benchmark
- Portfolio-level (pooled) historical VaR

New flags:
```
--benchmark SPY             # Fetch benchmark series (same period/interval) for factor comparison
--var-confidence 0.95       # Historical VaR confidence level (default 0.95)
--impact-model sqrt         # Select nonlinear impact model
--impact-power 0.6          # Power exponent if --impact-model power
```

Example:
```
python -m app.cli risk-report \
	--symbols AAPL MSFT GOOG \
	--benchmark SPY \
	--period 6mo \
	--participation-cap 0.2 \
	--impact-model power --impact-power 0.55 \
	--impact-coef 0.012 \
	--json
```

Alpha/Beta Method (simplified):
```
beta  = Cov(r_p, r_b) / Var(r_b)
alpha = mean(r_p) - beta * mean(r_b)
```
Where returns are simple period-over-period (matching interval). Alpha reported as raw per-period drift; convert to annualized externally if needed (multiply by periods per year). This lightweight OLS avoids extra dependencies while remaining interpretable.

Portfolio VaR: Combines per-symbol equity curves into aggregate returns, then computes historical percentile:
```
VaR(q) = - Quantile( portfolio_returns, 1 - q )
```
Reported as a positive loss number (e.g. 0.025 = 2.5%).

Future Improvements: Consider Cornish-Fisher adjustment, parametric covariance VaR, or expected shortfall (CVaR).

### Callback Instrumentation & Tracing

Node-level execution instrumentation is implemented via `graphs/callbacks.py` (`NodeCallbackManager`). Each LangGraph node (`research`, `strategy`, `risk`, `execution`, `supervisor`) is wrapped in a timing span: `span("node.<name>")`.

Activation Paths:
1. Set `TRACING=1` environment variable for local span logging only.
2. Provide `LANGCHAIN_API_KEY` (and optional `LANGCHAIN_PROJECT`) to enable LangSmith tracing (`init_langsmith()` auto-called when requested via CLI `--trace`).
3. Pass `enable_callbacks=True` when constructing the graph programmatically: `build_graph(enable_callbacks=True)`.

Design Principles:
- Zero / minimal overhead when disabled.
- Centralized instrumentation layer (no agent code changes required to expand tracing).
- Extensible: error hooks & structured event emission can be layered into `NodeCallbackManager` later.

Env Summary:
| Variable | Effect |
|----------|--------|
| TRACING=1 | Enable local span timing logs |
| LANGCHAIN_API_KEY | Enables LangSmith tracing (if provided) |
| LANGCHAIN_PROJECT | Optional project label for LangSmith |

Upcoming: Optional OpenTelemetry exporter + per-node success/failure counters.

CLI Example with tracing + nonlinear impact:
```
python -m app.cli backtest --symbol AAPL --period 3mo \
	--commission-pct 0.0005 --slippage-bps 5 --participation-cap 0.25 \
	--impact-model sqrt --impact-coef 0.02 --trace --json
```

Programmatic:
```python
from graphs.trading_graph import build_graph
g = build_graph(enable_callbacks=True)
state = g.run(max_loops=5)
```

Tracing Helper:
`core.tracing.tracing_enabled()` returns True if either `TRACING=1` or LangSmith variables are set.

Replacement: The current lightweight span system can be swapped with OpenTelemetry spans without altering agent implementations.

### Additional Analytical Extensions

The combination of cost metrics, nonlinear impact modeling, regression-style alpha/beta, and portfolio VaR supports a richer performance decomposition workflow. Export JSON to feed dashboards (e.g., Streamlit, Superset) for iterative strategy evaluation.

## Environment Variables
See `.env.example` and load via `Settings` (Pydantic). Always centralize tunables there.

## Running Locally
Python entrypoint:
```
python -m app.main
```
CLI modes:
```
python -m app.cli run --loops 5
python -m app.cli research AAPL MSFT
python -m app.cli backtest --symbol AAPL --period 1mo --interval 1d
```
Docker:
```
docker compose up --build
```

## Testing
```
pytest -q
```

## Safety & Validation Ideas
- Schema validate agent deltas to avoid unexpected state keys.
- Add guardrails for API rate limits (sleep/retry wrappers & exponential backoff).
- Enforce risk constraints before order emission (position caps, VaR checks).
- Introduce circuit breakers if volatility or slippage exceeds thresholds.
- Differential backtests (new strategy vs control) before enabling live mode.

## Directory Recap
```
app/                Entrypoints
agents/             Agent implementations
config/             Settings & logging
core/               (Future) primitives and shared infra
graphs/             Orchestration components
services/           Domain logic (portfolio, risk, execution)
tools/              External adapters (data, search, LLM, memory)
data/               Storage areas
scripts/            Operational scripts
tests/              Automated tests
```

## Next Steps Suggested
- Add richer strategy generation (momentum, mean reversion, sentiment blend).
- Portfolio & position ledger service.
- Optional websocket ingestion feeding event bus.
- Enhanced backtest (multi-symbol, commissions, slippage, position sizing).
- CI: Expand tests (agents, risk engine, backtest) & enforce ruff formatting.
- Documentation: Add sequence diagrams & state transition chart.

---
Generated scaffold — ready for iterative enhancement.
