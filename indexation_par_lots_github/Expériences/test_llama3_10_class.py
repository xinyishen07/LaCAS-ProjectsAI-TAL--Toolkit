import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer

'''
Fonction : Ce programme évalue la performance du modèle LLAMA3 en utilisant les données de test issues de l'entraînement du modèle BERT (fichier généré par `train_data_multi_labels.py`).

Entrée : 
- Un fichier CSV contenant les données de test utilisées pour l'entraînement de BERT.

Sortie : 
- `result_output` : Un fichier TXT contenant les réponses générées par LLAMA3.
- `file_output` : Un fichier CSV contenant les données de test ainsi que les résultats prédits par LLAMA3, montrant comment le modèle a classé chaque donnée.

Méthodes d'utilisation :
- Le programme prend les données de test du modèle BERT, les utilise pour évaluer LLAMA3, puis enregistre les prédictions de Mistral AI.

Remarque : Par défault, ce programme n'évalue que 10 classes, définies dans la variable `list_class`.
'''

file_test = 'result_expe_final/test_10_classes_bert.csv'
file_output = 'result_expe_final/test_10_classes_llama3_1_shots_mauvais_classes.csv'
result_output = 'result_expe_final/output_llama3_1_shots_mauvais_classes.txt'
df = pd.read_csv(file_test, encoding='utf-8', sep='\t')
df = df.drop('predicted labels', axis=1)
titles = df['text'].tolist()
test_labels = df['label'].tolist()

list_class = ['Études indiennes (Indologie)', 'Études japonaises', 'Études mexicaines' , 'Études russes', 'Anthropologie', 'Linguistique' , 'Architecture', 'Archéologie', 'Littératures du monde', 'Etudes cinématographiques']

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
model_id = 'unsloth/llama-3-8b-Instruct-bnb-4bit'
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, torch_dtype="auto", device_map="auto" )

def generate_prompt(title):
    texts = """Classifiez un texte à une ou plusieurs catégories correspondantes. \
    Les catégories sont 'Études indiennes (Indologie)', 'Études japonaises', 'Études mexicaines' , 'Études russes', 'Anthropologie', 'Linguistique' , 'Architecture', 'Archéologie', 'Littératures du monde', 'Etudes cinématographiques' \
    Si le texte correspond uniquement à une catégorie, répondez directement le nom de cette catégorie\
    Si le texte correspond à plusieurs catégories, répondez directement avec les noms des catégories séparés par des ',' \ \
    Par exemple : Centre de recherche berbère (CRB - équipe du LACNAD, EA 4092)Le Centre de recherche berbère (CRB) est un pôle de recherche en linguistique descriptive, historique et appli­quée berbère, en littérature berbère et anthropologie culturelle du monde berbère, s'appuyant sur la seule et la plus ancienne structure universitaire d'enseignement complète du berbère existant en France et en Europe (du premier au troisième cycle). Fondé en 1992 à l'Inalco en tant qu'équipe d'accueil (EA 3577), le CRB intègre en 2006 le laboratoire Langues et Cultures du Nord de l’Afrique et Diasporas (LACNAD, EA 4092). Ses activités s'organisent autour de trois axes : linguistique berbère, littérature berbère, culture et société berbères.\
    Réponse : Anthropologie \
    Le texte est '{}'. """.format(title)
    messages = [{"role": "user", "content": texts}]
    return messages

model.eval()
total_predict_labels = []
for title in titles :
    predict_labels = []
    messages = generate_prompt(title)
    input_ids = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
    outputs = model.generate( input_ids,
      max_new_tokens=1200,
      do_sample=True,
      temperature=0.6,
      top_p=0.9,)
    response = outputs[0][input_ids.shape[-1]:]
    response = tokenizer.decode(response, skip_special_tokens=True)
    with open(result_output, 'a+', encoding='utf-8') as file:
        file.write(str(response))
        file.write('\n\n')
    for label in list_class:
        if label in response:
            predict_labels.append(label)
    total_predict_labels.append(predict_labels)
df['predicted_labels'] = total_predict_labels
df.to_csv(file_output, encoding='utf-8', sep='\t')
'''
mlb = MultiLabelBinarizer()

Y_true = mlb.fit_transform(test_labels)
Y_pred = mlb.transform(total_predict_labels)

labels_names = mlb.classes_

print(classification_report(Y_true, Y_pred, target_names=labels_names))'''