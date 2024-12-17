import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import classification_report

'''
Fonction : Ce programme calcule le F1-score entre les annotations humaines et les prédictions des modèles de machine.

Entrée : 
- Un fichier CSV contenant plusieurs colonnes, où chaque colonne correspond soit aux annotations humaines (ex: human1, human2), soit aux prédictions de différents modèles de machine (ex: llama_0_shot, gpt_0_shot, mistral_0_shot, llama_1_shot... jusqu'à 2 shots).

Sortie : 
- Un rapport de classification contenant les métriques de performance, notamment l'Accuracy et le F1-score pour chaque modèle comparé aux annotations humaines.

'''
df = pd.read_csv('result_expe_final/all_labels_0_1_2_shots_version_final.csv', encoding='utf-8')

def clean_labels(label_series):
    return label_series.apply(lambda x: x.split(', ') if pd.notnull(x) and x != '' else [])

for col in df.columns:
    df[col] = clean_labels(df[col]) 
def calculate_f1(true_labels, pred_labels):
    true_labels = df[true_labels]
    pred_labels = df[pred_labels]
    mlb = MultiLabelBinarizer()
    true_labels_binary = mlb.fit_transform(true_labels)
    pred_labels_binary = mlb.transform(pred_labels)

    report = classification_report(true_labels_binary, pred_labels_binary, target_names=mlb.classes_, zero_division=0)
    return report

print(calculate_f1('humain 2', 'bert'))

