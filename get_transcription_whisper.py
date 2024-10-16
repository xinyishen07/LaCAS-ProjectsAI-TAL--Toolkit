import whisper
import pandas as pd
import subprocess
import sys
import requests
sys.path.insert(0, '/mnt/c/Users/utilisateur/Documents/newvenv/okapi')
from okapi_api import okapi_login, sparql_search

"""
Fonction : Ce programme transcrit une liste de vidéos provenant du projet LaCAS en utilisant le modèle Whisper.

Entrée :
- Si aucune entrée n'est fournie, le programme utilise par défaut la fonction `get_all_videos_pea()`, qui récupère un dataframe contenant toutes les vidéos PEA à transcrire. Si d'autres transcriptions sont nécessaires, la requête SPARQL devra être modifiée.
- Alternativement, on peut passer en entrée un fichier CSV/TSV comportant 4 colonnes : media, title, title2, url. Ce fichier est chargé à l'aide de la fonction `open_tsv_file()`.

Sortie : 
Les transcriptions sont enregistrées au format JSON dans le dossier `new_input_files`.

Méthodes d'utilisation :
1. Première option :
   - Utiliser la fonction `get_all_videos_pea()` pour obtenir un dataframe avec toutes les vidéos PEA à transcrire. Si d'autres transcriptions sont nécessaires, ajuster la requête SPARQL en conséquence.
   - Utiliser la fonction `get_transcriptions()` pour transcrire les vidéos et enregistrer les résultats en JSON dans le dossier `new_input_files`.

2. Deuxième option :
   - Utiliser la fonction `open_tsv_file()` pour charger une liste de vidéos depuis un fichier CSV/TSV. Ce fichier doit comporter 4 colonnes : media (l'URI de la vidéo), title, title2, et url (l'URL du fichier vidéo).
   - Utiliser la fonction `get_transcriptions()` pour transcrire les vidéos de la liste et sauvegarder les transcriptions en JSON dans le dossier `new_input_files`.

Remarques :
- La colonne "media" contient l'URI de la page de la vidéo.
- La colonne "url" contient l'URL de la vidéo elle-même.
- Si vous voulez passer un fichier CSV/TSV, il faut remplir le variable file. Sinon, lassiez file = ''

Exemple de dataframe ou fichier CSV/TSV :
media	title	title2	url	creationdate
http://campus-aar.fr/asa#oai:HAL:hal-04626402v1	"Étudier et enseigner le droit des pays arabes, entretien avec Nathalie Bernard-Maugiron (IRD)"@fr	"Programme I-DEA (Illustration et Documentation audiovisuelles des Études Aréales)"@fr	https://hal.campus-aar.fr/hal-04626402/document	2024-07-02T04:02:45Z

Prochaine étape : pour importer la transcription sur LaCAS, utilisez le programme Python Client Whisper Okapi.py
"""


okapi_url = 'https://lacas.inalco.fr/portals'
# TODO: Make the information invisible
login = input("Please enter your Okapi login: ")
passwd = input("Password: ")
opener = okapi_login(okapi_url, login, passwd)
model = whisper.load_model("large-v3")
file = 'new_video_list.csv'
# file = ''

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
    print(df.head())
    return df

def create_df():
    df = pd.DataFrame
def open_tsv_file(file):
    df = pd.read_csv(file, encoding='utf-8')
    df = df.iloc[21:]
    print(df)
    return df

def clean_json_file(file='liste_entretiens_TICE.json'):
    df = pd.read_json(file, encoding='utf-8')
    df['url'] = df['uri_s'].apply(lambda x : x + '/document')
    df['media'] = df['uri_s'].apply(lambda x : ':' + x.split('/')[-1] + 'v1')
    df = df[111:130]
    return df

def convert_video_to_audio(video_file_path, audio_file_path, audio_format):
    """
    Convert a video file to an audio file using FFmpeg.

    Args:
    - video_file_path (str): Path to the input video file.
    - audio_file_path (str): Path where the output audio file will be saved.
    - audio_format (str): The audio format (e.g., 'mp3', 'wav'). Defaults to 'mp3'.
    """
    try:
        command = ["ffmpeg", "-i", video_file_path, audio_file_path]
        subprocess.run(command, check=True)
        print(f"Audio extracted and saved to {audio_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def get_transcptions(df, media):
    for _, items in df.iterrows():
        url = requests.get(items['url'], allow_redirects=True)
        video_path = "input_whisper/" + items[media].split('/')[3] + '.mp4'
        audio_path = 'input_whisper/'  + items[media].split('/')[3] + '.mp3'
        output_path = 'new_input_files/' + items[media].split('/')[3] + '.lintoai.json'
        open(video_path, 'wb').write(url.content)
        convert_video_to_audio(video_path, audio_path, "mp3")
        print("Fin du traitement du vidéo " + items['title'])
        # print("Fin du traitement du vidéo " + items['label_s'])
        result = model.transcribe(audio_path, language = 'french')
        speech = pd.DataFrame.from_dict(result['segments'])
        speech.to_json(output_path, orient='records')

if file != '':    
    df = open_tsv_file(file)
    print(df)
    get_transcptions(df, media='url')
else : 
    df = get_all_videos_pea(okapi_url, opener)
    print(df)
    get_transcptions(df, media='url')