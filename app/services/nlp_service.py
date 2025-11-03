import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from typing import List, Dict

class NlpService:
    def __init__(self):
        # 假设你已经创建了 nlp_training_data.json
        try:
            with open("nlp_training_data.json", "r", encoding="utf-8") as f:
                training_data = json.load(f)
        except FileNotFoundError:
            print("警告: 未找到 nlp_training_data.json，NLP句子分类器将使用默认数据。")
            training_data = [ # 放一些默认数据以防文件不存在
                {"text": "symptoms appear on leaves", "label": "symptom"},
                {"text": "use fungicide to treat", "label": "treatment"},
                {"text": "our privacy policy", "label": "other"}
            ]

        X_train = [item["text"] for item in training_data]
        y_train = [item["label"] for item in training_data]

        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words='english')),
            ('clf', LinearSVC()),
        ])

        print("正在训练自研NLP句子分类模型...")
        self.pipeline.fit(X_train, y_train)
        print("✅ NLP模型训练完成。")

    def extract_key_info(self, full_text: str) -> Dict[str, List[str]]:
        """
        从长文本中提取'症状'和'防治方法'的关键句子。
        """
        if not full_text:
            return {"symptoms": [], "treatments": []}

        sentences = full_text.split('\n') # 基于我们之前的清理，按行分割
        predictions = self.pipeline.predict(sentences)
        
        extracted_info = {"symptoms": [], "treatments": []}
        for sentence, label in zip(sentences, predictions):
            if label == "symptom":
                extracted_info["symptoms"].append(sentence)
            elif label == "treatment":
                extracted_info["treatments"].append(sentence)
        
        return extracted_info

# 创建全局实例
nlp_service = NlpService()