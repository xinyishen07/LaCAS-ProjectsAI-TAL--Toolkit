# READ ME
Ce projet vise à optimiser et automatiser le processus d'indexation par lots sur la plateforme LaCAS, en utilisant une classification multi-label.

Pour en savoir plus sur le concept d'indexation par lots, consultez le billet suivant : : [Réaliser une indexation par lots de données](https://lacas.hypotheses.org/3007).

## Phases du Projet
Le projet se décompose en deux grandes phases :

**Expériences** : Choix du modèle et des classes

**Réalisation** : Automatisation des processus

## Expériences
Nous avons testé 4 modèles : BERT, GPT-4, LLAMA3 et Mistral AI. L'ensemble des programmes et configurations associés sont disponibles dans le répertoire "Expériences".

Pour plus de détails sur les expériences menées et les résultats obtenus : 

[Les grands modèles de langue dans les études aréales : une présentation de l’équipe LaCAS aux JEP TALN RECITAL 2024](https://lacas.hypotheses.org/2227)

[Évaluation de grands modèles de langue pour la classification de concepts et la génération de descriptions dans les études aréales](https://hal.science/hal-04678037v1)

### Préparation des données
**initial_data_me conpreparation_indexation_par_lots.py** : Ce programstitue la première étape de la préparation des données pour l'entraînement de l'indexation automatique par lots. Il récupère toutes les données existantes sur la plateforme LaCAS nécessaires à cet entraînement.

**split_corpus.py** : Ce programme prend deux sorties du initial_data_preparation_indexation_par_lots.py et prépare un corpus pour l'entraînement de classification multi-label.

### Entraînement et Test
**train_data_multi_labels_bert.py** : Ce programme entraîne les données avec un modèle choisi (le modèle par défaut est BERT).

**test_gpt4_10_class.py** :  Ce programme évalue la performance du modèle GPT4 en utilisant les données de test issues de l'entraînement du modèle BERT (fichier généré par `train_data_multi_labels.py`).

**test_llama3_10_class.py** : Ce programme évalue la performance du modèle LLAMA3 en utilisant les données de test issues de l'entraînement du modèle BERT (fichier généré par `train_data_multi_labels.py`).

**test_mistral_10_class.py** : Ce programme évalue la performance du modèle Mistral AI en utilisant les données de test issues de l'entraînement du modèle BERT (fichier généré par `train_data_multi_labels.py`).

### Evaluation

**calculate_accord.py** : Ce programme calcule l'accord de Krippendorff entre les machines, entre les humains, et entre les machines et les humains.

**calculate_f1score.py** : Ce programme calcule le F1-score entre les annotations humaines et les prédictions des modèles de machine.

**draw_confusion_matrix.py** : Ce programme génère des matrices de confusion à partir des prédictions des machines et des annotations humaines.

## Réalisation
