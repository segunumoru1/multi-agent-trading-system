from __future__ import annotations
"""Typer CLI for the multi-agent trading system.

Commands:
  run          - Run the full trading LangGraph loop.
  research     - Run only the research agent and show insights.
  backtest     - Run a simple backtest on a symbol over a period.

Example:
  python -m app.cli run --loops 3
  python -m app.cli research --symbols AAPL MSFT
  python -m app.cli backtest --symbol AAPL --period 1mo --interval 1d
"""
import typer
import logging, logging.config, yaml, os, sys
from typing import List, Optional
from graphs.trading_graph import build_graph
from core.tracing import init_langsmith
from agents import ResearchAgent
from services.backtest_service import backtest
from tools.market_data.yfinance_tool import fetch_history
import pandas as pd

app = typer.Typer(add_completion=False, help="Multi-agent trading system CLI")


def _setup_logging():
    cfg_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'logging.yaml')
    cfg_path = os.path.abspath(cfg_path)
    if os.path.exists(cfg_path):
        with open(cfg_path, 'r') as f:
            data = yaml.safe_load(f)
        os.makedirs('logs', exist_ok=True)
        logging.config.dictConfig(data)
    else:
        logging.basicConfig(level=logging.INFO)


@app.command()
def run(
    loops: int = typer.Option(5, help="Maximum loop iterations"),
    trace: bool = typer.Option(False, help="Enable LangSmith tracing if API key set"),
):
    """Run the full LangGraph trading pipeline."""
    _setup_logging()
    logger = logging.getLogger("cli.run")
    if trace:
        init_langsmith(project="trading-run")
    graph = build_graph()
    state = graph.run(max_loops=loops)
    logger.info("Final State: %s", state.json())


@app.command()
def research(symbols: List[str] = typer.Argument(None, help="Symbols to research (space separated)")):
    """Run only the research agent and display collected insights."""
    _setup_logging()
    if not symbols:
        symbols = ["AAPL"]
    agent = ResearchAgent()
    state = agent.step({"symbols": symbols})
    for line in state.get("research_insights", []):
        typer.echo(line)


@app.command()
def backtest_command(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Symbol to backtest"),
    period: str = typer.Option("3mo", help="yfinance period, e.g. 1mo,3mo,6mo,1y"),
    interval: str = typer.Option("1d", help="yfinance interval, e.g. 1d,1h,30m"),
    commission_pct: float = typer.Option(0.0005, help="Commission percent of notional (e.g. 0.0005=5bps)"),
    slippage_bps: int = typer.Option(5, help="Slippage in basis points added/subtracted to execution price"),
    trace: bool = typer.Option(False, help="Enable LangSmith tracing if API key set"),
    participation_cap: float = typer.Option(0.0, help="If >0, max fraction of bar volume to fill (enables partial fills)."),
    base_spread_bps: int = typer.Option(2, help="Approximate half-spread (bps) applied when partial fills enabled."),
    json_output: bool = typer.Option(False, "--json", help="Emit metrics as JSON to stdout"),
    json_path: Optional[str] = typer.Option(None, help="If set, write JSON metrics to this file"),
    impact_coef: float = typer.Option(0.0, help="Market impact coefficient"),
    impact_model: str = typer.Option("linear", help="Impact model: linear|sqrt|power"),
    impact_power: float = typer.Option(0.5, help="Exponent if impact_model=power"),
):
    """Generate naive strategy signals then backtest them."""
    _setup_logging()
    logger = logging.getLogger("cli.backtest")
    from pandas import DataFrame  # local import to avoid heavy top-level if unused
    df: DataFrame | None
    try:
        df = fetch_history(symbol, period=period, interval=interval)
    except Exception as e:
        typer.echo(f"Failed to download data: {e}")
        raise typer.Exit(code=1)
    if df is None or getattr(df, 'empty', True):
        typer.echo("No data returned.")
        raise typer.Exit(code=1)
    # Very naive: buy first day, sell last day
    first_date = df.index[0]
    last_date = df.index[-1]
    orders = [
        {"timestamp": str(first_date), "side": "BUY", "qty": 10},
        {"timestamp": str(last_date), "side": "SELL", "qty": 10},
    ]
    if trace:
        init_langsmith(project="backtest")
    participation = participation_cap if participation_cap > 0 else None
    result = backtest(
        df,
        orders,
        commission_pct=commission_pct,
        slippage_bps=slippage_bps,
        participation_cap=participation,
        base_spread_bps=base_spread_bps,
        impact_coef=impact_coef,
        impact_model=impact_model,
        impact_power=impact_power,
    )
    metrics = {
        "sharpe": result.sharpe,
        "max_drawdown": result.max_drawdown,
        "final_equity": float(result.equity_curve.iloc[-1]),
        "total_commission": result.total_commission,
        "total_slippage_cost": result.total_slippage_cost,
        "total_notional": result.total_notional,
        "total_trades": result.total_trades,
        "average_cost_bps": result.average_cost_bps,
        "gross_exposure_peak": result.gross_exposure_peak,
    }
    if json_output or json_path:
        import json
        payload = json.dumps(metrics, indent=2)
        if json_output:
            typer.echo(payload)
        if json_path:
            try:
                with open(json_path, 'w') as f:
                    f.write(payload)
            except Exception as e:
                typer.echo(f"Failed writing JSON metrics: {e}")
    else:
        typer.echo(f"Sharpe: {metrics['sharpe']:.3f}")
        typer.echo(f"Max Drawdown: {metrics['max_drawdown']:.3%}")
        typer.echo(f"Final Equity: {metrics['final_equity']:.2f}")
        typer.echo(f"Total Commission: {metrics['total_commission']:.2f}")
        typer.echo(f"Total Slippage Cost: {metrics['total_slippage_cost']:.2f}")
        typer.echo(f"Total Notional: {metrics['total_notional']:.2f}")
        typer.echo(f"Total Trades: {metrics['total_trades']}")
        typer.echo(f"Average Cost (bps): {metrics['average_cost_bps']:.2f}")
        typer.echo(f"Peak Gross Exposure: {metrics['gross_exposure_peak']:.2f}")


@app.command("risk-report")
def risk_report(
    symbols: List[str] = typer.Option(..., help="Symbols to include (multiple)"),
    period: str = typer.Option("3mo", help="yfinance period"),
    interval: str = typer.Option("1d", help="yfinance interval"),
    commission_pct: float = typer.Option(0.0005, help="Commission percent of notional"),
    slippage_bps: int = typer.Option(5, help="Slippage bps"),
    participation_cap: float = typer.Option(0.0, help="If >0 enables partial fills"),
    impact_coef: float = typer.Option(0.0, help="Market impact coefficient"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON summary"),
    benchmark: Optional[str] = typer.Option(None, help="Benchmark symbol for alpha/beta (e.g. ^GSPC)"),
    impact_model: str = typer.Option("linear", help="Impact model: linear|sqrt|power"),
    impact_power: float = typer.Option(0.5, help="Exponent if impact_model=power"),
    var_confidence: float = typer.Option(0.95, help="Confidence level for portfolio VaR"),
):
    """Run naive backtests per symbol and aggregate risk/cost metrics."""
    _setup_logging()
    if not symbols:
        typer.echo("No symbols provided")
        raise typer.Exit(code=1)
    participation = participation_cap if participation_cap > 0 else None
    import json
    rows = []
    benchmark_df = None
    if benchmark:
        try:
            benchmark_df = fetch_history(benchmark, period=period, interval=interval)
        except Exception as e:
            typer.echo(f"Benchmark fetch failed: {e}")
            benchmark_df = None

    for sym in symbols:
        try:
            df = fetch_history(sym, period=period, interval=interval)
        except Exception as e:
            typer.echo(f"Skip {sym}: {e}")
            continue
        if df is None or getattr(df, 'empty', True):
            typer.echo(f"No data for {sym}")
            continue
        # naive buy first / sell last
        orders = [
            {"timestamp": str(df.index[0]), "side": "BUY", "qty": 10},
            {"timestamp": str(df.index[-1]), "side": "SELL", "qty": 10},
        ]
        res = backtest(
            df,
            orders,
            commission_pct=commission_pct,
            slippage_bps=slippage_bps,
            participation_cap=participation,
            impact_coef=impact_coef,
            impact_model=impact_model,
            impact_power=impact_power,
        )
        rows.append({
            "symbol": sym,
            "sharpe": res.sharpe,
            "max_drawdown": res.max_drawdown,
            "final_equity": float(res.equity_curve.iloc[-1]),
            "total_commission": res.total_commission,
            "total_slippage_cost": res.total_slippage_cost,
            "total_notional": res.total_notional,
            "average_cost_bps": res.average_cost_bps,
        })
    if not rows:
        typer.echo("No successful backtests")
        raise typer.Exit(code=1)
    # Aggregate metrics
    # Portfolio VaR (historical) combining per-symbol naive equity changes equally weighted
    import math as _math
    import pandas as _pd
    portfolio_returns = []
    if rows:
        # Re-run minimal data collection for returns if needed (simple approach: fetch again and compute daily pct_change for each symbol, then average)
        ret_frames = []
        for sym in [r["symbol"] for r in rows]:
            try:
                df_ret = fetch_history(sym, period=period, interval=interval)
                if df_ret is not None and not getattr(df_ret, 'empty', True):
                    ret = df_ret['Close'].pct_change().dropna()
                    ret_frames.append(ret.rename(sym))
            except Exception:
                continue
        if ret_frames:
            merged = _pd.concat(ret_frames, axis=1).dropna()
            if not merged.empty:
                portfolio_returns = merged.mean(axis=1)
    var_value = 0.0
    if len(portfolio_returns) > 0:
        sorted_r = sorted(portfolio_returns)
        idx = int((1 - var_confidence) * len(sorted_r))
        if idx < 0:
            idx = 0
        var_value = -sorted_r[idx]

    # Alpha/Beta vs benchmark if provided
    alpha = None
    beta = None
    if benchmark_df is not None and not getattr(benchmark_df, 'empty', True):
        bench_ret = benchmark_df['Close'].pct_change().dropna()
        # Build simple portfolio equity from symbol final equity differences (reuse portfolio_returns if available)
        if len(portfolio_returns) == 0:
            pr = []
        else:
            pr = portfolio_returns
        try:
            # Align series
            pr_series = _pd.Series(pr, index=bench_ret.index[-len(pr):]) if len(pr) > 0 else None
            if pr_series is not None and not pr_series.empty:
                # OLS beta = cov(Rp,Rb)/var(Rb); alpha = mean(Rp) - beta*mean(Rb)
                cov = float(((pr_series - pr_series.mean()) * (bench_ret.reindex(pr_series.index) - bench_ret.mean())).sum())
                var_b = float(((bench_ret - bench_ret.mean()) ** 2).sum())
                if var_b != 0:
                    beta = cov / var_b
                    alpha = pr_series.mean() - beta * bench_ret.mean()
        except Exception:
            pass

    agg = {
        "symbols": len(rows),
        "avg_sharpe": sum(r["sharpe"] for r in rows) / len(rows),
        "avg_max_drawdown": sum(r["max_drawdown"] for r in rows) / len(rows),
        "total_commission": sum(r["total_commission"] for r in rows),
        "total_slippage_cost": sum(r["total_slippage_cost"] for r in rows),
        "total_notional": sum(r["total_notional"] for r in rows),
        "avg_cost_bps": sum(r["average_cost_bps"] for r in rows) / len(rows),
        "portfolio_var": var_value,
        "alpha": alpha,
        "beta": beta,
    }
    report = {"per_symbol": rows, "aggregate": agg}
    if json_output:
        typer.echo(json.dumps(report, indent=2))
    else:
        typer.echo("Aggregate Risk Report:")
        typer.echo(f"Symbols: {agg['symbols']}")
        typer.echo(f"Avg Sharpe: {agg['avg_sharpe']:.3f}")
        typer.echo(f"Avg Max Drawdown: {agg['avg_max_drawdown']:.3%}")
        typer.echo(f"Total Commission: {agg['total_commission']:.2f}")
        typer.echo(f"Total Slippage: {agg['total_slippage_cost']:.2f}")
        typer.echo(f"Total Notional: {agg['total_notional']:.2f}")
        typer.echo(f"Avg Cost (bps): {agg['avg_cost_bps']:.2f}")
        typer.echo(f"Portfolio VaR ({var_confidence:.2%}): {agg['portfolio_var']:.4f}")
        if beta is not None:
            typer.echo(f"Beta vs Benchmark: {beta:.3f}")
        if alpha is not None:
            typer.echo(f"Alpha vs Benchmark: {alpha:.5f}")
        typer.echo("Per Symbol:")
        for r in rows:
            typer.echo(f"  {r['symbol']}: Sharpe={r['sharpe']:.2f} DDraw={r['max_drawdown']:.2%} CostBps={r['average_cost_bps']:.2f}")


def main():  # entrypoint for python -m app.cli
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
