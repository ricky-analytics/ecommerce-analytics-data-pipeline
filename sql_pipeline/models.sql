-- ==============================================================================
-- COUCHE 1 : STAGING (Nettoyage et Normalisation)
-- ==============================================================================

CREATE OR REPLACE VIEW `ecommerce_staging.stg_customers` AS
SELECT
  CAST(id AS STRING) AS customer_id,
  CAST(signup_date AS DATE) AS signup_date,
  CAST(first_acquisition_channel AS STRING) AS acquisition_channel,
  CAST(country AS STRING) AS country,
  CAST(age AS INT64) AS customer_age,
  CAST(gender AS STRING) AS customer_gender
FROM `ecommerce_raw.customers`;

CREATE OR REPLACE VIEW `ecommerce_staging.stg_products` AS
SELECT
  CAST(id AS STRING) AS product_id,
  CAST(name AS STRING) AS product_name,
  CAST(category AS STRING) AS product_category,
  CAST(cost_price AS FLOAT64) AS cost_price_eur,
  CAST(retail_price AS FLOAT64) AS retail_price_ttc_eur
FROM `ecommerce_raw.products`;

CREATE OR REPLACE VIEW `ecommerce_staging.stg_orders` AS
SELECT
  CAST(id AS STRING) AS order_id,
  CAST(customer_id AS STRING) AS customer_id,
  CAST(session_id AS STRING) AS session_id,
  CAST(order_date AS DATE) AS order_date,
  CAST(status AS STRING) AS order_status,
  CAST(payment_method AS STRING) AS payment_method,
  CAST(shipping_fees AS FLOAT64) AS shipping_fees_eur,
  COALESCE(discount_code_used, 'NO_CODE') AS discount_code
FROM `ecommerce_raw.orders`;

CREATE OR REPLACE VIEW `ecommerce_staging.stg_order_items` AS
SELECT
  CAST(item_id AS STRING) AS item_id,
  CAST(order_id AS STRING) AS order_id,
  CAST(product_id AS STRING) AS product_id,
  CAST(quantity AS INT64) AS quantity,
  CAST(item_status AS STRING) AS item_status,
  CAST(unit_price_paid_ttc AS FLOAT64) AS unit_price_paid_ttc_eur,
  CAST(unit_tax_amount AS FLOAT64) AS unit_tax_amount_eur,
  CAST(unit_cost AS FLOAT64) AS unit_cost_eur
FROM `ecommerce_raw.order_items`;

CREATE OR REPLACE VIEW `ecommerce_staging.stg_web_sessions` AS
SELECT
  CAST(session_id AS STRING) AS session_id,
  CAST(customer_id AS STRING) AS customer_id,
  CAST(date AS DATE) AS session_date,
  LOWER(CAST(utm_source AS STRING)) AS utm_source,
  LOWER(CAST(utm_medium AS STRING)) AS utm_medium,
  LOWER(CAST(utm_campaign AS STRING)) AS utm_campaign,
  CAST(device AS STRING) AS device,
  CAST(pages_viewed AS INT64) AS pages_viewed
FROM `ecommerce_raw.web_sessions`;

CREATE OR REPLACE VIEW `ecommerce_staging.stg_marketing_performance` AS
SELECT
  CAST(date AS DATE) AS date,
  CAST(channel AS STRING) AS channel,
  CAST(ad_spend AS FLOAT64) AS ad_spend_eur,
  CAST(impressions AS INT64) AS impressions,
  CAST(clicks AS INT64) AS clicks
FROM `ecommerce_raw.marketing_performance`;

CREATE OR REPLACE VIEW `ecommerce_staging.stg_email_engagement` AS
SELECT
  CAST(email_id AS STRING) AS email_id,
  CAST(customer_id AS STRING) AS customer_id,
  CAST(date AS DATE) AS email_date,
  CAST(email_type AS STRING) AS email_type,
  CAST(event AS STRING) AS email_event
FROM `ecommerce_raw.email_engagement`;


-- ==============================================================================
-- COUCHE 2 : INTERMEDIATE (Calculs de Marges Métier)
-- ==============================================================================

CREATE OR REPLACE TABLE `ecommerce_intermediate.int_order_items_enriched` AS
SELECT
  item.item_id,
  item.order_id,
  item.product_id,
  item.quantity,
  item.item_status,
  (item.unit_price_paid_ttc_eur * item.quantity) AS total_ttc_eur,
  (item.unit_tax_amount_eur * item.quantity) AS total_tax_eur,
  ((item.unit_price_paid_ttc_eur - item.unit_tax_amount_eur) * item.quantity) AS total_ht_eur,
  (item.unit_cost_eur * item.quantity) AS total_cost_eur,
  (((item.unit_price_paid_ttc_eur - item.unit_tax_amount_eur) - item.unit_cost_eur) * item.quantity) AS net_margin_eur
FROM 
  `ecommerce_staging.stg_order_items` item;

CREATE OR REPLACE TABLE `ecommerce_intermediate.int_orders_financial_aggregated` AS
SELECT
  order_id,
  COUNT(item_id) as total_items_ordered,
  SUM(total_ttc_eur) AS order_revenue_ttc_eur,
  SUM(total_ht_eur) AS order_revenue_ht_eur,
  SUM(total_tax_eur) AS order_tax_eur,
  SUM(total_cost_eur) AS order_total_cost_eur,
  SUM(net_margin_eur) AS order_net_margin_eur
FROM 
  `ecommerce_intermediate.int_order_items_enriched`
WHERE 
  item_status != 'Cancelled'
GROUP_BY 
  order_id;


-- ==============================================================================
-- COUCHE 3 : MARTS (Modèles Finaux Prêts pour la BI)
-- ==============================================================================

CREATE OR REPLACE TABLE `ecommerce_marts.mart_finance_dashboard` AS
SELECT
  o.order_id,
  o.order_date,
  o.order_status,
  c.country,
  c.customer_age,
  c.customer_gender,
  o.payment_method,
  o.discount_code,
  o.shipping_fees_eur,
  f.total_items_ordered,
  f.order_revenue_ttc_eur,
  f.order_revenue_ht_eur,
  f.order_tax_eur,
  f.order_total_cost_eur,
  f.order_net_margin_eur
FROM 
  `ecommerce_staging.stg_orders` o
JOIN 
  `ecommerce_intermediate.int_orders_financial_aggregated` f ON o.order_id = f.order_id
JOIN 
  `ecommerce_staging.stg_customers` c ON o.customer_id = c.customer_id;

CREATE OR REPLACE TABLE `ecommerce_marts.mart_marketing_attribution` AS
SELECT
  o.order_id,
  o.order_date,
  COALESCE(s.utm_source, 'organic/direct') AS utm_source,
  COALESCE(s.utm_medium, 'none') AS utm_medium,
  COALESCE(s.utm_campaign, 'none') AS utm_campaign,
  s.device,
  f.order_revenue_ht_eur,
  f.order_net_margin_eur,
  o.discount_code
FROM 
  `ecommerce_staging.stg_orders` o
LEFT JOIN 
  `ecommerce_staging.stg_web_sessions` s ON o.session_id = s.session_id
JOIN 
  `ecommerce_intermediate.int_orders_financial_aggregated` f ON o.order_id = f.order_id;

CREATE OR REPLACE TABLE `ecommerce_marts.mart_customer_lifetime_value` AS
WITH customer_orders AS (
  SELECT
    o.customer_id,
    COUNT(o.order_id) AS number_of_orders,
    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS last_order_date,
    SUM(f.order_revenue_ht_eur) AS lifetime_value_ht_eur,
    SUM(f.order_net_margin_eur) AS lifetime_margin_eur
  FROM 
    `ecommerce_staging.stg_orders` o
  JOIN 
    `ecommerce_intermediate.int_orders_financial_aggregated` f ON o.order_id = f.order_id
  WHERE 
    o.order_status = 'Delivered'
  GROUP BY 
    o.customer_id
)
SELECT
  c.customer_id,
  c.signup_date,
  DATE_TRUNC(c.signup_date, MONTH) AS cohorte_mois,
  c.acquisition_channel,
  c.country,
  COALESCE(co.number_of_orders, 0) AS lifetime_orders_count,
  COALESCE(co.lifetime_value_ht_eur, 0) AS lifetime_value_ht_eur,
  COALESCE(co.lifetime_margin_eur, 0) AS lifetime_margin_eur,
  DATE_DIFF(co.last_order_date, co.first_order_date, DAY) AS customer_active_duration_days
FROM 
  `ecommerce_staging.stg_customers` c
LEFT JOIN 
  customer_orders co ON c.customer_id = co.customer_id;
