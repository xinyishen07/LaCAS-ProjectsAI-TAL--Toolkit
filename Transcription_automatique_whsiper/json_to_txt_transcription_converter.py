import pandas as pd
import os
import re
import sys
from okapi_api import okapi_login, sparql_search
"""
Fonction : Ce programme permet de faciliter la correction manuelle des transcriptions en effectuant deux actions :
1) Transformer les fichiers JSON en fichiers TXT en ne conservant que la timeline et la transcription.
2) Renommer les fichiers (passer de l'URI à un nom de vidéo compréhensible).

Entrée : 
- `input_files` : Le dossier contenant les transcriptions au format JSON.
- `input_csv_file` : Un fichier CSV/TSV contenant des informations sur les transcriptions JSON présentes dans 'input_files'. Ce fichier doit comporter 3 colonnes : media (URI de la vidéo), title (nom du fichier vidéo), et title2. Il est recommandé de bien conserver ce fichier CSV/TSV, notamment celui utilisé pour `get_transcription_whisper.py`.

Sortie : 
- `output_files` : Le dossier dans lequel seront enregistrés les fichiers TXT traités.

Remarques : 
- La colonne "media" dans le fichier CSV/TSV contient l'URI de la vidéo.
"""
okapi_url = 'https://lacas.inalco.fr/portals'
login = input("Please enter your Okapi login: ")
passwd = input("Password: ")
opener = okapi_login(okapi_url, login, passwd)

input_files = 'new_input_files/'
input_csv_file = 'new_video_list.csv'
output_files = 'txt_aar/'

def open_csv_file(file):
    df = pd.read_csv(file, encoding='utf-8')
    return df
def get_all_videos_pea(okapi_url, opener):
    data = []
    answer = sparql_search(okapi_url, '''
        PREFIX core: <http://www.ina.fr/core#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        SELECT DISTINCT ?media ?title ?title2 ?url ?creationdate
        WHERE {
        ?media a core:TemporalDocument .
        ?layer core:document ?media .
        ?layer core:segment ?media_segment .
        ?media_segment dc:title ?title .
        ?media_segment dc:title2 ?title2 .
        ?media_segment core:creationDate ?creationdate .
        ?media core:instance ?instance .
        ?instance core:http_url ?url .
        FILTER(CONTAINS(LCASE(?title2), "programme i-dea"))
        }ORDER BY ?creationdate
    ''', opener)
    for result in answer:
        media_value = result["media"]["value"]
        title1_value = result["title"]["value"]
        title2_value = result['title2']['value']
        url_value = result['url']['value']
        data.append({"media": media_value, "url":url_value, "title": title1_value, "title2":title2_value})
    df = pd.DataFrame(data)
    return df

def json2txt(df):
    for filejson in os.listdir(input_files):
        if filejson.endswith('.json'):
            full_path = os.path.join(input_files, filejson)
            data = pd.read_json(full_path, encoding='utf-8')
            for _, item in data.iterrows():
                start = item['start']
                end = item['end']
                text = item['text']
                uri = filejson[:-13]
                name = df.loc[df['media'].str.contains(uri), 'title'].iloc[0]
                name = re.sub(r'[^\w\s]', '', name)
                try : 
                    with open(output_files + uri + '.txt', 'a+', encoding='utf-8') as file:
                        file.write(str(start) + '-' + str(end) + ' : ' + text +'\n')
                except OSError:
                    print(uri)
df = open_csv_file(input_csv_file)
print(df["media"])
#df = get_all_videos_pea(okapi_url, opener)
df = df.iloc[-2:]
json2txt(df)
