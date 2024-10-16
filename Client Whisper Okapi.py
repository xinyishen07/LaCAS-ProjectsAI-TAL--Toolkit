from okapi_api import sparql_search, okapi_login, sparql_admin, remove_transcription
from rdflib import URIRef, Literal, Namespace, RDF, RDFS, XSD, Dataset
from ina_utilities import convert_seconds_to_MPEG7, convert_Okapi_time_to_timeRef, convert_timeRef_to_MPEG7, remove_layer_from_kb
from pathlib import Path
import json

"""
Fonction : Ce programme importe les transcriptions de vidéos sur la plateforme LaCAS après leur traitement.

Entrée : 
- Les fichiers JSON contenant les transcriptions, situés dans le dossier 'new_input_files'.

Sortie : 
- Aucune sortie (le programme n'affiche pas de résultat).

Méthodes d'utilisation :
1. Le programme vérifie automatiquement si le dossier 'new_input_files' contient des fichiers JSON.
2. Si le dossier n'est pas vide, il prend ces fichiers et les importe sur LaCAS.
3. Si vous souhaitez ré-importer une transcription existante, vous devez d'abord la supprimer en utilisant la fonction `remove_transcription()`. 
   Un exemple de suppression de transcription est fourni à la dernière ligne de ce programme.

Remarques : 
- Assurez-vous que les fichiers JSON ont été générés et enregistrés correctement dans le dossier 'new_input_files' avant d'exécuter le programme.
"""


okapi_url = "https://lacas.inalco.fr/portals"
login = input("Please enter your Okapi login: ")
passwd = input("Password: ")
opener = okapi_login(okapi_url, login, passwd)
kb = Dataset()

# example of use of the add_whisper_transcription method
# the method retrieves all TV/Radio media id from the Okapi base and look for a transcription json file related to each media.
# calls to add_whisper_transcription send each transcription (converted to the Okapi native RDF format) to Okapi API using the bulk api
# push triples (reserved to admin users)
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
        media2 = media[:-2]
        filename = 'new_input_files/' + media2.split(':')[-1] + ".lintoai.json"
        # filename = 'transcription_aar/'+media.split(':')[-1] + ".lintoai.json"
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
    media2 = media[:-2]
    filename = 'new_input_files/' + media2.split(':')[-1] + ".lintoai.json"
    #filename = 'transcription_aar/'+media.split(':')[-1] + ".lintoai.json"
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


#remove_transcription(okapi_url, 'http://campus-aar.fr/asa#oai:HAL:medihal-01378949v1', opener)
add_transcription_whisper(okapi_url, kb, opener)