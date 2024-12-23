# Tâches IA du projet LaCAS

## Introduction LaCAS

**LaCAS - une plateforme web dédiée à la collecte, au traitement et à la valorisation des études aréales**

LaCAS comprend deux portails:

1. Le portail LaCAS Data. LaCAS Data est réservé au moissonnage et au traitement (analyse, indexation, structuration...) des données de recherche. Le fonctionnement de ce portail repose sur le logiciel OKAPI ("Open Knowledge Annotation and Publishing Interface").
2. Le portail LaCAS Publications. LaCAS Publications est réservé aux projets de publication, de communication et de valorisation des données qu'on peut trouver sur LaCAS Data. Ce portail utilise la technologie du CMS Drupal.

<p align="right">cité par le site LaCAS Publication : https://lacas.inalco.fr/la-plateforme-lacas</p>

## Présentation des tâche IA au sein de LaCAS

Les tâches d'Intelligence Artificielle (IA) dans le cadre du projet LaCAS se divisent en deux grandes missions principales :

1. Transcription automatique des contenus multimédias
   Cette tâche consiste à convertir automatiquement les entretiens et autres vidéos en texte à l'aide de l'outil [Whisper](https://github.com/openai/whisper). Une fois les transcriptions générées, elles sont importées automatiquement dans la base de données LaCAS pour enrichir les ressources disponibles.
  Répertoire des programmes : Transcription_automatique_whisper
2. Indexation automatique par lots
   Cette mission utilise [GPT-4](https://openai.com/index/gpt-4/) pour réaliser une classification automatique multi-label des contenus. Ce processus permet de classer les ressources de manière efficace et précise, selon plusieurs catégories pertinentes identifiées par les équipes du projet.
  Répertoire des programmes : Indexation_par_lot_github

## Strcture du projet

Les programmes associés à chaque mission sont regroupés dans leurs répertoires respectifs. Chaque dossier contient :

1. Le code source des programmes.
2. Un fichier README spécifique décrivant le fonctionnement et l'utilisation des scripts.
