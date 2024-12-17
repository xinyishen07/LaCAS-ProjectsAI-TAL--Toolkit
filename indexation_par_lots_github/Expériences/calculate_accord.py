import pandas as pd
from nltk.metrics.agreement import AnnotationTask
from nltk.metrics import masi_distance

'''
Fonction : Ce programme calcule l'accord de Krippendorff entre les machines, entre les humains, et entre les machines et les humains.

Entrée : 
- Un fichier CSV contenant plusieurs colonnes, où chaque colonne correspond soit aux annotations humaines (ex: human1, human2), soit aux prédictions de différents modèles de machine (ex: llama_0_shot, gpt_0_shot, mistral_0_shot, llama_1_shot... jusqu'à 2 shots).

Sortie : 
- Un fichier CSV contenant les résultats de l'accord de Krippendorff entre les différents annotateurs (humains et machines).

Méthodes d'utilisation :
- Le programme compare les différentes annotations, qu'elles soient humaines ou générées par les machines, et calcule l'accord de Krippendorff pour évaluer le niveau de consensus entre chaque groupe (humains, machines, ou mélange des deux).
'''

df = pd.read_csv('result_expe_final/all_labels_0_1_2_shots_version_final.csv', encoding='utf-8')

def clean_labels(label_series):
    return label_series.apply(lambda x: x.split(', ') if pd.notnull(x) and x != '' else [0])

for col in df.columns:
    df[col] = clean_labels(df[col]) 

def calculate_labels_krippendorffs(labels1, labels2):
    task_data = []
    for idx, row in df.iterrows():
        item = f'Item{idx}'
        coder1_data = (labels1, item, frozenset(row[labels1]))
        coder2_data = (labels2, item, frozenset(row[labels2]))
        task_data.extend([coder1_data, coder2_data])
    task = AnnotationTask(distance = masi_distance)
    task.load_array(task_data)
    return task.alpha()

results_df = pd.DataFrame(columns=['Labels1', 'Labels2', 'Krippendorff_Alpha'])
lst = df.columns.tolist()
for i in range(len(lst)):
    for j in range(i+1, len(lst)):
        labels1 = lst[i]
        labels2 = lst[j]
        print(f"Calculating Krippendorff's alpha for {labels1} and {labels2}")
        result = calculate_labels_krippendorffs(labels1, labels2)
        print(f"Result for {labels1} and {labels2}: {result}")
        new_row = pd.DataFrame({
            'Labels1': [labels1],
            'Labels2': [labels2],
            'Krippendorff_Alpha': [result]
        })
        results_df = pd.concat([results_df, new_row], ignore_index=True)

results_df.to_csv('result_expe_final/krippendorff_results_0_1_2_shots.csv', encoding='utf-8', index=False)