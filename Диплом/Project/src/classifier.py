import torch
import torch.nn as nn
import numpy as np
import pickle
import time
from transformers import AutoModel, AutoTokenizer
from pathlib import Path
from chonkie import TokenChunker

chunker_tool = TokenChunker(
    chunk_size=512,
    chunk_overlap=50
)


# Нейросеть
class SimpleNet(nn.Module):
    def __init__(self, input_size=768, num_classes=11):
        super().__init__()
        self.layer1 = nn.Linear(input_size, 512)
        self.bn1 = nn.BatchNorm1d(512)
        self.layer2 = nn.Linear(512, 256)
        self.bn2 = nn.BatchNorm1d(256)
        self.layer3 = nn.Linear(256, 128)
        self.bn3 = nn.BatchNorm1d(128)
        self.layer4 = nn.Linear(128, num_classes)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        x = self.relu(self.bn1(self.layer1(x)))
        x = self.dropout(x)
        x = self.relu(self.bn2(self.layer2(x)))
        x = self.dropout(x)
        x = self.relu(self.bn3(self.layer3(x)))
        x = self.dropout(x)
        x = self.layer4(x)
        return x


# Главный класс
class ArticleClassifier:
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # Пути к моделям
        models_dir = Path(__file__).parent.parent / 'models'

        # Загрузка RuBERT
        rubert_path = models_dir / 'rubert_model'
        self.tokenizer = AutoTokenizer.from_pretrained(str(rubert_path))
        self.embedding_model = AutoModel.from_pretrained(str(rubert_path))
        self.embedding_model.to(self.device)
        self.embedding_model.eval()

        # Загрузка классификатора
        checkpoint = torch.load(models_dir / 'final_article_classifier.pth',
                                map_location=self.device)
        self.classifier = SimpleNet(
            input_size=checkpoint['input_size'],
            num_classes=checkpoint['num_classes']
        )
        self.classifier.load_state_dict(checkpoint['model_state_dict'])
        self.classifier.to(self.device)
        self.classifier.eval()

        with open(models_dir / 'class_mapping.pkl', 'rb') as f:
            self.class_mapping = pickle.load(f)
        self.id_to_class = {v: k for k, v in self.class_mapping.items()}
        self.class_names = list(self.class_mapping.keys())  # список для БД

    def get_embedding(self, text):
        chunks = chunker_tool(text)
        print('Создали чанки')
        chunk_embeddings = []
        n = len(chunks)
        print(n)

        for i in range(min(n, 100)):
            inputs = self.tokenizer(str(chunks[i]), return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self.embedding_model(**inputs)
                embedding = torch.mean(outputs.last_hidden_state, dim=1)
                chunk_embeddings.append(embedding.cpu().numpy())

            print(f'Обработали {i}-й чанк')

        return np.mean(chunk_embeddings, axis=0)

    def predict(self, text):
        start = time.time()
        embedding = self.get_embedding(text)
        tensor = torch.FloatTensor(embedding).to(self.device)

        with torch.no_grad():
            outputs = self.classifier(tensor)
            probs = torch.softmax(outputs, dim=1)
            class_id = torch.argmax(probs, dim=1).item()

        result = self.id_to_class[class_id]
        proc_time = time.time() - start

        return result, proc_time
