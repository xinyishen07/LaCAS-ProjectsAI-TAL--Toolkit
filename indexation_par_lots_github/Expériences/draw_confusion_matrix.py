import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MultiLabelBinarizer
'''
Fonction : Ce programme génère des matrices de confusion à partir des prédictions des machines et des annotations humaines.

Entrée : 
- Un fichier CSV contenant plusieurs colonnes, où chaque colonne correspond soit aux annotations humaines (ex: human1, human2), soit aux prédictions de différents modèles de machine (ex: llama_0_shot, gpt_0_shot, mistral_0_shot, llama_1_shot... jusqu'à 2 shots).
- La variable `true_label` qui désigne la colonne des annotations humaines servant de vérité terrain.
- La variable `predicted_label` qui désigne la colonne des prédictions des machines.

Sortie : 
- Une matrice de confusion basée sur les variables sélectionnées (`true_label` et `predicted_label`).

Méthodes d'utilisation :
- Le programme prend en entrée les annotations humaines comme référence et les compare aux prédictions des machines pour générer une matrice de confusion qui permet de visualiser la performance des modèles.
'''

true_label = 'humain 2'
predicted_label = 'mistral_1_shot'

file_path = 'result_expe_final/all_labels_0_1_2_shots_version_final.csv' 
data = pd.read_csv(file_path, encoding='utf-8')
empty_label = 'None'

data[true_label] = data[true_label].apply(lambda x: x.split(', ') if pd.notna(x) and x else [empty_label])
data[predicted_label] = data[predicted_label].apply(lambda x: x.split(', ') if pd.notna(x) and x else [empty_label])

mlb = MultiLabelBinarizer()
y_true = mlb.fit_transform(data[true_label])
y_pred = mlb.transform(data[predicted_label])

labels = mlb.classes_
if empty_label in labels:
    none_index = list(labels).index(empty_label)
    labels = np.delete(labels, none_index)
    y_true = np.delete(y_true, none_index, axis=1)
    y_pred = np.delete(y_pred, none_index, axis=1)

n_labels = len(labels)
combined_cm = np.zeros((n_labels, n_labels))

# Manual calculation of TP, FN, FP for each label
for i in range(n_labels):
    for j in range(n_labels):
        if i == j:
            combined_cm[i, j] = np.sum((y_true[:, i] == 1) & (y_pred[:, j] == 1))  # TP
        else:
            combined_cm[i, j] += np.sum((y_true[:, i] == 1) & (y_pred[:, j] == 1))  # FP for predicted label
            combined_cm[i, j] += np.sum((y_true[:, j] == 1) & (y_pred[:, i] == 1))  # FN for true label

fig, ax = plt.subplots(figsize=(14, 10))
cax = ax.matshow(combined_cm, cmap=plt.cm.Blues)
fig.colorbar(cax)

ax.set_xticks(np.arange(len(labels)))
ax.set_yticks(np.arange(len(labels)))
ax.xaxis.set_label_position('bottom')
ax.xaxis.tick_bottom()
ax.set_xticklabels(labels, rotation=45, ha='right', rotation_mode='anchor')
ax.set_yticklabels(labels, rotation=45, ha='right', rotation_mode='anchor')

plt.xlabel('Prédiction', fontsize=12)
plt.ylabel('Vrai', fontsize=12)

for (i, j), val in np.ndenumerate(combined_cm):
    ax.text(j, i, f'{val:.2f}', ha='center', va='center', color='white')

plt.title('Matrice de Confusion du Mistral 1 coup', fontsize=14)
plt.tight_layout()
plt.show()
