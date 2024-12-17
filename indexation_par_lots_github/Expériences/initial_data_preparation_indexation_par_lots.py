# -*- coding: utf-8 -*-
import pandas as pd
import sys
import json
sys.path.insert(0, '/mnt/c/Users/utilisateur/Documents/torchvenv/okapi') # add okapi folder to the system path
from okapi_api import okapi_login, sparql_search
from collections import defaultdict
'''
Fonction : Ce programme constitue la première étape de la préparation des données pour l'entraînement de l'indexation automatique par lots. Il récupère toutes les données existantes sur la plateforme LaCAS nécessaires à cet entraînement.

Entrée : 
- Aucune entrée requise.

Sortie : 
- Un fichier JSON (stocké dans la variable `json_output`) contenant toutes les données nécessaires pour l'entraînement à l'indexation.
- Un fichier CSV (stocké dans la variable `csv_output`) contenant les données prêtes pour l'entraînement à l'indexation. La différence entre le JSON et le CSV réside dans l'ordre des données : le fichier CSV est structuré de manière optimale pour l'entraînement.

Méthodes d'utilisation :
1. `get_all_entities()` : Exécute une requête SPARQL pour récupérer tous les termes du domaine de LaCAS avec leurs présentations et leurs URI. La sortie est un dataframe contenant les termes de domaine de LaCAS.
   
2. `get_donnees_liees()` : Pour chaque terme donné, exécute une requête SPARQL afin de récupérer toutes les données liées à ce terme, qui seront indexées par lots. La sortie est un dataframe des données liées à ce terme.

3. Le reste du code associe `get_all_entities()` et `get_donnees_liees()` pour extraire toutes les données liées à chaque terme de domaine de LaCAS. Les résultats sont ensuite enregistrés dans un fichier JSON. Ensuite, avec la fonction `csv_output_result()`, on peut générer un fichier CSV.

Remarque : 
- La sortie JSON présente les données dans l'ordre dans lequel elles sont récupérées depuis LaCAS. Cela signifie que pour chaque classe (terme), les médias sont listés sous cette classe.
- Pour l'entraînement, l'objectif est d'inverser cette relation, c'est-à-dire qu'à partir d'un média donné, on veut déterminer dans quelle(s) classe(s) (terme(s)) il se trouve. Par conséquent, la sortie CSV réorganise les données pour que chaque média soit associé à sa ou ses classes correspondantes.

Exemple de sortie JSON (pour un terme) :
{
        "term": "Th\u00e9\u00e2tre fran\u00e7ais",
        "uri": "http://lacas.inalco.fr/resource/theatre_francais",
        "details": [
            {
                "media_uri": "http://www.campus-AAR.fr/segment_tel-03507924v1",
                "media_name": "The Com\u00e9die-Fran\u00e7aise and the Orient (1680-1688) : Representing the oriental world on the stage of the Gu\u00e9n\u00e9gaud Theatre and in Louis XIV's France",
                "description_value": ""
            },
            {
                "media_uri": "http://www.campus-AAR.fr/segment_tel-04156107v1",
                "media_name": "Theatrical life in northwestern France (Brittany, Loire Valley, Poitou and Aunis regions) from the 13th to the 16th century",
                "description_value": ""
            },
            {
                "media_uri": "http://www.campus-AAR.fr/segment_hal-01599910v1",
                "media_name": "Fran\u00e7ois d'Assise dans le th\u00e9\u00e2tre fran\u00e7ais et italien du XXe si\u00e8cle (Joseph Delteil, Dario Fo, Marco Baliani... et les autres)",
                "description_value": ""
            },
            {
                "media_uri": "http://www.campus-AAR.fr/segment_tel-01752024v1",
                "media_name": "The theatre of the real in France, Great Britain, and Poland: self-representations at the turn of the 21st century",
                "description_value": ""
            }
        ]
    },

Exemple de sortie CSV (pour un media) :
media_name	terms	presentations	media_uri	description_value
Ereruyk, site paléochrétien et médiéval (Chirak, Arménie) Mission Ereruyk, rapport de fouilles et d'investigations, campagne 2012 : rapport d'opération archéologique	['Art paléochrétien', 'Patrimoine culturel matériel', 'Archéologie', 'Céramique architecturale', 'Patrimoine culturel', 'Arménie', 'Études arméniennes', 'Architecture', 'Ve - XVe siècle : Moyen Âge (européen)']	Archéologie L'archéologie est une discipline scientifique dont l'objectif d'étudier l'être humain depuis la Préhistoire jusqu’à l'époque contemporaine à travers sa technique grâce l'ensemble des vestiges matériels ayant subsisté et qu’il parfois nécessaire de mettre au jour par fouille outils, ossements, poteries, armes, pièces monnaie, bijoux, vêtements, empreintes, traces, peintures, bâtiments, infrastructures, etc.. L'ensemble artéfacts écofacts relevant d'une période, civilisation, région, ou d'un peuplement donné, s'appelle culture archéologique. Cette matérielle avant tout un concept basé sur l'assemblage retrouvés dans espaces chronologies contingentes, même site, exemple. On pe science historique anthropologique étudiant les sociétés passées peut alors parler, pour désigner ensemble cohérent, archéologique comme Hallstatt, Jomon, L’archéologue, approche diachronique, acquiert donc l’essentiel documentation travaux terrain, « opposition » l’historien, principales sources sont textes. Mais l'archéologue utilise aussi documents écrits lorsque ceux-ci matériellement disponibles il faire appel aux sciences vie terre autres humaines voir ci-dessous, regroupées méthodologiquement ce qu'on appelle archéosciences l'archéométrie, l'archéologie environnementale, L'existence non textuelles anciennes a permis d'établir division chronologique spécialités archéologiques en trois grandes périodes : absence textuelles, l'Archéologie Protohistoire peuples n'ayant pas mais étant cités ceux contemporains Périodes historiques existence textuelles. Il existe spécialisations faites suivant le type d’artefacts étudiés céramiques, bâti, etc., partir matière première artefacts pierre, crue, verre, os, cuir,Architecture L'architecture intègre le domaine de la planification spatiale et met en pratique les méthodes au service l'aménagement du territoire l'urbanisme.Patrimoine culturel matériel "Le patrimoine dit « matériel » est surtout constitué des paysages construits, de l'architecture et l'urbanisme, sites archéologiques géologiques, certains aménagements l'espace agricole ou forestier, d'objets d'art mobilier, du industriel outils, instruments, machines, bâti, etc." d'aprèsPatrimoine culturel Le patrimoine culturel est, dans son sens le plus large, à la fois un produit et processus qui fournit aux sociétés ensemble de ressources héritées du passé, créées présent mises disposition pour bénéfice des générations futures. Il comprend non seulement matériel, mais aussi naturel immatériel Cf. UnescoArchéologie L'archéologie est une discipline scientifique dont l'objectif d'étudier l'être humain depuis la Préhistoire jusqu’à l'époque contemporaine à travers sa technique grâce l'ensemble des vestiges matériels ayant subsisté et qu’il parfois nécessaire de mettre au jour par fouille outils, ossements, poteries, armes, pièces monnaie, bijoux, vêtements, empreintes, traces, peintures, bâtiments, infrastructures, etc.. L'ensemble artéfacts écofacts relevant d'une période, civilisation, région, ou d'un peuplement donné, s'appelle culture archéologique. Cette matérielle avant tout un concept basé sur l'assemblage retrouvés dans espaces chronologies contingentes, même site, exemple. On peut alors parler, pour désigner ensemble cohérent, archéologique comme Hallstatt, Jomon, L’archéologue, approche diachronique, acquiert donc l’essentiel documentation travaux terrain, « opposition » l’historien, les principales sources sont textes. Mais l'archéologue utilise aussi documents écrits lorsque ceux-ci matériellement disponibles il faire appel aux sciences vie terre autres humaines voir ci-dessous, regroupées méthodologiquement ce qu'on appelle archéosciences l'archéométrie, l'archéologie environnementale, L'existence non textuelles anciennes a permis d'établir division chronologique spécialités archéologiques en trois grandes périodes : absence textuelles, l'Archéologie Protohistoire peuples n'ayant pas mais étant cités ceux contemporains Périodes historiques existence textuelles. Il existe spécialisations faites suivant le type d’artefacts étudiés céramiques, bâti, etc., partir matière première artefacts pierre, crue, verre, os, cuir, science historique anthropologique étudiant sociétés passées peVe - XVe siècle : Moyen Âge (européen) Période de l'histoire l’Occident, située entre l'Antiquité et les Temps modernes ve-xve siècles. Le Moyen Âge occidental est traditionnellement situé la chute du dernier empereur romain d'Occident 476 découverte l'Amérique 1492, même si ces deux dates sont arbitraires restent discutables. La civilisation médiévale se définit par quatre caractéristiques majeures : le morcellement l'autorité politique recul notion d'État ; une économie à dominante agricole société cloisonnée noblesse militaire, qui possède terre, classe paysanne asservie enfin, un système pensée fondé sur foi religieuse défini l'Église chrétienne.Études arméniennes Les études arméniennes sont un domaine de recherche dédié à l'étude l'Arménie, son histoire, sa culture, langue et diaspora. chercheurs spécialisés dans les adoptent une approche interdisciplinaire pour comprendre différentes dimensions l'expérience arménienne, qu'il s'agisse l'Arménie elle-même ou des communautés dispersées travers le monde. Présentation générée l'aide du chatbot , synthétisée vérifiée par l'auteur la notice 19 juin 2023Arménie L'Arménie en arménien : Հայաստան, Hayastan, forme longue la république d'Arménie Հայաստանի Հանրապետություն, Hayastani Hanrapetut’yun, est un pays sans accès à mer situé dans région du Petit Caucase, Asie occidentale. Cette ancienne socialiste soviétique a des frontières terrestres avec Turquie l'ouest, Géorgie au nord-nord-ouest, l'Azerbaïdjan l'est et l'Iran sud-est. Bien que géographiquement située Asie, l'Arménie considérée comme faisant culturellement, historiquement politiquement parlant, partie de l'Europe, voire, géographiquement, sa lisière. Le d'ailleurs considéré berceau christianisme civilisations indo-européennes. Il joué rôle historique leur diffusion. membre plus trente-cinq organisations internationales, l'ONU, le Conseil Communauté États indépendants, etc. En 2015, nouvel accord partenariat l'Union européenne été initié . État-nation unitaire, démocratique multipartite doté d'un riche héritage culturel. Héritière d'une anciennes monde, Urartu, son territoire représente seulement dixième historique. L'arrivée Armens, peuplade indo-européenne, marque constitution satrapie VIe siècle av. J.-C. Au Ier J.-C., royaume sous Tigrane Grand atteint apogée. fut première nation adopter religion d'État 301. actuelle soit constitutionnellement séculier, chrétienne y tient une place importante. IXe siècle, rétabli par dynastie bagratide. Les guerres contre les Byzantins l'affaiblirent jusqu'à chute 1045 puis l'invasion Turcs seldjoukides s'ensuivit. La principauté ensuite Cilicie perduré sur côte méditerranéenne entre XIe XIVe siècles. Entre XVIe XIXe siècles, plateau composé occidentale orientale était contrôle empires ottoman iranien respectivement. conquise l'empire russe demeura ottoman. Peu après début Première Guerre mondiale, Arméniens vivant leurs terres ancestrales furent soumis extermination systématique, génocide arménien. 1918, révolution russe, non russes déclarèrent indépendance ce qui entraîne l'établissement d'Arménie. 1920, incorporé fédérative Transcaucasie devint fondateur soviétique. 1936, transcaucasienne dissoute entraîna l'émergence indépendante 1991 lorsque s'est désintégrée. CaucaseCéramique architecturale Encycl. universalis art. : Islam La civilisation islamique - L'art et l'architecture. 2014-01-23 céramique architecturale / A. Vallet, 1982. fait référence à un mélange cuit d'argile d'eau qui peut être utilisé dans une capacité non structurelle, semi-structurelle ou structurelle l'extérieur l'intérieur d'un bâtiment. poterie en terre cuite est ancien matériau de construction. Certaines terres cuites architecturales sont du grès, plus résistant. Il vitré, peint, glacé vitrifié .Art paléochrétien art produit par les chrétiens du IIIe au VIe siècle	http://www.campus-AAR.fr/segment_halshs-00800724v1	
'''
okapi_url = 'https://lacas.inalco.fr/portals'
login = 'xshen'
passwd = '@xSh_eN56'
opener = okapi_login(okapi_url, login, passwd)
json_output = 'term_with_donnees_liees_version_add_presentations.json'
csv_output = 'corpus_multi_label_presentation_version.csv'
def get_all_entities(okapi_url, opener):
    data = []
    answer = sparql_search(okapi_url, """
        PREFIX asa: <http://campus-aar.fr/asa#>
        PREFIX core: <http://www.ina.fr/core#>
        PREFIX fr: <http://www.campus-AAR.fr/>
        SELECT DISTINCT ?entity str(?label) AS ?strLabel ?class ?subclass (GROUP_CONCAT(?presentation; SEPARATOR=" ") AS ?presentations) ?page 
        WHERE {
        ?uriclass rdfs:subClassOf fr:resource_366954895 OPTION (inference "http://campus-aar/owl") .
        ?urisubclass rdfs:subClassOf ?uriclass . 
        ?uriclass rdfs:label ?fullClass .
        ?urisubclass rdfs:label ?fullsubclass .
        ?entity a ?urisubclass OPTION (inference "http://campus-aar/owl") .
        ?entity rdfs:label ?label .
        ?entity asa:description ?presentation .
        BIND(strafter(str(?fullClass), ': ') AS ?class) .
        BIND(strafter(str(?fullsubclass), ': ') AS ?subclass) .
        BIND(IF(strstarts(str(?entity),"http://lacas.inalco.fr"),?entity,IRI(concat("https://lacas.inalco.fr/portals/api/saphir/get_resource_page?uri=",str(?entity),"&portal=http://www.campus-AAR.fr/resource_339623745"))) AS ?page)
        FILTER (?uriclass != fr:resource_645534372)
        FILTER langMatches(lang(?label), "fr")
        FILTER langMatches(lang(?presentation), "fr")
        FILTER (?uriclass != fr:resource_112574934)
        }
        GROUP BY ?entity ?label ?class ?subclass ?page
                           """, opener)
    for result in answer:
        strLabel_value = result["strLabel"]["value"]
        entity_value = result['entity']['value']
        presentations_value = result['presentations']['value']
        data.append({ "term": strLabel_value, "uri":entity_value, "presentations":presentations_value})
    df = pd.DataFrame(data)
    pattern1 = r"(Présentation générée à [ |]l'aide du chatbot ChatGPT, synthétisée et vérifiée par l'auteur de la notice le .*)"
    pattern2 = r'@[^ ]'
    pattern3 = r"(Présentation réalisée avec l'aide du chatbot ChatGBT et vérifiée par l'auteur de la notice)"
    pattern4 = r'https?://\S+|www\.\S+'
    df['term'] = df['term'].str.replace('\n', '')
    df['term'] = df['term'].str.replace('\t', '')
    df['term'] = df['term'].str.replace('\xa0', '')
    df['term'] = df['term'].str.replace('<br/>', '')
    df['term'] = df['term'].str.replace('&nbsp', '')
    df['term'] = df['term'].str.replace('<p>','')
    df['term'] = df['term'].str.replace('</p>', '')
    df['term'] = df['term'].str.replace('<em>', '')
    df['term'] = df['term'].str.replace('</em>', '')
    df['presentations'] = df['presentations'].str.replace(pattern1, '')
    df['presentations'] = df['presentations'].str.replace(r'@BNF RAMEAU', '')
    df['presentations'] = df['presentations'].str.replace(r'BNF RAMEAU', '')
    df['presentations'] = df['presentations'].str.replace('♦', '')
    df['presentations'] = df['presentations'].str.replace('http://www.tlfq.ulaval.ca.', '')
    df['presentations'] = df['presentations'].str.replace('http://www.ethnologue.com.', '')
    df['presentations'] = df['presentations'].str.replace('http://fr.wikipedia.org.', '')
    df['presentations'] = df['presentations'].str.replace('http://www.universalis-edu.com', '')
    df['presentations'] = df['presentations'].str.replace('http://www.inalco.fr.', '')
    df['presentations'] = df['presentations'].str.replace('http://www.universalis-edu.com.', '')
    df['presentations'] = df['presentations'].str.replace('http://thecanadianencyclopedia.com.', '')
    df['presentations'] = df['presentations'].str.replace('http://www.axl.cefan.ulaval.ca.', '')
    df['presentations'] = df['presentations'].str.replace('@Wikidata', '')
    df['presentations'] = df['presentations'].str.replace('Wikidata', '')
    df['presentations'] = df['presentations'].str.replace('@Dbpedia', '')
    df['presentations'] = df['presentations'].str.replace('Dbpedia', '')
    df['presentations'] = df['presentations'].str.replace('ChatGPT', '')
    df['presentations'] = df['presentations'].str.replace('I. Vintila-Radulescu', '')
    df['presentations'] = df['presentations'].str.replace('Grand Larousse universel', '')
    df['presentations'] = df['presentations'].str.replace('Encyclopédie Universalis', '')
    df['presentations'] = df['presentations'].str.replace('ChatGBT', '')
    df['presentations'] = df['presentations'].str.replace('Larousse', '')
    df['presentations'] = df['presentations'].str.replace('- . -', '')
    df['presentations'] = df['presentations'].str.replace('*', '')
    df['presentations'] = df['presentations'].str.replace(pattern2, '')
    df['presentations'] = df['presentations'].str.replace(pattern3, '')
    df['presentations'] = df['presentations'].str.replace(pattern4, '')
    df['presentations'] = df['presentations'].str.replace(r"Wikipédia",'')
    df['presentations'] = df['presentations'].str.replace(r"Wikipedia",'')
    df['presentations'] = df['presentations'].str.replace(r"(Source : DBpedia)",'')
    df['presentations'] = df['presentations'].str.replace(r'\n+', ' ', regex=True)
    df['presentations'] = df['presentations'].str.replace('\xa0', ' ')
    df['presentations'] = df['presentations'].str.replace('(','')
    df['presentations'] = df['presentations'].str.replace(')','')
    df['presentations'] = df['presentations'].str.replace('(...) ','', regex=False)
    df.fillna('', inplace=True)
    df['presentations'] = df['presentations'].apply(lambda x: ' '.join(sorted(set(x.split()), key=x.split().index)))
    return df

def get_donnees_liees(okapi_url, opener, uri):
    data = []
    answer = sparql_search(okapi_url, """
        select distinct ?s (group_concat(DISTINCT ?label_s;separator=" | ") as ?label_s) ?thumbnail (group_concat(DISTINCT ?description;separator=" | ") as ?description) where {
            Graph ?s {
                        ?a3 ?p3 <""" + uri + """>.
                        ?s a ?s_type.
            }
            Filter(?s != <""" + uri + """>)
            OPTIONAL{Graph ?s{{?s <http://www.ina.fr/core#collection> <http://campus-aar.fr/collection#AAI>.} UNION {?s <http://www.ina.fr/core#collection> ?collection.}}}
            FILTER ( !bound(?collection) )
            OPTIONAL{Graph ?s{?s <http://campus-aar.fr/asa#description> ?desc. FILTER ( lang(?desc) = "fr" || lang(?desc) = "") BIND (STR(?desc) AS ?description) }}
            OPTIONAL{?s <http://www.ina.fr/core#thumbnailUrl> ?thumbnail}
            {?s <http://www.w3.org/2000/01/rdf-schema#label> ?label_subj.FILTER ( lang(?label_subj) = "fr" || lang(?label_subj) = "")}
            UNION
            {FILTER NOT EXISTS{?s <http://www.w3.org/2000/01/rdf-schema#label> ?lang_not_exist.FILTER ( lang(?lang_not_exist) = "fr" || lang(?lang_not_exist) = "") } ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label_subj.}
            UNION {?s_type rdfs:label ?label_subj. FILTER NOT EXISTS{?s rdfs:label ?rdfsLabel_3} FILTER ( lang(?label_subj) = "fr" || lang(?label_subj) = "")}
            FILTER NOT EXISTS{ Graph <""" + uri + """> {<""" + uri + """> ?p ?s.} }
            BIND (STR(?label_subj) AS ?label_s)} offset 0 limit 200""", opener)
    for result in answer:
        if result : 
            media_uri = result["s"]["value"]
            media_name = result['label_s']['value']
            description_value = result['description']['value']
            data.append({ "media_uri": media_uri, "media_name":media_name, "description_value":description_value})
    if data: 
        df = pd.DataFrame(data)
        df['media_name'] = df['media_name'].str.replace('\n', '')
        df['media_name'] = df['media_name'].str.replace('\t', '')
        df['media_name'] = df['media_name'].str.replace('\xa0', '')
        df['media_name'] = df['media_name'].str.replace('<br/>', '')
        df['media_name'] = df['media_name'].str.replace('&nbsp', '')
        df['media_name'] = df['media_name'].str.replace('<p>','')
        df['media_name'] = df['media_name'].str.replace('</p>', '')
        df['media_name'] = df['media_name'].str.replace('<em>', '')
        df['media_name'] = df['media_name'].str.replace('</em>', '')
        return df

def convert_csv():
    df = pd.read_csv('indexation_par_lot.csv', sep=';', encoding='utf-8')
    df = df.sort_values(by='entity')
    df.to_csv('sorted_indexation_par_lot.csv', sep=';', encoding='utf-8')

def json_result_output() :
    df_terms = get_all_entities(okapi_url, opener)
    json_structure = []
    for _, values in df_terms.iterrows():
        term, uri, presentations = values
        df_donnees_liees = get_donnees_liees(okapi_url, opener, uri)
        try:
            df_donnees_liees_dict = df_donnees_liees.to_dict(orient='records')
            entry = {
                'term': term,
                'uri': uri,
                'presentations': presentations,
                'details': df_donnees_liees_dict
            }
            json_structure.append(entry)
        except AttributeError:
            continue
    json_result = json.dumps(json_structure, indent=4)
    with open(json_output, 'w', encoding='utf-8') as file:
        file.write(json_result)

def csv_result_output():
    with open (json_output, 'r', encoding='utf-8') as file:
        data_list = json.load(file)

    for element in data_list:
        if 'presentations' in element:
            element['presentations'] = f"{element['term']} {element['presentations']}"
        else:
            element['presentations'] = f"{element['term']}"
    terms_by_label = defaultdict(lambda: defaultdict(set))
    for item in data_list:
        for detail in item['details']:
            label_s = detail['media_name']
            terms_by_label[label_s]['terms'].add(item['term'])
            terms_by_label[label_s]['presentations'].add(item['presentations'])
            terms_by_label[label_s]['media_uri'].add(detail['media_uri'])
            terms_by_label[label_s]['description_value'].add(detail['description_value'])

    data_for_df = []
    for label_s, details in terms_by_label.items():
        data_for_df.append({
            'media_name': label_s,
            'terms': list(details['terms']),
            'presentations': ''.join(details['presentations']),
            'media_uri': ''.join(details['media_uri']),
            'description_value': ''.join(details['description_value'])
        })

    df = pd.DataFrame(data_for_df)
    print(df)
    df.to_csv(csv_output, encoding='utf-8', sep=' ', index=False)

json_result_output()
csv_result_output()
