import numpy as np
import pandas as pd
from scipy.optimize import minimize
from langchain_core.tools import tool
from typing import Dict, Any, List
import logging
import yfinance as yf

logger = logging.getLogger(__name__)

@tool
def optimize_portfolio(tickers: str, start_date: str, end_date: str) -> str:
    """Optimize a portfolio using Markowitz mean-variance optimization."""
    try:
        ticker_list = tickers.split(',')
        data = yf.download(ticker_list, start=start_date, end=end_date)['Adj Close']
        
        # Calculate returns
        returns = data.pct_change().dropna()
        
        # Calculate mean returns and covariance matrix
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        # Number of assets
        num_assets = len(ticker_list)
        
        # Function to minimize (negative Sharpe ratio)
        def negative_sharpe_ratio(weights):
            portfolio_return = np.sum(mean_returns * weights) * 252
            portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
            return -portfolio_return / portfolio_std
        
        # Constraints
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for asset in range(num_assets))
        
        # Initial guess
        initial_guess = num_assets * [1. / num_assets]
        
        # Optimize
        result = minimize(negative_sharpe_ratio, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        
        optimal_weights = result.x
        
        # Calculate portfolio metrics
        portfolio_return = np.sum(mean_returns * optimal_weights) * 252
        portfolio_std = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix * 252, optimal_weights)))
        sharpe_ratio = portfolio_return / portfolio_std
        
        result_str = f"Optimal Portfolio Allocation:\n"
        for i, ticker in enumerate(ticker_list):
            result_str += f"{ticker}: {optimal_weights[i]:.2%}\n"
        result_str += f"\nExpected Annual Return: {portfolio_return:.2%}\n"
        result_str += f"Expected Annual Volatility: {portfolio_std:.2%}\n"
        result_str += f"Sharpe Ratio: {sharpe_ratio:.2f}"
        
        return result_str
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        return f"Error optimizing portfolio: {e}"

@tool
def calculate_portfolio_risk_metrics(tickers: str, start_date: str, end_date: str) -> str:
    """Calculate risk metrics for a portfolio."""
    try:
        ticker_list = tickers.split(',')
        data = yf.download(ticker_list, start=start_date, end=end_date)['Adj Close']
        
        returns = data.pct_change().dropna()
        portfolio_returns = returns.mean(axis=1)  # Equal-weighted portfolio
        
        # Calculate VaR (95% confidence)
        var_95 = np.percentile(portfolio_returns, 5)
        
        # Calculate CVaR (Conditional VaR)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        
        # Calculate maximum drawdown
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        result = f"Portfolio Risk Metrics:\n"
        result += f"VaR (95%): {var_95:.2%}\n"
        result += f"CVaR (95%): {cvar_95:.2%}\n"
        result += f"Maximum Drawdown: {max_drawdown:.2%}"
        
        return result
    except Exception as e:
        logger.error(f"Error calculating risk metrics: {e}")
        return f"Error calculating risk metrics: {e}"

class PortfolioOptimizationToolkit:
    def __init__(self, config):
        self.config = config
        self.optimize_portfolio = optimize_portfolio
        self.calculate_portfolio_risk_metrics = calculate_portfolio_risk_metrics