# READ ME
L’objectif de ce programme est d’ajouter des sous-titres aux entretiens sur la plateforme LaCAS, incluant les entretiens PEA, I-DEA et d'autres.

## Le processus comprend trois étapes principales :
1. Récupération des entretiens : D'abord, la liste des entretiens nécessitant des sous-titres ainsi que leurs informations complémentaires est récupérée via le serveur Okapi de LaCAS. 
2. Transcription automatique : Ensuite, des transcriptions sont générées à l'aide de Whisper (https://openai.com/index/whisper/ ), un modèle avancé de reconnaissance vocale automatique.
3. Vérification et importation : Enfin, une vérification manuelle est réalisée par les collègues de LaCAS. Les transcriptions corrigées sont ensuite importées sur la plateforme.

## Explications pour chaque fichier Python :
get_transcription_whisper.py : Ce programme transcrit une liste de vidéos provenant du projet LaCAS en utilisant le modèle Whisper.

Client Whipser Okapi.py : Ce programme importe les transcriptions de vidéos sur la plateforme LaCAS après leur traitement.

json_to_txt_transcription_converter.py : Ce programme permet de faciliter la correction manuelle des transcriptions en effectuant deux actions :
1) Transformer les fichiers JSON en fichiers TXT en ne conservant que la timeline et la transcription. 
2) Renommer les fichiers (passer de l'URI à un nom de vidéo compréhensible).

new_client_whisper.py : Ce programme permet de réimporter les transcriptions corrigées sur la plateforme LaCAS après les modifications manuelles.

get_transcription_whisper_version_app.py : Ce programme propose une interface utilisateur permettant de transcrire une liste de vidéos provenant du projet LaCAS en utilisant le modèle Whisper et d'importer des transcriptions sur la plateforme LaCAS.

delete_transcription_whisper_version_app.py : Ce programme propose une interface utilisateur permettant de enlever une transcription de vidéo sur LaCAS.
