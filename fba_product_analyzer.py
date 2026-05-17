def get_float(prompt):
    while True:
        try:
            value = float(input(prompt))
            if value < 0:
                print("Enter a positive number.")
                continue
            return value
        except ValueError:
            print("Invalid input. Enter a number.")


def get_choice(prompt, choices):
    while True:
        value = input(prompt).strip().lower()
        if value in choices:
            return value
        print(f"Choose one of: {', '.join(choices)}")


def calculate_score(margin, roi, reviews, competition, differentiation):
    score = 0

    # Margin (25)
    if margin >= 40:
        score += 25
    elif margin >= 30:
        score += 20
    elif margin >= 20:
        score += 10

    # ROI (25)
    if roi >= 100:
        score += 25
    elif roi >= 70:
        score += 20
    elif roi >= 40:
        score += 10

    # Reviews (20)
    if reviews <= 200:
        score += 20
    elif reviews <= 500:
        score += 12
    elif reviews <= 1000:
        score += 6

    # Competition (15)
    if competition == "low":
        score += 15
    elif competition == "medium":
        score += 8

    # Differentiation (15)
    if differentiation == "high":
        score += 15
    elif differentiation == "medium":
        score += 8

    return score


print("\n=== FBA PRODUCT ANALYZER ===\n")

# --- Inputs ---
product_name = input("Product name: ")

unit_cost = get_float("Unit cost: $")
shipping = get_float("Shipping per unit: $")
selling_price = get_float("Selling price: $")

fee_type = get_choice("Fee type (percent/fixed): ", ["percent", "fixed"])

if fee_type == "percent":
    fee_percent = get_float("Fee percent (%): ")
    fees = selling_price * (fee_percent / 100)
else:
    fees = get_float("Fixed fee: $")

reviews = int(get_float("Avg competitor reviews: "))
competition = get_choice("Competition (low/medium/high): ", ["low", "medium", "high"])
differentiation = get_choice("Differentiation (low/medium/high): ", ["low", "medium", "high"])

# --- Calculations ---
landed_cost = unit_cost + shipping
profit = selling_price - landed_cost - fees

margin = (profit / selling_price) * 100 if selling_price > 0 else 0
roi = (profit / landed_cost) * 100 if landed_cost > 0 else 0

score = calculate_score(margin, roi, reviews, competition, differentiation)

# --- Decision ---
if score >= 75:
    decision = "STRONG OPPORTUNITY"
elif score >= 55:
    decision = "VALIDATE FURTHER"
else:
    decision = "AVOID"

# --- Bulk Insight ---
if shipping > unit_cost:
    bulk_flag = "Shipping heavy — must validate bulk freight"
elif shipping < unit_cost * 0.5:
    bulk_flag = "Likely improves in bulk"
else:
    bulk_flag = "Moderate shipping impact"

# --- Output ---
print("\n=== RESULTS ===")
print(f"Product: {product_name}")
print(f"Landed Cost: ${landed_cost:.2f}")
print(f"Fees: ${fees:.2f}")
print(f"Profit: ${profit:.2f}")
print(f"Margin: {margin:.2f}%")
print(f"ROI: {roi:.2f}%")
print(f"Score: {score}/100")
print(f"Decision: {decision}")
print(f"Bulk Insight: {bulk_flag}")

# --- Claude Ready Output ---
print("\n=== COPY INTO CLAUDE ===\n")

print(f"""
Ingest this product:

Product name: {product_name}
Unit cost: ${unit_cost:.2f}
Shipping per unit: ${shipping:.2f}
Selling price: ${selling_price:.2f}
Fees: ${fees:.2f}

Landed cost: ${landed_cost:.2f}
Profit: ${profit:.2f}
Margin: {margin:.2f}%
ROI: {roi:.2f}%

Average competitor reviews: {reviews}
Competition: {competition}
Differentiation: {differentiation}

Opportunity Score: {score}/100
Decision: {decision}

Bulk Insight: {bulk_flag}

Analyze this product, update the product page, update index.md, and log it.
""")