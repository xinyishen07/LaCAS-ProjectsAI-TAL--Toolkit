import pandas as pd
import numpy as np
import ast
import os
import openai
import urllib.request
import urllib.parse
import sys
from rdflib import Dataset, Namespace, URIRef, RDFS, Literal
from okapi_api import okapi_login,  sparql_search,  get_media, set_media
sys.path.insert(0, 'C:\\Users\\utilisateur\\Documents\\newvenv\\indexation_par_lot\\okapi') # add okapi folder to the system path
import json
import time

# TOTAL A INDEXER : 36000
# TEMPS A FAIRE : 24 heures
openai.api_key = ''
okapi_url = 'https://lacas.inalco.fr/portals'
# TODO: Make the information invisible
login = input("Please enter your Okapi login: ")
passwd = input("Password: ")
opener = okapi_login(okapi_url, login, passwd)
model = 'gpt-4o-mini'
df_voca = pd.read_csv('lists_voca/list_voca_etudes_areales.csv', encoding='utf-8')
df_voca = df_voca.drop_duplicates()
df_voca['vocas'] = df_voca['strLabel'] + '('+ df_voca['subclass']+')'

num_rows_to_process = 500
json_file = 'temp_file_etudes_aréales.json'
df_file = 'all_media_filtered.csv'
#df_file = 'all_media_filtered_docs_videos.csv'
result_gpt_csv = 'result_gpt_etudes_areales.csv'
state_path = 'state_etudes_aréales.txt'
failed_data_path = 'temp_failed_data_etudes_aréales.json'
lists_classes = []
for start in range(0, len(df_voca), 27):
    end = start + 27
    lists_classes.append(df_voca[start:end]['vocas'].tolist())
#lists_classes = [['Arménie', 'Linguistique -- Chinois', 'Traduction (discipline)', 'Économie', 'Asie du Sud-Est', 'Japonais', 'Linguistique -- Arabe', 'Études françaises', 'Argentine', 'Mexique', 'Urbanisme (discipline)', 'Didactique', 'Géographie', 'Études littéraires', 'Études littéraires -- Asie du Sud-Est', 'Turquie', 'Corée du Sud', 'Chili', 'Autels', 'La Réunion (département)', 'Phonétique'], ['Études africaines', 'Russie', 'Monde arabe', 'Iran', 'Alimentation', 'Coréen', 'Pérou', 'Grammaire', 'Sarcophage', 'Madagascar', 'Sénégal', 'Mosaïque', 'Japon', 'France', 'Anglais (langue)', 'Chapiteaux', 'Études chinoises', 'Argentine', 'Démographie (discipline)', 'Historiographie', 'Archéologie'], ['Niger', 'Etudes cinématographiques', 'Cameroun', 'Linguistique -- Arabe', 'Soudan', "États-Unis d'Amérique", 'Algérie', 'Amérique du Sud', 'Littérature du monde', 'Dérivation (grammaire)', 'Études indiennes (Indologie)', 'Architecture', 'Inde', 'Autels', 'Maroc', 'Bretagne (région française)', 'Montagnes', 'Philosophie', 'îles', 'Études mexicaines', 'Technologie'], ['Littérature poétique', 'Agriculture', 'Migration', 'Chinois (Mandarin)', 'Tchad', 'Brésil', 'Syntaxe', 'Viêt Nam', 'Linguistique', 'Poésie', 'Népal', 'Chine (République populaire)', 'Cancer', 'Péninsule arabique', 'Syrie', 'Mali', 'Indonésie', 'Istanbul', 'Études russes', 'Études arabes'], ['Études japonaises', 'Archéologie -- Moyen-Orient', 'Français', 'Droit (Discipline)', 'Culture culinaire', 'Turquie', 'Études américaines', 'Études aréales -- Littératures', 'Sociologie', 'Dynamique des populations', 'Géographie humaine (discipline)', "Science de l'éducation", 'Islam', 'Géographie', "Histoire de l'art", 'Ecologie', 'Histoire des religions', 'Migration humaine', 'Lexique', 'Morphologie linguistique']]
# BIND(xsd:dateTime(NOW()) AS ?now)
# FILTER ( bif:datediff('day', ?creationdate, ?now) < 3)
# FILTER ( bif:datediff('day', ?creationdate, ?now) > 1 && bif:datediff('day', ?creationdate, ?now) < 5)
def get_list_vocabulaires():
    lists_vocabulaires = ['list_general', 'list_etudes_areales', 'list_discipilines_scientifiques']
    
def get_documents(okapi_url, opener):
    data = []
    answer1 = sparql_search(okapi_url, """                  
        PREFIX core: <http://www.ina.fr/core#>
        prefix asa: <http://campus-aar.fr/asa#>
        prefix fr: <http://www.campus-AAR.fr/>
        prefix dc: <http://purl.org/dc/elements/1.1/>
        prefix user: <http://www.ina.fr/user/>
        SELECT DISTINCT group_concat(DISTINCT ?lab1; separator = " | ") as ?lab ?media ?url ?pre 
                        (GROUP_CONCAT(?keyword; SEPARATOR=", ") AS ?keywords) ?media_seg ?creationdate
        WHERE {
        ?media a core:Text OPTION (inference "http://campus-aar/owl") . 
        ?layer core:document ?media .        
        ?layer core:segment ?media_seg . 
        ?media_seg rdfs:label ?lab1 .
        ?media_seg core:creationDate ?creationdate .
        ?media_seg dc:description ?pre .
        ?media_seg dc:subject ?keyword.
        ?media core:instance ?instance .
        ?media_seg core:lastUser user:harvester .
        ?instance core:http_url ?url .       
        }
        ORDER BY ?url
        """, opener)
    for result in answer1:
        lab_value = result["lab"]["value"]
        media_value = result["media"]["value"]
        media_seg_value = result['media_seg']['value']
        url_value = result["url"]["value"]
        pre_value = result['pre']['value']
        key_value = result['keywords']['value']
        creationdate_value = result['creationdate']['value']
        data.append({"lab" : lab_value, "media": media_value, 'media_seg': media_seg_value, "url": url_value, 'presentation': pre_value, 'keywords': key_value, "creation_date":creationdate_value})
    answer2 = sparql_search(okapi_url, """
        PREFIX core: <http://www.ina.fr/core#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        SELECT DISTINCT ?lab ?media ?url ?pre (GROUP_CONCAT(?keyword; SEPARATOR=", ") AS ?keywords) ?media_seg
        WHERE {
        ?media a core:TemporalDocument .
        ?layer core:document ?media .
        ?layer core:segment ?media_segment .
        ?media_segment dc:title ?lab .
        ?media_segment dc:description ?pre .
        ?media_seg core:creationDate ?creationdate .
        ?media_seg dc:subject ?keyword .
        ?media core:instance ?instance .
        ?instance core:http_url ?url .
        }ORDER BY ?creationdate
        """, opener)
    for result in answer2:
        lab_value = result["lab"]["value"]
        media_value = result["media"]["value"]
        media_seg_value = result['media_seg']['value']
        url_value = result["url"]["value"]
        pre_value = result['pre']['value']
        key_value = result['keywords']['value']
        creationdate_value = result['creationdate']['value']
        data.append({"lab" : lab_value, "media": media_value, 'media_seg': media_seg_value, "url": url_value, 'presentation': pre_value, 'keywords': key_value, "creation_date":creationdate_value})
    df = pd.DataFrame(data)
    df = df.drop_duplicates(subset='media', keep='first')
    df = clean_dataframe(df)
    df = df.reset_index(drop=True)
    df.to_csv(df_file, encoding='utf8', mode='a')
    return df

def clean_dataframe(df):
    df['presentation'] = df['presentation'].apply(lambda x: ' | '.join(set(x.split(' | '))))
    df['presentation'] = df.groupby('media')['presentation'].transform(lambda x: ' | '.join(set(x)))
    df = df.drop_duplicates(subset=['media'])
    df['text'] = df['lab'] + ' '+ df['presentation'] + ' Les mot-clés du texte : '+ df['keywords']
    return df

def open_all_media():
    df = pd.read_csv(df_file, encoding='utf-8')
    df = df.drop_duplicates(subset='media', keep='first')
    df = clean_dataframe(df)
    df = df.drop('Unnamed: 0', axis=1 )
    df = df.reset_index(drop=True)
    df.to_csv(df_file, encoding='utf8')
    return df

def indexation_gpt(df, titles, list_class):
    if 'predicted_labels' not in df:
        df['predicted_labels'] = [[] for _ in range(len(titles))]
    for idx, title in enumerate(titles) :
        predict_labels = []
        completion = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",  "content": "Classifiez un texte à une ou plusieurs catégories correspondantes, chaque catégorie étant suivie de sa classe entre parenthèses. Si le texte correspond uniquement à une catégorie, répondez directement le nom de cette catégorie. Si le texte correspond à plusieurs catégories, répondez directement avec les noms des catégories séparés par des ','. S'il n'y a pas de bonne réponse , répondez 'Rien'. Si vous n'êtes pas certain de la classification pour certaines catégories, ne pas choisir ces catégories. Faites particulièrement attention lorsque vous choisissez des catégories linguistiques, afin de vous assurer qu'elles sont précises et appropriées."},
            {"role": "user", "content": "Le texte : " +  title},
            {"role": "system", "content": "Choisissez le(s) domaine(s) pertinent(s) parmi les suivants, chaque catégorie étant suivie de sa classe entre parenthèses :" + ' '.join(list_class) + "Avant de répondre, veuillez vérifier une fois de plus l'exactitude de la réponse."}
        ]
        )
        response = completion.choices[0].message.content
        if response.strip():
            response_labels = [label.strip() for label in response.split(',')] 
            for label in response_labels:
                if label in list_class:  
                    predict_labels.append(label)
        df['predicted_labels'][idx].extend(predict_labels)

def set_media(base_url, media_ref, media_url, identifier, mimeType, segmentType, threshold, media_segment_ref, kb,
              opener,
              unlock="true"):
    if media_url is None:
        url = base_url + "/api/saphir/set_media?uri=" + urllib.parse.quote(media_ref.toPython()) + \
      "&mimetype=" + mimeType + \
      "&segmenttype=" + urllib.parse.quote(segmentType) + \
      "&threshold=" + threshold + \
      "&unlock=" + unlock
    trig_string = kb.graph(media_segment_ref.toPython()).serialize(format='trig', base='.', encoding='utf-8')
    req = urllib.request.Request(url, trig_string, {'Content-Type': 'application/trig; charset: UTF-8'})
    op = urllib.request.urlopen(req)
    return op.read().decode()
'''
def drop_results():
    with open(json_file, 'r', encoding='utf-8') as file:
        data_list = json.load(file)
    threshold = str(0.0)
    mimetype = "application/pdf"
    media_segment_type = "http://campus-aar.fr/asa#ASAIngestionText"
    identifier = None
    media_url = None
    kb = Dataset(default_union=True)
    failed_data = []
    for _, data in enumerate(data_list):
        media = data.get('media')
        try:
            if not get_media(okapi_url, URIRef(media), kb, opener, write="true"):
                print("Error on loading " + media + " in write mode (certainly locked by another user)... SKIP")
            else : 
                media_seg = data.get('media_seg')
                predicted_labels = data.get("predicted_labels", [])
                if predicted_labels !='':
                    for label in predicted_labels:
                        entity =label.get('entity')
                        uriclass = label.get('uriclass')
                        get_media(okapi_url, URIRef(media), kb, opener, write="true")
                        kb.add((URIRef(media_seg), URIRef(uriclass), URIRef(entity),URIRef(media_seg))) # Triplet : segment_uri du texte, uri du domaine de connaissance du terme, uri du terme
                        try:
                            print(set_media(okapi_url, URIRef(media), media_url, identifier, mimetype, media_segment_type, threshold, URIRef(media_seg), kb, opener, unlock="true"))
                        except Exception as e:
                            print("the error is from ", media)
                            failed_data.append(data)
        except Exception as e:
            print("the error is from ", media)
            failed_data.append(data)
    for data in failed_data :
        media = data.get('media')
        try:
            if not get_media(okapi_url, URIRef(media), kb, opener, write="true"):
                print("Retry failed: Error on loading " + media + " in write mode (still locked)... SKIP")
            else:
                media_seg = data.get('media_seg')
                predicted_labels = data.get("predicted_labels", [])
                if predicted_labels != '':
                    for label in predicted_labels:
                        entity = label.get('entity')
                        uriclass = label.get('uriclass')
                        get_media(okapi_url, URIRef(media), kb, opener, write="true")
                        kb.add((URIRef(media_seg), URIRef(uriclass), URIRef(entity), URIRef(media_seg)))  # Triplet : segment_uri du texte, uri du domaine de connaissance du terme, uri du terme
                        try:
                            print(set_media(okapi_url, URIRef(media), media_url, identifier, mimetype, media_segment_type, threshold, URIRef(media_seg), kb, opener, unlock="true"))
                        except Exception as e:
                            print("Retry failed: the error is from ", media)
        except Exception as e:
            print("Retry failed: the error is from ", media)
'''
def make_hashable(value):
    if isinstance(value, list):
        # Convertit chaque élément de la liste en une version hachable
        return tuple(make_hashable(v) for v in value)
    elif isinstance(value, dict):
        # Convertit le dictionnaire en un frozenset de paires clé-valeur hachables
        return frozenset((k, make_hashable(v)) for k, v in value.items())
    return value

def drop_results():
    with open(json_file, 'r', encoding='utf-8') as file:
        data_list = json.load(file)
    
    threshold = str(0.0)
    mimetype = "application/pdf"
    media_segment_type = "http://campus-aar.fr/asa#ASAIngestionText"
    identifier = None
    media_url = None
    kb = Dataset(default_union=True)
    failed_data = []

    for _, data in enumerate(data_list):
        media = data.get('media')
        try:
            if not get_media(okapi_url, URIRef(media), kb, opener, write="true"):
                print("Error on loading " + media + " in write mode (certainly locked by another user)... SKIP")
            else:
                media_seg = data.get('media_seg')
                predicted_labels = data.get("predicted_labels", [])
                if predicted_labels != '':
                    for label in predicted_labels:
                        entity = label.get('entity')
                        uriclass = label.get('uriclass')
                        get_media(okapi_url, URIRef(media), kb, opener, write="true")
                        kb.add((URIRef(media_seg), URIRef(uriclass), URIRef(entity), URIRef(media_seg)))  # Triplet : segment_uri du texte, uri du domaine de connaissance du terme, uri du terme
                        try:
                            print(set_media(okapi_url, URIRef(media), media_url, identifier, mimetype, media_segment_type, threshold, URIRef(media_seg), kb, opener, unlock="true"))
                        except Exception as e:
                            failed_data.append(data)
        except Exception as e:
            failed_data.append(data)

    retry_count = 0
    max_retry_per_data = 3 
    data_retry_count = {}

    while retry_count < 5:
        retry_count += 1
        current_failed_data = failed_data
        failed_data = []
        
        for data in current_failed_data:
            data_id = data.get('media') 
            data_retry_count[data_id] = data_retry_count.get(data_id, 0) + 1
            
            # Ajouter les éléments à failed_data s'ils dépassent le nombre max de tentatives
            if data_retry_count[data_id] > max_retry_per_data:
                failed_data.append(data)
                continue
            
            media = data.get('media')
            try:
                if not get_media(okapi_url, URIRef(media), kb, opener, write="true"):
                    print(f"Retry failed: Error on loading {media} in write mode (still locked)... SKIP")
                else:
                    media_seg = data.get('media_seg')
                    predicted_labels = data.get("predicted_labels", [])
                    if predicted_labels != '':
                        for label in predicted_labels:
                            entity = label.get('entity')
                            uriclass = label.get('uriclass')
                            get_media(okapi_url, URIRef(media), kb, opener, write="true")
                            kb.add((URIRef(media_seg), URIRef(uriclass), URIRef(entity), URIRef(media_seg)))  # Triplet : segment_uri du texte, uri du domaine de connaissance du terme, uri du terme
                            try:
                                print(set_media(okapi_url, URIRef(media), media_url, identifier, mimetype, media_segment_type, threshold, URIRef(media_seg), kb, opener, unlock="true"))
                            except Exception as e:
                                # Ajouter uniquement les données qui n'ont pas dépassé le max retry
                                if data_retry_count[data_id] <= max_retry_per_data:
                                    failed_data.append(data)
            except Exception as e:
                # Ajouter uniquement les données qui n'ont pas dépassé le max retry
                if data_retry_count[data_id] <= max_retry_per_data:
                    failed_data.append(data)

    if failed_data:
        unique_failed_data = {frozenset((k, make_hashable(v)) for k, v in item.items()): item for item in failed_data}.values()
        with open(failed_data_path, 'w', encoding='utf-8') as outfile:
            json.dump(list(unique_failed_data), outfile, ensure_ascii=False, indent=4)
        print('The failed_data is saved in the file temp_failed_data.json. You can index them manually.')
    else:
        print('All the data is processed.')

    print(f"Number of retry attempts: {retry_count}")

def check_status():
    # if it is the first time we run the program
    if not os.path.exists(df_file) and not os.path.exists(state_path):
        start_index = 0
        df = get_documents(okapi_url, opener)
        df = df.iloc[:num_rows_to_process]
        df = clean_dataframe(df)
        titles = df['text'].tolist()
        for list_class in lists_classes:
            indexation_gpt(df, titles, list_class)
        print('----GPT----FINI----')
        df.to_csv(result_gpt_csv, encoding='utf-8')
        return df, start_index
    # if we have a csv file with all the media, but it's the first time to run the program
    if os.path.exists(df_file) and not os.path.exists(state_path):
        start_index = 0
        df = open_all_media()
        df = df.iloc[:num_rows_to_process]
        df = clean_dataframe(df)
        titles = df['text'].tolist()
        for list_class in lists_classes:
            indexation_gpt(df, titles, list_class)
        print('----GPT----FINI----')
        df.to_csv(result_gpt_csv, encoding='utf-8')
        return df, start_index
    # if it is not the first time that we run the program
    if os.path.exists(df_file) and os.path.exists(state_path):
        df = pd.read_csv(df_file, encoding='utf8')
        df = df.drop('Unnamed: 0', axis=1 )
        length_df = len(df['media'].tolist())
        with open(state_path, 'r') as state_file:
            start_index = int(state_file.read())
        print('---- TRAITER LES DONNEES A PARTIR DE LA LIGNE ', start_index, '----')
        result_gpt = pd.read_csv(result_gpt_csv, encoding='utf-8')
        num_line_result_gpt = result_gpt.shape[0]
        print(num_line_result_gpt)
        # s'il y a un problème de la dernière action, il faut refaire cette action.
        if start_index  < num_line_result_gpt :
            num_delete_line = num_line_result_gpt - start_index
            result_gpt = result_gpt[:-num_delete_line]
            result_gpt.reset_index(drop=True, inplace=True)
            result_gpt.to_csv(result_gpt_csv, index=False, encoding='utf-8')
            df = df.iloc[start_index : num_rows_to_process+start_index]
            df = clean_dataframe(df)
            df = df.reset_index(drop=True)
            titles = df['text'].tolist()
            for list_class in lists_classes:
                indexation_gpt(df, titles, list_class)
            print('----GPT----FINI----')
            df.to_csv(result_gpt_csv, encoding='utf-8', mode='a', header=False, index=False)
            return df, start_index
        if start_index == num_line_result_gpt :
            if length_df > start_index :
                if length_df >= start_index + num_rows_to_process: 
                    df = df.iloc[start_index : num_rows_to_process+start_index]
                    df = clean_dataframe(df)
                    df = df.reset_index(drop=True)
                    titles = df['text'].tolist()
                    for list_class in lists_classes:
                        indexation_gpt(df, titles, list_class)
                    print('----GPT----FINI----')
                    df.to_csv(result_gpt_csv, encoding='utf8', mode='a', header=False, index=False)
                    return df, start_index
                else:
                    df = df.iloc[start_index :]
                    df = clean_dataframe(df)
                    df = df.reset_index(drop=True)
                    titles = df['text'].tolist()
                    for list_class in lists_classes:
                        indexation_gpt(df, titles, list_class)
                    print('----GPT----FINI----')
                    df.to_csv(result_gpt_csv, encoding='utf8', mode='a', header=False, index=False)
                return df, start_index
            else : 
                print('All the media in the dataframe is processed.')
# TODO Si le processus coupe ici, une fonction qui arrive à prendre le fichier csv et trouver où commence      
starttime = time.time()
df, start_index = check_status()
results = []
for index, row in df.iterrows():
    entry = {col : row[col] for col in df.columns if col != 'predicted_labels'}
    entry['predicted_labels'] = []
    for label in row['predicted_labels']:
        matching_row = df_voca[df_voca['vocas'] == label]
        if not matching_row.empty:
            label_dict = matching_row.to_dict('records')[0]
            entry['predicted_labels'].append(label_dict)
    results.append(entry)

    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(results, file, indent=4)

drop_results()
with open(state_path, 'w') as file:
    file.write(str(num_rows_to_process + start_index))
endtime = time.time()
print((endtime-starttime), 's')
