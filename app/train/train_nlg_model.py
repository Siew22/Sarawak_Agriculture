# train/train_nlg_model.py
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import json
from tqdm import tqdm

# --- 配置 ---
TRAINING_DATA_PATH = 'knowledge_base/nlg_training_data.json'
MODEL_SAVE_PATH = 'models_store/self_trained_nlg_core.pth'
NUM_EPOCHS = 100
EMBEDDING_DIM = 64 # 向量维度
HIDDEN_DIM = 128

# 1. 创建我们的词汇表和数据集
class SentenceDataset(Dataset):
    def __init__(self, data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        all_sentences = []
        for item in self.data:
            all_sentences.extend([item['anchor'], item['positive'], item['negative']])
        
        # 构建词汇表
        self.word_to_idx = {"<PAD>": 0, "<UNK>": 1}
        for sentence in all_sentences:
            for word in sentence.split():
                if word not in self.word_to_idx:
                    self.word_to_idx[word] = len(self.word_to_idx)
        
        # 保存词汇表，以便推理时使用
        vocab_path = os.path.join(os.path.dirname(MODEL_SAVE_PATH), 'nlg_vocab.json')
        with open(vocab_path, 'w', encoding='utf-8') as f:
            json.dump(self.word_to_idx, f, ensure_ascii=False, indent=4)

    def __len__(self):
        return len(self.data)

    def sentence_to_tensor(self, sentence):
        indices = [self.word_to_idx.get(word, 1) for word in sentence.split()]
        return torch.tensor(indices, dtype=torch.long)

    def __getitem__(self, idx):
        item = self.data[idx]
        anchor = self.sentence_to_tensor(item['anchor'])
        positive = self.sentence_to_tensor(item['positive'])
        negative = self.sentence_to_tensor(item['negative'])
        return anchor, positive, negative

# 2. 定义我们的“孪生大脑” (一个简单的LSTM编码器)
class SentenceEncoder(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim):
        super(SentenceEncoder, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        self.dropout = nn.Dropout(0.3)
    
    def forward(self, x):
        embedded = self.embedding(x)
        # 我们只需要LSTM最后一个时间步的隐藏状态作为整个句子的表示
        _, (hidden, _) = self.lstm(embedded.unsqueeze(0))
        hidden = self.dropout(hidden) # 在输出前随机“丢掉”一些信息
        return hidden.squeeze(0)

# 3. 定义训练逻辑
def train_nlg_model():
    dataset = SentenceDataset(TRAINING_DATA_PATH)
    dataloader = DataLoader(dataset, batch_size=1, shuffle=True)
    
    vocab_size = len(dataset.word_to_idx)
    encoder = SentenceEncoder(vocab_size, EMBEDDING_DIM, HIDDEN_DIM)
    
    # 使用 TripletMarginLoss，这是训练孪生网络的标准损失函数
    loss_fn = nn.TripletMarginLoss(margin=1.0, p=2)
    # 在 optimizer 定义处，加入 weight_decay
    optimizer = optim.Adam(encoder.parameters(), lr=0.001, weight_decay=1e-4)

    print("--- 开始训练自研NLG核心 ---")
    for epoch in range(NUM_EPOCHS):
        total_loss = 0
        for anchor, positive, negative in tqdm(dataloader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS}"):
            optimizer.zero_grad()
            
            anchor_vec = encoder(anchor.squeeze(0))
            positive_vec = encoder(positive.squeeze(0))
            negative_vec = encoder(negative.squeeze(0))
            
            loss = loss_fn(anchor_vec, positive_vec, negative_vec)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        print(f"Epoch {epoch+1} Loss: {total_loss / len(dataloader):.4f}")

    print("✅ 自研NLG核心训练完成！")
    # 保存整个模型（包括结构和权重）
    torch.save(encoder.state_dict(), MODEL_SAVE_PATH)
    print(f"模型已保存至: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_nlg_model()