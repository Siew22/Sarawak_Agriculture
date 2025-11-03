import torch
import torch.nn as nn
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from typing import Dict, List, Any
from pathlib import Path
import json

# 导入我们自己创建的模块
from ..schemas.diagnosis import PredictionResult, RiskAssessment, FullDiagnosisReport
from ..services.knowledge_base_service import kb_service

# 动态导入，如果失败则禁用网络搜索功能
try:
    from sentence_transformers import util
except ImportError:
    # 这个库现在只用于计算余弦相似度，我们可以自己实现一个简单的替代品
    print("⚠️ 警告: 'sentence-transformers' 未安装。将使用内置函数计算相似度。")
    util = None


# --- 关键：在这里重新定义一遍我们训练时用的模型结构！---
# Python在加载模型权重时，需要知道这个模型的“建筑图纸”。
class SentenceEncoder(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim):
        super(SentenceEncoder, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        self.dropout = nn.Dropout(0.3)
    
    def forward(self, x):
        embedded = self.embedding(x)
        _, (hidden, _) = self.lstm(embedded.unsqueeze(0))
        hidden = self.dropout(hidden)
        return hidden.squeeze(0)


class AdvancedNLGGenerator:
    def __init__(self):
        self.embedding_model = None
        self.word_to_idx: Dict[str, int] = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(">>> 正在加载自研NLG核心...")
        try:
            base_dir = Path(__file__).resolve().parent.parent.parent
            model_path = base_dir / "models_store" / "self_trained_nlg_core.pth"
            vocab_path = base_dir / "models_store" / "nlg_vocab.json"
            
            if not model_path.is_file() or not vocab_path.is_file():
                raise FileNotFoundError("自研NLG模型或词汇表文件未找到。请先运行 train_nlg_model.py。")

            with open(vocab_path, 'r', encoding='utf-8') as f:
                self.word_to_idx = json.load(f)
            
            # --- 终极的、绝对正确的模型加载方式 ---
            vocab_size = len(self.word_to_idx)
            EMBEDDING_DIM = 64
            HIDDEN_DIM = 128
            
            # 1. First, create a "blank" model structure
            self.embedding_model = SentenceEncoder(vocab_size, EMBEDDING_DIM, HIDDEN_DIM)
            
            # 2. Then, load the trained weights (state_dict) into it
            self.embedding_model.load_state_dict(torch.load(model_path, map_location=self.device))
            # --- 修复结束 ---

            self.embedding_model.to(self.device)
            self.embedding_model.eval()
            print("✅ 自研NLG核心加载完成。")

        except Exception as e:
            print(f"❌ 加载自研NLG核心失败: {e}. 网络搜索增强功能将被禁用。")
            self.embedding_model = None

    def _sentence_to_tensor(self, sentence: str) -> torch.Tensor:
        indices = [self.word_to_idx.get(word, self.word_to_idx.get("<UNK>", 1)) for word in sentence.lower().split()]
        return torch.tensor(indices, dtype=torch.long, device=self.device)

    def _get_embedding(self, text: str) -> torch.Tensor:
        tensor = self._sentence_to_tensor(text)
        with torch.no_grad():
            return self.embedding_model(tensor)

    def _cosine_similarity(self, vec1: torch.Tensor, vec2: torch.Tensor) -> float:
        if util:
            return util.cos_sim(vec1, vec2)[0].item()
        else: # 如果 sentence-transformers 没装，用PyTorch内置函数
            return nn.functional.cosine_similarity(vec1, vec2, dim=-1).item()

    def web_search_and_summarize(self, disease_name: str, lang: str) -> List[str]:
        if not self.embedding_model: return []

        print(f"🔎 正在为 '{disease_name}' 进行网络搜索增强...")
        summaries = []
        try:
            query = f"{disease_name.replace('_', ' ')} pepper plant treatment {lang}"
            search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            links = [a['href'] for a in soup.find_all('a', class_='result__a', limit=3)]
            disease_embedding = self._get_embedding(disease_name.replace("_", " "))

            for i, link in enumerate(links):
                try:
                    article = Article(link, language=lang)
                    article.download(); article.parse()
                    
                    sentences = [s.strip() for s in article.text.split('.') if len(s.strip()) > 50]
                    if not sentences: continue

                    best_sentence, max_similarity = "", -1
                    for sentence in sentences:
                        sentence_embedding = self._get_embedding(sentence)
                        similarity = self._cosine_similarity(disease_embedding, sentence_embedding)
                        if similarity > max_similarity:
                            max_similarity = similarity
                            best_sentence = sentence
                    
                    if best_sentence:
                        summaries.append(f"参考资料 #{i+1}: {best_sentence}.")
                        print(f"   - 提取到相关信息 (相似度: {max_similarity:.2f}): {best_sentence[:60]}...")
                except Exception: continue
        except Exception as e:
            print(f"   - ❌ 网络搜索失败: {e}")
        return summaries

    def generate(self, prediction: PredictionResult, risk: RiskAssessment, lang: str = 'en', confidence_threshold: float = 0.75) -> FullDiagnosisReport:
        if prediction.confidence < confidence_threshold:
            return self._generate_default_report(prediction, risk, lang)

        disease_key = prediction.disease
        base_info = kb_service.get_disease_info(disease_key)
        
        if not base_info:
            return self._generate_default_report(prediction, risk, lang)

        name_map = base_info.get("name", {})
        name_local = name_map.get(lang, name_map.get("en", disease_key))
        
        title = f"{self._get_i18n('report_title', lang)} ({name_local})"
        
        summary_map = base_info.get("summary", {})
        summary = summary_map.get(lang, summary_map.get("en", "No detailed description."))
        diagnosis_summary = f"{self._get_i18n('diagnosis_summary_label', lang)} {summary} ({self._get_i18n('confidence_label', lang)}: {prediction.confidence:.2%})"
        
        risk_text_map = {
            "High": {"en": "The current conditions are highly favorable for disease.", "ms": "Keadaan semasa sangat sesuai untuk penyakit.", "zh": "当前环境极易诱发病害。"},
            "Medium": {"en": "The environment may encourage disease development.", "ms": "Persekitaran mungkin menggalakkan perkembangan penyakit.", "zh": "当前环境可能诱发病害。"},
            "Low": {"en": "Current environmental conditions are relatively stable.", "ms": "Keadaan persekitaran semasa agak stabil.", "zh": "当前环境条件相对有利。"}
        }
        risk_text = risk_text_map.get(risk.risk_level, {}).get(lang, "")
        environmental_context = (f"{self._get_i18n('env_risk_analysis_label', lang)} {self._get_i18n('risk_level_label', lang)} {risk.risk_level} "
                                 f"({self._get_i18n('risk_score_label', lang)}: {risk.risk_score:.1f}/10). {risk_text}")
        
        management_suggestion = ""
        treatments = base_info.get("treatments", [])
        if treatments:
            management_suggestion += f"【{self._get_i18n('core_suggestion_title', lang)} (来自本地知识库)】:\n"
            for treatment in treatments:
                title_map = treatment.get("title", {})
                treatment_title = title_map.get(lang, title_map.get("en", "Suggestion"))
                management_suggestion += f"\n--- {treatment_title} ---\n"
                steps = treatment.get("steps", [])
                if steps:
                    for i, step in enumerate(steps):
                        step_map = step if isinstance(step, dict) else {"en": str(step)}
                        step_text = step_map.get(lang, step_map.get("en", ""))
                        management_suggestion += f"{i+1}. {step_text}\n"
        
        web_summaries = self.web_search_and_summarize(disease_key, lang)
        if web_summaries:
            management_suggestion += f"\n\n【{self._get_i18n('web_reference_title', lang)} (实时网络参考)】:\n"
            for web_sum in web_summaries:
                management_suggestion += f"- {web_sum}\n"
        
        if not management_suggestion:
            management_suggestion = self._get_default_suggestion(lang)

        return FullDiagnosisReport(
            title=title,
            diagnosis_summary=diagnosis_summary,
            environmental_context=environmental_context,
            management_suggestion=management_suggestion.strip(),
            xai_image_url=None # 初始化为None
        )

    def _get_i18n(self, key: str, lang: str) -> str:
        i18n_dict = {
            "report_title": {"en": "Crop Health Diagnosis Report", "ms": "Laporan Diagnosis Kesihatan Tanaman", "zh": "作物健康诊断报告"},
            "diagnosis_summary_label": {"en": "Diagnosis:", "ms": "Diagnosis:", "zh": "诊断结果:"},
            "confidence_label": {"en": "Model Confidence", "ms": "Keyakinan Model", "zh": "模型置信度"},
            "env_risk_analysis_label": {"en": "Environmental Risk Analysis:", "ms": "Analisis Risiko Persekitaran:", "zh": "环境风险分析:"},
            "risk_level_label": {"en": "Risk", "ms": "Risiko", "zh": "风险"},
            "risk_score_label": {"en": "Score", "ms": "Skor", "zh": "评分"},
            "core_suggestion_title": {"en": "Core Suggestions", "ms": "Cadangan Teras", "zh": "核心建议"},
            "web_reference_title": {"en": "Web References", "ms": "Rujukan Web", "zh": "网络参考信息"},
            "unknown_condition_title": {"en": "Uncertain Diagnosis Report", "ms": "Laporan Diagnosis Tidak Pasti", "zh": "不确定诊断报告"},
            "unknown_summary_prefix": {"en": "The model identified a condition with code", "ms": "Model telah mengenal pasti keadaan dengan kod", "zh": "模型识别出一个代号为"},
            "unknown_summary_suffix": {"en": "but the confidence is below the threshold or the disease is not in the knowledge base. Please consult an expert.", "ms": "tetapi keyakinan berada di bawah ambang atau penyakit tiada dalam pangkalan pengetahuan. Sila rujuk pakar.", "zh": "但置信度低于阈值或知识库中无此病害。请咨询专家。"}
        }
        return i18n_dict.get(key, {}).get(lang, i18n_dict.get(key, {}).get("en", f"[{key}]"))

    def _get_default_suggestion(self, lang: str) -> str:
        suggestions = {
            "en": "You are strongly advised to consult with a local agricultural extension officer for an accurate diagnosis.",
            "ms": "Anda amat dinasihatkan untuk berunding dengan pegawai pengembangan pertanian tempatan untuk diagnosis yang tepat.",
            "zh": "强烈建议您立即联系本地农业推广人员或专家进行确认。"
        }
        return suggestions.get(lang, suggestions["en"])

    def _generate_default_report(self, prediction: PredictionResult, risk: RiskAssessment, lang: str) -> FullDiagnosisReport:
        title = self._get_i18n('unknown_condition_title', lang)
        summary_prefix = self._get_i18n('unknown_summary_prefix', lang)
        summary_suffix = self._get_i18n('unknown_summary_suffix', lang)
        
        diagnosis_summary = f"{summary_prefix} '{prediction.disease}' ({self._get_i18n('confidence_label', lang)}: {prediction.confidence:.2%}). {summary_suffix}"
        
        environmental_context = (f"{self._get_i18n('env_risk_analysis_label', lang)} {self._get_i18n('risk_level_label', lang)} {risk.risk_level} "
                                 f"({self._get_i18n('risk_score_label', lang)}: {risk.risk_score:.1f}/10).")
        
        return FullDiagnosisReport(
            title=title,
            diagnosis_summary=diagnosis_summary,
            environmental_context=environmental_context,
            management_suggestion=self._get_default_suggestion(lang),
            xai_image_url=None
        )

# 创建一个全局实例
report_generator_v3 = AdvancedNLGGenerator()