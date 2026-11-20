# GTA VI Trophy Rarity Forecast

Forecast how many GTA VI players earn each trophy in week one after launch.

## About

This repository contains a Python program that forecasts the earn rate (percentage of players who have earned each trophy) for every trophy in Grand Theft Auto VI on PlayStation 5, one week after launch.

The program reads input cases from the `/input` directory, analyzes trophy rate history, and writes forecast quantiles to the `/output` directory.

## How It Works

- **Input**: JSON case files containing trophy data and historical rate readings
- **Process**: Analyzes each trophy's rate history for trend and volatility
- **Output**: JSON files with 5 quantiles (0.05, 0.25, 0.5, 0.75, 0.95) for each trophy

## Competition

- **make.fun**: [gta6-trophy-rarity-forecast-01](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
- **Forecast target**: 2026-11-26T00:00:00Z (one week after launch)
- **Deadline**: 2026-11-21T11:30:00Z

## Badges

[![make.fun](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![Rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/slavaolena/gta6-trophy-rarity-forecast-01/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![Reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/slavaolena/gta6-trophy-rarity-forecast-01/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)

## Usage

```bash
# Set environment variables
export MAKEFUN_INPUT_DIR=/path/to/input
export MAKEFUN_OUTPUT_DIR=/path/to/output

# Run the forecasting program
python3 main.py
```

## Requirements

- Python 3.13+
- Standard library only (no external dependencies)