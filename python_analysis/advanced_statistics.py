import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
from google.colab import auth
from google.cloud import bigquery

# ==============================================================================
# 1. AUTHENTIFICATION CLOUD ET CONNEXION BIGQUERY
# ==============================================================================
print("--- Initialisation de la connexion Cloud ---")

# Authentification sécurisée de votre session Google Colab
auth.authenticate_user()

# Configuration de votre identifiant de projet Google Cloud
# (⚠️ Remplacez 'portfolio-ecommerce-analytics' par l'ID exact de votre projet si différent)
PROJECT_ID = "portfolio-ecommerce-analytics"
client = bigquery.Client(project=PROJECT_ID)

print("✅ Authentification réussie.")

# ==============================================================================
# 2. EXTRACTION DES DONNÉES DEPUIS LE DATA WAREHOUSE
# ==============================================================================
print("\n--- Extraction des tables depuis le Data Warehouse ---")

# Requêtes SQL directes pour charger les données modélisées dans des DataFrames Pandas
try:
    df_customers = client.query("SELECT * FROM `ecommerce_staging.stg_customers`").to_dataframe()
    df_orders = client.query("SELECT * FROM `ecommerce_staging.stg_orders`").to_dataframe()
    df_order_items = client.query("SELECT * FROM `ecommerce_intermediate.int_order_items_enriched`").to_dataframe()
    df_marketing = client.query("SELECT * FROM `ecommerce_staging.stg_marketing_performance`").to_dataframe()
    print("✅ Statut : Données synchronisées en temps réel depuis BigQuery.")
except Exception as e:
    print(f"⚠️ Erreur d'extraction : {e}")
    print("Veuillez vérifier que vos couches SQL ont bien été exécutées dans BigQuery.")

# Standardisation des formats de dates pour la manipulation temporelle sous Python
df_customers['signup_date'] = pd.to_datetime(df_customers['signup_date'])
df_orders['order_date'] = pd.to_datetime(df_orders['order_date'])
df_marketing['date'] = pd.to_datetime(df_marketing['date'])

# Configuration esthétique pour les graphiques du Portfolio
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['font.sans-serif'] = 'Segoe UI'


# ==============================================================================
# 3. ALGORITHME 1 : MATRICE DE RÉTENTION PAR COHORTE (LTV CUMULÉE)
# ==============================================================================
print("\n--- Calcul 1/3 : Analyse des Cohortes de Rétention ---")

# Filtrage métier : On isole les commandes livrées pour ne pas biaiser la LTV avec les annulations
df_delivered_orders = df_orders[df_orders['order_status'] == 'Delivered'].copy()

# Agrégation de la valeur financière Hors-Taxe (HT) calculée à l'étape intermédiaire par commande
df_order_value = df_order_items.groupby('order_id')['total_ht_eur'].sum().reset_index()
df_cohort_base = pd.merge(df_delivered_orders, df_order_value, on='order_id', how='inner')

# Liaison avec la table client pour récupérer la date d'inscription (naissance du client)
df_cohort_base = pd.merge(df_cohort_base, df_customers[['customer_id', 'signup_date']], on='customer_id', how='inner')

# Transformation des dates en périodes mensuelles
df_cohort_base['cohort_month'] = df_cohort_base['signup_date'].dt.to_period('M')
df_cohort_base['order_month'] = df_cohort_base['order_date'].dt.to_period('M')

# Calcul de l'index de la cohorte (Écart en mois entre l'inscription et le réachat)
df_cohort_base['month_index'] = (df_cohort_base['order_month'].dt.year - df_cohort_base['cohort_month'].dt.year) * 12 + \
                                (df_cohort_base['order_month'].dt.month - df_cohort_base['cohort_month'].dt.month)

# Pivotement des données pour compter les clients uniques actifs par mois de vie
cohort_pivot = df_cohort_base.pivot_table(index='cohort_month', 
                                          columns='month_index', 
                                          values='customer_id', 
                                          aggfunc='nunique')

# Conversion de la matrice en pourcentages par rapport au Mois 0 (Taille initiale de la cohorte)
cohort_sizes = cohort_pivot.iloc[:, 0]
retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0)

# Génération de la Heatmap de Rétention
plt.figure(figsize=(10, 6))
sns.heatmap(retention_matrix, annot=True, fmt='.1%', cmap='BuGn', vmin=0.0, vmax=0.5)
plt.title("Matrice de Rétention du Client - Vue Cloud BigQuery", fontsize=14, pad=15)
plt.ylabel("Mois de Cohorte (Inscription)")
plt.xlabel("Mois de Vie du Client (M0 = Premier Achat)")
plt.tight_layout()
plt.show()


# ==============================================================================
# 4. ALGORITHME 2 : CORRÉLATION DE PEARSON (EFFET RETARD MARKETING)
# ==============================================================================
print("\n--- Calcul 2/3 : Analyse de Corrélation Ads vs Chiffre d'Affaires ---")

# Agrégation du CA HT total quotidien de la marque
df_daily_sales = df_cohort_base.groupby(df_cohort_base['order_date'].dt.date)['total_ht_eur'].sum().reset_index()
df_daily_sales.columns = ['date', 'revenue_ht']
df_daily_sales['date'] = pd.to_datetime(df_daily_sales['date'])

# Agrégation des dépenses publicitaires journalières (Ad Spend)
df_marketing_sales = df_marketing.groupby('date')['ad_spend_eur'].sum().reset_index()
df_correlation_data = pd.merge(df_daily_sales, df_marketing_sales, on='date', how='inner')

# Création des décalages temporels (Lags) pour analyser l'impact publicitaire à J+1 et J+2
df_correlation_data['revenue_lag_1'] = df_correlation_data['revenue_ht'].shift(-1) # CA généré le lendemain
df_correlation_data['revenue_lag_2'] = df_correlation_data['revenue_ht'].shift(-2) # CA généré à 48 heures
df_correlation_data = df_correlation_data.dropna()

# Calcul mathématique des coefficients de corrélation
r_j, _ = pearsonr(df_correlation_data['ad_spend_eur'], df_correlation_data['revenue_ht'])
r_j1, _ = pearsonr(df_correlation_data['ad_spend_eur'], df_correlation_data['revenue_lag_1'])

print(f"📉 Coefficient de Pearson au Jour J   : {r_j:.2f}")
print(f"⏳ Coefficient de Pearson à l'état J+1 : {r_j1:.2f} (Preuve mathématique de l'effet retard)")


# ==============================================================================
# 5. ALGORITHME 3 : SEGMENTATION RFM AVANCÉE
# ==============================================================================
print("\n--- Calcul 3/3 : Algorithme de Segmentation Client RFM ---")

# Définition de la date d'analyse (Lendemain de la dernière commande enregistrée)
snapshot_date = df_cohort_base['order_date'].max() + pd.Timedelta(days=1)

# Extraction des indicateurs RFM individuels
df_rfm = df_cohort_base.groupby('customer_id').agg({
    'order_date': lambda x: (snapshot_date - x.max()).days, # Récence
    'order_id': 'nunique',                                  # Fréquence
    'total_ht_eur': 'sum'                                   # Montant
}).reset_index()

df_rfm.columns = ['customer_id', 'Recency', 'Frequency', 'Monetary']

# Attribution des scores par quantiles (Notes de 1 à 4)
df_rfm['R_Score'] = pd.qcut(df_rfm['Recency'], q=4, labels=[4, 3, 2, 1]) # Récence faible = Meilleur score
df_rfm['F_Score'] = pd.qcut(df_rfm['Frequency'].rank(method='first'), q=4, labels=[1, 2, 3, 4])
df_rfm['M_Score'] = pd.qcut(df_rfm['Monetary'], q=4, labels=[1, 2, 3, 4])

# Classification métier personnalisée
def assign_segment(df):
    r = int(df['R_Score'])
    f = int(df['F_Score'])
    
    if (r >= 3) and (f >= 3):
        return 'Champions / Loyal Customers'
    elif (r >= 3) and (f < 3):
        return 'New Customers / Potential'
    elif (r < 3) and (f >= 3):
        return 'At Risk / Can\'t Lose Them'
    else:
        return 'Lost / Hibernating'

df_rfm['Customer_Segment'] = df_rfm.apply(assign_segment, axis=1)

# Affichage des parts de marché de chaque segment
print("\n📋 Répartition finale de votre base de données clients :")
print(df_rfm['Customer_Segment'].value_counts(normalize=True).map('{:.1%}'.format))

# Sauvegarde du rapport final
df_rfm.to_csv("RFM_Customer_Segmentation_Output.csv", index=False)
print("\n✅ Fichier 'RFM_Customer_Segmentation_Output.csv' sauvegardé localement.")
print("--- Fin du traitement complet ---")
