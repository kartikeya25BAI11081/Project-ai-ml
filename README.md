# Project-ai-ml
# 📈 FinTech Projection Dashboard

A clean, modular Python desktop application for personal financial projection and risk assessment. Built with **Tkinter** (GUI) and standard-library Python (logic), with an optional **Matplotlib** chart embedded in the window.

---

## Features

- Input **Monthly Income**, **Monthly Expenses**, and **Risk Tolerance %**
- **CAGR projection** — deterministic Future Value formula for 5, 10, and 20-year horizons
- **Monte Carlo simulation** — up to 10,000 randomised annual-return paths; reports Mean, Median, P10 (pessimistic), and P90 (optimistic) terminal values
- **Risk Assessment** — colour-coded flags for deficit detection, high expense ratios (>50% and >75%), and extreme risk tolerance levels
- **Interactive chart** — MC confidence band + CAGR line plotted via Matplotlib
- **Threaded simulation** — UI stays responsive during heavy computation
- **Auto-scaling currency** — values displayed in Lakhs (L) or Crores (Cr) automatically

---

## Project Structure

```
fintech_sim/
├── logic.py       # Financial engine — no UI dependencies
├── gui.py         # Tkinter dashboard — imports logic.py
└── README.md
```

---

## Requirements

| Package      | Purpose                     | Required |
|--------------|-----------------------------|----------|
| Python 3.10+ | Core runtime                | ✅ Yes   |
| `tkinter`    | GUI (bundled with Python)   | ✅ Yes   |
| `matplotlib` | Embedded projection chart   | Optional |

> If `matplotlib` is not installed, the app still runs fully — the chart area shows install instructions instead.

---

## Installation

```bash
# 1. Clone or copy the fintech_sim folder
# 2. (Optional) Install matplotlib for the chart
pip install matplotlib
```

---

## Usage

```bash
cd fintech_sim
python gui.py
```

---

## How It Works

### Logic Module (`logic.py`)

| Component               | Description |
|-------------------------|-------------|
| `FinancialInput`        | Validates inputs; derives savings, expense ratio, return rate, and volatility |
| `cagr_projection()`     | `FV = P × [(1+r)^n − 1] / r` — deterministic annuity formula |
| `monte_carlo_projection()` | Simulates N independent annual-return paths using `Normal(mean, σ)` |
| `assess_risk()`         | Returns human-readable risk flags based on spending and risk profile |
| `run_projection()`      | Single public entry-point — runs all three horizons and returns `ProjectionResult` |
| `format_currency()`     | Auto-scales to ₹ Lakhs / Crores |

### Return Rate Mapping

| Risk Tolerance | Expected Annual Return | Volatility |
|----------------|------------------------|------------|
| 0% (min)       | 4%                     | 2%         |
| 50% (mid)      | 11%                    | 12%        |
| 100% (max)     | 18%                    | 22%        |

### Risk Flags

| Condition                    | Flag                              |
|------------------------------|-----------------------------------|
| Expenses > Income            | ⚠ Deficit warning                |
| Expense ratio > 75%          | 🔴 Critically high               |
| Expense ratio > 50%          | ⚠ High financial stress          |
| Risk tolerance < 20%         | ℹ Returns may not beat inflation  |
| Risk tolerance > 80%         | ⚡ Expect high portfolio swings   |

---

## Example Output (₹80,000 income · ₹35,000 expenses · 40% risk)

| Horizon | MC Mean   | CAGR      |
|---------|-----------|-----------|
| 5 Years | ₹35.88 L  | ₹32.71 L  |
| 10 Years| ₹92.65 L  | ₹84.43 L  |
| 20 Years| ₹3.24 Cr  | ₹2.96 Cr  |

---

## GUI Overview

| Section           | Description |
|-------------------|-------------|
| Input Panel       | Income, expenses, risk %, MC simulation count slider |
| Savings Summary   | Live: monthly/annual savings, expense ratio, expected return |
| Risk Assessment   | Colour-coded badge list of active risk flags |
| Snapshot Cards    | CAGR + MC stats card for each horizon (5 / 10 / 20 Y) |
| Projection Chart  | Matplotlib line chart with MC band and CAGR line |
| Status Bar        | Run summary after each projection |

---

## License

MIT — free to use, modify, and distribute.

