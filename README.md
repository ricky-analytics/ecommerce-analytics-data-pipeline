# 📊 E-Commerce & Growth Marketing Data Platform 

Ce projet simule l'architecture, la modélisation et l'analyse statistique d'une plateforme e-commerce internationale opérant sur 24 mois. L'objectif est de dépasser les analyses de surface pour traiter les problématiques complexes du e-commerce moderne : **l'attribution marketing multi-touch post-iOS14**, la **fiscalité internationale (marges réelles HT)** et la **rétention client (LTV & Cohortes)**.

L'infrastructure reproduit fidèlement un écosystème d'entreprise moderne utilisant l'approche moderne de l'Analytics Engineering.

## 🛠️ Tech Stack & Architecture
- * **Génération & Statistiques :** Python (Pandas, Numpy, Scipy, Matplotlib, Seaborn)
* **Data Warehouse :** Google BigQuery (Sandbox Environment)
* **Modélisation & Transformation :** SQL (Architecture inspirée de dbt - Couches Staging, Intermediate, Marts)
* **Business Intelligence :** Looker Studio (Live Interactive Dashboard)

## 🏗️ Architecture des Données & Pipeline SQL
Le projet refuse l'analyse directe de fichiers bruts. Les données suivent un flux ELT (Extract, Load, Transform) strict à travers 3 couches distinctes :
[Données Brutes CSV] ──> [Couche STAGING (Nettoyage & Casting)]
└──> [Couche INTERMEDIATE (Règles métiers / TVA / Marges)]
└──> [Couche MARTS (Tables dimensionnelles & Faits OLAP)]


### 1. Couche Staging (`ecommerce_staging`)
Modélisation de type "Vues" pour isoler, renommer et typer les colonnes brutes (ex: forçage des formats de date, exclusion des anomalies de tracking).
* *Fichiers SQL sources :* `stg_customers.sql`, `stg_orders.sql`, `stg_web_sessions.sql`, etc.

### 2. Couche Intermediate (`ecommerce_intermediate`)
C'est ici que sont appliquées les règles financières de niveau expert. 
* **Calcul de la marge nette HT réelle :** Intégration d'une logique douanière et fiscale asymétrique selon le pays (France 20%, Belgique 21%, Suisse 8.1%). Les marges sont calculées sur le chiffre d'affaires déduit de sa taxe et du coût d'achat unitaire :
    `Marge = (Prix TTC - Montant Taxe) - Coût de revient`

### 3. Couche Marts (`ecommerce_marts`)
Tables de faits optimisées pour la BI et prêtes pour l'exposition aux outils de Dataviz.
* `mart_finance_dashboard` : Vue unifiée pour le COMEX.
* `mart_marketing_attribution` : Table de réconciliation associant l'ID de commande (`order_id`) au canal d'acquisition exact (`session_id`) via un modèle d'attribution **Last Click**.

---

## 📈 Analyses Statistiques Avancées (Python)
Le dossier `/notebooks` contient l'ensemble du code de modélisation mathématique du projet :

### A. Analyse de Causalité & Effet de Halo (Marketing Spend vs Sales)
Utilisation du **Coefficient de corrélation de Pearson** combiné à une analyse de séries temporelles avec décalage (**Lag Analysis**).
* **Insight technique :** La corrélation à J0 montre les limites du tracking publicitaire moderne. L'introduction d'un modèle à J+1 et J+2 met en évidence l'effet de halo et le comportement mémoriel du consommateur (décalage entre le clic publicitaire et la conversion finale).

### B. Modélisation de la Customer Lifetime Value (LTV) par Cohorte
Analyse de la rétention en regroupant les utilisateurs par mois d'inscription (`cohort_month`) et en mesurant la somme cumulée de leur valeur sur 24 mois.
* **Insight business :** Preuve de la santé financière de la marque : la LTV moyenne par client progresse linéairement de M+0 à M+6, validant l'efficacité de la brique de marketing automation (emailing).

### C. Segmentation RFM Automatisée
Classification algorithmique des 5 000 clients sur 3 axes : Récence de l'achat, Fréquence et Montant cumulé. Les clients sont segmentés dynamiquement en 5 catégories : *Champions, À risque de churn, Nouveaux Acheteurs, Clients Dormants, Potentiels*.

---

## 🚀 Dashboard Decisionnel (Looker Studio)
Le tableau de bord est conçu de manière descendante pour répondre aux besoins des différentes strates de l'entreprise :

* **Page 1 : Direction Financière (Executive)** ➔ Suivi du Chiffre d'Affaires Net HT et de la marge brute. *Mise en évidence d'une anomalie logistique sur la Suisse avec un taux d'échec/retour de 10% (problème douanier simulé).*
* **Page 2 : Performance Publicitaire (Growth)** ➔ Analyse fine du ROAS (Return on Ad Spend) par canal publicitaire (Facebook Ads vs Google Ads vs TikTok Ads) croisé avec les données du Data Warehouse.
* **Page 3 : CRM & Rétention** ➔ Suivi de la matrice des cohortes de LTV et répartition visuelle de la segmentation RFM pour les équipes marketing.

** [CLIQUEZ ICI POUR ACCÉDER AU DASHBOARD INTERACTIF LIVE]**
🔗 https://datastudio.google.com/reporting/d2c92754-68d4-49bb-856e-b8f0b792d9e3
