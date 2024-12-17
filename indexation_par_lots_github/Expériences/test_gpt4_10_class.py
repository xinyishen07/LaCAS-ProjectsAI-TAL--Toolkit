import pandas as pd
import numpy as np
import openai
import time
from sklearn.metrics import classification_report
from sklearn.preprocessing import MultiLabelBinarizer

'''
Fonction : Ce programme évalue la performance du modèle GPT4 en utilisant les données de test issues de l'entraînement du modèle BERT (fichier généré par `train_data_multi_labels.py`).

Entrée : 
- Un fichier CSV contenant les données de test utilisées pour l'entraînement de BERT.

Sortie : 
- `file_output` : Un fichier CSV contenant les données de test ainsi que les résultats prédits par GPT4, montrant comment le modèle a classé chaque donnée.

Méthodes d'utilisation :
- Le programme prend les données de test du modèle BERT, les utilise pour évaluer GPT4, puis enregistre les prédictions de Mistral AI.

Remarque : Par défault, ce programme n'évalue que 10 classes, définies dans la variable `list_class`.
'''

openai.api_key = ''
#client = OpenAI()
model = "gpt-4-0125-preview"
filename = 'result_expe_final/test_10_classes_bert.csv'
file_output = 'result_expe_final/test_10_classes_gpt_2_shots_mauvais_classes.csv'
df = pd.read_csv(filename, encoding='utf-8', sep='\t')
df = df.drop('predicted labels', axis=1)
titles = df['text'].tolist()
test_labels = df['label'].tolist()
list_class = ['Études indiennes (Indologie)', 'Études japonaises', 'Études mexicaines' , 'Études russes', 'Anthropologie', 'Linguistique' , 'Architecture', 'Archéologie', 'Littératures du monde', 'Etudes cinématographiques']

total_predict_labels = []
for title in titles :
    predict_labels = []
    completion = openai.chat.completions.create(
    model=model,
    messages=[
        {"role": "system",  "content": "Classifiez un texte à une ou plusieurs catégories correspondantes. Si le texte correspond uniquement à une catégorie, répondez directement le nom de cette catégorie. Si le texte correspond à plusieurs catégories, répondez directement avec les noms des catégories séparés par des ','. Par exemple : Centre de recherche berbère (CRB - équipe du LACNAD, EA 4092)Le Centre de recherche berbère (CRB) est un pôle de recherche en linguistique descriptive, historique et appli­quée berbère, en littérature berbère et anthropologie culturelle du monde berbère, s'appuyant sur la seule et la plus ancienne structure universitaire d'enseignement complète du berbère existant en France et en Europe (du premier au troisième cycle). Fondé en 1992 à l'Inalco en tant qu'équipe d'accueil (EA 3577), le CRB intègre en 2006 le laboratoire Langues et Cultures du Nord de l’Afrique et Diasporas (LACNAD, EA 4092). Ses activités s'organisent autour de trois axes : linguistique berbère, littérature berbère, culture et société berbères. Réponse : Anthropologie. Par exemple : Interactions, transferts, ruptures artistiques et culturels (InTRu ; EA 6301)Au-delà de ces convergences méthodologiques, ils ont en commun un certain nombre d’objets thématiques. L’un de ces pôles thématiques concerne la construction des cultures visuelles contemporaines, entre peinture, photographie, cinéma, graphisme, design et image imprimée. Un autre de ces pôles concerne l’histoire de l’architecture et de l’urbanisme, la représentation des espaces habités, les liens entre l’action publique et les enjeux politiques et sociaux. Entre ces deux pôles circule enfin un intérêt commun pour les enjeux critiques et les stratégies d’émancipation qui permettent de comprendre et de déjouer les formes de la domination spatiale, culturelle et visuelle. | L’InTRu est une équipe de recherches de l’université de Tours (Équipe d’accueil n° 6301). L’acronyme « InTRu » renvoie aux termes « Interactions, Transferts, Ruptures artistiques et culturelles ».Le laboratoire InTRu réunit des chercheurs et des chercheuses issues de l’histoire de l’art et de l’architecture, de la littérature, la philosophie, l’esthétique de la bande dessinée, l’histoire de la photographie, du cinéma, du design. Réponse : Etudes cinématographiques"},
        {"role": "user", "content": "Le texte : " +  title},
        {"role": "system", "content": "Choisissez le(s) domaine(s) pertinent(s) parmi les suivants : 'Études indiennes (Indologie)', 'Études japonaises', 'Études mexicaines' , 'Études russes', 'Anthropologie', 'Linguistique' , 'Architecture', 'Archéologie', 'Littératures du monde', 'Etudes cinématographiques'"}
    ]
    )
    response = completion.choices[0].message.content
    # response = response.split()
    for label in list_class:
        if label in response:
            predict_labels.append(label)
    total_predict_labels.append(predict_labels)
    time.sleep(3)
df['predicted_labels'] = total_predict_labels
df.to_csv(file_output, encoding='utf-8', sep='\t')
