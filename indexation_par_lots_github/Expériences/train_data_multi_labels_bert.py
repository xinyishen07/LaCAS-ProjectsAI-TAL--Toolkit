from transformers import AutoTokenizer, AutoModelForSequenceClassification, LlamaForSequenceClassification, TrainingArguments, Trainer, RobertaForSequenceClassification
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
import pandas as pd
import ast
import torch
from sklearn.metrics import classification_report, multilabel_confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

'''
Fonction : Ce programme entraîne les données avec un modèle choisi (le modèle par défaut est BERT).

Entrée : 
- Le corpus au format CSV, qui est la sortie du programme `split_corpus.py`.

Sortie : 
- Un fichier de rapport de F1-score contenant les résultats de l'entraînement.

Méthodes d'utilisation :
- Le programme prend en entrée le corpus CSV et utilise le modèle BERT (par défaut) pour entraîner les données.
- Le fichier de rapport contient F1-score et les performances du modèle après l'entraînement.

'''

# https://github.com/dtolk/multilabel-BERT/blob/master/notebooks/multi_label_text_classification_BERT.ipynb
torch.cuda.empty_cache()
# modelname = 'google-bert/bert-base-uncased'
modelname = 'google-bert/bert-large-uncased'
# modelname = 'FacebookAI/roberta-large'
filename = 'corpus_presentation_10_class_final.csv'
num_labels = 10
report_file = 'result_expe_final/10_class_bert_report.txt'

# prepare the data
data = pd.read_csv(filename, encoding='utf-8', sep=' ')
data['filtered_terms'] = data['filtered_terms'].apply(ast.literal_eval)
data['label'] = data['filtered_terms']
mlb = MultiLabelBinarizer()
labels = mlb.fit_transform(data['label'])
df = pd.concat([data[['description']], pd.DataFrame(labels)], axis=1)
df.columns = ['description'] + list(mlb.classes_)

class UrduThreatDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()} # 这行代码的作用是从编码字典self.encodings中提取出索引为idx的样本的所有编码信息，并将这些信息转换为张量格式，然后把这些张量存储在一个新的字典item中。这样，item字典就包含了单个样本的所有必要信息，便于后续的模型训练和评估过程。
        item['labels'] = torch.tensor(self.labels.iloc[idx].values, dtype=torch.float)
        return item

    def __len__(self):
        return len(self.labels)

X = df['description'].tolist() 
Y = df.drop('description', axis=1)
train_texts, test_texts, train_labels, test_labels = train_test_split(X, Y, test_size=.2, shuffle=True)
test_labels_np = test_labels.to_numpy()
test_labels_list = mlb.inverse_transform(test_labels_np)

df_test = pd.DataFrame({'text': test_texts,
                        'label': test_labels_list})

tokenizer = AutoTokenizer.from_pretrained(modelname, model_max_length=250)
# tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForSequenceClassification.from_pretrained(modelname, num_labels=num_labels)
# model = LlamaForSequenceClassification.from_pretrained(modelname, num_labels=num_labels)
train_encodings = tokenizer(train_texts, truncation=True, padding=True)
train_dataset = UrduThreatDataset(train_encodings, train_labels)

test_encodings = tokenizer(test_texts, truncation=True, padding=True)
test_dataset = UrduThreatDataset(test_encodings, test_labels)

training_args = TrainingArguments(
    output_dir='./resultsA',
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=10,
    weight_decay=0.01,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    tokenizer=tokenizer,
)

trainer.train()
numpredictions = trainer.predict(test_dataset).predictions

threshold = 0.5

testpreds_binary = (numpredictions > threshold).astype(int)
testpreds_list = mlb.inverse_transform(testpreds_binary)
df_test['predicted labels'] = testpreds_list
df_test.to_csv('result_expe_final/test_10_classes_bert.csv', encoding='utf-8', sep='\t')
report = classification_report(test_labels_np, testpreds_binary, target_names=list(mlb.classes_))
print(report)
with open(report_file, 'w') as file:
    file.write(report)