# 📊 E-Commerce Analytics & Modern Data Pipeline 

An end-to-end Modern Data Stack project designed to clean, model, and analyze data for a fast-growing e-commerce platform. This project showcases enterprise-grade data engineering and analytics capabilities, moving from raw data to advanced operational insights.

## 🛠️ Tech Stack & Architecture
- **Storage & Compute:** Google Cloud BigQuery (Data Warehouse)
- **Data Modeling:** SQL (dbt-inspired architecture with `Staging`, `Intermediate`, and `Marts` layers)
- **Advanced Analytics:** Python (Pandas, Seaborn, SciPy)
- **Data Visualization:** Looker Studio

## 🏗️ Data Pipeline Architecture
The pipeline follows a strict ELT (Extract, Load, Transform) architecture:
1. **`ecommerce_raw`**: Direct ingestion of operational source tables.
2. **`ecommerce_staging`**: Views dedicated to data cleaning, schema enforcement, and type casting.
3. **`ecommerce_intermediate`**: Physical tables embedding business logic (VAT isolation by country, net margin calculations, filtering cancelled orders).
4. **`ecommerce_marts`**: Optimized BI-ready stars-schema models (`Finance`, `Marketing Attribution`, `Customer Lifetime Value`).

## 📈 Advanced Statistical Models Built (Python)
- **Cohort Retention Matrix:** Visualizing customer lifetime value degradation month-over-month.
- **Pearson Correlation (Lagged Effects):** Mathematically proving a 24-48h delayed effect between Marketing Ad Spend and Net Revenue.
- **RFM Customer Segmentation:** Algorithmic categorization of the customer database into actionable segments (*Champions, Loyal, At Risk, Hibernating*).

## 🚀 Business Impact & Insights Discovered
- **The Swiss Border Bug:** Isolated a severe operational anomaly in Switzerland where a 10% delivery failure rate due to custom clearing issues was destroying product margin.
- **Black Friday ROI Trap:** Proved that while revenue spiked during late November, the aggressive -30% discount codes actually reduced the brand's overall net margin.

Link Dashboard Looker Studio : 
https://datastudio.google.com/reporting/d2c92754-68d4-49bb-856e-b8f0b792d9e3
