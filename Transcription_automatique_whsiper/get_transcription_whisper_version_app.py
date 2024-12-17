import pandas as pd
import subprocess
import sys
import openai
import requests
sys.path.insert(0, '/mnt/c/Users/utilisateur/Documents/newvenv/okapi')
from okapi_api import okapi_login, sparql_search, sparql_admin, remove_transcription
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from rdflib import URIRef, Literal, Namespace, RDF, RDFS, XSD, Dataset
from ina_utilities import convert_seconds_to_MPEG7, convert_Okapi_time_to_timeRef, convert_timeRef_to_MPEG7, remove_layer_from_kb
from pathlib import Path
import json
"""
Fonction : Ce programme propose une interface utilisateur permettant de transcrire une liste de vidéos provenant du projet LaCAS en utilisant le modèle Whisper.

Entrée : 
- Compte administratif LaCAS : Identifiants nécessaires pour se connecter à la plateforme.
- Fichier txt qui contient des titres de vidéos à transcrire (un titre par ligne obligatoire)

Sortie : 
Les transcriptions sont enregistrées au format JSON dans le dossier `new_input_files`.

Méthodes d'utilisation :
1. Se connecter : Saisissez les informations de votre compte administratif LaCAS, puis cliquez sur "Login".
2. Sélectionner un fichier txt
3. Lancer le programme : Cliquer sur 'Importation'

Remarque : 
 - Pensez à saisir deux variable : source_dir (pour le répértoire new_input_files) et target_dir (pour le répértoire old_input_files)
"""

openai.api_key = ''
okapi_url = 'https://lacas.inalco.fr/portals'
opener = None
model = 'whisper-1'
file = 'new_video_list.csv'
language = 'fr'
kb = Dataset()
filename = None
source_dir = Path(r'C:\Users\utilisateur\Documents\newvenv\client_whisper_okapi\new_input_files')
target_dir = Path(r'C:\Users\utilisateur\Documents\newvenv\client_whisper_okapi\old_input_files')

def open_file():
    file_path = filedialog.askopenfilename(title='Open a txt file', filetypes=[('Text files', '*.txt')])
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = []
            for line in file:
                df = get_all_videos_pea(okapi_url, opener, line.strip())
                data.append(df)
            combined_df = pd.concat(data, ignore_index=True) if data else None
        output_text.insert(tk.END, f"Files are found. Begin to convert the videos to audios\n" + '')
        return combined_df
    return None


def get_all_videos_pea(okapi_url, opener, title):
    data = []
    query =f'''
    PREFIX core: <http://www.ina.fr/core#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        SELECT DISTINCT ?media ?url ?creationdate
        WHERE {{
        ?media a core:TemporalDocument .
        ?layer core:document ?media .
        ?layer core:segment ?media_segment .
        ?media_segment dc:title "{title}"@fr .
        ?media_segment core:creationDate ?creationdate .
        ?media core:instance ?instance .
        ?instance core:http_url ?url .
        }}ORDER BY ?creationdate
    '''
    answer = sparql_search(okapi_url, query, opener)
    for result in answer:
        media_value = result["media"]["value"]
        url_value = result['url']['value']
        data.append({"media": media_value, "url":url_value, "title": title})
    df = pd.DataFrame(data)
    return df

def convert_video_to_audio(video_file_path, audio_file_path, audio_format):
    try:
        command = ["ffmpeg", "-i", video_file_path, audio_file_path]
        subprocess.run(command, check=True)
        output_text.insert(tk.END, f"Audio extracted and saved to {audio_file_path}" + '')
    except subprocess.CalledProcessError as e:
        output_text.insert(tk.END, f"An error occurred: {e}")

def get_transcriptions(df):
    if df is None:
        output_text.insert(tk.END, "No data available for transcription.")
        return
    for _, items in df.iterrows():
        url = requests.get(items['url'], allow_redirects=True)
        if "hal" in items["media"]:
            video_path = "input_whisper/" + items["media"].split('/')[3] + '.mp4'
            audio_path = 'input_whisper/'  + items["media"].split('/')[3] + '.mp3'
            output_path = 'new_input_files/' + items["media"].split('/')[3] + '.lintoai.json'
        if 'nakala' in items['media']:
            video_path = 'input_whisper/' + ".".join(items["media"].split('/')[4:]) + '.mp4'
            audio_path = 'input_whisper/'  + ".".join(items["media"].split('/')[4:]) + '.mp3'
            output_path = 'new_input_files/' + ".".join(items["media"].split('/')[4:]) + '.lintoai.json'
        open(video_path, 'wb').write(url.content)
        output_text.insert(tk.END, 'Downloading the video...\n')
        convert_video_to_audio(video_path, audio_path, "mp3")
        output_text.insert(tk.END, "Begin to transcribe the file " + items['title'] + '')
        with open(audio_path, 'rb') as audio_file:
            result = openai.audio.transcriptions.create(
                model = model,
                file = audio_file,
                response_format = 'verbose_json',
                language = language
            )
        result = dict(result)
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(result["segments"], json_file, indent=2)
    output_text.insert(tk.END, f"The transcription process of the video(s) is/are complete. The file(s) is/are saved at new_input_files. Click on 'Importation' to import the transcription into LaCAS.\n")
        
def login():
    global opener
    login = entry_login.get()
    passwd = entry_passwd.get()
    opener = okapi_login(okapi_url, login, passwd)
    messagebox.showinfo("Login", "Login successful.")
    output_text.insert(tk.END, f"Click on 'open file' to continue the process.\n")

def password():
    messagebox.showinfo("Password", "Password functionality not yet implemented.")

# example of use of the add_whisper_transcription method
# the method retrieves all TV/Radio media id from the Okapi base and look for a transcription json file related to each media.
# calls to add_whisper_transcription send each transcription (converted to the Okapi native RDF format) to Okapi API using the bulk api
# push triples (reserved to admin users)
def add_transcription_whisper(okapi_url, kb, opener):
    global filename
    list_media = sparql_search(okapi_url, """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX core: <http://www.ina.fr/core#>
            PREFIX oopaip: <http://www.ina.fr/oopaip#>
            SELECT DISTINCT ?media
            WHERE {
            ?media a core:TemporalDocument .
            }""", opener)

    for item in list_media:
        media = item["media"]["value"]
        if 'hal' in media : 
            media2 = media[:-2]
            filename = 'new_input_files/' + media2.split(':')[-1] + ".lintoai.json"
        # filename = 'transcription_aar/'+media.split(':')[-1] + ".lintoai.json"
        if 'nakala' in media : 
            filename = 'new_input_files/' + ".".join(media.split('/')[4:]) + '.lintoai.json'
        if Path(filename).is_file():
            if add_whisper_transcription(media, kb, opener):
                print(media)
        '''
        else:
            print("no whisper file exists for media: " + media)
        '''
    kb.serialize(destination='whisper.trig', format='trig', encoding='utf-8')
    push_triples(okapi_url, kb, opener) # push triples into the database using SPARQL UPDATE protocol
    messagebox.showinfo("Success", "Transcription process finished successfully!\n")
    move_files_to_directory()
    messagebox.showinfo("Success", "Transcription files are now move to old_input_file!")
    root.quit()

# generate the Okapi compliant rdf triples for the specific layer which hold the transcription
def add_whisper_transcription(media, kb, opener):
    global filename
    core = Namespace("http://www.ina.fr/core#")
    if 'hal' in media : 
        media2 = media[:-2]
        filename = 'new_input_files/' + media2.split(':')[-1] + ".lintoai.json"
        # filename = 'transcription_aar/'+media.split(':')[-1] + ".lintoai.json"
    if 'nakala' in media : 
        filename = 'new_input_files/' + ".".join(media.split('/')[4:]) + '.lintoai.json'
    if Path(filename).is_file():
        with open(filename, 'r') as f:
            list_segments = json.load(f)    
            layer_root2 = media.replace('media', 'layer')
            speech_turn_layer = URIRef(layer_root2 + "/transcription/whisper")
            if kb.graph(speech_turn_layer):
                print("REMOVE the transcription layer if already present into kb ...just in case")
                remove_layer_from_kb(speech_turn_layer, kb)
            # create the layer (the structure is similar to the media ingestion segment)
            kb.add((speech_turn_layer, RDF.type, core.ASRLayer, speech_turn_layer))
            kb.add((speech_turn_layer, RDFS.label, Literal("Transcription WHISPER"), speech_turn_layer))
            kb.add((speech_turn_layer, core.document, URIRef(media), speech_turn_layer))
            for segment in list_segments:
                create_speech_segment_whisper(speech_turn_layer, segment, kb)
    return True

# generate the Okapi compliant rdf triples for a whisper speech turn
def create_speech_segment_whisper(layer_uri, root, kb):
    core = Namespace("http://www.ina.fr/core#")
    beginTime = str(root['start'])
    endTime = str(root['end'])
    segment_uri = URIRef(layer_uri + "/segment_" + beginTime.replace('.', '_'))
    # create segment properties values... begin, end, duration, type and segment text
    kb.add((URIRef(layer_uri), core.segment, segment_uri, URIRef(layer_uri)))
    beginTimeTC = convert_seconds_to_MPEG7(beginTime)
    endTimeTC = convert_seconds_to_MPEG7(endTime)
    beginTimeTR = convert_Okapi_time_to_timeRef(beginTimeTC)
    endTimeTR = convert_Okapi_time_to_timeRef(endTimeTC)
    durationTC = convert_timeRef_to_MPEG7(endTimeTR - beginTimeTR, isDuration=True)
    kb.add((segment_uri, core.beginTime, Literal(beginTimeTC), segment_uri))
    kb.add((segment_uri, core.beginTimeTR, Literal(beginTimeTR, datatype=XSD.integer), segment_uri))
    kb.add((segment_uri, core.endTime, Literal(endTimeTC), segment_uri))
    kb.add((segment_uri, core.endTimeTR, Literal(endTimeTR, datatype=XSD.integer), segment_uri))
    kb.add((segment_uri, core.duration, Literal(durationTC), segment_uri))
    kb.add((segment_uri, core.durationTR, Literal(endTimeTR - beginTimeTR, datatype=XSD.integer), segment_uri))
    kb.add((segment_uri, RDF.type, core.ASRSegment, segment_uri))
    kb.add((segment_uri, core.text, Literal(root['text']), segment_uri))
    if "confidence" in root: # add confidence if present
        kb.add((segment_uri, core.confidence, Literal(root['confidence'],datatype=XSD.float), segment_uri))

def push_triples(okapi_url, graph, opener):
    #trig_string = kb.serialize(format='trig', base='.', encoding='utf-8')
    #print(trig_string)
    n = 0
    query = "INSERT DATA {"
    for s, p, o, g in graph.quads((None,None,None,None)):
        n += 1
        if (n%500 == 0):
            query += "GRAPH " + g.n3() + " {" + s.n3() + " " + p.n3() + " " + o.n3() + "}} "
            # print(query)
            answer = sparql_admin(okapi_url, query, opener)
            # print(answer)
            query = "INSERT DATA {"
        else:
            query += "GRAPH " + g.n3() + " {" + s.n3() + " " + p.n3() + " " + o.n3() + "} "
    query += "}"
    # print(query)
    answer = sparql_admin(okapi_url, query, opener)
    print(answer)

def move_files_to_directory():
    target_dir.mkdir(parents=True, exist_ok=True)
    for file in source_dir.iterdir():
        if file.is_file():
            file.rename(target_dir / file.name)
#remove_transcription(okapi_url, 'http://campus-aar.fr/asa#oai:HAL:medihal-01378949v1', opener)

root = tk.Tk()
root.title("Video to Audio Transcription Tool")
root.geometry("600x400")

tk.Label(root, text="Login:").grid(row=0, column=0)
entry_login = tk.Entry(root)
entry_login.grid(row=0, column=1)
tk.Label(root, text="Password:").grid(row=1, column=0)
entry_passwd = tk.Entry(root, show="*")
entry_passwd.grid(row=1, column=1)

login_button = tk.Button(root, text="Login", command=login)
login_button.grid(row=2, column=0, columnspan=2, pady=5)

transcription_button = tk.Button(root, text="Open File and transcribe", command=lambda: get_transcriptions(open_file()))
transcription_button.grid(row=3, column=0, columnspan=2, pady=10)

importation_button = tk.Button(root, text='Importation', command=lambda : add_transcription_whisper(okapi_url, kb, opener))
importation_button.grid(row=4, column=0, columnspan=2, pady=10)

#delte_button = tk.Button(root, text='delete a transcription', command=)
output_text = tk.Text(root, wrap='word', height=10)
output_text.grid(row=5, column=0, columnspan=2, pady=10)
root.mainloop()

