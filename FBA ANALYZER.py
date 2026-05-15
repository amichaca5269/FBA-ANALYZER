"""
FBA Product Analyzer — full-featured Amazon FBA opportunity calculator.

Includes:
  - Bundle-aware bulk shipping split
  - Real Amazon referral + FBA fulfillment fees (2025 rates)
  - PPC / advertising costs
  - Amazon storage fees (standard + peak season)
  - Return rate impact on real profit
  - Minimum price calculator (to hit target margins)
  - Monthly profit projection + sell-through timeline
  - Multi-product session with ranked comparison table
  - Save results to TXT and CSV
"""

import csv
import os
from datetime import datetime

# ── Amazon fee tables (2025 rates) ────────────────────────────────────────────

REFERRAL_FEES = {
    "1":  ("Apparel & Accessories",       17.0),
    "2":  ("Automotive",                  12.0),
    "3":  ("Baby Products",               15.0),
    "4":  ("Beauty & Personal Care",      15.0),
    "5":  ("Books",                       15.0),
    "6":  ("Electronics",                  8.0),
    "7":  ("Grocery & Gourmet Food",      15.0),
    "8":  ("Health & Household",          15.0),
    "9":  ("Home & Kitchen",              15.0),
    "10": ("Jewelry",                     20.0),
    "11": ("Kitchen & Dining",            15.0),
    "12": ("Musical Instruments",         15.0),
    "13": ("Office Products",             15.0),
    "14": ("Pet Supplies",                15.0),
    "15": ("Sports & Outdoors",           15.0),
    "16": ("Tools & Home Improvement",    15.0),
    "17": ("Toys & Games",                15.0),
    "18": ("Video Games & Consoles",      15.0),
    "19": ("Other / General",             15.0),
}

FBA_FEES = {
    "1":  ("Small Standard — up to 6 oz",       3.22),
    "2":  ("Small Standard — 6 to 12 oz",       3.40),
    "3":  ("Small Standard — 12 to 16 oz",      3.58),
    "4":  ("Large Standard — up to 6 oz",       3.86),
    "5":  ("Large Standard — 6 to 12 oz",       4.08),
    "6":  ("Large Standard — 12 to 16 oz",      4.24),
    "7":  ("Large Standard — 1 to 2 lb",        4.75),
    "8":  ("Large Standard — 2 to 3 lb",        5.45),
    "9":  ("Large Standard — 3 lb+",            6.37),
    "10": ("Small Oversize — up to 70 lb",      9.73),
    "11": ("Medium Oversize — up to 150 lb",   19.05),
    "12": ("Large / Special Oversize",         89.98),
}

STORAGE_RATE_STANDARD = 0.78   # $/cubic ft/month  Jan–Sep
STORAGE_RATE_PEAK     = 2.40   # $/cubic ft/month  Oct–Dec


# ── Print helpers ─────────────────────────────────────────────────────────────

W = 62  # output width

def line(char="="):
    print(char * W)

def header_line(title):
    print()
    line()
    pad = (W - len(title)) // 2
    print(" " * pad + title)
    line()
    print()

def section(title):
    print()
    print(f"  {title}")
    print("  " + "─" * (len(title) + 2))

def row(label, value, indent=4):
    print(f"{' ' * indent}{label:<22} {value}")

def fmt(value):
    return f"${value:.2f}" if value >= 0 else f"-${abs(value):.2f}"

def score_bar(score):
    filled = round(score / 5)
    return "[" + "█" * filled + "░" * (20 - filled) + "]"


# ── Input helpers ─────────────────────────────────────────────────────────────

def get_float(prompt, min_val=0.0, allow_zero=False):
    while True:
        try:
            val = float(input(f"  {prompt}: ").strip())
            if not allow_zero and val <= min_val:
                print(f"  ! Must be greater than {min_val}.")
            elif allow_zero and val < min_val:
                print("  ! Cannot be negative.")
            else:
                return val
        except ValueError:
            print("  ! Enter a valid number.")

def get_int(prompt, min_val=1):
    while True:
        try:
            val = int(input(f"  {prompt}: ").strip())
            if val < min_val:
                print(f"  ! Must be at least {min_val}.")
            else:
                return val
        except ValueError:
            print("  ! Enter a whole number.")

def get_yes_no(prompt):
    while True:
        val = input(f"  {prompt} (y/n): ").strip().lower()
        if val in ("y", "yes"):
            return True
        if val in ("n", "no"):
            return False
        print("  ! Enter y or n.")

def pick_referral_fee():
    print()
    print("  Select product category:")
    print()
    for k, (label, pct) in REFERRAL_FEES.items():
        print(f"    {k:>2}. {label:<34} {pct:.0f}%")
    print()
    while True:
        choice = input("  Enter number: ").strip()
        if choice in REFERRAL_FEES:
            label, pct = REFERRAL_FEES[choice]
            print(f"  > Referral fee: {pct:.0f}%  ({label})")
            return label, pct
        print(f"  ! Enter 1–{len(REFERRAL_FEES)}.")

def pick_fba_fee():
    print()
    print("  Select size / weight tier:")
    print()
    for k, (label, fee) in FBA_FEES.items():
        print(f"    {k:>2}. {label:<42} ${fee:.2f}")
    print()
    while True:
        choice = input("  Enter number: ").strip()
        if choice in FBA_FEES:
            label, fee = FBA_FEES[choice]
            print(f"  > FBA fulfillment fee: ${fee:.2f}  ({label})")
            return label, fee
        print(f"  ! Enter 1–{len(FBA_FEES)}.")

def get_competition():
    opts = {"low":"low","l":"low","medium":"medium","m":"medium","high":"high","h":"high"}
    while True:
        val = input("  Competition level (low / medium / high): ").strip().lower()
        if val in opts:
            return opts[val]
        print("  ! Enter: low, medium, or high.")


# ── Core calculations ─────────────────────────────────────────────────────────

def calculate(p):
    """Fills in all derived fields on the product dict."""
    price          = p["price"]
    landed         = p["cost_per_unit"] + p["shipping_per_unit"]
    referral_amt   = price * (p["referral_pct"] / 100)
    amazon_fees    = referral_amt + p["fba_fee"]
    return_loss    = price * (p["return_rate"] / 100)
    total_costs    = landed + amazon_fees + p["ppc"] + p["storage_per_unit"] + return_loss

    profit_no_ads  = price - landed - amazon_fees
    profit_w_ads   = profit_no_ads - p["ppc"]
    profit_w_stor  = profit_w_ads  - p["storage_per_unit"]
    profit_final   = profit_w_stor - return_loss

    margin = (profit_final / price * 100) if price > 0 else 0
    roi    = (profit_final / landed  * 100) if landed > 0 else 0

    p.update({
        "landed_cost":      landed,
        "referral_amt":     referral_amt,
        "amazon_fees":      amazon_fees,
        "return_loss":      return_loss,
        "total_costs":      total_costs,
        "profit_no_ads":    profit_no_ads,
        "profit_w_ads":     profit_w_ads,
        "profit_w_stor":    profit_w_stor,
        "profit":           profit_final,
        "margin":           margin,
        "roi":              roi,
        "total_investment": landed * p["units"],
        "total_profit":     profit_final * p["units"],
    })

    # Break-even
    revenue_net = price - amazon_fees - p["ppc"] - p["storage_per_unit"] - return_loss
    if revenue_net > 0:
        p["break_even"] = int((landed * p["units"]) / revenue_net) + 1
    else:
        p["break_even"] = None

    # Opportunity score
    p["s_margin"]      = score_margin(margin)
    p["s_roi"]         = score_roi(roi)
    p["s_reviews"]     = score_reviews(p["reviews"])
    p["s_competition"] = score_competition(p["competition"])
    p["score"]         = p["s_margin"] + p["s_roi"] + p["s_reviews"] + p["s_competition"]

    decision, rationale = get_decision(p["score"])
    p["decision"]  = decision
    p["rationale"] = rationale

    # Minimum prices for target margins
    fixed = landed + p["fba_fee"] + p["ppc"] + p["storage_per_unit"]
    min_prices = {}
    for target in [20, 25, 30, 40]:
        denom = 1 - p["referral_pct"]/100 - p["return_rate"]/100 - target/100
        min_prices[target] = fixed / denom if denom > 0 else None
    p["min_prices"] = min_prices

    # Monthly projection
    ms = p["monthly_sales"]
    if ms > 0:
        p["monthly_revenue"]       = ms * price
        p["monthly_profit"]        = ms * profit_final
        p["months_to_sell_through"] = p["units"] / ms
    else:
        p["monthly_revenue"]       = 0
        p["monthly_profit"]        = 0
        p["months_to_sell_through"] = None


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_margin(m):
    if m >= 40: return 30
    if m >= 30: return 24
    if m >= 20: return 18
    if m >= 10: return 10
    return 0

def score_roi(r):
    if r >= 100: return 30
    if r >= 75:  return 24
    if r >= 50:  return 18
    if r >= 25:  return 10
    return 0

def score_reviews(r):
    if r < 100:  return 20
    if r < 500:  return 15
    if r < 1000: return 8
    if r < 2000: return 3
    return 0

def score_competition(c):
    return {"low": 20, "medium": 10, "high": 0}[c]

def get_decision(score):
    if score >= 75:
        return "STRONG BUY", "High opportunity — metrics align well."
    if score >= 55:
        return "POTENTIAL", "Moderate opportunity — review risks before proceeding."
    return "AVOID", "Low opportunity — margins, ROI, or competition are unfavorable."


# ── Input collection ──────────────────────────────────────────────────────────

def collect_product():
    p = {}

    section("Product & Bundle")
    p["name"]          = input("  Product name: ").strip() or "Unnamed Product"
    p["units"]         = get_int("Units in this order")
    p["cost_per_unit"] = get_float("Product cost per unit ($)")

    total_ship = get_float("Total shipping for the whole order ($)", allow_zero=True)
    if total_ship == 0:
        print("  ! WARNING: $0 shipping is unrealistic.")
        print("    Typical: sea freight $1–$3/unit, air $3–$8/unit.")
    p["shipping_per_unit"] = total_ship / p["units"]
    p["total_shipping"]    = total_ship
    print(f"  > Shipping/unit: ${p['shipping_per_unit']:.2f}  "
          f"(${total_ship:.2f} ÷ {p['units']:,} units)")

    p["price"] = get_float("Selling price per unit ($)")

    section("Amazon Fees")
    p["category_label"], p["referral_pct"] = pick_referral_fee()
    p["fba_label"],      p["fba_fee"]      = pick_fba_fee()

    section("Advertising (PPC)")
    print("  Typical Amazon PPC cost per sale:")
    print("    New product   : $5 – $10")
    print("    Established   : $2 – $5")
    print("    Enter 0 if not running ads.")
    p["ppc"] = get_float("PPC / ad cost per unit sold ($)", allow_zero=True)

    section("Storage Fees")
    print("  Enter packaged product dimensions to calculate storage cost.")
    length = get_float("Package length (inches)")
    width  = get_float("Package width (inches)")
    height = get_float("Package height (inches)")
    cubic_feet = (length * width * height) / 1728
    print(f"  > Volume: {cubic_feet:.4f} cubic feet")
    months_stored = get_float("Avg months sitting in Amazon warehouse")
    peak = get_yes_no("Will inventory sit during Oct–Dec peak season?")
    rate = STORAGE_RATE_PEAK if peak else STORAGE_RATE_STANDARD
    p["storage_per_unit"] = cubic_feet * rate * months_stored
    p["cubic_feet"]       = cubic_feet
    p["months_stored"]    = months_stored
    p["peak_storage"]     = peak
    print(f"  > Storage cost: ${p['storage_per_unit']:.2f}/unit  "
          f"({'peak' if peak else 'standard'} rate ${rate}/cu ft × {months_stored:.1f} mo)")

    section("Returns")
    print("  Typical return rates by category:")
    print("    Electronics   : 10–15%")
    print("    Apparel       : 15–30%")
    print("    Home / Kitchen:  5–10%")
    print("    Other         :  5–8%")
    p["return_rate"] = get_float("Expected return rate (%)", allow_zero=True)

    section("Market Data")
    p["reviews"]     = get_int("Average competitor reviews", min_val=0)
    p["competition"] = get_competition()

    section("Monthly Projection")
    print("  How many units do you expect to sell per month?")
    p["monthly_sales"] = get_int("Estimated monthly sales (units)", min_val=1)

    calculate(p)
    return p


# ── Results output ────────────────────────────────────────────────────────────

def print_product_results(p):
    header_line(f"  RESULTS — {p['name'].upper()}")

    section("Bundle Order")
    row("Product:",         p["name"])
    row("Units Ordered:",   f"{p['units']:,}")
    row("Cost / Unit:",     f"${p['cost_per_unit']:.2f}")
    row("Total Shipping:",  f"${p['total_shipping']:.2f}")
    row("Shipping / Unit:", f"${p['shipping_per_unit']:.2f}  (÷ {p['units']:,} units)")
    row("Landed Cost:",     f"${p['landed_cost']:.2f}")

    section("Amazon Fees (per unit)")
    row("Category:",        p["category_label"])
    row("Referral Fee:",    f"${p['referral_amt']:.2f}  ({p['referral_pct']:.0f}% of ${p['price']:.2f})")
    row("FBA Fulfillment:", f"${p['fba_fee']:.2f}  ({p['fba_label']})")
    row("Total Amazon:",    f"${p['amazon_fees']:.2f}")

    section("All Costs Per Unit")
    row("Landed Cost:",     f"${p['landed_cost']:.2f}")
    row("Amazon Fees:",     f"${p['amazon_fees']:.2f}")
    row("PPC / Ads:",       f"${p['ppc']:.2f}")
    row("Storage:",         f"${p['storage_per_unit']:.2f}  ({p['cubic_feet']:.4f} cu ft × {p['months_stored']:.1f} mo)")
    row("Return Loss:",     f"${p['return_loss']:.2f}  ({p['return_rate']:.1f}% × ${p['price']:.2f})")
    print(f"    {'─' * 28}")
    row("TOTAL COSTS:",     f"${p['total_costs']:.2f}")

    section("Profit Layers (per unit)")
    row("Selling Price:",   f"${p['price']:.2f}")
    row("After Amazon:",    f"{fmt(p['profit_no_ads'])}")
    row("After PPC:",       f"{fmt(p['profit_w_ads'])}")
    row("After Storage:",   f"{fmt(p['profit_w_stor'])}")
    row("After Returns:",   f"{fmt(p['profit'])}  ← real profit")
    print(f"    {'─' * 28}")
    row("Net Margin:",      f"{p['margin']:.1f}%")
    row("ROI:",             f"{p['roi']:.1f}%")

    section("Bundle Totals")
    row("Total Invested:",  f"${p['total_investment']:,.2f}")
    row("Total Profit:",    fmt(p["total_profit"]))
    if p["break_even"]:
        row("Break-even:",  f"sell {p['break_even']} of {p['units']:,} units")
    else:
        row("Break-even:",  "N/A — not profitable per unit")

    section("Monthly Projection")
    row("Monthly Sales:",   f"{p['monthly_sales']:,} units")
    row("Monthly Revenue:", f"${p['monthly_revenue']:,.2f}")
    row("Monthly Profit:",  fmt(p["monthly_profit"]))
    if p["months_to_sell_through"]:
        mts = p["months_to_sell_through"]
        row("Sell-through:",f"{mts:.1f} months  ({mts/12:.1f} years)" if mts >= 12 else f"{mts:.1f} months")
    else:
        row("Sell-through:", "N/A")

    section("Minimum Price to Hit Target Margin")
    print(f"    (based on your costs — includes returns & storage)")
    print()
    for target, mp in p["min_prices"].items():
        if mp is None:
            print(f"    {target}% margin   →  not achievable (costs too high)")
        else:
            gap = mp - p["price"]
            note = f"  ✓ you're above" if gap <= 0 else f"  ↑ raise by ${gap:.2f}"
            print(f"    {target}% margin   →  ${mp:.2f}{note}")

    section("Market Context")
    row("Avg Competitor Reviews:", f"{p['reviews']:,}")
    row("Competition:",            p["competition"].capitalize())

    section("Opportunity Score")
    row("Margin score:",    f"{p['s_margin']:>3} / 30")
    row("ROI score:",       f"{p['s_roi']:>3} / 30")
    row("Reviews score:",   f"{p['s_reviews']:>3} / 20")
    row("Competition:",     f"{p['s_competition']:>3} / 20")
    print(f"    {'─' * 28}")
    row("Total:", f"{p['score']:>3} / 100  {score_bar(p['score'])}")

    print()
    line()
    pad = (W - len(p["decision"]) - 8) // 2
    print(" " * pad + f">>>  {p['decision']}  <<<")
    print()
    print(f"  {p['rationale']}")
    line()
    print()


# ── Comparison table ──────────────────────────────────────────────────────────

def print_comparison(products):
    ranked = sorted(products, key=lambda x: x["score"], reverse=True)

    header_line("  PRODUCT COMPARISON — RANKED BY SCORE")

    # Header row
    print(f"  {'#':<3} {'Product':<22} {'Price':>7} {'Margin':>8} {'ROI':>8} "
          f"{'Score':>6}  {'Decision'}")
    print("  " + "─" * 68)

    for i, p in enumerate(ranked, 1):
        print(f"  {i:<3} {p['name'][:22]:<22} "
              f"${p['price']:>6.2f} "
              f"{p['margin']:>7.1f}% "
              f"{p['roi']:>7.1f}% "
              f"{p['score']:>5}/100  "
              f"{p['decision']}")

    print()
    best = ranked[0]
    print(f"  Top pick: {best['name']}  (score {best['score']}/100)")
    print()


# ── File export ───────────────────────────────────────────────────────────────

def save_results(products):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder    = os.path.dirname(os.path.abspath(__file__))

    # ── TXT
    txt_path = os.path.join(folder, f"fba_results_{timestamp}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"FBA ANALYZER RESULTS — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 62 + "\n\n")
        for p in products:
            f.write(f"Product        : {p['name']}\n")
            f.write(f"Units Ordered  : {p['units']:,}\n")
            f.write(f"Selling Price  : ${p['price']:.2f}\n")
            f.write(f"Landed Cost    : ${p['landed_cost']:.2f}\n")
            f.write(f"Amazon Fees    : ${p['amazon_fees']:.2f}\n")
            f.write(f"PPC            : ${p['ppc']:.2f}\n")
            f.write(f"Storage/Unit   : ${p['storage_per_unit']:.2f}\n")
            f.write(f"Return Loss    : ${p['return_loss']:.2f}\n")
            f.write(f"Net Profit/Unit: {fmt(p['profit'])}\n")
            f.write(f"Margin         : {p['margin']:.1f}%\n")
            f.write(f"ROI            : {p['roi']:.1f}%\n")
            f.write(f"Total Invested : ${p['total_investment']:,.2f}\n")
            f.write(f"Total Profit   : {fmt(p['total_profit'])}\n")
            f.write(f"Monthly Profit : {fmt(p['monthly_profit'])}\n")
            f.write(f"Sell-through   : {p['months_to_sell_through']:.1f} months\n")
            f.write(f"Opp Score      : {p['score']}/100\n")
            f.write(f"Decision       : {p['decision']}\n")
            f.write("\n" + "-" * 62 + "\n\n")

    # ── CSV
    csv_path = os.path.join(folder, f"fba_results_{timestamp}.csv")
    fields = [
        "name", "units", "price", "cost_per_unit", "shipping_per_unit",
        "ppc", "storage_per_unit", "return_rate", "landed_cost",
        "amazon_fees", "profit_no_ads", "profit_w_ads", "profit",
        "margin", "roi", "total_investment", "total_profit",
        "monthly_sales", "monthly_revenue", "monthly_profit",
        "months_to_sell_through", "reviews", "competition", "score", "decision",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(products)

    print(f"\n  Saved TXT : {txt_path}")
    print(f"  Saved CSV : {csv_path}")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print()
    line()
    print("           FBA PRODUCT ANALYZER")
    line()
    print()
    print("  Analyze one product or many — ranked comparison at the end.")
    print("  Press Ctrl+C at any time to exit.")

    products = []

    while True:
        print()
        p = collect_product()
        print_product_results(p)
        products.append(p)

        if not get_yes_no("Analyze another product?"):
            break

    if len(products) > 1:
        print_comparison(products)

    if get_yes_no("Save results to file?"):
        save_results(products)

    print("  Done. Good luck with your sourcing.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Exiting. Goodbye.\n")
