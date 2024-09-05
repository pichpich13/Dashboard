import pandas as pd
import streamlit as st
import seaborn as sns  # Importe Seaborn
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import requests 

# Configuration graphique de matplotlib
plt.rcParams['font.size'] = 12
plt.style.use('classic')

# Charger les données
@st.cache_data
def load_data(filepath):
    # Charger le fichier JSON contenant les codes-barres
    df = pd.read_json(filepath)
    return df

def get_ecoscore_data(codes):
    # Liste pour stocker les résultats
    products_info = []
    
    # Itérer sur chaque code-barre pour requêter l'API Open Food Facts
    for code in codes:
        url = f"https://world.openfoodfacts.org/api/v0/product/{code}.json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 1:  # Vérifier si le produit est trouvé
                product = data['product']
                ecoscore_score = product.get('ecoscore_score', 'Non disponible')
                ecoscore_grade = product.get('ecoscore_grade', 'Non disponible')
                catégorie = product.get('categories', 'Non disponible')
                products_info.append({'code_barre': code, 'ecoscore_score': ecoscore_score, 'ecoscore_grade': ecoscore_grade, 'catégorie': catégorie})
            else:
                products_info.append({'code_barre': code, 'ecoscore_score': 'Produit non trouvé', 'ecoscore_grade': 'Produit non trouvé', 'catégorie': 'Produit non trouvé'})
        else:
            products_info.append({'code_barre': code, 'ecoscore_score': 'Erreur de requête', 'ecoscore_grade': 'Erreur de requête', 'catégorie': 'Erreur de requête'})
    
    # Convertir la liste des résultats en DataFrame pour un traitement ultérieur
    return pd.DataFrame(products_info)

# Emplacement de votre fichier JSON
filepath = '0_usr_example_json.json'
df = load_data(filepath)
codes = df[0].tolist()  # Supposant que les codes-barres sont dans la première colonne

# Appel de la fonction pour récupérer les données d'ecoscore
ecoscore_data = get_ecoscore_data(codes)

def plot_ecoscore_ecograde_means(df):
    # Convertir les colonnes en type numérique
    df['ecoscore_score'] = pd.to_numeric(df['ecoscore_score'], errors='coerce')
    df['ecoscore_score'] = df['ecoscore_score'].fillna(0)

    # supprimer les unknown
    df = df[df['ecoscore_grade'] != 'unknown']
    df['ecoscore_grade'] = df['ecoscore_grade'].fillna('Non disponible')

    
    # Convertir les colonnes en type catégorie
    df['ecoscore_grade'] = df['ecoscore_grade'].astype('category')
    
    # Créer un dansity plot pour l'écoscore moyen
    fig, ax = plt.subplots(1, 2, figsize=(15, 5))
    sns.kdeplot(df['ecoscore_score'], ax=ax[0], fill=True)
    ax[0].set_title('Moyenne de l\'ecoscore par produit')
    
    # Créer un graphique à barres pour l'écoscore_grade moyen
    sns.countplot(x='ecoscore_grade', data=df, ax=ax[1])
    ax[1].set_title('Moyenne de l\'ecoscore_grade par produit')
    
    # Afficher les graphiques
    st.pyplot(fig)

def ecoscore_by_product_catégorie(df):
    # S'assurer que le score ecoscore est numérique
    df['ecoscore_score'] = pd.to_numeric(df['ecoscore_score'], errors='coerce')
    
    # Remplacer les valeurs manquantes ou nulles par zéro (ou une autre logique selon le besoin)
    df['ecoscore_score'].fillna(0, inplace=True)
    
    # Nettoyer les données de catégorie pour s'assurer qu'elles sont utilisables
    # Par exemple, on pourrait vouloir séparer les catégories si elles sont listées ensemble dans une chaîne
    # Ici, nous allons simplement supprimer les entrées où la catégorie n'est pas disponible
    df_clean = df[df['catégorie'] != 'Non disponible']
    
    # Pour simplifier, on peut extraire la première catégorie si plusieurs sont listées
    df_clean['catégorie'] = df_clean['catégorie'].apply(lambda x: x.split(',')[0] if isinstance(x, str) else x)
    
    # Calculer la moyenne de l'ecoscore par catégorie
    mean_ecoscores = df_clean.groupby('catégorie')['ecoscore_score'].mean().reset_index()
    
    # Trier les résultats pour une meilleure visualisation
    mean_ecoscores_sorted = mean_ecoscores.sort_values(by='ecoscore_score', ascending=False)
    
    # Utiliser Plotly Express pour créer un graphique à barres
    fig = px.bar(mean_ecoscores_sorted, x='catégorie', y='ecoscore_score',
                 title='Moyenne de l\'Ecoscore par Catégorie de Produit',
                 labels={'ecoscore_score': 'Ecoscore Moyen', 'catégorie': 'Catégorie'})
    
    # Afficher le graphique dans Streamlit
    st.plotly_chart(fig)


st.title('Analyse des Données des Produits Scannés')

# Créer un conteneur pour regrouper des graphiques
with st.expander("Voir les graphiques des Ecoscores"):
    with st.container():
        st.subheader('Moyenne de l\'Ecoscore et de l\'ecoscore_grade pour l\'utilisateur')
        plot_ecoscore_ecograde_means(ecoscore_data)

# Créer un conteneur pour regrouper des graphiques
with st.expander("Voir les graphiques des Ecoscores par catégorie de produit"):
    with st.container():
        st.subheader('Moyenne de l\'Ecoscore par catégorie de produit')
        ecoscore_by_product_catégorie(ecoscore_data)