# FBA Product Analyzer

A Python CLI tool for evaluating Amazon FBA product opportunities with real 2025 fee data.

## Features

- **Bundle-aware** — enter total shipping for the whole order, split automatically per unit
- **Real Amazon fees** — referral fees by category + FBA fulfillment fees by size tier (2025 rates)
- **PPC / Advertising** — factors in ad spend per unit sold
- **Storage fees** — calculates monthly Amazon storage cost from product dimensions (standard + peak season rates)
- **Return rate impact** — shows how returns erode your real profit per unit
- **Profit layers** — see profit step by step: after Amazon fees → after PPC → after storage → after returns
- **Minimum price calculator** — tells you the minimum selling price to hit 20%, 25%, 30%, and 40% margin
- **Monthly projection** — monthly revenue, profit, and sell-through timeline
- **Multi-product sessions** — analyze multiple products and get a ranked comparison table
- **Export results** — saves a `.txt` summary and `.csv` (Excel-ready) with timestamp

## How to Run

```bash
python "FBA ANALYZER.py"
```

Requires Python 3.8+. No external libraries needed.

## What It Calculates

| Metric | Description |
|---|---|
| Landed Cost | Product cost + shipping per unit |
| Amazon Fees | Referral fee + FBA fulfillment fee |
| Net Profit | After all costs including PPC, storage, returns |
| Margin | Net profit / selling price |
| ROI | Net profit / landed cost |
| Opportunity Score | 0–100 based on margin, ROI, reviews, competition |

## Opportunity Score Breakdown

| Factor | Max Points | Logic |
|---|---|---|
| Margin | 30 | ≥40% → 30 pts, scales down |
| ROI | 30 | ≥100% → 30 pts, scales down |
| Reviews | 20 | <100 reviews → 20 pts, scales down |
| Competition | 20 | Low → 20, Medium → 10, High → 0 |

## Decision Thresholds

- **STRONG BUY** — score ≥ 75
- **POTENTIAL** — score ≥ 55
- **AVOID** — score < 55

## Amazon Fee Rates (2025)

Referral fees range from 8% (Electronics) to 20% (Jewelry).
FBA fulfillment fees range from $3.22 (small standard) to $89.98 (large oversize).
Storage fees: $0.78/cubic ft/month (Jan–Sep), $2.40/cubic ft/month (Oct–Dec peak).
# FBA-ANALYZER
