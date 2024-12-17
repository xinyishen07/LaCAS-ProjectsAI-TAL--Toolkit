import json
import pandas as pd

'''
Fonction : Ce programme prend deux sorties du initial_data_preparation_indexation_par_lots.py et prépare un corpus pour l'entraînement de classification multi-label.

Entrée : 
- sortie JSON du initial_data_preparation_indexation_par_lots.py
- sortie CSV du initial_data_preparation_indexation_par_lots.py

Sortie : 
- fichier CSV filtré

Méthodes d'utilisation:
1. filter_classes_by_annotation_count() : il filtre les classes (media) avec ses nombres d'annotation (terme). La sortie est une liste de classes filtrés.
2. filter_corpus(): à partir de la liste de classe, il permet de construire un corpus.
'''

input_json = 'term_with_donnees_liees_version_add_presentations.json'
input_csv = 'corpus_multi_label_presentation_version2.csv'
output_csv = 'corpus_presentation_more_than150_class_final.csv'

def open_jsonfile(input_json):
    with open (input_json, 'r', encoding='utf-8') as file:
        data_list = json.load(file)
    return data_list

def filter_classes_by_annotation_count(data_list, n):
    list_term = []
    n = 150
    count = 0
    for item in data_list:
        if len(item['details']) >= n:
            term = item['term']
            list_term.append(term)
            count += 1
    return list_term

def filter_corpus(list_class):
    #list_class = ['Études indiennes (Indologie)', 'Études japonaises', 'Études mexicaines' , 'Études russes', 'Anthropologie', 'Linguistique' , 'Architecture', 'Archéologie', 'Littératures du monde', 'Etudes cinématographiques']
    df = pd.read_csv(input_csv, sep=' ')
    df_corpus = pd.DataFrame(columns=df.columns)

    temp_dataframes = []
    for _, item in df.iterrows():
        media_name, terms, presentations, media_uri, description_value = item
        terms = eval(terms)
        for term in terms:
            if term in list_class :
                temp_dataframes.append(pd.DataFrame([item], columns=df.columns))
    df_corpus = pd.concat(temp_dataframes, ignore_index=True)
    df_corpus.to_csv(output_csv, sep=' ', encoding='utf-8')
