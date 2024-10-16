from okapi_api import sparql_search, okapi_login, sparql_admin, remove_transcription
from rdflib import URIRef, Literal, Namespace, RDF, RDFS, XSD, Dataset
from ina_utilities import convert_seconds_to_MPEG7, convert_Okapi_time_to_timeRef, convert_timeRef_to_MPEG7, remove_layer_from_kb
import pandas as pd
import os
from pathlib import Path
import json
'''
"""
Fonction : Ce programme permet de réimporter les transcriptions corrigées sur la plateforme LaCAS après les modifications manuelles.

Entrée : 
- Les transcriptions corrigées au format TXT, stockées dans la variable `chemin_txt_entre`.
- Les transcriptions converties au format JSON seront enregistrées dans la variable `chemin_json_final`.

Sortie : 
- Aucune sortie visible (le programme n'affiche pas de résultat).

Méthodes d'utilisation :
1. `name2uri()` : Cette fonction gère deux types de noms pour les fichiers TXT :
   - 1) Fichiers avec "lintoai" dans le nom.
   - 2) Le nom complet du fichier vidéo lui-même. Dans certains cas, il peut y avoir plusieurs versions de la même vidéo, par exemple 'v1' et 'v2', et cette fonction les distingue.
   
   La sortie de cette fonction est :
   - Le nom du fichier TXT (en français).
   - Le nom au format JSON (URI de la vidéo).

2. `txt2json()` : Cette fonction convertit un fichier TXT en fichier JSON.

3. Après cela, les fonctions standards d'importation des transcriptions sur LaCAS peuvent être utilisées. Les détails de ces fonctions se trouvent dans le programme `Client Whisper Okapi.py`.

Remarque : 
- Ce programme part du principe qu'il existe déjà une transcription sur LaCAS, qui n'a pas encore été corrigée manuellement.
"""

'''
#filename = 'input_files/hal-04107881v1.lintoai.json'

okapi_url = "https://lacas.inalco.fr/portals"
# okapi_url = 'http://ulysse31.inalco.fr:8080/portals/'
login = input("Please enter your Okapi login: ")
passwd = input("Password: ")
opener = okapi_login(okapi_url, login, passwd)
kb = Dataset()

dffile = 'list_videos_idea.csv'
df = pd.read_csv(dffile, encoding='utf-8')
chemin_json_final = "transcription_idea_miseajour/"
chemin_txt_entre = "txt_idea_verifie/"

def name2uri(txtname, df):
    if 'lintoai' in txtname:
        jsonname = txtname.split('__.')[1][:-3] + 'json'
    else :
        print(txtname)
        jsonname = txtname.split('entretien avec ')[1].split('(')[0] # the name of the interviewer
        #uri = df[df['title'].str.contains(jsonname, case=False)]['media'].split(':')[-1]
        filtered_series = df[df['title'].str.contains(jsonname, case=False)]['media'].str.split(':').apply(lambda x: x[-1])
        if len(filtered_series) > 1:
            v2_entries = filtered_series[filtered_series.str.endswith('v2')]
            # Select the first 'v2' entry if available, otherwise fallback to the first available entry
            uri = v2_entries.iloc[0] if not v2_entries.empty else filtered_series.iloc[0]
        else:
            # Only one entry or none, use it directly
            uri = filtered_series.iloc[0] if not filtered_series.empty else "No match found"
        jsonname = uri + '.lintoai.json'
    return txtname, jsonname


def txt2json(jsonname, txtname):
    start_list, end_list, text_list = [], [], []
    with open(chemin_txt_entre + txtname, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if ':' in line : 
                parts =  line.split(':')
                if len(parts) > 1  and parts[-1].strip() : # S'assure que du texte suit le dernier ':'
                    start = line.split('-')[0].strip()
                    end = line.split('-')[1].split(':')[0].strip()
                    text = parts[-1].strip()
                    # Accumuler le texte si les lignes suivantes sont vides jusqu'à une ligne avec texte
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().split(':')[-1].strip(): # si le texte est vide
                        next_end = lines[j].strip().split('-')[1].split(':')[0].strip()
                        if next_end:
                            end = next_end
                        j += 1 
                    i = j - 1

                    start_list.append(start)
                    end_list.append(end)
                    text_list.append(text)
            i += 1
    df = pd.DataFrame({'start' : start_list, 'end' : end_list, 'text': text_list})
    json_result = df.to_json(chemin_json_final + jsonname, orient='records')
    return json_result


def add_transcription_whisper(okapi_url, kb, opener):
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
        #media2 = media[:-2]
        #filename = 'txt_aar_mettre_a_jour/' + media.split(':')[-1] + ".lintoai.json"
        filename = chemin_json_final + media.split(':')[-1] + ".lintoai.json"
        if Path(filename).is_file():
            if add_whisper_transcription(media, kb, opener):
                print(media)
        '''
        else:
            print("no whisper file exists for media: " + media)
        '''
    kb.serialize(destination='whisper.trig', format='trig', encoding='utf-8')
    push_triples(okapi_url, kb, opener) # push triples into the database using SPARQL UPDATE protocol

# generate the Okapi compliant rdf triples for the specific layer which hold the transcription
def add_whisper_transcription(media, kb, opener):
    core = Namespace("http://www.ina.fr/core#")
    #media2 = media[:-2]
    # filename = 'txt_aar_mettre_a_jour/' + media.split(':')[-1] + ".lintoai.json"
    filename = chemin_json_final + media.split(':')[-1] + ".lintoai.json"
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


for txtname in os.listdir(chemin_txt_entre):
    txtname, jsonname = name2uri(txtname, df)
    txt2json(jsonname, txtname)

for jsonname in os.listdir(chemin_json_final):
    uri = 'http://campus-aar.fr/asa#oai:HAL:' + jsonname.split('.')[0]
    remove_transcription(okapi_url, uri, opener)
add_transcription_whisper(okapi_url, kb, opener)
