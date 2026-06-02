import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import date, timedelta
import os
fake = Faker()
np.random.seed(42)
random.seed(42)

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- Reference Data ----
BRANDS = ["Ram", "Jeep", "Dodge", "Chrysler", "Alfa Romeo", "Fiat"]

SEGMENTS = {
    "Truck":        {"brands": ["Ram"],                        "msrp_range": (35000, 82000)},
    "SUV":          {"brands": ["Jeep", "Dodge"],              "msrp_range": (28000, 75000)},
    "Crossover":    {"brands": ["Jeep", "Fiat"],               "msrp_range": (22000, 45000)},
    "Sedan":        {"brands": ["Chrysler", "Alfa Romeo"],     "msrp_range": (25000, 58000)},
    "Sports":       {"brands": ["Dodge", "Alfa Romeo"],        "msrp_range": (32000, 75000)},
    "Minivan":      {"brands": ["Chrysler"],                   "msrp_range": (33000, 48000)},
    "Commercial":   {"brands": ["Ram"],                        "msrp_range": (38000, 68000)},
}

# Discount rate by channel: (min%, max%) of MSRP
CHANNEL_DISCOUNT = {
    "Retail":  (0.01, 0.08),   # typical consumer deal
    "Fleet":   (0.06, 0.16),   # corporate/gov contracts, high volume low margin
    "Rental":  (0.10, 0.20),   # fleet disposal pricing
}

# Channel mix weights: Retail is dominant, Fleet and Rental are secondary
CHANNEL_WEIGHTS = [0.76, 0.16, 0.08]   # Retail, Fleet, Rental

FINANCE_TYPES = ["Cash", "Loan", "Lease"]
# Lease skews toward Crossover/Sedan/SUV; Cash skews older buyers; Loan is modal
FINANCE_WEIGHTS_BY_SEGMENT = {
    "Truck":      [0.15, 0.65, 0.20],
    "SUV":        [0.10, 0.50, 0.40],
    "Crossover":  [0.12, 0.45, 0.43],
    "Sedan":      [0.18, 0.48, 0.34],
    "Sports":     [0.20, 0.45, 0.35],
    "Minivan":    [0.20, 0.60, 0.20],
    "Commercial": [0.05, 0.80, 0.15],  # commercial almost always financed
}

REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]

# Q4 incentive boost — additional discount layered on top of channel discount
def q4_discount_boost(sale_date):
    """Returns an additional discount rate applied in Q4 (Oct-Dec) to simulate
    year-end push incentives — mirrors Stellantis model year clearance behavior."""
    if sale_date.month in [10, 11, 12]:
        return np.random.uniform(0.01, 0.04)
    elif sale_date.month in [7, 8, 9]:  # slight Q3 bump for model year changeover
        return np.random.uniform(0.00, 0.015)
    else:
        return 0.0

def load_dimension_ids():
    """Pull dealer_ids and VINs from previously generated dimension CSVs."""
    dealers_df = pd.read_csv(f"{OUTPUT_DIR}/dim_dealers.csv")
    dealers_df.columns = dealers_df.columns.str.lower()  # ensure lowercase for consistency
    vehicles_df = pd.read_csv(f"{OUTPUT_DIR}/dim_vehicles.csv")
    vehicles_df.columns = vehicles_df.columns.str.lower()  # ensure lowercase for consistency
    return dealers_df, vehicles_df

def generate_fact_vehicle_sales(n=15000):
    print(f"Generating {n} vehicle sales transactions...")
    dealers_df, vehicles_df = load_dimension_ids()
    dealer_ids = dealers_df["dealer_id"].tolist()
    
    records = []

# Date range: 3 full fiscal years to enable YoY comparisons
    start_date = date(2022, 1, 1)
    end_date   = date(2024, 12, 31)
    date_range_days = (end_date - start_date).days

    for i in range(n):
        # --- Pick a vehicle from dim_vehicles ---
        vehicle_row = vehicles_df.sample(1).iloc[0]
        vin         = vehicle_row["vin"]
        segment     = vehicle_row["segment"]
        msrp        = float(vehicle_row["msrp"])

# --- Pick a dealer ---
        dealer_id = random.choice(dealer_ids)

# --- Sale date with slight Q4 volume skew ---
        # Weight date selection so Q4 has ~30% more transactions
        rand_day = random.randint(0, date_range_days)
        sale_date = start_date + timedelta(days=rand_day)

# Rejection sampling to lightly inflate Q4 volume
        # ~30% of the time, if not in Q4, resample once more
        if sale_date.month not in [10, 11, 12]:
            if random.random() < 0.23:
                rand_day  = random.randint(0, date_range_days)
                sale_date = start_date + timedelta(days=rand_day)

# --- Sales channel ---
        channel = random.choices(
            ["Retail", "Fleet", "Rental"],
            weights=CHANNEL_WEIGHTS
        )[0]

# Rental channel almost never leases; Fleet rarely leases
        if channel == "Rental":
            finance_type = random.choices(
                FINANCE_TYPES, weights=[0.10, 0.88, 0.02]
            )[0]
        elif channel == "Fleet":
            finance_type = random.choices(
                FINANCE_TYPES, weights=[0.08, 0.85, 0.07]
            )[0]
        else:
            weights = FINANCE_WEIGHTS_BY_SEGMENT.get(segment, [0.15, 0.55, 0.30])
            finance_type = random.choices(FINANCE_TYPES, weights=weights)[0]

# --- Discount calculation ---
        ch_min, ch_max = CHANNEL_DISCOUNT[channel]
        base_discount_rate = np.random.uniform(ch_min, ch_max)

        # Segment modifier: trucks negotiate harder than sedans
        segment_modifier = {
            "Truck":      0.010,
            "Commercial": 0.015,
            "Minivan":    0.008,
            "SUV":        0.005,
            "Crossover":  0.003,
            "Sedan":      0.002,
            "Sports":     0.000,  # sports cars hold price
        }.get(segment, 0.0)

        # Q4 / model-year-end boost
        seasonal_boost = q4_discount_boost(sale_date)

        total_discount_rate = min(
            base_discount_rate + segment_modifier + seasonal_boost,
            0.25  # hard cap: no deal exceeds 25% off MSRP
        )

        discount_amount = round(msrp * total_discount_rate, 2)
        sale_price      = round(msrp - discount_amount, 2)

        # --- Days on lot ---
        # Rental/Fleet inventory moves faster (bulk delivery)
        # Hot segments (Truck, SUV) also move faster at retail
        if channel in ["Fleet", "Rental"]:
            days_on_lot = int(np.random.exponential(scale=12))
        elif segment in ["Truck", "SUV"]:
            days_on_lot = int(np.random.exponential(scale=28))
        else:
            days_on_lot = int(np.random.exponential(scale=45))

        days_on_lot = max(1, min(days_on_lot, 180))  # clamp 1–180 days

        # --- Trade-in ---
        # Retail customers trade in ~45% of the time; Fleet/Rental almost never
        if channel == "Retail":
            trade_in_flag = 1 if random.random() < 0.45 else 0
        else:
            trade_in_flag = 1 if random.random() < 0.04 else 0

        records.append({
            "sale_id":          i + 1,
            "vin":              vin,
            "dealer_id":        dealer_id,
            "sale_date":        sale_date.strftime("%Y-%m-%d"),
            "msrp":             msrp,
            "discount_amount":  discount_amount,
            "sale_price":       sale_price,
            "finance_type":     finance_type,
            "sales_channel":    channel,
            "trade_in_flag":    trade_in_flag,
            "days_on_lot":      days_on_lot,
        })

    df = pd.DataFrame(records)
    out_path = f"{OUTPUT_DIR}/fact_vehicle_sales.csv"
    df.to_csv(out_path, index=False)
    print(f"  Saved {len(df):,} rows → {out_path}")
    print(f"  Channel mix:\n{df['sales_channel'].value_counts(normalize=True).round(3)}")
    print(f"  Finance mix:\n{df['finance_type'].value_counts(normalize=True).round(3)}")
    print(f"  Avg discount rate: {(df['discount_amount'] / df['msrp']).mean():.1%}")
    return df

PROGRAM_TYPES = [
    "dealer_cash",
    "customer_cash",
    "apr_subvention",
    "lease_subvention",
    "conquest",
    "loyalty",
]
# Incentive amount ranges by program type (dollars or rate-equivalent)
INCENTIVE_RANGES = {
    "dealer_cash":      (500,   3500),
    "customer_cash":    (750,   5000),
    "apr_subvention":   (200,   1800),   # dollar-equivalent cost of rate buydown
    "lease_subvention": (800,   4500),
    "conquest":         (500,   2500),
    "loyalty":          (300,   1500),
}

# Typical program duration (days) by type
DURATION_BY_TYPE = {
    "dealer_cash":      (28, 90),
    "customer_cash":    (21, 60),
    "apr_subvention":   (30, 90),
    "lease_subvention": (28, 60),
    "conquest":         (45, 120),
    "loyalty":          (60, 180),
}

# Expected lift multiplier over baseline: (min, max)
# dealer_cash and customer_cash lift hardest; loyalty/apr lift modestly
LIFT_MULTIPLIER = {
    "dealer_cash":      (1.10, 1.45),
    "customer_cash":    (1.15, 1.55),
    "apr_subvention":   (1.05, 1.25),
    "lease_subvention": (1.10, 1.40),
    "conquest":         (1.03, 1.20),
    "loyalty":          (1.02, 1.15),
}

def generate_fact_incentive_programs(n=120):
    print(f"Generating {n} incentive program records...")
    
    records = []
    start_date_range = date(2022, 1, 1)
    end_date_range   = date(2024, 12, 31)
    date_range_days  = (end_date_range - start_date_range).days

# Dealer pool size — pulled from dim_dealers if available, else default
    try:
        dealers_df = pd.read_csv(f"{OUTPUT_DIR}/dim_dealers.csv")
        total_dealers = len(dealers_df)
    except FileNotFoundError:
        total_dealers = 250

    for i in range(n):
        # --- Assign brand and segment ---
        brand = random.choice(BRANDS)

# Pick segment eligible for this brand
        eligible_segments = [
            seg for seg, meta in SEGMENTS.items()
            if brand in meta["brands"]
        ]
        if not eligible_segments:
            eligible_segments = list(SEGMENTS.keys())
        segment = random.choice(eligible_segments)

# --- Program type ---
        program_type = random.choice(PROGRAM_TYPES)

# --- Dates ---
        dur_min, dur_max = DURATION_BY_TYPE[program_type]
        duration_days = random.randint(dur_min, dur_max)

        prog_start_offset = random.randint(0, date_range_days - duration_days)
        prog_start = start_date_range + timedelta(days=prog_start_offset)
        prog_end   = prog_start + timedelta(days=duration_days)

# Q4 programs are more aggressive
        is_q4 = prog_start.month in [10, 11, 12]
        q4_multiplier = np.random.uniform(1.10, 1.25) if is_q4 else 1.0

# --- Incentive amount ---
        amt_min, amt_max = INCENTIVE_RANGES[program_type]
        incentive_amount = round(
            random.randint(amt_min, amt_max) * q4_multiplier, -2  # round to nearest $100
        )

# --- Dealer participation ---
        # eligible_dealer_count: subset of network targeted by this program
        # participating_dealer_count: those who actually opt in (always <= eligible)
        eligible_share      = np.random.uniform(0.30, 0.85)
        participation_rate  = np.random.uniform(0.55, 0.95)

        eligible_dealer_count     = max(10, int(total_dealers * eligible_share))
        participating_dealer_count = max(5,  int(eligible_dealer_count * participation_rate))

# --- Baseline units ---
        # Simulates the 3-month pre-program average monthly run rate for this
        # brand/segment combination. This is what you'd expect to sell without
        # the program — the counterfactual denominator for Sales Lift.
        # Trucks and SUVs have higher baseline volume; Fiat/Alfa are niche.
        brand_volume_factor = {
            "Ram":       1.6,
            "Jeep":      1.4,
            "Dodge":     1.0,
            "Chrysler":  0.7,
            "Alfa Romeo":0.4,
            "Fiat":      0.3,
        }.get(brand, 1.0)

        segment_volume_factor = {
            "Truck":     1.8,
            "SUV":       1.5,
            "Crossover": 1.2,
            "Sedan":     0.9,
            "Sports":    0.6,
            "Minivan":   0.7,
            "Commercial":1.1,
        }.get(segment, 1.0)

# baseline = participating dealers × brand/segment volume × noise
        baseline_units = max(5, int(
            participating_dealer_count
            * brand_volume_factor
            * segment_volume_factor
            * np.random.uniform(0.04, 0.12)  # units per dealer per month
        ))

# --- Units sold during program (with lift) ---
        lift_min, lift_max = LIFT_MULTIPLIER[program_type]
        lift = np.random.uniform(lift_min, lift_max)

# Scale baseline to program duration (baseline is monthly; program may span multiple months)
        program_months   = max(1, duration_days / 30)
        expected_baseline_total = baseline_units * program_months

        units_sold_during_program = max(
            baseline_units,
            int(expected_baseline_total * lift * np.random.uniform(0.85, 1.15))
        )

# --- Program name ---
        year = prog_start.year
        quarter = (prog_start.month - 1) // 3 + 1
        program_name = (
            f"{year} Q{quarter} {brand} {segment} "
            f"{program_type.replace('_', ' ').title()}"
        )

        records.append({
            "program_id":                  i + 1,
            "program_name":                program_name,
            "brand":                       brand,
            "program_type":                program_type,
            "vehicle_segment":             segment,
            "start_date":                  prog_start.strftime("%Y-%m-%d"),
            "end_date":                    prog_end.strftime("%Y-%m-%d"),
            "incentive_amount":            incentive_amount,
            "eligible_dealer_count":       eligible_dealer_count,
            "participating_dealer_count":  participating_dealer_count,
            "baseline_units":              baseline_units,
            "units_sold_during_program":   units_sold_during_program,
        })

    df = pd.DataFrame(records)
    out_path = f"{OUTPUT_DIR}/fact_incentive_programs.csv"
    df.to_csv(out_path, index=False)
    print(f"  Saved {len(df):,} rows → {out_path}")
    print(f"  Program type mix:\n{df['program_type'].value_counts()}")
    print(f"  Avg incentive amount: ${df['incentive_amount'].mean():,.0f}")
    print(f"  Avg sales lift: {(df['units_sold_during_program'] / (df['baseline_units'] * (pd.to_datetime(df['end_date']) - pd.to_datetime(df['start_date'])).dt.days / 30)).mean():.2f}x")
    return df

def validate_outputs(sales_df, incentives_df):
    """Sanity checks on generated data — catch distribution problems early."""
    print("\n=== VALIDATION ===")
    
    # Sales checks
    assert sales_df["sale_price"].min() > 0, "Negative sale prices detected"
    assert (sales_df["discount_amount"] >= 0).all(), "Negative discounts detected"
    assert (sales_df["sale_price"] <= sales_df["msrp"]).all(), "Sale price exceeds MSRP"
    
    discount_rates = sales_df["discount_amount"] / sales_df["msrp"]
    print(f"Discount rate range: {discount_rates.min():.1%} – {discount_rates.max():.1%}")
    print(f"Discount rate mean:  {discount_rates.mean():.1%}")
    q4_sales = sales_df[pd.to_datetime(sales_df["sale_date"]).dt.month.isin([10,11,12])]
    non_q4   = sales_df[~pd.to_datetime(sales_df["sale_date"]).dt.month.isin([10,11,12])]
    print(f"Q4 avg discount:     {(q4_sales['discount_amount'] / q4_sales['msrp']).mean():.1%}")
    print(f"Non-Q4 avg discount: {(non_q4['discount_amount'] / non_q4['msrp']).mean():.1%}")
    assert (q4_sales["discount_amount"] / q4_sales["msrp"]).mean() > \
           (non_q4["discount_amount"] / non_q4["msrp"]).mean(), \
           "Q4 should have higher avg discounts than non-Q4"

# Incentive checks
    assert (incentives_df["participating_dealer_count"] <= incentives_df["eligible_dealer_count"]).all(), \
        "Participating count exceeds eligible count"
    assert (incentives_df["units_sold_during_program"] >= incentives_df["baseline_units"]).all(), \
        "units_sold should be >= baseline (program should not reduce sales)"
    
    lift = (
        incentives_df["units_sold_during_program"] /
        incentives_df["baseline_units"]
    )
    print(f"Avg program lift multiplier: {lift.mean():.2f}x")
    print(f"Lift range: {lift.min():.2f}x – {lift.max():.2f}x")
    print("\nAll validation checks passed.")

if __name__ == "__main__":
    sales_df      = generate_fact_vehicle_sales(n=15000)
    incentives_df = generate_fact_incentive_programs(n=120)
    validate_outputs(sales_df, incentives_df)
    print("\nDay 4 complete. Output files:")
    print("  data/fact_vehicle_sales.csv")
    print("  data/fact_incentive_programs.csv")

