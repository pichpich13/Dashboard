import pandas as pd
import streamlit as st
# import seaborn as sns  # Importe Seaborn
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
# import de la libnrairie pour appelé l'api
import requests
import io


# Configuration graphique de matplotlib
plt.rcParams['font.size'] = 12
plt.style.use('classic')

# Charger les données
@st.cache_data(ttl=3600)
def load_data():
    try:
        data_response = requests.get('http://93.4.84.5:5000/get_csv_pipeline', timeout=10)
        data_emission_response = requests.get('http://93.4.84.5:5000/get_csv_food_emission', timeout=10)

        data_response.raise_for_status()  # Génère une erreur pour un code HTTP 4xx/5xx
        data_emission_response.raise_for_status()
        
        # Lire les CSV à partir de la réponse
        data = pd.read_csv(io.StringIO(data_response.text), encoding='utf-8', sep='\t', low_memory=True)
        data_emission_food_cycle = pd.read_csv(io.StringIO(data_emission_response.text), encoding='utf-8', sep='\t', low_memory=False)
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return None, None

    return data, data_emission_food_cycle

df, data_emission_food_cycle = load_data()

def plot_ecoscore_distribution(data):
    ecoscores = data['ecoscore_grade'].value_counts().sort_index()
    # Suppression des valeurs manquantes et des not-applicable
    ecoscores = ecoscores.drop(labels=['unknown', 'not-applicable'], errors='ignore')
    
    # Définir les couleurs pour chaque note d'EcoScore
    colors = {
        'a': 'green',  # Vert pour A
        'b': 'lightgreen',  # Vert clair pour B
        'c': 'yellow',  # Jaune pour C
        'd': 'orange',  # Orange pour D
        'e': 'red'  # Rouge pour E
    }
    
    # Créer une liste de couleurs dans l'ordre des ecoscores
    bar_colors = [colors[grade].upper() for grade in ecoscores.index]
    
    fig, ax = plt.subplots()
    ecoscores.plot(kind='barh', ax=ax, color=bar_colors)
    ax.set_title('Répartition des Ecoscores')
    
    # Convertir les labels de l'axe X en majuscules
    ax.set_yticklabels([grade.upper() for grade in ecoscores.index])
    ax.set_xlabel('Nombre de Produits')
    ax.set_ylabel('Eco-score')
    
    # Afficher le graphique
    st.pyplot(fig)

def dansity_plot_ecoscore_distribution(data):
    # Supprimer les valeurs manquantes et les not-applicable
    filtered_data = data.dropna(subset=['ecoscore_score'])
    
    # Créer un graphique de densité pour les éco-scores
    fig, ax = plt.subplots()
    # sns.kdeplot(data=filtered_data['ecoscore_score'], ax=ax, fill=True, color='skyblue')
    ax.set_title('Densité des Ecoscores')
    ax.set_xlabel('Eco-score')
    ax.set_ylabel('Densité')
    st.pyplot(fig)


def plot_ecoscore_distribution_by_country(data):  
    
    # Préparation des données comme précédemment
    filtered_data = data.dropna(subset=['ecoscore_score', 'countries_en'])
    filtered_data = filtered_data[filtered_data['ecoscore_score'] > 0]
    filtered_data = filtered_data[~filtered_data['countries_en'].str.contains(",")]
    country_scores = filtered_data.groupby('countries_en')['ecoscore_score'].mean().reset_index()
    country_scores = country_scores[country_scores['ecoscore_score'] > 0]

    # limitation du nombre de pays a afficher a 30
    country_scores = country_scores.sort_values(by='ecoscore_score', ascending=False).head(30)
     
    
    # Calcul d'une nouvelle métrique pour inverser la relation taille-valeur
    max_score = country_scores['ecoscore_score'].max()
    country_scores['inverted_score'] = max_score + 1 - country_scores['ecoscore_score']
    
    # On garde les 20 premiers pays ayant les pires moyennes d'éco-scores
    country_scores = country_scores.sort_values(by='inverted_score', ascending=False).head(20)
    
    # Utiliser 'inverted_score' pour la taille des blocs
    fig = px.treemap(country_scores, path=['countries_en'], values='inverted_score',
                     color='ecoscore_score', color_continuous_scale='RdYlGn')
    
    # Mise à jour du layout pour positionner la légende de la gradation de couleur en bas
    fig.update_layout(coloraxis_colorbar=dict(
        title='Ecoscore',
        orientation='h',
        x=0.5,
        y=-0.15,
        xanchor='center',
        yanchor='bottom'
    ))

    # Ajustement des marges pour s'assurer que la légende est visible
    fig.update_layout(margin=dict(t=35, l=5, r=5, b=50))
    
    # Afficher le Treemap
    st.plotly_chart(fig, use_container_width=True)

    
    
def plot_ecoscore_distribution_by_big_country(data):
    # Liste des 15 pays les plus connus
    known_countries = [
        "United States", "China", "India", "France", "United Kingdom",
        "Germany", "Japan", "Brazil", "Russia", "Italy",
        "Canada", "Australia", "Mexico", "Spain", "South Korea"
    ]
    
    # Filtrer pour s'assurer que 'ecoscore_score' est numérique et non nul
    filtered_data = data.dropna(subset=['ecoscore_score', 'countries_en'])
    filtered_data = filtered_data[filtered_data['ecoscore_score'] > 0]
    
    # Exclure les entrées avec plusieurs pays dans le label 'countries_en'
    filtered_data = filtered_data[~filtered_data['countries_en'].str.contains(",")]
    
    # Filtrer pour ne garder que les données correspondant aux 15 pays les plus connus
    filtered_data = filtered_data[filtered_data['countries_en'].isin(known_countries)]
    
    # Grouper les données par pays et calculer la moyenne des éco-scores
    country_scores = filtered_data.groupby('countries_en')['ecoscore_score'].mean().reset_index()
    
    # nouvelle métrique pour inverser la relation taille-valeur
    max_score = country_scores['ecoscore_score'].max()
    country_scores['inverted_score'] = max_score + 1 - country_scores['ecoscore_score']
    
    # On pourrait trier et limiter à 15 ici, mais tous les pays sont déjà dans notre liste des pays les plus connus
    country_scores = country_scores.sort_values(by='inverted_score', ascending=False)
    
    # Générer le Treemap
    fig = px.treemap(country_scores, path=['countries_en'], values='inverted_score',
                     color='ecoscore_score', color_continuous_scale='RdYlGn')
    
    # Afficher le Treemap
    fig.update_layout(margin=dict(t=10, l=5, r=5, b=25))
    st.plotly_chart(fig, use_container_width=True)
    
def plot_less_ecoscore_distribution_by_country(data):
    # Filtrer pour s'assurer que 'ecoscore_score' est numérique et non nul
    filtered_data = data.dropna(subset=['ecoscore_score', 'countries_en'])
    filtered_data = filtered_data[filtered_data['ecoscore_score'] > 0]
    
    # Exclure les entrées avec plusieurs pays dans le label 'countries_en'
    filtered_data = filtered_data[~filtered_data['countries_en'].str.contains(",")]
    
    # Grouper les données par pays et calculer la moyenne des éco-scores
    country_scores = filtered_data.groupby('countries_en')['ecoscore_score'].mean().reset_index()
    
    # S'assurer d'éliminer les éventuels pays avec un éco-score moyen de zéro (normalement pas nécessaire après la première filtration, mais on ne sait jamais)
    country_scores = country_scores[country_scores['ecoscore_score'] > 0]
    
    # On garde les 20 premiers pays ayant les meilleures moyennes d'éco-scores
    country_scores = country_scores.sort_values(by='ecoscore_score', ascending=False).head(10)
    
    # Générer le Treemap
    fig = px.treemap(country_scores, path=['countries_en'], values='ecoscore_score',
                     color_continuous_scale='RdYlGn_r',
                     color='ecoscore_score')
    
    # Afficher le Treemap
    fig.update_layout(margin=dict(t=10, l=5, r=5, b=25))
    st.plotly_chart(fig, use_container_width=True)



def plot_ecoscore_by_product_category(data):
    # Supposer que 'ecoscore_score' est un proxy pour le bilan carbone
    # Grouper les données par 'pnns_groups_2' et calculer la moyenne des scores d'éco-score
    category_scores = data.groupby('pnns_groups_2')['ecoscore_score'].mean().sort_values(ascending=False)

    # supprimer les unknown
    category_scores = category_scores[category_scores.index != 'unknown']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    category_scores.plot(kind='bar', ax=ax, color='skyblue')
    ax.set_title('Moyenne des EcoScores par Catégorie de Produit')
    ax.set_xlabel('Catégorie de Produit')
    ax.set_ylabel('Moyenne EcoScore')
    st.pyplot(fig)
    
def plot_ecoscore_by_food_category(data):
    # filtre pour s'assurer que 'ecoscore_score' est numérique et non nul
    filtered_data = data.dropna(subset=['ecoscore_score', 'pnns_groups_1'])
    filtered_data = filtered_data[filtered_data['ecoscore_score'] > 0]

    # on supprime les unknown
    filtered_data = filtered_data[filtered_data['pnns_groups_1'] != 'unknown']
    
    # Grouper les données par 'pnns_groups_1' et calculer la moyenne des scores d'éco-score
    food_category_scores = data.groupby('pnns_groups_1')['ecoscore_score'].mean().sort_values(ascending=False)

    # on supprime les unknown
    food_category_scores = food_category_scores[food_category_scores.index != 'unknown']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    food_category_scores.plot(kind='bar', ax=ax, color='lightgreen')
    ax.set_title('Moyenne des EcoScores par Catégorie Alimentaire Principale')
    ax.set_xlabel('Catégorie Alimentaire Principale')
    ax.set_ylabel('Moyenne EcoScore')
    st.pyplot(fig)
    
    
def plot_emission_life_cycle_food(data_emission_food_cycle, year_range):
    # Filtrer les données pour la plage d'années sélectionnée
    filtered_data = data_emission_food_cycle[(data_emission_food_cycle['Year'] >= year_range[0]) & (data_emission_food_cycle['Year'] <= year_range[1])]
    
    # Sélectionner les colonnes des étapes du cycle de vie, à l'exception de 'Entity', 'Code', et 'Year'
    stages = ['End-of-Life food emissions', 'Food consumption emissions', 'Food retail emissions', 
              'Food packaging emissions', 'Food transport emissions', 'Food processing emissions', 
              'Agricultural production emissions', 'Land use change emissions']
    
    # Calculer la moyenne des émissions pour chaque étape sur les années filtrées
    avg_emissions = filtered_data[stages].mean().sort_values(ascending=False)
    
    # Créer un graphique à barres pour les émissions moyennes par étape
    fig, ax = plt.subplots(figsize=(10, 6))
    avg_emissions.plot(kind='bar', ax=ax, color='skyblue')
    
    ax.set_title(f'Emissions de CO2 par étape du cycle de vie des aliments ({year_range[0]} - {year_range[1]})')
    ax.set_xlabel('Étape du Cycle de Vie')
    ax.set_ylabel('Émissions moyennes de CO2 (kg CO2e)')
    
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)



st.title('Analyse des Données des Produits')

# Créer un conteneur pour regrouper des graphiques
with st.expander("Voir les graphiques des Ecoscores"):
    with st.container():
        st.subheader('Répartition des Ecoscores')
        plot_ecoscore_distribution(df)

        st.subheader('Répartition de la dansité des Ecoscores')
        dansity_plot_ecoscore_distribution(df)

def update_year_range():
    st.session_state['year_range'] = st.session_state['slider_year_range']

# Initialiser 'year_range' dans le session state s'il n'existe pas
if 'year_range' not in st.session_state:
    st.session_state['year_range'] = (1990, 2015)

with st.expander("Voir les graphiques des émissions de CO2 par étape du cycle de vie des aliments"):
    with st.container():
        # Créer un slider et utiliser un callback pour mettre à jour 'year_range' dans le session state
        year_range = st.slider('year', 1990, 2015, st.session_state['year_range'], key='slider_year_range', on_change=update_year_range)
        
        st.subheader('Emissions de CO2 par étape du cycle de vie des aliments')

        # Vérifier si 'year_range' a changé avant de redessiner le graphique
        if 'year_range' in st.session_state:
            # Cette fonction doit utiliser la valeur de 'year_range' pour filtrer les données avant de dessiner le graphique.
            plot_emission_life_cycle_food(data_emission_food_cycle, st.session_state['year_range'])
        
       # sous-sous titre pour afficher les sources des données
        st.subheader('Sources des données')
        st.markdown("""
            Les données sur les émissions de CO2 par étape du cycle de vie des aliments proviennent de [Our World in Data](https://ourworldindata.org/grapher/food-emissions-life-cycle?time=earliest..2015).
        """) 

# Vous pouvez créer autant de conteneurs que nécessaire pour organiser votre application
with st.expander("Voir les graphiques des Ecoscores par Pays"):
    with st.container():
        st.subheader('Répartition des Ecoscores par Pays')
        plot_ecoscore_distribution_by_country(df)
        
        st.subheader('Répartition des Ecoscores parmi les 15 Pays les Plus Connus')
        plot_ecoscore_distribution_by_big_country(df)

        st.subheader('Répartition des Ecoscores parmi les 10 Pays ayant les meilleurs éco-scores')
    plot_less_ecoscore_distribution_by_country(df)

# Un autre conteneur pour une autre catégorie de graphiques
with st.expander("Voir les graphiques des Ecoscores par Catégorie de Produit"):
    with st.container():
        st.subheader('Moyenne des Ecoscores par Catégorie de Produit')
        plot_ecoscore_by_product_category(df)

        st.subheader('Moyenne des Ecoscores par Catégorie Alimentaire Principale')
        plot_ecoscore_by_food_category(df)

