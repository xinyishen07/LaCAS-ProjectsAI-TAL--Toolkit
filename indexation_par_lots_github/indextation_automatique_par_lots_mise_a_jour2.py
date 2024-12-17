
import pandas as pd
import numpy as np
import ast
import os
import openai
import urllib.request
import urllib.parse
import sys
from rdflib import Dataset, Namespace, URIRef, RDFS, Literal
from okapi_api import okapi_login, sparql_search, get_media, set_media
import json
import time
from datetime import date, datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext, StringVar, Radiobutton
import threading
import traceback

"""
Fonctionnalités
Ce programme propose une interface utilisateur permettant d’indexer automatiquement des lots sur la plateforme LaCAS en s'appuyant sur le modèle GPT.

Entrée : 
- Compte administratif LaCAS : Identifiants nécessaires pour se connecter à la plateforme.
- Répertoire list_voca : Contient les listes de vocabulaire utilisées pour l’indexation sur LaCAS.

Sortie : 
- Répertoire 'result_mise_a_jour' :
    Fichiers CSV au format result_gpt_list_x_mise_a_jour.csv : Chaque fichier contient les informations sur les nouvelles entités de médias indexées sur LaCAS et les vocabulaires associés prédits par GPT.
    Fichiers TXT au format state_list_x_mise_a_jour.txt : Chaque fichier enregistre la date de la dernière action effectuée (correspondant à la dernière exécution du programme).

- Répertoire 'temp_file_mise_a_jour' : 
    Fichiers JSON au format temp_file_liste_x.json : Ces fichiers contiennent temporairement les nouvelles données mises à jour lors de l’exécution du programme. Les anciens contenus sont supprimés après chaque action.
    Fichiers JSON au format temp_liste_x_failed_data.json : Ces fichiers listent temporairement les médias pour lesquels l'importation sur LaCAS a échoué. Leur contenu est également effacé après chaque action.

Méthodes d'utilisation : 
1. Se connecter : Saisissez les informations de votre compte administratif LaCAS, puis cliquez sur "Login".
2. Sélectionner une liste : Choisissez une liste de vocabulaire à partir du répertoire list_voca.
3. Lancer l’indexation : Cliquez sur "Start indexation" pour commencer le processus.
"""

openai.api_key = ''
okapi_url = 'https://lacas.inalco.fr/portals'
opener = None
model = 'gpt-4o-mini'
'''
df_voca = pd.read_csv('lists_voca/list_voca_filter.csv', encoding='utf-8')
df_voca = df_voca.drop_duplicates()'''

today = date.today()
date_format = "%Y-%m-%d"
lists_classes = []
voca_options = {
    "liste générale": 'list_voca_general.csv',
    "liste études aréales": 'list_voca_etudes_areales.csv',
    "liste disciplines scientifiques": 'list_voca_disciplines_scientifiques.csv',
    "liste aires linguistiques": 'list_voca_aires_linguistiques.csv',
    "liste société du monde": 'list_voca_societe_du_monde.csv',
    "liste démographie, poplulations, migrations": 'list_voca_demographie.csv',
    'liste réseau et mouvements sociaux':'list_voca_reseau_mouvements_sociaux.csv',
    'liste médecine et santé, hygiène, cosmétiques': 'list_voca_sante.csv',
    'liste Croyances et cultes': 'list_voca_croyances_cultes.csv',
    'liste relations internationales, sécurité': 'list_voca_relations_internationales_securite.csv',
    'liste histoire et préhistoire': 'list_voca_histoire_prehistoire.csv',
    'liste milieu géographique': 'list_voca_milieu_geographique.csv',
    'liste art, littérature, cinéma, musique' : 'list_voca_art_litterature_cinema_architecture.csv'
}

def load_vocabulary(df_voca):
    global lists_classes
    if df_voca is not None:
        lists_classes = []
        for start in range(0, len(df_voca), 27):
            end = start + 27
            lists_classes.append(df_voca[start:end]['strLabel'].tolist())

class VocabularySelector:
    def __init__(self,root):
        self.root = root
        self.selected_option_global = None
        self.df_voca = None 
        self.json_file = None
        self.result_gpt_csv = None
        self.state_path = None
        self.failed_data_path = None
    
    def select_vocabulary(self):
        def on_select():
            selected_option = self.voca_option.get()
            csv_file = voca_options.get(selected_option)
            if not csv_file:
                messagebox.showwarning("Selection Error", "Please select a valid option.")
                return
            try:
                self.df_voca = pd.read_csv('lists_voca/' + csv_file, encoding='utf-8')
                self.df_voca = self.df_voca.drop_duplicates()
                load_vocabulary(self.df_voca)
                messagebox.showinfo("Success", f"Vocabulary loaded from {csv_file}!")
                self.selected_option_global = selected_option
                top.destroy()
                self.update_paths()
                btn_start.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while loading the vocabulary: {e}")

        top = tk.Toplevel(root)
        top.title("Select Vocabulary")
        self.voca_option = StringVar()
        self.voca_option.set("liste générale")

        for idx, option in enumerate(voca_options.keys()):
            Radiobutton(top, text=option, variable=self.voca_option, value=option).pack(anchor='w')

        btn_select = tk.Button(top, text="Select", command=on_select)
        btn_select.pack(pady=10)

        top.wait_window()

    def get_selected_option(self):
        return self.selected_option_global
    
    def get_vocabulary_dataframe(self):
        return self.df_voca

    def update_paths(self):
        self.selected_option_global = self.get_selected_option()
        self.selected_option_global = self.selected_option_global.replace(' ', '_').replace('é', 'e').replace('è', 'e')
        if self.selected_option_global is not None:
            self.json_file = 'temp_file_mise_a_jour/temp_file_' + self.selected_option_global +'.json'
            self.result_gpt_csv = 'result_mise_a_jour/result_gpt_' + self.selected_option_global +'_mise_a_jour.csv'
            self.state_path = 'result_mise_a_jour/state_'+ self.selected_option_global +'_mise_a_jour.txt'
            self.failed_data_path = 'temp_file_mise_a_jour/temp_'+ self.selected_option_global +'_failed_data.json'
        else:
            messagebox.showwarning("Selection Warning", 'No list selected yet.')
    def get_update_paths(self):
        return self.json_file, self.result_gpt_csv, self.state_path, self.failed_data_path

def login():
    global opener
    login = entry_login.get()
    passwd = entry_passwd.get()
    if not login or not passwd:
        messagebox.showwarning("Input Error", "Please enter both login and password.")
        return
    try:
        opener = okapi_login(okapi_url, login, passwd)
        messagebox.showinfo("Success", "Login successful!")
        btn_select_voca.config(state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror("Login Failed", f"An error occurred during login: {e}")

def get_documents(okapi_url, opener, days):
    data = []
    query = f'''PREFIX core: <http://www.ina.fr/core#>
        prefix asa: <http://campus-aar.fr/asa#>
        prefix fr: <http://www.campus-AAR.fr/>
        prefix dc: <http://purl.org/dc/elements/1.1/>
        prefix user: <http://www.ina.fr/user/>
        SELECT DISTINCT group_concat(DISTINCT ?lab1; separator = " | ") as ?lab ?media ?url ?pre 
                        (GROUP_CONCAT(?keyword; SEPARATOR=", ") AS ?keywords) ?media_seg ?creationdate
        WHERE {{
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
        BIND(xsd:dateTime(NOW()) AS ?now)
        FILTER ( bif:datediff('day', ?creationdate, ?now) < {days})       
        }}
        ORDER BY ?creationdate'''
    answer = sparql_search(okapi_url, query, opener)
    for result in answer:
        lab_value = result["lab"]["value"]
        media_value = result["media"]["value"]
        media_seg_value = result['media_seg']['value']
        url_value = result["url"]["value"]
        pre_value = result['pre']['value']
        key_value = result['keywords']['value']
        creationdate_value = result['creationdate']['value']
        data.append({"lab" : lab_value, "media": media_value, 'media_seg': media_seg_value, "url": url_value, 'presentation': pre_value, 'keywords': key_value, "creation_date":creationdate_value})
    df = pd.DataFrame(data)
    if df.empty:
        messagebox.showinfo("Empty Dataframe", 'There is no new data available. Please close the window and disregard any displayed errors.')
    df = df.drop_duplicates(subset='media', keep='first')
    df = clean_dataframe(df)
    df = df.reset_index(drop=True)
    return df

def clean_dataframe(df):
    df['presentation'] = df['presentation'].apply(lambda x: ' | '.join(set(x.split(' | '))))
    df['presentation'] = df.groupby('media')['presentation'].transform(lambda x: ' | '.join(set(x)))
    df = df.drop_duplicates(subset=['media'])
    df['text'] = df['lab'] + ' '+ df['presentation'] + ' Les mot-clés du texte : '+ df['keywords']
    return df

def indexation_gpt(df, titles, list_class, selected_option_global):
    if 'predicted_labels' not in df:
        df['predicted_labels'] = [[] for _ in range(len(titles))]
    for idx, title in enumerate(titles) :
        predict_labels = []
        completion = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",  "content": "Classifiez un texte à une ou plusieurs catégories correspondantes. Toutes les catégories appartiennent à la grande catégorie " + selected_option_global+" .Si le texte correspond uniquement à une catégorie, répondez directement le nom de cette catégorie. Si le texte correspond à plusieurs catégories, répondez directement avec les noms des catégories séparés par des ','. Si il n'y pas de bonne réponse, répondez 'Rien'."},
            {"role": "user", "content": "Le texte : " +  title},
            {"role": "system", "content": "Choisissez le(s) domaine(s) pertinent(s) parmi les suivants :" + ' '.join(list_class)}
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

def make_hashable(value):
    if isinstance(value, list):
        # Convertit chaque élément de la liste en une version hachable
        return tuple(make_hashable(v) for v in value)
    elif isinstance(value, dict):
        # Convertit le dictionnaire en un frozenset de paires clé-valeur hachables
        return frozenset((k, make_hashable(v)) for k, v in value.items())
    return value

def drop_results():
    json_file, result_gpt_csv, state_path, failed_data_path = vocabulary_selector.get_update_paths()
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
                terminal_output.insert(tk.END,"Error", "Retry failed: Error on loading {media} in write mode (still locked)... SKIP\n")

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
                            time.sleep(0.5)
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
                    terminal_output.insert(tk.END,"Error", "Retry failed: Error on loading {media} in write mode (still locked)... SKIP\n")
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
                                time.sleep(0.5)
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
        terminal_output.insert(tk.END, "The failed_data is saved in the file temp_failed_data.json. You can index them manually.\n")
    else:
        terminal_output.insert(tk.END, "All the data is processed.\n")
        
    print(f"Number of retry attempts: {retry_count}")

def check_status():
    json_file, result_gpt_csv, state_path, failed_data_path = vocabulary_selector.get_update_paths()
    # if it is the first time we run the program
    if not os.path.exists(json_file) and not os.path.exists(state_path):  
        df = get_documents(okapi_url, opener, days=10)
        titles = df['text'].tolist()
        for list_class in lists_classes:
            indexation_gpt(df, titles, list_class, vocabulary_selector.selected_option_global)
        terminal_output.insert(tk.END, "-----GPT-----FIN-----\n")
        df.to_csv(result_gpt_csv, encoding='utf-8')
        return df
    # if it is not the first time that we run the program
    if os.path.exists(json_file) and os.path.exists(state_path):
        
        result_gpt_df = pd.read_csv(result_gpt_csv, encoding='utf-8')
        last_creation_date = result_gpt_df['creation_date'].iloc[-1].split('T')[0] # the format of the date is like 2023-06-09T05:59:12Z
        print(last_creation_date)
        terminal_output.insert(tk.END, f"The indexing process will begin from the {last_creation_date}")

        last_creation_date = datetime.strptime(str(last_creation_date), date_format).date()
        with open(state_path, 'r') as state_file:
            last_datetime = str(state_file.read()) # the format is %y-%m-%d
        last_datetime = datetime.strptime(last_datetime, date_format).date()
        # if there is no problem during the last action, we continue
        if last_creation_date != today and last_datetime != today:
            days_difference = (today - last_datetime).days
            df = get_documents(okapi_url, opener, str(days_difference))
            df = df.reset_index(drop=True)
            titles = df['text'].tolist()
            for list_class in lists_classes:
                indexation_gpt(df, titles, list_class, vocabulary_selector.selected_option_global)
            terminal_output.insert(tk.END, "-----GPT-----FIN-----\n")
            df.to_csv(result_gpt_csv, encoding='utf8', mode='a', header=False, index=True)
            return df
        # if there is a problem during the last action, we redo it
        if last_datetime != today and last_creation_date == today:
            last_index = result_gpt_df[result_gpt_df['creation_date'].str.contains(str(last_datetime))].index[-1]
            result_gpt_df = result_gpt_df.iloc[:last_index + 1]
            result_gpt_df.reset_index(drop=True, inplace=True)
            result_gpt_df.to_csv(result_gpt_csv, index=False, encoding='utf-8')
            days_difference = (today - last_datetime).days
            df = get_documents(okapi_url, opener, str(days_difference))
            df = clean_dataframe(df)
            df = df.reset_index(drop=True)
            titles = df['text'].tolist()
            for list_class in lists_classes:
                indexation_gpt(df, titles, list_class, vocabulary_selector.selected_option_global)
            terminal_output.insert(tk.END, "-----GPT-----FIN-----\n")
            df.to_csv(result_gpt_csv, encoding='utf8', mode='a', header=False, index=True)
            return df

# Tkinter GUI for login and indexation control
def run_indexation(terminal_output):
    json_file, result_gpt_csv, state_path, failed_data_path = vocabulary_selector.get_update_paths()
    try:
        df = check_status()
        results = []
        for _, row in df.iterrows():
            entry = {col: row[col] for col in df.columns if col != 'predicted_labels'}
            entry['predicted_labels'] = []
            for label in row['predicted_labels']:
                matching_row = vocabulary_selector.df_voca[vocabulary_selector.df_voca['strLabel'] == label]
                if not matching_row.empty:
                    label_dict = matching_row.to_dict('records')[0]
                    entry['predicted_labels'].append(label_dict)
            results.append(entry)
            with open(json_file, 'w', encoding='utf-8') as file:
                json.dump(results, file, indent=4)
        drop_results()     
        with open(state_path, 'w') as file:
            file.write(str(today))

        terminal_output.insert(tk.END, "Indexation complete!\n")
        messagebox.showinfo("Success", "Indexation process finished successfully!")
        root.quit()

    except Exception as e:
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))  # Get full error traceback
        terminal_output.insert(tk.END, f"An error occurred:\n{error_message}\n")
        messagebox.showerror("Error", "An error occurred. Please check the terminal output for details. Copy and paste the error information and send it to xinyishen07@gmail.com.\n")

def start_indexation():
    if not opener:
        messagebox.showwarning("Login Required", "Please login first before starting the indexation.")
        return
    if vocabulary_selector.df_voca is None:
        messagebox.showwarning("Vocabulary Required", "Please select a vocabulary before starting the indexation.")
        return
    terminal_output.insert(tk.END, "Starting the indexation process...")
    threading.Thread(target=run_indexation, args=(terminal_output,)).start()
    
# Tkinter GUI for login and indexation control
root = tk.Tk()
root.title("Indexation Tool")
root.geometry("500x500")

frame = tk.Frame(root)
frame.pack(pady=10)

# Login inputs
tk.Label(frame, text="Login:").grid(row=0, column=0, padx=5, pady=5)
entry_login = tk.Entry(frame)
entry_login.grid(row=0, column=1, padx=5, pady=5)
tk.Label(frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
entry_passwd = tk.Entry(frame, show="*")
entry_passwd.grid(row=1, column=1, padx=5, pady=5)

# Button to login
btn_login = tk.Button(frame, text="Login", command=login)
btn_login.grid(row=2, column=0, columnspan=2, pady=10)

# Button to select vocabulary
vocabulary_selector = VocabularySelector(root)
btn_select_voca = tk.Button(frame, text="Select Vocabulary", command=vocabulary_selector.select_vocabulary, state=tk.DISABLED)
btn_select_voca.grid(row=3, column=0, columnspan=2, pady=10)

# Button to start the indexing process
btn_start = tk.Button(frame, text="Start Indexation", command=start_indexation, state=tk.DISABLED)
btn_start.grid(row=4, column=0, columnspan=2, pady=10)

# Terminal output box (ScrolledText widget)
terminal_output = scrolledtext.ScrolledText(frame, width=60, height=15)
terminal_output.grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()
