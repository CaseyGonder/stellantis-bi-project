Dashboard 1: Sales Performance Command Center
Business question: Which Stellantis brands, segments, and regions are 
hitting retail sales targets, and what discount depth and days-on-lot 
patterns explain over- or under-performance?

Dashboard 2: Incentive Program Effectiveness Tracker
Business question: Which incentive program types (dealer cash, APR, 
lease, conquest) are generating the highest incremental units-sold 
per incentive dollar, and how does performance vary by brand and segment?

Dashboard 3: Finance & Payment Analytics (supporting view)
Business question: How is finance type mix (cash, retail finance, lease) 
shifting across brands and regions, and how does APR subvention 
penetration correlate with transaction price and discount depth?

# Stellantis Commercial Analytics Portfolio — Project Charter
Project Purpose

Demonstrate senior BI analyst capabilities aligned to the Stellantis 
Commercial Analytics team role by building a end-to-end analytics 
portfolio: synthetic data generation, SQL Server data warehouse, and 
two executive-facing Power BI dashboards covering vehicle sales 
performance and incentive program effectiveness.

Business Context

Stellantis Commercial Analytics supports brand-level and dealer-network 
decisions around retail sales targets, incentive program design, and 
finance product penetration. This project simulates that reporting 
environment using realistic synthetic data across Ram, Jeep, Dodge, 
Chrysler, Alfa Romeo, and Fiat brands.

Three Dashboard Products
| Dashboard | Business Question | Primary Audience |
|---|---|---|
| Sales Performance Command Center | Which brands, segments, and regions are hitting retail targets, and what operational patterns explain variance? | VP of Sales, Regional Directors |
| Incentive Program Effectiveness Tracker | Which program types deliver the highest incremental units per incentive dollar by brand and segment? | Incentive Strategy Team, Finance |
| Finance & Payment Analytics | How is finance type mix shifting, and how does APR subvention correlate with transaction price? | Commercial Finance, Pricing Team |

Data Architecture

Platform: SQL Server (local) → Power BI Desktop

Model type: Star schema with 2 fact tables, 4 dimension tables

Data source: Synthetic data generated in Python using Faker

Refresh: Static dataset (portfolio demonstration)
Scope

In scope: Sales data (2022–2024), incentive programs, dealer network, 
vehicle catalog, time intelligence, regional hierarchy
Out of scope: Real Stellantis proprietary data, live data refresh, 
inventory/ordering systems, warranty or service data

Data Model Summary

fact_vehicle_sales — one row per vehicle sold (VIN-level)

fact_incentive_programs — one row per program-period

dim_vehicles — vehicle catalog (VIN, brand, model, trim, segment)

dim_dealers — dealer master (dealer_id, region, state, metro_area)

dim_time — fiscal calendar (fiscal_week, fiscal_month, fiscal_quarter, 

  fiscal_year)
dim_regions — [see note below on this dimension]

Note on dim_regions:
dim_regions was listed in the initial schema sketch but has been folded into dim_dealers for this project. Here's the reasoning:
In a full Stellantis production environment, region hierarchy runs four levels deep — Zone → Region → District → Dealer — and would warrant its own dimension table. For this portfolio project, that level of complexity adds overhead without adding analytical value.
Instead, dim_dealers carries all the regional attributes you need:

region (Northeast / Southeast / Midwest / Southwest / West)
state
metro_area
dealer_group

This gives your dashboards full geographic sliceability without a separate join. If an interviewer asks why you didn't build dim_regions separately, your answer is: "I made a deliberate grain decision — for a two-dashboard portfolio the regional attributes live cleanly on the dealer dimension. In a production environment with zone-level reporting and multi-level hierarchy navigation I'd normalize that into its own table."
That answer demonstrates you understand the tradeoff, which is more impressive than just blindly building extra tables.
## Design Decision: dim_regions
Regional hierarchy (region, zone, market_area) is embedded in dim_dealers 
for this portfolio project, consistent with how many automotive DWs 
handle dealer-centric geographic rollups. A separate dim_regions table 
is defined for extensibility but joins through dim_dealers in practice.

Add that to your docs folder as well — it shows the kind of documented design decision that the JD language around "strong governance" is looking for.

Deliverables

Python data generation scripts (/data-gen)

SQL Server schema + views (/sql)

Power BI dashboard files (/powerbi)

Project documentation (/docs)

Timeline

14 days | Phases: Architecture → Data Gen → SQL → Power BI → Polish

Author

Casey Gonder | [5/31/2026]