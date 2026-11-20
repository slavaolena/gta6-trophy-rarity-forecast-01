#!/usr/bin/env python3
"""
GTA VI Trophy Rarity Forecast - From Scratch
Predicts quantiles of trophy earn rates for week one after launch.
"""

import json
import os
import math
import sys
from typing import List, Dict, Any

# Constants
LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]


def logit(p: float) -> float:
    """Logit transform: ln(p / (1-p)) with p clamped to (0.01, 0.99)."""
    p = max(0.01, min(0.99, p))
    return math.log(p / (1 - p))


def expit(x: float) -> float:
    """Inverse logit: 1 / (1 + exp(-x))."""
    return 1 / (1 + math.exp(-x))


def clamp_rate(rate: float) -> float:
    """Clamp rate to valid range [0, 100]."""
    return max(0.0, min(100.0, rate))


def parse_rate(rate_str: str) -> float:
    """Parse rate string like '1.10' to float."""
    try:
        return float(rate_str)
    except (ValueError, TypeError):
        return 0.0


def analyze_trophy_history(histories: List[Dict]) -> Dict[str, Any]:
    """
    Analyze trophy rate history and return features for forecasting.
    """
    if not histories:
        return {"last_rate": 0.0, "mean_rate": 0.0, "trend": 0.0, "volatility": 0.0, "n_reads": 0}
    
    rates = []
    for h in histories:
        rate = h.get('rate')
        if rate is not None:
            rates.append(rate)
    
    if not rates:
        return {"last_rate": 0.0, "mean_rate": 0.0, "trend": 0.0, "volatility": 0.0, "n_reads": 0}
    
    last_rate = rates[-1]
    mean_rate = sum(rates) / len(rates)
    
    # Trend: simple linear regression slope
    n = len(rates)
    if n > 1:
        x_mean = (n - 1) / 2
        y_mean = mean_rate
        numerator = sum((i - x_mean) * (rates[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        trend = numerator / denominator if denominator > 0 else 0.0
    else:
        trend = 0.0
    
    # Volatility: standard deviation of rates
    if n > 1:
        variance = sum((r - mean_rate) ** 2 for r in rates) / (n - 1)
        volatility = math.sqrt(variance) if variance > 0 else 0.0
    else:
        volatility = 0.0
    
    return {
        "last_rate": last_rate,
        "mean_rate": mean_rate,
        "trend": trend,
        "volatility": volatility,
        "n_reads": n
    }


def forecast_trophy_quantiles(trophy_id: int, history: List[Dict], horizon_days: float) -> Dict:
    """
    Forecast quantiles for a single trophy.
    
    Uses a diffusion-based model: rates follow a random walk on the logit scale
    with drift toward the mean. Quantiles are generated from the predicted distribution.
    """
    analysis = analyze_trophy_history(history)
    last_rate = analysis["last_rate"]
    trend = analysis["trend"]
    volatility = analysis["volatility"]
    mean_rate = analysis["mean_rate"]
    n_reads = analysis["n_reads"]
    
    # Convert to logit scale
    last_logit = logit(last_rate / 100)
    mean_logit = logit(mean_rate / 100) if mean_rate > 0 else 0.0
    
    # Horizon in logit-diffusion units
    # Diffusion scales with sqrt(horizon)
    diffusion_scale = math.sqrt(horizon_days) * 0.5  # Calibrated to ~1 week horizon
    
    # Drift toward mean (mean reversion)
    if n_reads >= 2:
        # Estimate mean reversion strength from trend vs volatility
        reversion_strength = 0.1 / (1 + volatility / 10)  # weaker reversion for volatile trophies
    else:
        reversion_strength = 0.05
    
    # Predicted mean: starts at last rate, drifts toward global mean
    drift_hours = horizon_days * 24
    drift_toward_mean = reversion_strength * drift_hours * (mean_logit - last_logit)
    predicted_mean_logit = last_logit + drift_toward_mean + trend * drift_hours
    
    # Predicted volatility over horizon
    predicted_vol = volatility * math.sqrt(horizon_days) if volatility > 0 else 1.0
    
    # Generate quantiles on logit scale
    # Using normal approximation around predicted mean
    quantiles = []
    for tau in LEVELS:
        # Standard normal quantile (pre-computed)
        z = {
            0.05: -1.645,
            0.25: -0.674,
            0.5: 0.0,
            0.75: 0.674,
            0.95: 1.645
        }[tau]
        
        # Quantile on logit scale
        q_logit = predicted_mean_logit + z * predicted_vol
        
        # Convert back to rate
        q_rate = expit(q_logit) * 100
        
        # Clamp to valid range
        q_rate = clamp_rate(q_rate)
        
        quantiles.append(round(q_rate, 4))
    
    # Ensure quantiles are non-decreasing
    for i in range(1, len(quantiles)):
        if quantiles[i] < quantiles[i-1]:
            quantiles[i] = quantiles[i-1]
    
    return {
        "id": trophy_id,
        "q": quantiles
    }


def process_case(input_path: str, output_path: str) -> Dict:
    """
    Process a single case: read input, forecast, write output.
    """
    with open(input_path, 'r') as f:
        case = json.load(f)
    
    case_id = case["id"]
    trophies = case["trophies"]
    horizon_minutes = case["horizon_minutes"]
    horizon_days = horizon_minutes / (24 * 60)
    
    forecasts = []
    
    for trophy in trophies:
        trophy_id = trophy["id"]
        
        # Extract history for this trophy
        history = []
        for h in case.get("history", []):
            rates = h.get("rates", [])
            if trophy_id <= len(rates) and rates[trophy_id - 1] is not None:
                rate = parse_rate(rates[trophy_id - 1])
                if rate > 0:
                    history.append({
                        "at": h["at"],
                        "rate": rate
                    })
        
        # Forecast quantiles
        forecast = forecast_trophy_quantiles(trophy_id, history, horizon_days)
        forecasts.append(forecast)
    
    # Write output
    output = {"trophies": forecasts}
    
    # Ensure output directory exists (or use existing)
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except PermissionError:
            # If we can't create, use a temp directory
            output_dir = "/tmp/forecast-output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, os.path.basename(output_path))
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    return output


def main():
    """
    Main entry point: process all .in files in input directory.
    """
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    
    # Find all .in files
    in_files = sorted([f for f in os.listdir(input_dir) if f.endswith(".in")])
    
    for in_file in in_files:
        case_id = in_file.replace(".in", "")
        input_path = os.path.join(input_dir, in_file)
        output_path = os.path.join(output_dir, f"{case_id}.out")
        
        print(f"Processing case: {case_id}")
        result = process_case(input_path, output_path)
        print(f"  Forecasted {len(result['trophies'])} trophies")
    
    print("Done!")


if __name__ == "__main__":
    main()
