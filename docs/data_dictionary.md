# Stellantis Commercial Analytics — Data Dictionary
Project: Stellantis BI Portfolio — Commercial Analytics  
Author: Casey Gonder  
Last Updated: [today's date]  
Purpose: Defines grain, keys, columns, data types, and valid value ranges for all tables in the stellantis-bi-project data model. This document governs synthetic data generation, SQL schema design, and Power BI model relationships.
---

Data Model Overview
| Table | Type | Grain |
|---|---|---|
| fact_vehicle_sales | Fact | One row per vehicle sold (one transaction per VIN) |
| fact_incentive_programs | Fact | One row per incentive program per active period |
| dim_vehicles | Dimension | One row per unique vehicle configuration (VIN) |
| dim_dealers | Dimension | One row per franchised dealer location |
| dim_time | Dimension | One row per calendar date |

---

## fact_vehicle_sales
Grain: One row = one completed vehicle sale transaction. Each VIN appears exactly once.  
Primary Key: sale_id  
Foreign Keys: VIN → dim_vehicles.VIN | dealer_id → dim_dealers.dealer_id | sale_date → dim_time.date_id

| Column | Data Type | Description | Valid Range / Example Values |
|---|---|---|---|
| sale_id | INT (PK, IDENTITY) | Surrogate key, auto-incremented per transaction | 1, 2, 3 … 50,000 |
| VIN | VARCHAR(17) | Vehicle Identification Number; joins to dim_vehicles | 17-char alphanumeric, e.g. 1C4RJFAG0NC123456 |
| dealer_id | INT (FK) | Joins to dim_dealers; identifies selling dealer | 1001–1500 |
| sale_date | DATE (FK) | Date the sale was finalized; joins to dim_time.date_id | 2022-01-01 to 2024-12-31 |
| sale_price | DECIMAL(10,2) | Final transaction price after all negotiation and discounts | $18,000–$95,000 |
| MSRP | DECIMAL(10,2) | Manufacturer's Suggested Retail Price at time of sale | $22,000–$110,000 |
| discount_amount | DECIMAL(10,2) | Total dollar discount off MSRP (dealer + customer incentives combined) | $0–$12,000; typically $500–$5,000 |
| finance_type | VARCHAR(20) | How the buyer financed the vehicle | 'Cash', 'Finance', 'Lease', 'Fleet' |
| trade_in_flag | BIT | 1 = buyer traded in a vehicle, 0 = no trade | 0, 1 |
| days_on_lot | INT | Number of days vehicle sat on dealer lot before sale | 0–365; target range 15–75 for healthy inventory |

Business Rules:

sale_price must always be ≤ MSRP

discount_amount = MSRP − sale_price (derived, but stored for query performance)

No VIN may appear more than once (one vehicle sold once)

sale_date must fall within an active fiscal period in dim_time
---

## fact_incentive_programs
Grain: One row = one incentive program for one brand during one active program period. The same program_id can recur across model years but not overlap dates within the same brand/segment.  
Primary Key: program_id  
Foreign Keys: None direct — joined to dim_vehicles via brand + vehicle_segment match; date range spans dim_time

| Column | Data Type | Description | Valid Range / Example Values |
|---|---|---|---|
| program_id | INT (PK, IDENTITY) | Surrogate key per unique program offering | 1–500 |
| program_name | VARCHAR(100) | Descriptive marketing name of the incentive program | 'Ram Truck Month', 'Jeep Spring Sales Event' |
| brand | VARCHAR(30) | Stellantis brand the program applies to | 'Ram', 'Jeep', 'Dodge', 'Chrysler', 'Alfa Romeo', 'Fiat' |
| program_type | VARCHAR(30) | Category of incentive offered | 'Dealer Cash', 'Customer Cash', 'APR Subvention', 'Lease Subvention', 'Conquest' |
| vehicle_segment | VARCHAR(30) | Vehicle segment the program targets | 'Truck', 'SUV', 'Sedan', 'Minivan', 'Sports Car', 'Crossover' |
| start_date | DATE | First day the incentive program is active | 2022-01-01 to 2024-12-31 |
| end_date | DATE | Last day the incentive program is active | Must be ≥ start_date; programs typically run 30–90 days |
| incentive_amount | DECIMAL(10,2) | Dollar value of the incentive offered per unit | $250–$7,500; APR/lease programs may store rate discount as dollar equivalent |
| participating_dealer_count | INT | Number of dealers enrolled in the program | 50–1,400 |
| units_sold_during_program | INT | Total units sold under this program during its active period | 100–25,000 |

Business Rules:

end_date must always be ≥ start_date

A given brand + program_type + vehicle_segment combination should not have overlapping date ranges

units_sold_during_program is an aggregate stored at the program grain — not a join to individual VINs (this is intentional: reflects how Stellantis reports program-level lift)

Conquest programs apply across brands and may show lower participating_dealer_count
---

## dim_vehicles
Grain: One row = one unique vehicle configuration, identified by VIN.  
Primary Key: VIN  
Foreign Keys: None (dimension source)

| Column | Data Type | Description | Valid Range / Example Values |
|---|---|---|---|
| VIN | VARCHAR(17) (PK) | Vehicle Identification Number | 17-char alphanumeric |
| brand | VARCHAR(30) | Stellantis brand | 'Ram', 'Jeep', 'Dodge', 'Chrysler', 'Alfa Romeo', 'Fiat' |
| model | VARCHAR(50) | Vehicle model name | 'Ram 1500', 'Grand Cherokee', 'Durango', 'Pacifica', 'Giulia', '500X' |
| trim | VARCHAR(50) | Trim level designation | 'Tradesman', 'Laramie', 'Limited', 'Rubicon', 'Scat Pack', 'Touring' |
| MSRP | DECIMAL(10,2) | Base MSRP for this vehicle configuration | $22,000–$110,000 |
| segment | VARCHAR(30) | Vehicle segment classification | 'Truck', 'SUV', 'Sedan', 'Minivan', 'Sports Car', 'Crossover' |

---

## dim_dealers
Grain: One row = one franchised dealer physical location.  
Primary Key: dealer_id  
Foreign Keys: None (dimension source)

| Column | Data Type | Description | Valid Range / Example Values |
|---|---|---|---|
| dealer_id | INT (PK) | Unique dealer identifier | 1001–1500 |
| dealer_name | VARCHAR(100) | Dealer business name | 'Auburn Hills CDJR', 'Motor City Ram' |
| region | VARCHAR(30) | Stellantis sales region | 'Northeast', 'Southeast', 'Midwest', 'Southwest', 'West', 'Central' |
| dealer_group | VARCHAR(100) | Parent dealer group if part of a multi-store group | 'AutoNation', 'Penske', 'Independent' |
| state | CHAR(2) | US state abbreviation | 'MI', 'TX', 'FL', 'CA', 'OH' |
| metro_area | VARCHAR(50) | Metropolitan area or city | 'Detroit', 'Dallas-Fort Worth', 'Miami', 'Los Angeles' |

---

## dim_time
Grain: One row = one calendar date.  
Primary Key: date_id  
Foreign Keys: None (dimension source)

| Column | Data Type | Description | Valid Range / Example Values |
|---|---|---|---|
| date_id | DATE (PK) | Calendar date; serves as the join key | 2022-01-01 to 2024-12-31 |
| date | DATE | Duplicate of date_id for readability in reports | Same as date_id |
| fiscal_week | INT | Stellantis fiscal week number within fiscal year | 1–52 |
| fiscal_month | INT | Fiscal month number | 1–12 |
| fiscal_quarter | VARCHAR(6) | Fiscal quarter label | 'FY2023Q1', 'FY2024Q3' |
| fiscal_year | INT | Fiscal year | 2022, 2023, 2024 |
| model_year_flag | VARCHAR(6) | Model year the date falls in for inventory planning | 'MY2023', 'MY2024' |

---

## Views (defined in SQL, documented here for reference)
| View | Source Tables | Purpose |
|---|---|---|
| vw_sales_performance | fact_vehicle_sales, dim_vehicles, dim_dealers, dim_time | Pre-joined sales data with brand, region, and fiscal period context for Power BI |
| vw_incentive_analysis | fact_incentive_programs, dim_time | Incentive program performance with date range expansion and cost-per-unit calculation |
| vw_executive_kpis | All tables | Aggregate KPIs: total units, total revenue, average discount rate, days-on-lot by brand and region |

---

Key Metric Definitions
| Metric | Formula | Notes |
|---|---|---|
| Discount Rate | (MSRP − sale_price) / MSRP | Expressed as a percentage; benchmark is 8–15% for Stellantis volume brands |
| Incentive Cost Per Unit | incentive_amount × units_sold_during_program / units_sold_during_program | = incentive_amount at the program grain |
| Days on Lot | days_on_lot | 0–30 = fast mover; 31–75 = normal; 76+ = aging inventory |
| Finance Mix | COUNT(sale_id) WHERE finance_type = 'X' / COUNT(sale_id) | Lease mix, finance mix, cash mix — key to APR subvention program ROI |

---

